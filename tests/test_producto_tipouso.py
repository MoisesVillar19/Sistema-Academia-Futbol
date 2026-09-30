"""F1: insertar producto en BD legacy con tipo_uso NOT NULL."""
from database.connection import get_connection


def _cat():
    from services import inventario_service
    cats = inventario_service.listar_categorias()
    if cats:
        return cats[0]["id_categoria_producto"]
    ok, _, cid = inventario_service.crear_categoria({"nombre": "CatTUso"})
    assert ok
    return cid


def test_insertar_con_tipo_uso_legacy():
    from repositories import producto_repository
    from models.producto import Producto
    conn = get_connection()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(producto)").fetchall()]
    if "tipo_uso" not in cols:
        conn.execute("ALTER TABLE producto ADD COLUMN tipo_uso TEXT NOT NULL DEFAULT 'X'")
        conn.commit()
    id_t = producto_repository.insertar(Producto(
        id_categoria_producto=_cat(), canal="TIENDITA", codigo="TU-1",
        nombre="TipoUso Tienda", precio_venta=10.0))
    row = producto_repository.obtener_por_id(id_t)
    assert row["tipo_uso"] == "VENTA", row
    id_a = producto_repository.insertar(Producto(
        id_categoria_producto=_cat(), canal="ALMACEN", codigo="TU-2",
        nombre="TipoUso Almacen", precio_venta=5.0))
    row2 = producto_repository.obtener_por_id(id_a)
    assert row2["tipo_uso"] == "CONSUMO_INTERNO", row2
