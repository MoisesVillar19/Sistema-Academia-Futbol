from database.connection import get_connection, fetch_one, fetch_all
from models.producto import Producto


def _tiene_columna(conn, tabla: str, columna: str) -> bool:
    try:
        return any(r[1] == columna for r in conn.execute(f"PRAGMA table_info({tabla})").fetchall())
    except Exception:
        return False


def insertar(producto: Producto) -> int:
    conn = get_connection()
    if _tiene_columna(conn, "producto", "tipo_empaque"):
        cursor = conn.execute(
            """INSERT INTO producto
               (id_categoria_producto, canal, codigo, nombre,
                stock_actual, stock_minimo, precio, precio_compra, precio_venta,
                tipo_empaque, cantidad_por_caja, precio_compra_total,
                id_tipo_uniforme, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                producto.id_categoria_producto,
                producto.canal,
                producto.codigo,
                producto.nombre,
                producto.stock_actual,
                producto.stock_minimo,
                producto.precio,
                producto.precio_compra,
                producto.precio_venta,
                producto.tipo_empaque or "Unidad",
                producto.cantidad_por_caja or 1,
                producto.precio_compra_total or 0,
                producto.id_tipo_uniforme,
                producto.activo,
            ),
        )
    else:
        cursor = conn.execute(
            """INSERT INTO producto
               (id_categoria_producto, canal, codigo, nombre,
                stock_actual, stock_minimo, precio, precio_compra, precio_venta, id_tipo_uniforme, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                producto.id_categoria_producto,
                producto.canal,
                producto.codigo,
                producto.nombre,
                producto.stock_actual,
                producto.stock_minimo,
                producto.precio,
                producto.precio_compra,
                producto.precio_venta,
                producto.id_tipo_uniforme,
                producto.activo,
            ),
        )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_producto: int) -> dict | None:
    return fetch_one(
        """SELECT p.*, cp.nombre as categoria_nombre
           FROM producto p
           JOIN categoria_producto cp ON p.id_categoria_producto = cp.id_categoria_producto
           WHERE p.id_producto = ?""",
        (id_producto,),
    )


def obtener_por_codigo(codigo: str) -> dict | None:
    return fetch_one(
        "SELECT * FROM producto WHERE codigo = ?",
        (codigo,),
    )


def obtener_todos(activo: int | None = None) -> list[dict]:
    sql = """
        SELECT p.*, cp.nombre as categoria_nombre
        FROM producto p
        JOIN categoria_producto cp ON p.id_categoria_producto = cp.id_categoria_producto
    """
    if activo is not None:
        sql += " WHERE p.activo = ?"
        return fetch_all(sql, (activo,))
    return fetch_all(sql)


def obtener_bajo_stock() -> list[dict]:
    return fetch_all(
        """SELECT p.*, cp.nombre as categoria_nombre
           FROM producto p
           JOIN categoria_producto cp ON p.id_categoria_producto = cp.id_categoria_producto
           WHERE p.stock_actual <= p.stock_minimo AND p.activo = 1
           ORDER BY p.stock_actual""",
    )


def actualizar_stock(id_producto: int, nuevo_stock: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE producto SET stock_actual = ? WHERE id_producto = ?",
        (nuevo_stock, id_producto),
    )
    conn.commit()


def existe_codigo(codigo: str, exclude_id: int | None = None) -> bool:
    if exclude_id:
        row = fetch_one(
            "SELECT id_producto FROM producto WHERE codigo = ? AND id_producto != ?",
            (codigo, exclude_id),
        )
    else:
        row = fetch_one(
            "SELECT id_producto FROM producto WHERE codigo = ?",
            (codigo,),
        )
    return row is not None


def actualizar(producto: Producto) -> None:
    conn = get_connection()
    if _tiene_columna(conn, "producto", "tipo_empaque"):
        conn.execute(
            """UPDATE producto SET
               id_categoria_producto = ?, canal = ?, codigo = ?, nombre = ?,
               stock_actual = ?, stock_minimo = ?, precio = ?, precio_compra = ?, precio_venta = ?,
               tipo_empaque = ?, cantidad_por_caja = ?, precio_compra_total = ?,
               id_tipo_uniforme = ?, activo = ?
               WHERE id_producto = ?""",
            (
                producto.id_categoria_producto,
                producto.canal,
                producto.codigo,
                producto.nombre,
                producto.stock_actual,
                producto.stock_minimo,
                producto.precio,
                producto.precio_compra,
                producto.precio_venta,
                producto.tipo_empaque or "Unidad",
                producto.cantidad_por_caja or 1,
                producto.precio_compra_total or 0,
                producto.id_tipo_uniforme,
                producto.activo,
                producto.id_producto,
            ),
        )
    else:
        conn.execute(
            """UPDATE producto SET
               id_categoria_producto = ?, canal = ?, codigo = ?, nombre = ?,
               stock_actual = ?, stock_minimo = ?, precio = ?, precio_compra = ?, precio_venta = ?, id_tipo_uniforme = ?, activo = ?
               WHERE id_producto = ?""",
            (
                producto.id_categoria_producto,
                producto.canal,
                producto.codigo,
                producto.nombre,
                producto.stock_actual,
                producto.stock_minimo,
                producto.precio,
                producto.precio_compra,
                producto.precio_venta,
                producto.id_tipo_uniforme,
                producto.activo,
                producto.id_producto,
            ),
        )
    conn.commit()


def buscar_paginado(q: str = "", limit: int = 50, offset: int = 0,
                    id_categoria_producto: int | None = None) -> tuple[list[dict], int]:
    """Búsqueda SQL real por nombre/código con paginación (Bloque A3).

    Devuelve (rows, total). Solo productos activos.
    ``id_categoria_producto`` filtra por categoría (Bloque B2, opcional).
    """
    base = """
        FROM producto p
        JOIN categoria_producto cp ON p.id_categoria_producto = cp.id_categoria_producto
        WHERE p.activo = 1
    """
    params: list = []
    if q and q.strip():
        like = f"%{q.strip()}%"
        base += " AND (p.nombre LIKE ? OR p.codigo LIKE ?)"
        params.extend([like, like])
    if id_categoria_producto is not None:
        base += " AND p.id_categoria_producto = ?"
        params.append(id_categoria_producto)
    cnt = fetch_one(f"SELECT COUNT(*) as c {base}", tuple(params))
    total = cnt["c"] if cnt else 0
    rows = fetch_all(
        f"""SELECT p.*, cp.nombre as categoria_nombre {base}
            ORDER BY p.nombre LIMIT ? OFFSET ?""",
        tuple(params + [limit, offset]),
    )
    return rows, total


def soft_delete(id_producto: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE producto SET activo = 0 WHERE id_producto = ?",
        (id_producto,),
    )
    conn.commit()
