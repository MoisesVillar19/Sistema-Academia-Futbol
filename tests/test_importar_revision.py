"""E2: revisión previa con opciones + resoluciones aplicadas."""
import pytest

pytestmark = pytest.mark.ui

from services import importar_revision as rev
from controllers import importar_controller


def test_hallazgos_estudiantes():
    filas = [
        {"DNI": "", "Nombres": "A", "Apellidos": "B"},
        {"DNI": "123", "Nombres": "C", "Apellidos": "D"},
        {"DNI": "12345678", "Nombres": "E", "Apellidos": "F",
         "Fecha_Nacimiento": "mal", "Sexo": "X"},
    ]
    h = rev.revisar_estudiantes(filas)
    por_cod = {}
    for x in h:
        por_cod.setdefault(x["codigo"], []).append(x)
    assert por_cod["FALTA_DNI"][0]["opciones"][0]["id"] == "provisional"
    assert "DNI_INVALIDO" in por_cod
    assert "FECHA_INVALIDA" in por_cod and "SEXO_INVALIDO" in por_cod
    assert all(x["default"] for x in h)


def test_hallazgo_duplicado_bd(crear_persona):
    crear_persona(dni="11111111")
    h = rev.revisar_estudiantes([{"DNI": "11111111", "Nombres": "A", "Apellidos": "B"}])
    assert any(x["codigo"] == "DNI_DUPLICADO" and "sistema" in x["mensaje"] for x in h)


def test_hallazgos_tienda():
    h = rev.revisar_tienda([
        {"PRODUCTOS": "X", "CANTIDAD": "5", "COSTO TOTAL": "10",
         "COSTO VENTA": "2", "CANTIDAD VENDIDO": "3", "QUEDAN": "9"},
        {"PRODUCTOS": "", "CANTIDAD": "1"},
    ])
    cods = [x["codigo"] for x in h]
    assert "QUEDAN_MAL" in cods and "FALTA_NOMBRE" in cods
    q = next(x for x in h if x["codigo"] == "QUEDAN_MAL")
    assert q["opciones"][0]["id"] == "corregir"


def test_aplicar_omitir_y_provisional():
    filas = [
        {"DNI": "", "Nombres": "A", "Apellidos": "B"},
        {"DNI": "123", "Nombres": "C", "Apellidos": "D"},
        {"DNI": "22222222", "Nombres": "E", "Apellidos": "F"},
    ]
    h = rev.revisar("Estudiantes", filas)
    res = {x["id"]: x["default"] for x in h}
    # el inválido va con omitir por defecto; el faltante con provisional
    ef, notas = rev.aplicar_resoluciones("Estudiantes", filas, None, res)
    assert len(ef) == 2
    assert ef[0]["DNI"] == "90000001"
    assert any("provisional" in n for n in notas)
    assert any("omitidas" in n for n in notas)


def test_aplicar_corregir_quedan():
    filas = [{"PRODUCTOS": "X", "CANTIDAD": "5", "COSTO TOTAL": "10",
              "COSTO VENTA": "2", "CANTIDAD VENDIDO": "3", "QUEDAN": "9"}]
    h = rev.revisar("Tienda", filas)
    res = {x["id"]: x["default"] for x in h}
    ef, _ = rev.aplicar_resoluciones("Tienda", filas, None, res)
    assert str(ef[0]["QUEDAN"]) == "2"


def test_ejecutar_con_resoluciones(usuario_admin):
    filas = [
        {"DNI": "", "Nombres": "Res", "Apellidos": "UELTO"},
        {"DNI": "33333333", "Nombres": "Bien", "Apellidos": "Ok"},
    ]
    h = importar_controller.revisar_importacion(filas, None, "Estudiantes")
    res = {x["id"]: x["default"] for x in h}
    ok, _, out = importar_controller.ejecutar_importacion(filas, None, "Estudiantes", res)
    assert ok, out
    assert out["estudiantes_creados"] == 2
    from repositories import persona_repository
    assert persona_repository.obtener_por_dni("90000001") is not None


def test_vista_validar_y_ejecutar(crear_vista, usuario_admin):
    import pytest
    pytest.importorskip("customtkinter")
    import tkinter.messagebox as mb
    from views.importar.importar_view import ImportarView
    vista = crear_vista(ImportarView)
    vista._datos_cargados = [
        {"DNI": "", "Nombres": "V", "Apellidos": "W"},
        {"DNI": "44444444", "Nombres": "X", "Apellidos": "Y"},
    ]
    vista._mapeo_actual = {}
    vista._validar()
    vista.update_idletasks()
    assert len(vista._hallazgos_actuales) == 1
    assert vista._hallazgos_actuales[0]["codigo"] == "FALTA_DNI"
    assert vista.btn_ejecutar_rev.cget("state") == "normal"
    vista._resoluciones_dict()  # no revienta sin selecciones manuales


def test_provisionales_unicos_en_lote():
    filas = [
        {"DNI": "", "Nombres": "A", "Apellidos": "B"},
        {"DNI": "", "Nombres": "C", "Apellidos": "D"},
    ]
    h = rev.revisar("Estudiantes", filas)
    res = {x["id"]: x["default"] for x in h}
    ef, _ = rev.aplicar_resoluciones("Estudiantes", filas, None, res)
    assert ef[0]["DNI"] != ef[1]["DNI"]
