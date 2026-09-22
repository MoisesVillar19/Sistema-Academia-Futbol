"""Fase 6a: scoping por canal en services (sin cruce Tiendita/Almacén)."""
from services import inventario_service, venta_service


def _prod(nombre, canal):
    cats = inventario_service.listar_categorias()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre, "canal": canal, "precio_venta": 10.0,
    })
    assert ok
    return id_prod


def test_listar_por_canal_no_cruza():
    id_t = _prod("SoloTienda 6a", "TIENDITA")
    id_a = _prod("SoloAlmacen 6a", "ALMACEN")
    ids_t = {p["id_producto"] for p in inventario_service.listar_por_canal("TIENDITA")}
    ids_a = {p["id_producto"] for p in inventario_service.listar_por_canal("ALMACEN")}
    assert id_t in ids_t and id_t not in ids_a
    assert id_a in ids_a and id_a not in ids_t
    assert inventario_service.listar_por_canal("XX") == []


def test_venta_almacen_rechazada(usuario_admin):
    id_a = _prod("NoVendible 6a", "ALMACEN")
    inventario_service.registrar_compra({
        "id_producto": id_a, "cantidad": 5, "monto_total": "10.00",
        "metodo_pago": "EFECTIVO",
    })
    ok, msg, _ = venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": id_a, "cantidad": 1}],
        "id_usuario": usuario_admin["id_usuario"],
    })
    assert ok is False and "Almac" in msg


def test_movimiento_manual_tiendita_rechazado_compra_ok(usuario_admin):
    id_t = _prod("MovT 6a", "TIENDITA")
    ok, msg, _ = inventario_service.registrar_movimiento({
        "id_producto": id_t, "tipo_movimiento": "ENTRADA", "cantidad": 2,
        "motivo": "manual", "id_usuario": usuario_admin["id_usuario"],
    })
    assert ok is False and "Compras" in msg
    ok, _, _ = inventario_service.registrar_compra({
        "id_producto": id_t, "cantidad": 2, "monto_total": "4.00",
        "metodo_pago": "EFECTIVO",
    })
    assert ok


def test_ajuste_almacen_ok(usuario_admin):
    id_a = _prod("Ajuste 6a", "ALMACEN")
    ok, _, _ = inventario_service.registrar_movimiento({
        "id_producto": id_a, "tipo_movimiento": "AJUSTE", "cantidad": 7,
        "motivo": "conteo", "id_usuario": usuario_admin["id_usuario"],
    })
    assert ok
    assert inventario_service.obtener_producto(id_a)["stock_actual"] == 7
