from database.connection import get_connection, fetch_one, fetch_all
from models.pago import Pago
from utils.dates import get_now


def insertar(pago: Pago) -> int:
    conn = get_connection()
    now = get_now()
    cursor = conn.execute(
        """INSERT INTO pago
           (id_usuario, numero_recibo, fecha_pago, monto_total,
            metodo_pago, observacion, comprobante_path, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            pago.id_usuario,
            pago.numero_recibo,
            pago.fecha_pago,
            pago.monto_total,
            pago.metodo_pago,
            pago.observacion,
            pago.comprobante_path or "",
            pago.activo,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_pago: int) -> dict | None:
    return fetch_one(
        """SELECT p.*, u.username
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           WHERE p.id_pago = ?""",
        (id_pago,),
    )


def obtener_por_recibo(numero_recibo: str) -> dict | None:
    return fetch_one(
        "SELECT * FROM pago WHERE numero_recibo = ?",
        (numero_recibo,),
    )


def obtener_todos(limit: int = 100, offset: int = 0) -> list[dict]:
    return fetch_all(
        """SELECT p.*, u.username
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           WHERE p.activo = 1
           ORDER BY p.fecha_pago DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    )


def obtener_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT p.*, u.username
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           WHERE p.fecha_pago BETWEEN ? AND ? AND p.activo = 1
           ORDER BY p.fecha_pago DESC""",
        (fecha_inicio, fecha_fin),
    )


def obtener_por_estudiante(id_estudiante: int) -> list[dict]:
    return fetch_all(
        """SELECT DISTINCT p.*, u.username
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           JOIN detalle_pago dp ON p.id_pago = dp.id_pago
           JOIN cuota c ON dp.id_cuota = c.id_cuota
           JOIN matricula m ON c.id_matricula = m.id_matricula
           WHERE m.id_estudiante = ? AND p.activo = 1
           ORDER BY p.fecha_pago DESC""",
        (id_estudiante,),
    )


def contar_por_fecha(fecha_inicio: str, fecha_fin: str) -> int:
    row = fetch_one(
        """SELECT COUNT(*) as total FROM pago
           WHERE fecha_pago BETWEEN ? AND ? AND activo = 1""",
        (fecha_inicio, fecha_fin),
    )
    return row["total"] if row else 0


def sumar_por_fecha(fecha_inicio: str, fecha_fin: str) -> float:
    row = fetch_one(
        """SELECT COALESCE(SUM(monto_total), 0) as total FROM pago
           WHERE fecha_pago BETWEEN ? AND ? AND activo = 1""",
        (fecha_inicio, fecha_fin),
    )
    return row["total"] if row else 0.0


def buscar_paginado(q: str = "", limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    """Búsqueda SQL real (recibo/método/documento/nombres) con paginación."""
    base = """
        FROM pago p
        JOIN usuario u ON p.id_usuario = u.id_usuario
        LEFT JOIN detalle_pago dp ON dp.id_pago = p.id_pago
        LEFT JOIN cuota c ON c.id_cuota = dp.id_cuota
        LEFT JOIN matricula m ON m.id_matricula = c.id_matricula
        LEFT JOIN estudiante e ON e.id_estudiante = m.id_estudiante
        LEFT JOIN persona per ON per.id_persona = e.id_persona
        WHERE p.activo = 1
    """
    params: list = []
    if q and q.strip():
        like = f"%{q.strip()}%"
        base += """ AND (p.numero_recibo LIKE ? OR p.metodo_pago LIKE ?
                         OR per.dni LIKE ? OR per.nombres LIKE ? OR per.apellidos LIKE ?)"""
        params.extend([like, like, like, like, like])
    cnt = fetch_one(f"SELECT COUNT(DISTINCT p.id_pago) as c {base}", tuple(params))
    total = cnt["c"] if cnt else 0
    rows = fetch_all(
        f"""SELECT DISTINCT p.*, u.username, per.dni, per.nombres, per.apellidos {base}
            ORDER BY p.fecha_pago DESC LIMIT ? OFFSET ?""",
        tuple(params + [limit, offset]),
    )
    return rows, total


def obtener_sin_comprobante(limit: int = 200) -> list[dict]:
    """Fase 1: pagos no-efectivo sin comprobante archivado (RN-042 pendiente).

    Cubre históricos (pre-Fase-0, cuando se descartaba) y cualquier vía que
    guarde sin archivo.
    """
    return fetch_all(
        """SELECT DISTINCT p.*, u.username, per.dni, per.nombres, per.apellidos
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           LEFT JOIN detalle_pago dp ON dp.id_pago = p.id_pago
           LEFT JOIN cuota c ON c.id_cuota = dp.id_cuota
           LEFT JOIN matricula m ON m.id_matricula = c.id_matricula
           LEFT JOIN estudiante e ON e.id_estudiante = m.id_estudiante
           LEFT JOIN persona per ON per.id_persona = e.id_persona
           WHERE p.activo = 1 AND p.metodo_pago <> 'EFECTIVO'
                 AND (p.comprobante_path IS NULL OR p.comprobante_path = '')
           ORDER BY p.fecha_pago DESC LIMIT ?""",
        (limit,),
    )


def buscar_por_texto(texto: str) -> list[dict]:
    like = f"%{texto}%"
    return fetch_all(
        """SELECT DISTINCT p.*, u.username, per.dni, per.nombres, per.apellidos
           FROM pago p
           JOIN usuario u ON p.id_usuario = u.id_usuario
           LEFT JOIN detalle_pago dp ON dp.id_pago = p.id_pago
           LEFT JOIN cuota c ON c.id_cuota = dp.id_cuota
           LEFT JOIN matricula m ON m.id_matricula = c.id_matricula
           LEFT JOIN estudiante e ON e.id_estudiante = m.id_estudiante
           LEFT JOIN persona per ON per.id_persona = e.id_persona
           WHERE p.activo=1 AND (p.numero_recibo LIKE ? OR p.metodo_pago LIKE ? OR per.dni LIKE ? OR per.nombres LIKE ? OR per.apellidos LIKE ?)
           ORDER BY p.fecha_pago DESC LIMIT 100""",
        (like, like, like, like, like),
    )
