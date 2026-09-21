from database.connection import get_connection, fetch_one, fetch_all
from models.matricula import Matricula
from utils.dates import get_now


def insertar(matricula: Matricula) -> int:
    conn = get_connection()
    now = get_now()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(matricula)").fetchall()]
    except Exception:
        cols = []
    if "tipo" in cols and matricula.tipo:
        cursor = conn.execute(
            """INSERT INTO matricula
               (id_estudiante, id_tarifa, monto_pactado, pago_matricula, monto_matricula,
                fecha_inicio, fecha_fin, dia_vencimiento, tipo, estado, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                matricula.id_estudiante,
                matricula.id_tarifa,
                matricula.monto_pactado,
                matricula.pago_matricula,
                matricula.monto_matricula,
                matricula.fecha_inicio,
                matricula.fecha_fin,
                matricula.dia_vencimiento,
                matricula.tipo,
                matricula.estado,
                matricula.activo,
            ),
        )
    else:
        cursor = conn.execute(
            """INSERT INTO matricula
               (id_estudiante, id_tarifa, monto_pactado, pago_matricula, monto_matricula,
                fecha_inicio, fecha_fin, dia_vencimiento, estado, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                matricula.id_estudiante,
                matricula.id_tarifa,
                matricula.monto_pactado,
                matricula.pago_matricula,
                matricula.monto_matricula,
                matricula.fecha_inicio,
                matricula.fecha_fin,
                matricula.dia_vencimiento,
                matricula.estado,
                matricula.activo,
            ),
        )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_matricula: int) -> dict | None:
    return fetch_one(
        """SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                  c.nombre as categoria_nombre
           FROM matricula m
           JOIN tarifa t ON m.id_tarifa = t.id_tarifa
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE m.id_matricula = ?""",
        (id_matricula,),
    )


def obtener_por_estudiante(id_estudiante: int) -> list[dict]:
    return fetch_all(
        """SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                  c.nombre as categoria_nombre
           FROM matricula m
           JOIN tarifa t ON m.id_tarifa = t.id_tarifa
           JOIN categoria c ON t.id_categoria = c.id_categoria
           WHERE m.id_estudiante = ? AND m.activo = 1
           ORDER BY m.fecha_inicio DESC""",
        (id_estudiante,),
    )


def obtener_activas() -> list[dict]:
    return fetch_all(
        """SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                  c.nombre as categoria_nombre,
                  p.nombres, p.apellidos, p.dni
           FROM matricula m
           JOIN tarifa t ON m.id_tarifa = t.id_tarifa
           JOIN categoria c ON t.id_categoria = c.id_categoria
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE m.estado = 'ACTIVO' AND m.activo = 1
           ORDER BY p.apellidos, p.nombres""",
    )


def buscar_paginado(q: str = "", limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    """Búsqueda SQL real (documento/nombres/apellidos) con paginación.

    Cubre el mismo conjunto que ``obtener_activas`` (matriculas activas).
    """
    base = """
        FROM matricula m
        JOIN tarifa t ON m.id_tarifa = t.id_tarifa
        JOIN categoria c ON t.id_categoria = c.id_categoria
        JOIN estudiante e ON m.id_estudiante = e.id_estudiante
        JOIN persona p ON e.id_persona = p.id_persona
        WHERE m.estado = 'ACTIVO' AND m.activo = 1
    """
    params: list = []
    if q and q.strip():
        like = f"%{q.strip()}%"
        base += " AND (p.dni LIKE ? OR p.nombres LIKE ? OR p.apellidos LIKE ?)"
        params.extend([like, like, like])
    cnt = fetch_one(f"SELECT COUNT(*) as c {base}", tuple(params))
    total = cnt["c"] if cnt else 0
    rows = fetch_all(
        f"""SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                   c.nombre as categoria_nombre,
                   p.nombres, p.apellidos, p.dni {base}
            ORDER BY p.apellidos, p.nombres LIMIT ? OFFSET ?""",
        tuple(params + [limit, offset]),
    )
    return rows, total


def actualizar(matricula: Matricula) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE matricula SET
           id_estudiante = ?, id_tarifa = ?, monto_pactado = ?,
           pago_matricula = ?, monto_matricula = ?,
           fecha_inicio = ?, fecha_fin = ?, dia_vencimiento = ?,
           estado = ?, activo = ?
           WHERE id_matricula = ?""",
        (
            matricula.id_estudiante,
            matricula.id_tarifa,
            matricula.monto_pactado,
            matricula.pago_matricula,
            matricula.monto_matricula,
            matricula.fecha_inicio,
            matricula.fecha_fin,
            matricula.dia_vencimiento,
            matricula.estado,
            matricula.activo,
            matricula.id_matricula,
        ),
    )
    conn.commit()


def soft_delete(id_matricula: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE matricula SET activo = 0 WHERE id_matricula = ?",
        (id_matricula,),
    )
    conn.commit()


def cambiar_estado(id_matricula: int, estado: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE matricula SET estado = ? WHERE id_matricula = ?",
        (estado, id_matricula),
    )
    conn.commit()


def contar_por_mes(fecha_inicio: str, fecha_fin: str) -> int:
    row = fetch_one(
        """SELECT COUNT(*) as total FROM matricula
           WHERE fecha_inicio BETWEEN ? AND ? AND activo = 1""",
        (fecha_inicio, fecha_fin),
    )
    return row["total"] if row else 0


def listar_antiguos_por_mes(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                  c.nombre as categoria_nombre, e.es_nuevo as es_nuevo,
                  p.nombres, p.apellidos, p.dni
           FROM matricula m
           JOIN tarifa t ON m.id_tarifa = t.id_tarifa
           JOIN categoria c ON t.id_categoria = c.id_categoria
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE m.fecha_inicio BETWEEN ? AND ? AND m.activo = 1
                 AND e.es_nuevo = 0
           ORDER BY m.fecha_inicio DESC""",
        (fecha_inicio, fecha_fin),
    )


def listar_por_mes(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT m.*, t.nombre as tarifa_nombre, t.monto as tarifa_monto,
                  c.nombre as categoria_nombre, e.es_nuevo as es_nuevo,
                  p.nombres, p.apellidos, p.dni
           FROM matricula m
           JOIN tarifa t ON m.id_tarifa = t.id_tarifa
           JOIN categoria c ON t.id_categoria = c.id_categoria
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE m.fecha_inicio BETWEEN ? AND ? AND m.activo = 1
           ORDER BY m.fecha_inicio DESC""",
        (fecha_inicio, fecha_fin),
    )
