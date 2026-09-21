from database.connection import get_connection, fetch_one, fetch_all
from models.movimiento_inventario import MovimientoInventario
from utils.dates import get_now


def insertar(movimiento: MovimientoInventario) -> int:
    conn = get_connection()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(movimiento_inventario)").fetchall()]
    except Exception:
        cols = []
    if "metodo_pago" in cols:
        cursor = conn.execute(
            """INSERT INTO movimiento_inventario
               (id_producto, id_usuario, tipo_movimiento, cantidad,
                stock_anterior, stock_nuevo, fecha_movimiento, motivo,
                metodo_pago, monto_total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                movimiento.id_producto,
                movimiento.id_usuario,
                movimiento.tipo_movimiento,
                movimiento.cantidad,
                movimiento.stock_anterior,
                movimiento.stock_nuevo,
                movimiento.fecha_movimiento,
                movimiento.motivo,
                movimiento.metodo_pago,
                movimiento.monto_total or 0,
            ),
        )
    else:
        cursor = conn.execute(
            """INSERT INTO movimiento_inventario
               (id_producto, id_usuario, tipo_movimiento, cantidad,
                stock_anterior, stock_nuevo, fecha_movimiento, motivo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                movimiento.id_producto,
                movimiento.id_usuario,
                movimiento.tipo_movimiento,
                movimiento.cantidad,
                movimiento.stock_anterior,
                movimiento.stock_nuevo,
                movimiento.fecha_movimiento,
                movimiento.motivo,
            ),
        )
    conn.commit()
    return cursor.lastrowid


def obtener_por_producto(id_producto: int) -> list[dict]:
    return fetch_all(
        """SELECT m.*, u.username
           FROM movimiento_inventario m
           JOIN usuario u ON m.id_usuario = u.id_usuario
           WHERE m.id_producto = ?
           ORDER BY m.fecha_movimiento DESC""",
        (id_producto,),
    )


def sumar_compras_por_metodo(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT metodo_pago AS metodo, COALESCE(SUM(monto_total), 0) AS total
           FROM movimiento_inventario
           WHERE tipo_movimiento = 'ENTRADA' AND metodo_pago IN ('YAPE', 'EFECTIVO')
             AND fecha_movimiento BETWEEN ? AND ?
           GROUP BY metodo_pago""",
        (fecha_inicio, fecha_fin + " 23:59:59" if len(fecha_fin) == 10 else fecha_fin),
    )


def obtener_compras_con_metodo(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT m.*, p.nombre AS producto_nombre
           FROM movimiento_inventario m
           JOIN producto p ON p.id_producto = m.id_producto
           WHERE m.tipo_movimiento = 'ENTRADA' AND m.metodo_pago IN ('YAPE', 'EFECTIVO')
             AND m.fecha_movimiento BETWEEN ? AND ?
           ORDER BY m.fecha_movimiento DESC""",
        (fecha_inicio, fecha_fin + " 23:59:59" if len(fecha_fin) == 10 else fecha_fin),
    )


def obtener_todos(limit: int = 100, offset: int = 0) -> list[dict]:
    return fetch_all(
        """SELECT m.*, u.username, p.nombre as producto_nombre, p.codigo
           FROM movimiento_inventario m
           JOIN usuario u ON m.id_usuario = u.id_usuario
           JOIN producto p ON m.id_producto = p.id_producto
           ORDER BY m.fecha_movimiento DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    )


def obtener_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT m.*, u.username, p.nombre as producto_nombre, p.codigo
           FROM movimiento_inventario m
           JOIN usuario u ON m.id_usuario = u.id_usuario
           JOIN producto p ON m.id_producto = p.id_producto
           WHERE m.fecha_movimiento BETWEEN ? AND ?
           ORDER BY m.fecha_movimiento DESC""",
        (fecha_inicio, fecha_fin),
    )


def obtener_por_tipo(tipo_movimiento: str) -> list[dict]:
    return fetch_all(
        """SELECT m.*, u.username, p.nombre as producto_nombre, p.codigo
           FROM movimiento_inventario m
           JOIN usuario u ON m.id_usuario = u.id_usuario
           JOIN producto p ON m.id_producto = p.id_producto
           WHERE m.tipo_movimiento = ?
           ORDER BY m.fecha_movimiento DESC""",
        (tipo_movimiento,),
    )
