"""Fase 3: validación visible de imágenes + centralización de comprobantes."""
import os

from utils.imagenes import validar_imagen, extension_real


def _png(path, size=(10, 10), color="red"):
    from PIL import Image
    Image.new("RGB", size, color).save(path)


def test_validar_inexistente_y_vacio(tmp_path):
    ok, msg = validar_imagen(str(tmp_path / "no.jpg"))
    assert ok is False and "encontrado" in msg
    v = tmp_path / "vacio.jpg"
    v.write_bytes(b"")
    ok, msg = validar_imagen(str(v))
    assert ok is False and "vacío" in msg


def test_validar_tamano(tmp_path):
    g = tmp_path / "grande.jpg"
    g.write_bytes(b"0" * (2 * 1024 * 1024 + 1))
    ok, msg = validar_imagen(str(g), max_mb=2)
    assert ok is False and "MB" in msg


def test_validar_extension(tmp_path):
    t = tmp_path / "doc.txt"
    t.write_text("hola")
    ok, msg = validar_imagen(str(t))
    assert ok is False and "Formato" in msg
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    ok, _ = validar_imagen(str(p))
    assert ok is False
    ok, _ = validar_imagen(str(p), permitir_pdf=True)
    assert ok is True


def test_validar_contenido(tmp_path):
    falso = tmp_path / "falso.jpg"
    falso.write_text("no soy imagen")
    ok, msg = validar_imagen(str(falso))
    assert ok is False and "válida" in msg
    real = tmp_path / "real.png"
    _png(str(real))
    ok, msg = validar_imagen(str(real))
    assert ok is True, msg


def test_extension_real():
    assert extension_real("foto.PNG") == ".png"
    assert extension_real("doc.pdf") == ".pdf"
    assert extension_real("raro.bmp") == ".jpg"
    assert extension_real("") == ".jpg"


def test_pago_centraliza_comprobante(crear_matricula, usuario_admin, tmp_path, monkeypatch):
    import utils.constants as const
    monkeypatch.setattr(const, "COMPROBANTES_DIR", str(tmp_path / "comp"))
    from services import pago_service
    from repositories import pago_repository
    img = tmp_path / "voucher.png"
    _png(str(img))
    m = crear_matricula()
    ok, _, id_pago = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": 10.0, "metodo_pago": "YAPE",
        "comprobante_path": str(img),
    })
    assert ok
    guardado = pago_repository.obtener_por_id(id_pago)["comprobante_path"]
    assert guardado.startswith(str(tmp_path / "comp"))
    assert guardado.endswith(".png")
    assert os.path.isfile(guardado)
