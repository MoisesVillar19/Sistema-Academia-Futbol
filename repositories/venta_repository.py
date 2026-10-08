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


def actualizar_campos(id_venta: int, fecha_venta: str, metodo_pago: str,
                       comprobante_path: str | None) -> None:
    """Edición acotada: fecha/método/comprobante (sin tocar ítems/stock)."""
    conn = get_connection()
    conn.execute(
        """UPDATE venta SET fecha_venta = ?, metodo_pago = ?,
           comprobante_path = ? WHERE id_venta = ?""",
        (fecha_venta, metodo_pago, comprobante_path, id_venta),
    )
    conn.commit()


def obtener_todos(fecha_inicio: str | None = None, fecha_fin: str | None = None,
                  tipo_venta: str | None = None, anio: int | None = None,
                  meses: list[int] | None = None,
                  orden: str | None = None) -> list[dict]:
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
    if anio:
        sql += " AND strftime('%Y', fecha_venta) = ?"
        params.append(str(anio))
    if meses:
        sql += " AND strftime('%m', fecha_venta) IN (%s)" % ",".join("?" for _ in meses)
        params.extend([f"{m:02d}" for m in meses])
    sql += " ORDER BY fecha_venta %s" % ("ASC" if orden == "ASC" else "DESC")
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


def obtener_uniformes(limit: int = 200, anio: int | None = None,
                      meses: list[int] | None = None,
                      orden: str | None = None) -> list[dict]:
    """Ventas de uniforme en 1 query (estudiante + producto incluidos)."""
    sql = """SELECT v.*, per.nombres, per.apellidos,
                    GROUP_CONCAT(p.codigo, ',') AS codigos,
                    GROUP_CONCAT(p.nombre, ' | ') AS productos_txt,
                    SUM(d.cantidad) AS cantidad_total
             FROM venta v
             JOIN detalle_venta d ON d.id_venta = v.id_venta
             JOIN producto p ON p.id_producto = d.id_producto
             LEFT JOIN estudiante e ON e.id_estudiante = v.id_estudiante
             LEFT JOIN persona per ON per.id_persona = e.id_persona
             WHERE v.activo = 1
               AND (v.tipo_venta = 'UNIFORME'
                    OR p.codigo IN ('UNIFORME-COM', 'CAMISETA-ENT'))"""
    params: list = []
    if anio:
        sql += " AND strftime('%Y', v.fecha_venta) = ?"
        params.append(str(anio))
    if meses:
        sql += " AND strftime('%m', v.fecha_venta) IN (%s)" % ",".join("?" for _ in meses)
        params.extend([f"{m:02d}" for m in meses])
    sql += " GROUP BY v.id_venta ORDER BY v.fecha_venta %s LIMIT ?" % (
        "ASC" if orden == "ASC" else "DESC")
    params.append(limit)
    return fetch_all(sql, tuple(params))


def detalle_ventas_por_producto(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """Balance estilo Excel: por producto, con split YAPE/EFECTIVO por montos.
    Ganancia con costo vigente (misma aproximación que ganancia_por_metodo)."""
    return fetch_all(
        """SELECT p.id_producto AS id_producto, p.nombre AS nombre, p.codigo AS codigo,
                  COALESCE(SUM(d.cantidad), 0) AS vendidas,
                  COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS ingresos,
                  COALESCE(SUM(d.cantidad * (d.precio_unitario - COALESCE(p.precio_compra, 0))), 0) AS ganancia,
                  COALESCE(SUM(CASE WHEN v.metodo_pago = 'YAPE' THEN d.cantidad * d.precio_unitario ELSE 0 END), 0) AS monto_yape,
                  COALESCE(SUM(CASE WHEN v.metodo_pago = 'EFECTIVO' THEN d.cantidad * d.precio_unitario ELSE 0 END), 0) AS monto_efectivo
           FROM detalle_venta d
           JOIN venta v ON v.id_venta = d.id_venta
           JOIN producto p ON p.id_producto = d.id_producto
           WHERE v.fecha_venta BETWEEN ? AND ? AND v.activo = 1
             AND v.metodo_pago IN ('YAPE', 'EFECTIVO')
           GROUP BY p.id_producto
           ORDER BY p.nombre""",
        (fecha_inicio, fecha_fin),
    )


def soft_delete(id_venta: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE venta SET activo = 0 WHERE id_venta = ?", (id_venta,))
    conn.commit()
