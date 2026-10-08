from database.connection import get_connection, fetch_one, fetch_all
from models.tarifa import Tarifa
from utils.dates import get_now


def insertar(tarifa: Tarifa) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO tarifa
           (id_categoria, nombre, monto, descripcion, observaciones,
            fecha_vigencia_desde, fecha_vigencia_hasta, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tarifa.id_categoria,
            tarifa.nombre,
            tarifa.monto,
            tarifa.descripcion,
            tarifa.observaciones,
            tarifa.fecha_vigencia_desde,
            tarifa.fecha_vigencia_hasta,
            tarifa.activo,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_tarifa: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM tarifa WHERE id_tarifa = ?",
        (id_tarifa,),
    )


def obtener_por_categoria(id_categoria: int) -> list[dict]:
    return fetch_all(
        """SELECT t.*, c.nombre as categoria_nombre
           FROM tarifa t
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE t.id_categoria = ? AND t.activo = 1
           ORDER BY t.nombre""",
        (id_categoria,),
    )


def obtener_activas(tipo: str | None = None) -> list[dict]:
    sql = """SELECT t.*, c.nombre as categoria_nombre, c.tipo as categoria_tipo
           FROM tarifa t
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE t.activo = 1"""
    params: list = []
    if tipo:
        sql += " AND c.tipo = ?"
        params.append(tipo)
    sql += " ORDER BY c.nombre, t.nombre"
    return fetch_all(sql, tuple(params))


def obtener_vigente(tipo: str, fecha: str) -> dict | None:
    """Obtiene la tarifa vigente para un tipo en una fecha dada."""
    return fetch_one(
        """SELECT t.*, c.nombre as categoria_nombre, c.tipo as categoria_tipo
           FROM tarifa t
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE c.tipo = ? AND t.activo = 1
           AND (t.fecha_vigencia_desde IS NULL OR t.fecha_vigencia_desde <= ?)
           AND (t.fecha_vigencia_hasta IS NULL OR t.fecha_vigencia_hasta >= ?)
           ORDER BY t.fecha_vigencia_desde DESC
           LIMIT 1""",
        (tipo, fecha, fecha),
    )


def actualizar(tarifa: Tarifa) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE tarifa SET
           id_categoria = ?, nombre = ?, monto = ?,
           descripcion = ?, observaciones = ?,
           fecha_vigencia_desde = ?, fecha_vigencia_hasta = ?, activo = ?
           WHERE id_tarifa = ?""",
        (
            tarifa.id_categoria,
            tarifa.nombre,
            tarifa.monto,
            tarifa.descripcion,
            tarifa.observaciones,
            tarifa.fecha_vigencia_desde,
            tarifa.fecha_vigencia_hasta,
            tarifa.activo,
            tarifa.id_tarifa,
        ),
    )
    conn.commit()


def obtener_inactivas() -> list[dict]:
    return fetch_all(
        """SELECT t.*, c.nombre as categoria_nombre, c.tipo as categoria_tipo
           FROM tarifa t
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE t.activo = 0
           ORDER BY c.nombre, t.nombre""",
    )


def soft_delete(id_tarifa: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE tarifa SET activo = 0 WHERE id_tarifa = ?",
        (id_tarifa,),
    )
    conn.commit()


def activar(id_tarifa: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE tarifa SET activo = 1 WHERE id_tarifa = ?",
        (id_tarifa,),
    )
    conn.commit()


def contar_matriculas_por_tarifa(id_tarifa: int) -> int:
    row = fetch_one(
        "SELECT COUNT(*) as cnt FROM matricula WHERE id_tarifa = ? AND activo = 1",
        (id_tarifa,),
    )
    return row["cnt"] if row else 0
