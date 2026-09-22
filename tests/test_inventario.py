"""Tests del servicio de inventario: categorias, productos y movimientos de stock."""
from services import inventario_service


def _crear_categoria(nombre="Categoria QA"):
    """Obtiene o crea una categoria de producto por nombre."""
    existentes = inventario_service.listar_categorias()
    for cat in existentes:
        if cat["nombre"] == nombre:
            return cat["id_categoria_producto"]
    exito, msg, id_cat = inventario_service.crear_categoria({"nombre": nombre})
    assert exito, msg
    return id_cat


def _crear_producto(id_cat=None, codigo=None, **overrides):
    # Fase 6a: movimientos manuales viven en ALMACEN (Tiendita usa Compras/Ventas)
    data = {
        "id_categoria_producto": id_cat or _crear_categoria(),
        "nombre": "Balon #5",
        "canal": "ALMACEN",
        "precio": 50.0,
        "stock_minimo": 2,
    }
    if codigo:
        data["codigo"] = codigo
    data.update(overrides)
    exito, msg, id_prod = inventario_service.crear_producto(data)
    assert exito, msg
    return id_prod


def test_crear_categoria_duplicada_rechazada():
    _crear_categoria("DupCat")
    exito, msg, _ = inventario_service.crear_categoria({"nombre": "DupCat"})
    assert exito is False


def test_crear_producto_sin_nombre_rechazado():
    exito, msg, _ = inventario_service.crear_producto({
        "id_categoria_producto": _crear_categoria(), "nombre": "",
    })
    assert exito is False


def test_crear_producto_codigo_automatico():
    id_prod = _crear_producto()
    prod = inventario_service.obtener_producto(id_prod)
    assert prod["codigo"]
    assert prod["stock_actual"] == 0


def test_codigo_duplicado_rechazado():
    _crear_producto(codigo="QA-0001")
    exito, msg, _ = inventario_service.crear_producto({
        "id_categoria_producto": _crear_categoria(),
        "nombre": "Otro", "codigo": "QA-0001",
    })
    assert exito is False


def test_movimiento_entrada_aumenta_stock():
    id_prod = _crear_producto()
    exito, msg, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA",
        "cantidad": 10, "motivo": "Compra inicial",
    })
    assert exito is True
    assert inventario_service.obtener_producto(id_prod)["stock_actual"] == 10


def test_movimiento_salida_disminuye_stock():
    id_prod = _crear_producto()
    inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA", "cantidad": 8,
    })
    exito, msg, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "SALIDA", "cantidad": 3,
    })
    assert exito is True
    assert inventario_service.obtener_producto(id_prod)["stock_actual"] == 5


def test_salida_sin_stock_suficiente_rechazada():
    id_prod = _crear_producto()
    exito, msg, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "SALIDA", "cantidad": 5,
    })
    assert exito is False
    assert "insuficiente" in msg.lower()


def test_ajuste_fija_stock_absoluto():
    id_prod = _crear_producto()
    inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA", "cantidad": 9,
    })
    exito, _, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "AJUSTE", "cantidad": 4,
    })
    assert exito
    assert inventario_service.obtener_producto(id_prod)["stock_actual"] == 4


def test_tipo_movimiento_invalido_rechazado():
    id_prod = _crear_producto()
    exito, msg, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ROBO", "cantidad": 1,
    })
    assert exito is False


def test_bajo_stock_detecta_productos():
    id_cat = _crear_categoria("BajoStockCat")
    data = {
        "id_categoria_producto": id_cat,
        "nombre": "Conos",
        "stock_minimo": 5,
    }
    exito, _, id_prod = inventario_service.crear_producto(data)
    assert exito
    inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA", "cantidad": 2,
    })

    bajos = inventario_service.obtener_bajo_stock()
    assert any(p["id_producto"] == id_prod for p in bajos)


def test_historial_por_producto():
    id_prod = _crear_producto()
    inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA", "cantidad": 3,
    })
    movs = inventario_service.listar_movimientos_por_producto(id_prod)
    assert len(movs) >= 1
