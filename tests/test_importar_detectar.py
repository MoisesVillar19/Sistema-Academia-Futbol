"""E1: autodetección de tipo + registro extensible."""
from services import importar_service


def test_detecta_estudiantes():
    tipo, motivo = importar_service.detectar_tipo(["DNI", "Nombres", "Apellidos"], [])
    assert tipo == "Estudiantes" and motivo


def test_detecta_tienda():
    tipo, _ = importar_service.detectar_tipo(
        ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "COSTO VENTA"], [])
    assert tipo == "Tienda"


def test_detecta_historial():
    tipo, _ = importar_service.detectar_tipo(
        [], ["RELACIÓN DE ALUMNOS", "INGRESOS", "VENTA UNIFORME"])
    assert tipo == "Historial"


def test_no_reconocible_y_ambiguo():
    tipo, _ = importar_service.detectar_tipo(["ZZZ"], [])
    assert tipo is None
    # DNI + PRODUCTOS a la vez = ambiguo
    tipo, motivo = importar_service.detectar_tipo(["DNI", "Nombres", "PRODUCTOS"], [])
    assert tipo is None and "ambiguo" in motivo


def test_registro_extensible_sin_tocar_ui():
    assert set(importar_service.TIPOS_IMPORTACION) >= {"Estudiantes", "Tienda", "Historial"}
    for nombre, spec in importar_service.TIPOS_IMPORTACION.items():
        for clave in ("descripcion", "detectar", "campos", "obligatorios", "validar", "ejecutar"):
            assert clave in spec, (nombre, clave)


def test_vista_autodetecta(crear_vista, usuario_admin, tmp_path):
    import pytest
    pytest.importorskip("customtkinter")
    from views.importar.importar_view import ImportarView
    p = tmp_path / "est.csv"
    p.write_text("DNI,Nombres,Apellidos\n12345678,A,B\n", encoding="utf-8-sig")
    vista = crear_vista(ImportarView)
    vista._archivo_actual = str(p)
    vista._cargar_archivo()
    vista.update_idletasks()
    assert vista._tipo_importacion == "Estudiantes"
    assert "Estudiantes" in vista.label_deteccion.cget("text")
