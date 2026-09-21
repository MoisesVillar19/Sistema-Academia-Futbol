"""P1: empaque, costo unitario auto, compra con método y ganancias."""
from services import inventario_service
from repositories import producto_repository


def _cat():
    cats = inventario_service.listar_categorias()
    if cats:
        return cats[0]["id_categoria_producto"]
    exito, _, cid = inventario_service.crear_categoria({"nombre": "Empaque QA"})
    assert exito
    return cid


def test_crear_caja_calcula_unitario():
    exito, msg, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Lapiceros x12",
        "tipo_uso": "VENTA", "tipo_empaque": "Caja x12", "cantidad_por_caja": 12,
        "precio_compra_total": 24.0, "precio_venta": 3.0,
    })
    assert exito, msg
    p = producto_repository.obtener_por_id(pid)
    assert p["precio_compra"] == 2.0
    assert p["cantidad_por_caja"] == 12
    assert p["precio_compra_total"] == 24.0


def test_unidad_fuerza_cantidad_uno():
    exito, msg, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Unidad QA",
        "tipo_uso": "VENTA", "tipo_empaque": "Unidad", "cantidad_por_caja": 99,
        "precio_compra_total": 10.0, "precio_venta": 12.0,
    })
    assert exito, msg
    p = producto_repository.obtener_por_id(pid)
    assert p["cantidad_por_caja"] == 1
    assert p["precio_compra"] == 10.0


def test_empaque_invalido_y_totales_invalidos():
    base = {"id_categoria_producto": _cat(), "nombre": "X", "tipo_uso": "VENTA"}
    exito, _, _ = inventario_service.crear_producto(
        dict(base, tipo_empaque="Bolsa", cantidad_por_caja=1,
             precio_compra_total=10, precio_venta=12))
    assert exito is False
    exito, _, _ = inventario_service.crear_producto(
        dict(base, tipo_empaque="Caja x12", cantidad_por_caja=0,
             precio_compra_total=10, precio_venta=12))
    assert exito is False
    exito, _, _ = inventario_service.crear_producto(
        dict(base, tipo_empaque="Caja x12", cantidad_por_caja=12,
             precio_compra_total=-5, precio_venta=12))
    assert exito is False


def test_compra_registra_monto_y_metodo():
    exito, _, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Compra QA",
        "tipo_uso": "VENTA", "tipo_empaque": "Caja x100", "cantidad_por_caja": 100,
        "precio_compra_total": 200.0, "precio_venta": 3.0,
    })
    assert exito
    exito, msg, _ = inventario_service.registrar_compra({
        "id_producto": pid, "cantidad": 50, "monto_total": 100.0, "metodo_pago": "YAPE",
    })
    assert exito, msg
    p = producto_repository.obtener_por_id(pid)
    assert p["stock_actual"] == 50
    movs = inventario_service.listar_movimientos_por_producto(pid)
    assert movs and movs[0]["metodo_pago"] == "YAPE" and movs[0]["monto_total"] == 100.0


def test_compra_metodo_invalido_y_monto_invalido():
    exito, _, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Compra QA2",
        "tipo_uso": "VENTA", "precio_venta": 5.0,
    })
    assert exito
    exito, _, _ = inventario_service.registrar_compra({
        "id_producto": pid, "cantidad": 5, "monto_total": 10, "metodo_pago": "PLIN"})
    assert exito is False
    exito, _, _ = inventario_service.registrar_compra({
        "id_producto": pid, "cantidad": 5, "monto_total": 0, "metodo_pago": "YAPE"})
    assert exito is False


def test_calcular_unitario_y_ganancia():
    r = inventario_service.calcular_unitario_y_ganancia(24.0, 12, 3.0)
    assert r == {"unitario": 2.0, "ganancia_unitaria": 1.0, "ganancia_pct": 50.0}
    r = inventario_service.calcular_unitario_y_ganancia(0, 0, 5.0)
    assert r["unitario"] == 0 and r["ganancia_pct"] == 0


def test_resumen_dinero_mes():
    from controllers import dashboard_controller
    from services import venta_service
    from repositories import tarifa_repository
    from models.tarifa import Tarifa
    from database.connection import fetch_one
    exito, _, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Dinero QA",
        "tipo_uso": "VENTA", "precio_compra_total": 20.0, "precio_venta": 30.0,
    })
    assert exito
    exito, _, _ = inventario_service.registrar_compra({
        "id_producto": pid, "cantidad": 10, "monto_total": 200.0, "metodo_pago": "YAPE"})
    assert exito
    cat = fetch_one("SELECT id_categoria FROM categoria LIMIT 1")
    tid = tarifa_repository.insertar(Tarifa(id_categoria=cat["id_categoria"], nombre="T", monto=50.0))
    prods = inventario_service.listar_productos(activo=1)
    assert prods
    exito, _, _ = venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": pid, "cantidad": 2}]})
    assert exito
    r = dashboard_controller.resumen_dinero()
    assert r["compras_yape"] == 200.0
    assert r["ventas_efectivo"] >= 60.0
    assert r["ganancia_efectivo"] >= 20.0  # 2 x (30-20)
    assert r["ganancia_total"] == round(r["ganancia_yape"] + r["ganancia_efectivo"], 2)
    assert len(dashboard_controller.listar_compras_mes()) >= 1
    assert len(dashboard_controller.listar_ganancias_mes()) >= 1


def test_stock_inicial_genera_entrada():
    exito, _, pid = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "StockInit QA",
        "tipo_uso": "VENTA", "precio_compra_total": 20.0, "precio_venta": 25.0,
        "stock_inicial": 4, "modo_compra": "EFECTIVO",
    })
    assert exito
    p = producto_repository.obtener_por_id(pid)
    assert p["stock_actual"] == 4
