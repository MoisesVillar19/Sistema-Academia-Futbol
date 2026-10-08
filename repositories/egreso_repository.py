from database.connection import get_connection, fetch_one, fetch_all
from models.egreso import Egreso


def insertar(egreso: Egreso) -> int:
    conn = get_connection()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(egreso)").fetchall()]
    except Exception:
        cols = []
    if "id_tarifa" in cols:
        cursor = conn.execute(
            "INSERT INTO egreso (concepto, monto, fecha, responsable, id_usuario, observacion, comprobante_path, id_tarifa, activo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (egreso.concepto, egreso.monto, egreso.fecha, egreso.responsable, egreso.id_usuario, egreso.observacion, egreso.comprobante_path, egreso.id_tarifa, egreso.activo),
        )
    else:
        cursor = conn.execute(
            "INSERT INTO egreso (concepto, monto, fecha, responsable, id_usuario, observacion, comprobante_path, activo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (egreso.concepto, egreso.monto, egreso.fecha, egreso.responsable, egreso.id_usuario, egreso.observacion, egreso.comprobante_path, egreso.activo),
        )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_egreso: int) -> dict | None:
    return fetch_one("SELECT * FROM egreso WHERE id_egreso = ?", (id_egreso,))


def obtener_todos(fecha_inicio: str | None = None, fecha_fin: str | None = None,
                  anio: int | None = None, meses: list[int] | None = None,
                  orden: str | None = None, conceptos: list[str] | None = None,
                  limit: int | None = None) -> list[dict]:
    sql = "SELECT * FROM egreso WHERE 1=1"
    params: list = []
    if fecha_inicio:
        sql += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        sql += " AND fecha <= ?"
        params.append(fecha_fin)
    if anio:
        sql += " AND strftime('%Y', fecha) = ?"
        params.append(str(anio))
    if meses:
        sql += " AND strftime('%m', fecha) IN (%s)" % ",".join("?" for _ in meses)
        params.extend([f"{m:02d}" for m in meses])
    if conceptos:
        sql += " AND concepto IN (%s)" % ",".join("?" for _ in conceptos)
        params.extend(conceptos)
    sql += " ORDER BY fecha %s" % ("ASC" if orden == "ASC" else "DESC")
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return fetch_all(sql, tuple(params))


def ultimo_por_responsable(concepto: str = "PROFESOR") -> list[dict]:
    """Último egreso por responsable para un concepto (recordatorio)."""
    return fetch_all(
        """SELECT responsable, MAX(fecha) as ultima_fecha, COUNT(*) as n
           FROM egreso WHERE concepto = ? AND activo = 1
           GROUP BY responsable""",
        (concepto,),
    )


def sumar_por_periodo(fecha_inicio: str, fecha_fin: str) -> float:
    row = fetch_one("SELECT COALESCE(SUM(monto),0) as total FROM egreso WHERE fecha BETWEEN ? AND ? AND activo = 1", (fecha_inicio, fecha_fin))
    return float(row["total"]) if row else 0.0


def soft_delete(id_egreso: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE egreso SET activo = 0 WHERE id_egreso = ?", (id_egreso,))
    conn.commit()


def eliminar(id_egreso: int) -> None:
    # Deprecado: usar soft_delete para RN-028
    soft_delete(id_egreso)
