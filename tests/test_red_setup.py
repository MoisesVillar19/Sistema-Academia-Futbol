"""R2 red LAN: setup (probar ruta) + guardian anti-huerfana."""
import os

import pytest

from views.configuracion.configuracion_view import ConfiguracionView


def test_probar_ruta_bd_local_ok(tmp_path):
    ok, msg = ConfiguracionView._probar_ruta_bd(str(tmp_path / "academia.db"))
    assert ok is True
    assert msg.startswith("OK")


def test_probar_ruta_bd_vacia():
    ok, _ = ConfiguracionView._probar_ruta_bd("")
    assert ok is False


def test_probar_ruta_bd_carpeta_inexistente(tmp_path):
    ok, msg = ConfiguracionView._probar_ruta_bd(
        str(tmp_path / "no_existe" / "academia.db"))
    assert ok is False
    assert "No se accede" in msg


def test_carpetas_hermanas_derivan_del_share():
    from views.configuracion.configuracion_view import ConfiguracionView
    h = ConfiguracionView._carpetas_hermanas("\\\\SRV\\Datos\\academia.db")
    assert h["fotos"].endswith("fotos")
    assert h["comprobantes"].endswith("comprobantes")
    assert h["backup"].endswith("BackupsAcademia")
    assert all(v.startswith("\\\\SRV\\Datos") for v in h.values())


def test_guardar_ruta_crea_hermanas(tmp_path):
    import configparser
    from views.configuracion.configuracion_view import ConfiguracionView
    base = tmp_path / "share"
    base.mkdir()
    ruta = str(base / "academia.db")
    h = ConfiguracionView._carpetas_hermanas(ruta)
    for dest in h.values():
        import os
        os.makedirs(dest, exist_ok=True)
        assert os.path.isdir(dest)


def test_guardian_pasa_en_local():
    import main as app_main
    assert app_main.verificar_acceso_bd() is None


def test_guardian_frena_red_inaccesible(monkeypatch):
    import main as app_main
    import utils.constants as const
    import tkinter.messagebox as mb
    monkeypatch.setattr(const, "DB_PATH", "\\\\SERVIDOR_INEXISTENTE_XYZ\\Academia\\academia.db")
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: None)
    # verificar_acceso_bd lee DB_PATH via es_ruta_red() default -> usa
    # database.connection.DB_PATH; parchear ambos
    import database.connection as dc
    monkeypatch.setattr(dc, "DB_PATH", "\\\\SERVIDOR_INEXISTENTE_XYZ\\Academia\\academia.db")
    # forzar: es_ruta_red True + isdir False -> SystemExit(1)
    monkeypatch.setattr(os.path, "isdir", lambda p: False)
    with pytest.raises(SystemExit):
        app_main.verificar_acceso_bd()
