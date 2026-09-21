from database.connection import get_connection, fetch_one, fetch_all
from models.venta import Venta


def insertar(venta: Venta) -> int:
    conn = get_connection()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(venta)").fetchall()]
    except Exception:
        cols = []
    if "id_tarifa" in cols:
        cursor = conn.execute(
            """INSERT INTO venta (id_estudiante, id_usuario, fecha_venta, monto_total, metodo_pago, tipo_venta, numero_recibo, comprobante_path, id_tarifa, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                venta.id_estudiante,
                venta.id_usuario,
                venta.fecha_venta,
                venta.monto_total,
                venta.metodo_pago,
                venta.tipo_venta,
                venta.numero_recibo,
                venta.comprobante_path,
                venta.id_tarifa,
                venta.activo,
            ),
        )
    else:
        cursor = conn.execute(
            """INSERT INTO venta (id_estudiante, id_usuario, fecha_venta, monto_total, metodo_pago, tipo_venta, numero_recibo, comprobante_path, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                venta.id_estudiante,
                venta.id_usuario,
                venta.fecha_venta,
                venta.monto_total,
                venta.metodo_pago,
                venta.tipo_venta,
                venta.numero_recibo,
                venta.comprobante_path,
                venta.activo,
            ),
        )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_venta: int) -> dict | None:
    return fetch_one("SELECT * FROM venta WHERE id_venta = ?", (id_venta,))


def obtener_todos(fecha_inicio: str | None = None, fecha_fin: str | None = None, tipo_venta: str | None = None) -> list[dict]:
    sql = "SELECT * FROM venta WHERE activo = 1"
    params: list = []
    if fecha_inicio:
        sql += " AND fecha_venta >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        sql += " AND fecha_venta <= ?"
        params.append(fecha_fin)
    if tipo_venta:
        sql += " AND tipo_venta = ?"
        params.append(tipo_venta)
    sql += " ORDER BY fecha_venta DESC"
    return fetch_all(sql, tuple(params))


def obtener_por_estudiante(id_estudiante: int) -> list[dict]:
    return fetch_all("SELECT * FROM venta WHERE id_estudiante = ? AND activo = 1 ORDER BY fecha_venta DESC", (id_estudiante,))


def sumar_por_periodo(fecha_inicio: str, fecha_fin: str) -> float:
    row = fetch_one("SELECT COALESCE(SUM(monto_total),0) as total FROM venta WHERE fecha_venta BETWEEN ? AND ? AND activo = 1", (fecha_inicio, fecha_fin))
    return float(row["total"]) if row else 0.0


def ventas_por_metodo(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT metodo_pago AS metodo, COALESCE(SUM(monto_total), 0) AS total,
                  COUNT(*) AS n
           FROM venta
           WHERE fecha_venta BETWEEN ? AND ? AND activo = 1
             AND metodo_pago IN ('YAPE', 'EFECTIVO')
           GROUP BY metodo_pago""",
        (fecha_inicio, fecha_fin),
    )


def detalle_ganancia_por_venta(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT v.numero_recibo AS recibo, v.metodo_pago AS metodo,
                  v.fecha_venta AS fecha,
                  COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS ingresos,
                  COALESCE(SUM(d.cantidad * (d.precio_unitario - COALESCE(p.precio_compra, 0))), 0) AS ganancia
           FROM venta v
           JOIN detalle_venta d ON d.id_venta = v.id_venta
           JOIN producto p ON p.id_producto = d.id_producto
           WHERE v.fecha_venta BETWEEN ? AND ? AND v.activo = 1
             AND v.metodo_pago IN ('YAPE', 'EFECTIVO')
           GROUP BY v.id_venta
           ORDER BY v.fecha_venta DESC""",
        (fecha_inicio, fecha_fin),
    )


def ganancia_por_metodo(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """Ganancia = Σ cantidad × (precio_unitario − costo actual). Aproximación
    documentada: usa el costo unitario vigente del producto."""
    return fetch_all(
        """SELECT v.metodo_pago AS metodo,
                  COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS ingresos,
                  COALESCE(SUM(d.cantidad * (d.precio_unitario - COALESCE(p.precio_compra, 0))), 0) AS ganancia
           FROM venta v
           JOIN detalle_venta d ON d.id_venta = v.id_venta
           JOIN producto p ON p.id_producto = d.id_producto
           WHERE v.fecha_venta BETWEEN ? AND ? AND v.activo = 1
             AND v.metodo_pago IN ('YAPE', 'EFECTIVO')
           GROUP BY v.metodo_pago""",
        (fecha_inicio, fecha_fin),
    )


def soft_delete(id_venta: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE venta SET activo = 0 WHERE id_venta = ?", (id_venta,))
    conn.commit()
