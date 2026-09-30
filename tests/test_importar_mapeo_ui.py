"""Regresión: mapeo UI estilo-UI debe validar (Tienda fallaba entero)."""
import pytest

pytestmark = pytest.mark.ui

TIENDA_HDR = ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "COSTO X UNIDAD",
              "COSTO VENTA", "YAPE", "EFECTIVO", "CANTIDAD VENDIDO",
              "QUEDAN", "CATEGORIA", "FECHA"]
TIENDA_ROW = ["Gaseosa 500ml", "12", "21.00", "1.75", "3.30",
              "13.20", "26.40", "12", "0", "Bebidas", "2026-05-01"]


def _csv(path, delim=","):
    import csv
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=delim)
        w.writerow(TIENDA_HDR)
        w.writerow(TIENDA_ROW)


def test_mapeo_ui_tienda_valida(crear_vista, usuario_admin, tmp_path):
    from views.importar.importar_view import ImportarView
    p = str(tmp_path / "t.csv")
    _csv(p)
    vista = crear_vista(ImportarView)
    vista._archivo_actual = p
    vista._cargar_archivo()
    vista.update_idletasks()
    assert vista._tipo_importacion == "Tienda"
    mapeo = vista._mapeo_dict()
    # valores sys (los que resuelven los services), no cabeceras
    assert mapeo.get("PRODUCTOS") == "nombre", mapeo
    assert mapeo.get("COSTO TOTAL") == "costo_total", mapeo
    assert "Faltan obligatorios" not in vista.label_mapeo_resumen.cget("text")
    assert vista._hallazgos_actuales == [], [h["mensaje"] for h in vista._hallazgos_actuales]


def test_mapeo_ui_tienda_puntoycoma(crear_vista, usuario_admin, tmp_path):
    from views.importar.importar_view import ImportarView
    p = str(tmp_path / "t.csv")
    _csv(p, delim=";")
    vista = crear_vista(ImportarView)
    vista._archivo_actual = p
    vista._cargar_archivo()
    vista.update_idletasks()
    assert vista._tipo_importacion == "Tienda"
    assert vista._hallazgos_actuales == [], [h["mensaje"] for h in vista._hallazgos_actuales]


def test_sugerir_sys_names(crear_vista, usuario_admin):
    from views.importar.importar_view import ImportarView
    vista = crear_vista(ImportarView)
    vista._tipo_importacion = "Pagos"
    campos = ["DNI", "PERIODO", "MONTO", "METODO", "FECHA"]
    assert vista._sugerir_mapeo("PERIODO", campos) == "periodo"
    assert vista._sugerir_mapeo("MONTO", campos) == "monto"
    vista._tipo_importacion = "Estudiantes"
    assert vista._sugerir_mapeo("DNI", ["DNI"]) == "dni"
