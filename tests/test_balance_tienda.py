"""Tab Ganancias en Tiendita (balance estilo Excel)."""
import pytest

pytestmark = pytest.mark.ui

from services import inventario_service, venta_service, reporte_service


def _prod(nombre="Bal QA"):
    cats = inventario_service.listar_categorias()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre, "canal": "TIENDITA",
        "precio_compra_total": "21.00", "cantidad_por_caja": "12",
        "tipo_empaque": "Personalizado", "precio_venta": 3.30,
    })
    assert ok
    return id_prod


def test_balance_filas_y_totales(usuario_admin):
    id_prod = _prod()
    inventario_service.registrar_compra({
        "id_producto": id_prod, "cantidad": 12, "monto_total": "21.00",
        "metodo_pago": "EFECTIVO", "fecha_movimiento": "2026-05-10"})
    venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "YAPE",
        "items": [{"id_producto": id_prod, "cantidad": 10}],
        "fecha_venta": "2026-05-12", "id_usuario": usuario_admin["id_usuario"]})
    venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": id_prod, "cantidad": 2}],
        "fecha_venta": "2026-05-13", "id_usuario": usuario_admin["id_usuario"]})
    filas, totales = reporte_service.balance_tienda("2026-05-01", "2026-05-31")
    assert len(filas) == 1
    f = filas[0]
    assert f["nombre"] == "Bal QA" and f["cantidad"] == 12
    assert f["costo_total"] == 21.00 and f["costo_unitario"] == 1.75
    assert f["costo_venta"] == 3.30
    assert f["yape"] == 33.00 and f["efectivo"] == 6.60
    assert f["vendidas"] == 12 and f["quedan"] == 0
    assert f["ganancia"] == round(12 * (3.30 - 1.75), 2)
    assert totales["ganancia"] == f["ganancia"]


def test_balance_fuera_de_periodo_vacio(usuario_admin):
    _prod("Fuera QA")
    filas, totales = reporte_service.balance_tienda("2020-01-01", "2020-01-31")
    assert filas == [] and totales["ganancia"] == 0


def test_tab_ganancias_en_tiendita(crear_vista, usuario_admin):
    from views.tiendita.tiendita_view import TienditaView
    vista = crear_vista(TienditaView)
    vista.update_idletasks()
    assert "Ganancias" in list(vista._tabs.keys())
    assert vista.scroll_ganancias.winfo_exists()
    assert "Ganancia" in vista.label_ganancias.cget("text")
