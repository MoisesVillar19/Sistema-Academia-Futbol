"""Importador tienda: validación + flujo producto/compra/ventas + selector UI."""
import pytest

pytestmark = pytest.mark.ui

from services import importar_service
from controllers import importar_controller


def _fila(**kw):
    d = {"PRODUCTOS": "Gaseosa QA", "CANTIDAD": "12", "COSTO TOTAL": "21.00",
         "COSTO X UNIDAD": "1.75", "COSTO VENTA": "3.30",
         "YAPE": "13.20", "EFECTIVO": "26.40", "CANTIDAD VENDIDO": "12",
         "QUEDAN": "0"}
    d.update(kw)
    return d


def test_validar_tienda_ok_y_errores():
    ok, _, errores = importar_service.validar_filas_tienda([_fila()])
    assert ok, errores
    ok, _, errores = importar_service.validar_filas_tienda([_fila(PRODUCTOS="")])
    assert not ok and any("PRODUCTOS" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_tienda([_fila(**{"CANTIDAD VENDIDO": "20"})])
    assert not ok and any("VENDIDAS" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_tienda([_fila(QUEDAN="5")])
    assert not ok and any("QUEDAN" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_tienda([_fila(), _fila()])
    assert not ok and any("duplicado" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_tienda([_fila(**{"COSTO VENTA": "abc"})])
    assert not ok


def test_importar_tienda_flujo_completo(usuario_admin):
    from repositories import producto_repository
    ok, msg, res = importar_service.importar_tienda([_fila()], id_usuario=1)
    assert ok, msg
    assert res["productos_creados"] == 1 and res["compras"] == 1 and res["ventas"] == 2
    prods = [p for p in producto_repository.obtener_todos() if p["nombre"] == "Gaseosa QA"]
    assert len(prods) == 1
    assert prods[0]["canal"] == "TIENDITA"
    assert prods[0]["stock_actual"] == 0  # 12 compradas − 12 vendidas
    assert float(prods[0]["precio_venta"]) == 3.30


def test_importar_tienda_quedan_stock(usuario_admin):
    from repositories import producto_repository
    ok, _, res = importar_service.importar_tienda(
        [_fila(PRODUCTOS="Parcial QA", CANTIDAD="10", **{"CANTIDAD VENDIDO": "6"},
               YAPE="6.60", EFECTIVO="13.20", QUEDAN="4")], id_usuario=1)
    assert ok, res
    prods = [p for p in producto_repository.obtener_todos() if p["nombre"] == "Parcial QA"]
    assert prods[0]["stock_actual"] == 4


def test_fecha_nacimiento_se_valida():
    errores = importar_service.validar_fila(
        {"DNI": "12345678", "Nombres": "A", "Apellidos": "B",
         "Fecha_Nacimiento": "31-02-2020"}, 1)
    assert any("Fecha_Nacimiento" in e for e in errores)
    errores = importar_service.validar_fila(
        {"DNI": "12345678", "Nombres": "A", "Apellidos": "B",
         "Fecha_Nacimiento": "2020-02-29"}, 1)
    assert not any("Fecha_Nacimiento" in e for e in errores)


def test_gate_admin(usuario_secretaria):
    from services import auth_service
    assert importar_controller.puede_acceder() is False
    auth_service.logout()
    assert auth_service.login("admin", "admin123") is not None
    assert importar_controller.puede_acceder() is True


def test_controller_dispatch_tienda(usuario_admin):
    ok, _, res = importar_controller.ejecutar_importacion([_fila()], tipo="Tienda")
    assert ok, res
    assert res["productos_creados"] == 1


def test_vista_selector_tipo(crear_vista, usuario_admin):
    import pytest
    pytest.importorskip("customtkinter")
    pytestmark = pytest.mark.ui
    from views.importar.importar_view import ImportarView
    vista = crear_vista(ImportarView)
    assert vista._tipo_importacion == "Estudiantes"
    vista.seg_tipo.set("Tienda")
    vista._on_tipo_cambiar("Tienda")
    assert vista._tipo_importacion == "Tienda"
    assert "PRODUCTOS" in importar_controller.obtener_campos_sistema("Tienda")
    assert "PRODUCTOS" in importar_controller.obtener_campos_obligatorios("Tienda")
