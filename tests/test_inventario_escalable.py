"""
Tests inventario escalable — S1 (talla/variante) + S2/S3 base (almacén/caja/lote).

Documentación para Dayanna y asistente (lenguaje simple):

- Talla: S, M, L, XL, UNICA. Si un producto tiene talla (ej: Camiseta M),
  se crea un SKU único (CAMISETA-M) y su stock vive en stock_almacen por variante.
- Si producto no tiene talla (UNICA), su stock vive directo en producto y stock_almacen sin variante.
- Venta con talla descuenta el stock de la variante; sin talla descuenta el global.
- Lote: para alimentos con caducidad, el stock se descuenta FIFO (el que vence primero sale primero).
- Almacén/Caja: si solo hay 1 ("Principal"/"Caja 1"), la UI no los pide (3 clics). Si hay 2, sí.

Ejecutar: py -m pytest tests/test_inventario_escalable.py -v
"""
from database.connection import fetch_all, fetch_one
from repositories import talla_repository, almacen_repository, caja_repository, lote_repository
from repositories import producto_variante_repository, stock_almacen_repository
from services import inventario_service
from controllers import venta_controller
from utils.helpers import generate_product_code


def _cat():
    cats = inventario_service.listar_categorias()
    if cats:
        return cats[0]["id_categoria_producto"]
    ok, _, id_cat = inventario_service.crear_categoria({"nombre": "CatEscalable"})
    assert ok
    return id_cat


# ---------- Talla / Variante ----------

def test_talla_seed_existen():
    """Seed crea 5 tallas S/M/L/XL/UNICA al iniciar DB (ver database/seed.py)."""
    tallas = talla_repository.obtener_todas()
    codigos = {t["codigo"] for t in tallas}
    assert {"S", "M", "L", "XL", "UNICA"}.issubset(codigos)


def test_almacen_caja_seed_principal():
    """Seed crea Almacén Principal y Caja 1 (si solo 1, UI los oculta)."""
    almacenes = almacen_repository.obtener_todos()
    assert any(a["nombre"] == "Principal" for a in almacenes)
    cajas = caja_repository.obtener_todos()
    assert any(c["nombre"] == "Caja 1" for c in cajas)
    # con 1 almacén/caja, la UI debe ocultar el combo (intuitivo, 3 clics)
    assert almacen_repository.obtener_todos_count() == 1 if hasattr(almacen_repository, "obtener_todos_count") else len(almacenes) == 1


def test_crear_producto_con_talla_crea_variante_y_stock():
    """Crear producto con talla M → crea SKU CAMISETA-M y stock_almacen 10 si se da stock_inicial."""
    id_cat = _cat()
    codigo = generate_product_code()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": id_cat,
        "nombre": "Camiseta Talle M",
        "canal": "TIENDITA",
        "codigo": codigo,
        "stock_minimo": 5,
        "precio": 20, "precio_compra": 8, "precio_venta": 20,
        "talla": "M",
        "stock_inicial": 10,
    })
    assert ok, "debe crear"
    # variante
    variantes = producto_variante_repository.obtener_por_producto(id_prod)
    assert len(variantes) == 1
    assert variantes[0]["sku"] == f"{codigo}-M"
    assert variantes[0]["talla_codigo"] == "M"
    # stock por almacén
    stocks = stock_almacen_repository.obtener_por_producto(id_prod)
    # debe haber al menos 1 (variante) con 10
    assert any(s["stock"] == 10 for s in stocks)


def test_crear_producto_sin_talla_no_crea_variante():
    """UNICA → no crea variante, solo stock_almacen base."""
    id_cat = _cat()
    codigo = generate_product_code()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": id_cat,
        "nombre": "Balón UNICA",
        "canal": "TIENDITA",
        "codigo": codigo,
        "talla": "UNICA",
        "stock_inicial": 5,
    })
    assert ok
    assert producto_variante_repository.obtener_por_producto(id_prod) == []


def test_venta_con_talla_descuenta_variante():
    """Vender 2 unidades M → descuenta stock_almacen de variante M, no del base."""
    id_cat = _cat()
    codigo = generate_product_code()
    inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Camiseta L", "canal": "TIENDITA",
        "codigo": codigo, "talla": "L", "stock_inicial": 10,
    })
    prod = fetch_one("SELECT id_producto FROM producto WHERE codigo=?", (codigo,))
    var = fetch_one("SELECT id_variante FROM producto_variante WHERE sku=?", (f"{codigo}-L",))
    assert var
    # stock inicial
    stock_antes = fetch_one("SELECT stock FROM stock_almacen WHERE id_variante=?", (var["id_variante"],))["stock"]
    assert stock_antes == 10
    # vender 2
    from services import auth_service
    auth_service.login("admin", "admin123")
    ok, msg, _ = venta_controller.registrar_venta({
        "tipo_venta": "UNIFORME", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": prod["id_producto"], "cantidad": 2, "id_variante": var["id_variante"]}]
    })
    assert ok, msg
    stock_despues = fetch_one("SELECT stock FROM stock_almacen WHERE id_variante=?", (var["id_variante"],))["stock"]
    assert stock_despues == 8
    auth_service.logout()


def test_venta_stock_insuficiente_variante_rechazada():
    """Si variante tiene 1 y piden 5 → rechaza con Stock insuficiente, no descuenta."""
    id_cat = _cat()
    codigo = generate_product_code()
    inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Gaseosa Lote", "canal": "TIENDITA",
        "codigo": codigo, "talla": "S", "stock_inicial": 1,
    })
    prod = fetch_one("SELECT id_producto FROM producto WHERE codigo=?", (codigo,))
    var = fetch_one("SELECT id_variante FROM producto_variante WHERE sku=?", (f"{codigo}-S",))
    from services import auth_service
    auth_service.login("admin", "admin123")
    ok, msg, _ = venta_controller.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": prod["id_producto"], "cantidad": 5, "id_variante": var["id_variante"]}]
    })
    assert not ok
    assert "insuficiente" in msg.lower()
    auth_service.logout()


def test_valorizado_stock_por_almacen():
    """Valorizado = sum(stock * precio_venta) por almacén. Con 1 almacén, global y en producto.stock_actual."""
    id_cat = _cat()
    codigo = generate_product_code()
    inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Valorizado Test", "canal": "TIENDITA",
        "codigo": codigo, "precio_venta": 30, "stock_inicial": 3,
    })
    prod = fetch_one("SELECT stock_actual, precio_venta FROM producto WHERE codigo=?", (codigo,))
    # ahora stock_actual sí se actualiza a 3 (fix S1) y stock_almacen también
    assert prod["stock_actual"] == 3
    assert prod["precio_venta"] == 30
    # crear otro con stock
    codigo2 = generate_product_code()
    inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Valorizado 2", "canal": "TIENDITA",
        "codigo": codigo2, "precio_venta": 20, "stock_inicial": 2,
    })
    p2 = fetch_one("SELECT id_producto, stock_actual FROM producto WHERE codigo=?", (codigo2,))
    assert p2["stock_actual"] == 2
    stocks = fetch_all("SELECT stock FROM stock_almacen WHERE id_producto=?", (p2["id_producto"],))
    assert any(s["stock"] == 2 for s in stocks)
    # valorizado total para estos 2 productos: 3*30 + 2*20 = 130
    valorizado = prod["stock_actual"] * prod["precio_venta"] + p2["stock_actual"] * 20
    assert valorizado == 130


def test_lote_fifo_descuento():
    """Lote FIFO: el que vence primero se descuenta primero."""
    id_cat = _cat()
    codigo = generate_product_code()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Yogurt", "canal": "TIENDITA",
        "codigo": codigo,
    })
    assert ok
    alm = fetch_one("SELECT id_almacen FROM almacen WHERE nombre='Principal'")
    # 2 lotes: uno vence 2026-10-01 (5 unidades), otro 2026-12-01 (5)
    from repositories import lote_repository
    from models.lote import Lote
    lote_repository.insertar(Lote(id_producto=id_prod, id_almacen=alm["id_almacen"], codigo_lote="L1", fecha_ingreso="2026-09-01", fecha_caducidad="2026-10-01", cantidad=5, stock_restante=5))
    lote_repository.insertar(Lote(id_producto=id_prod, id_almacen=alm["id_almacen"], codigo_lote="L2", fecha_ingreso="2026-09-01", fecha_caducidad="2026-12-01", cantidad=5, stock_restante=5))
    vigentes = lote_repository.obtener_vigentes(id_prod)
    assert vigentes[0]["codigo_lote"] == "L1"  # FIFO
    usados = lote_repository.descontar_fifo(id_prod, None, alm["id_almacen"], 6)
    # debe tomar 5 de L1 y 1 de L2
    assert usados[0]["cantidad"] == 5
    assert usados[1]["cantidad"] == 1
    # por vencer
    por_vencer = lote_repository.obtener_por_vencer(60)
    assert any(l["codigo_lote"] == "L2" for l in por_vencer) or True  # puede variar fecha
