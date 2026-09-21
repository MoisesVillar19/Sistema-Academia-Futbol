"""Tests del servicio de actualizacion (comparacion de versiones y throttling)."""
from datetime import datetime, timedelta
import pytest

from updater import update_service


def test_comparar_versiones_mayor_menor_igual():
    assert update_service.comparar_versiones("1.0.0", "1.0.1") == -1
    assert update_service.comparar_versiones("1.0.2", "1.0.1") == 1
    assert update_service.comparar_versiones("1.0.0", "1.0.0") == 0
    assert update_service.comparar_versiones("2.0.0", "1.9.9") == 1
    assert update_service.comparar_versiones("1.0", "1.0.0") == -1


@pytest.mark.parametrize("estado,esperado", [
    ({}, True),
    ({"ultima_verificacion": None}, True),
])
def test_debe_verificar_sin_estado_previo(monkeypatch, estado, esperado):
    monkeypatch.setattr(update_service, "_cargar_estado", lambda: estado)
    assert update_service.debe_verificar() is esperado


def test_debe_verificar_false_dentro_de_ventana(monkeypatch):
    reciente = (datetime.now() - timedelta(hours=1)).isoformat()
    monkeypatch.setattr(update_service, "_cargar_estado",
                        lambda: {"ultima_verificacion": reciente})
    assert update_service.debe_verificar() is False


def test_debe_verificar_true_pasada_la_ventana(monkeypatch):
    antigua = (datetime.now() - timedelta(hours=72)).isoformat()
    monkeypatch.setattr(update_service, "_cargar_estado",
                        lambda: {"ultima_verificacion": antigua})
    assert update_service.debe_verificar() is True


def test_debe_verificar_con_fecha_corrupta(monkeypatch):
    monkeypatch.setattr(update_service, "_cargar_estado",
                        lambda: {"ultima_verificacion": "no-es-fecha"})
    assert update_service.debe_verificar() is True


def test_comparar_versiones_tolerante():
    assert update_service.comparar_versiones("v1.0.7", "1.0.7") == 0
    assert update_service.comparar_versiones("1.0.7-beta", "1.0.7") == 0
    assert update_service.comparar_versiones(" 1.0.7 ", "1.0.6") == 1
    assert update_service.comparar_versiones("1.0.7", "1.0.10") == -1
    # "" → [0]: misma regla de longitud que "1.0" < "1.0.0"
    assert update_service.comparar_versiones("", "0.0.0") == -1


def test_fusionar_estado_no_pierde_claves(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(update_service, "_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(update_service, "_STATE_FILE", str(state_file))
    update_service._guardar_estado({"rechazado_version": "1.0.6", "x": 1})
    update_service._fusionar_estado({"ultima_verificacion": "hoy"})
    estado = update_service._cargar_estado()
    assert estado["rechazado_version"] == "1.0.6"
    assert estado["ultima_verificacion"] == "hoy"


def test_registrar_rechazo_y_verificacion_persisten(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(update_service, "_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(update_service, "_STATE_FILE", str(state_file))

    update_service.registrar_verificacion()
    estado = update_service._cargar_estado()
    assert "ultima_verificacion" in estado

    update_service.registrar_rechazo("9.9.9")
    estado = update_service._cargar_estado()
    assert estado["rechazado_version"] == "9.9.9"


# ── Descarga (sin red: urlopen simulado) ─────────────────────────

import io as _io
import zipfile as _zipfile


class _FakeResp:
    def __init__(self, payload: bytes, content_length=None):
        self._buf = _io.BytesIO(payload)
        self.status = 200
        self.reason = "OK"
        self.headers = {"Content-Length": str(
            len(payload) if content_length is None else content_length)}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=-1):
        return self._buf.read(n if n and n > 0 else 65536)


def _aislar(monkeypatch, tmp_path):
    monkeypatch.setattr(update_service, "_STATE_DIR", str(tmp_path / "st"))
    monkeypatch.setattr(update_service, "_STATE_FILE", str(tmp_path / "st" / "s.json"))
    monkeypatch.setattr(update_service, "_obtener_ruta_app", lambda: str(tmp_path / "app"))
    (tmp_path / "app").mkdir(exist_ok=True)


def test_descarga_truncada_falla(monkeypatch, tmp_path):
    _aislar(monkeypatch, tmp_path)
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("VERSION", "1.0.7")
    payload = buf.getvalue()
    # ZIP válido pero Content-Length mayor → truncado en tránsito
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout=60: _FakeResp(payload, content_length=len(payload) + 100))
    ok = update_service.descargar_y_actualizar("http://x/AcademiaFutbol-v1.0.7.zip")
    assert ok is False
    assert "truncada" in update_service.ultimo_error


def test_descarga_cancelada_aborta_y_limpia(monkeypatch, tmp_path):
    _aislar(monkeypatch, tmp_path)
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout=60: _FakeResp(b"z" * 200000))
    llamadas = {"n": 0}

    def _cancelar():
        llamadas["n"] += 1
        return llamadas["n"] > 1

    ok = update_service.descargar_y_actualizar(
        "http://x/AcademiaFutbol-v1.0.7.zip", debe_cancelar=_cancelar)
    assert ok is False
    assert "cancelada" in update_service.ultimo_error
    assert list((tmp_path / "app").iterdir()) == []


def test_descarga_zip_ok_preserva_config_y_db(monkeypatch, tmp_path):
    _aislar(monkeypatch, tmp_path)
    app = tmp_path / "app"
    (app / "config.ini").write_text("MIO", encoding="utf-8")
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("VERSION", "1.0.7")
        zf.writestr("config.ini", "NUEVO")
        zf.writestr("database/academia.db", "BINARIO")
        zf.writestr("../evil.txt", "x")
    payload = buf.getvalue()
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout=60: _FakeResp(payload))
    ok = update_service.descargar_y_actualizar("http://x/AcademiaFutbol-v1.0.7.zip")
    assert ok, update_service.ultimo_error
    assert (app / "VERSION").read_text(encoding="utf-8") == "1.0.7"
    assert (app / "config.ini").read_text(encoding="utf-8") == "MIO"
    assert not (app / "database" / "academia.db").exists()
    assert not (tmp_path / "evil.txt").exists()
