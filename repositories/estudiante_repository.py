from database.connection import get_connection, fetch_one, fetch_all
from models.estudiante import Estudiante
from utils.dates import get_now


def insertar(estudiante: Estudiante) -> int:
    conn = get_connection()
    now = get_now()
    cursor = conn.execute(
        """INSERT INTO estudiante
           (id_persona, estado, fecha_ingreso, fecha_retiro, es_nuevo, foto_path, comprobante_pago_path, fecha_matricula, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            estudiante.id_persona,
            estudiante.estado,
            estudiante.fecha_ingreso,
            estudiante.fecha_retiro,
            getattr(estudiante, "es_nuevo", 0),
            estudiante.foto_path,
            estudiante.comprobante_pago_path,
            estudiante.fecha_matricula,
            estudiante.activo,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def actualizar_foto(id_estudiante: int, foto_path: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE estudiante SET foto_path = ? WHERE id_estudiante = ?", (foto_path, id_estudiante))
    conn.commit()


def obtener_por_id(id_estudiante: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM estudiante WHERE id_estudiante = ?",
        (id_estudiante,),
    )


def obtener_por_persona(id_persona: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM estudiante WHERE id_persona = ?",
        (id_persona,),
    )


def obtener_todos(activo: int | None = None, estado=None) -> list[dict]:
    sql = """
        SELECT e.*, p.dni, p.nombres, p.apellidos, p.fecha_nacimiento,
               p.sexo, p.telefono, p.correo
        FROM estudiante e
        JOIN persona p ON e.id_persona = p.id_persona
    """
    conditions = []
    params = []
    if activo is not None:
        conditions.append("e.activo = ?")
        params.append(activo)
    if estado is not None:
        if isinstance(estado, (list, tuple)):
            placeholders = ",".join("?" * len(estado))
            conditions.append(f"e.estado IN ({placeholders})")
            params.extend(estado)
        else:
            conditions.append("e.estado = ?")
            params.append(estado)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    return fetch_all(sql, tuple(params))


def obtener_becados(activo: int | None = 1) -> list[dict]:
    """Estudiantes con beca activa en matrícula, con nombre de beca (filtro Becados)."""
    sql = """
        SELECT DISTINCT e.*, p.dni, p.nombres, p.apellidos, p.fecha_nacimiento,
               p.sexo, p.telefono, p.correo, b.nombre AS beca_nombre,
               b.tipo AS beca_tipo, b.valor AS beca_valor
        FROM estudiante e
        JOIN persona p ON e.id_persona = p.id_persona
        JOIN matricula m ON m.id_estudiante = e.id_estudiante AND m.activo = 1
        JOIN matricula_beca mb ON mb.id_matricula = m.id_matricula AND mb.activo = 1
        JOIN beca b ON b.id_beca = mb.id_beca AND b.activo = 1
    """
    params: list = []
    if activo is not None:
        sql += " WHERE e.activo = ?"
        params.append(activo)
    sql += " ORDER BY p.apellidos, p.nombres"
    return fetch_all(sql, tuple(params))


def obtener_por_id_con_persona(id_estudiante: int) -> dict | None:
    return fetch_one(
        """SELECT e.*, p.dni, p.nombres, p.apellidos, p.fecha_nacimiento,
                  p.sexo, p.direccion, p.telefono, p.correo
           FROM estudiante e
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE e.id_estudiante = ?""",
        (id_estudiante,),
    )


def contar_nuevos_por_periodo(fecha_inicio: str, fecha_fin: str) -> int:
    row = fetch_one("SELECT COUNT(*) as total FROM estudiante WHERE fecha_ingreso BETWEEN ? AND ? AND activo=1", (fecha_inicio, fecha_fin))
    return row["total"] if row else 0


def contar_nuevos_es_nuevo(activo: int = 1) -> int:
    row = fetch_one("SELECT COUNT(*) as total FROM estudiante WHERE es_nuevo=1 AND activo=?", (activo,))
    return row["total"] if row else 0


def listar_nuevos_por_periodo(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return fetch_all(
        """SELECT e.*, p.dni, p.nombres, p.apellidos, p.fecha_nacimiento,
                  p.sexo, p.telefono, p.correo
           FROM estudiante e
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE e.es_nuevo = 1 AND e.fecha_ingreso BETWEEN ? AND ?
                 AND e.activo = 1
           ORDER BY e.fecha_ingreso DESC""",
        (fecha_inicio, fecha_fin),
    )


def contar_por_es_nuevo(es_nuevo: int = 1, fecha_inicio: str | None = None, fecha_fin: str | None = None) -> int:
    if fecha_inicio and fecha_fin:
        row = fetch_one("SELECT COUNT(*) as total FROM estudiante WHERE es_nuevo=? AND fecha_ingreso BETWEEN ? AND ? AND activo=1", (es_nuevo, fecha_inicio, fecha_fin))
    else:
        row = fetch_one("SELECT COUNT(*) as total FROM estudiante WHERE es_nuevo=? AND activo=1", (es_nuevo,))
    return row["total"] if row else 0


def actualizar(estudiante: Estudiante) -> None:
    conn = get_connection()
    now = get_now()
    conn.execute(
        """UPDATE estudiante SET
           id_persona = ?, estado = ?, fecha_ingreso = ?,
           fecha_retiro = ?, activo = ?
           WHERE id_estudiante = ?""",
        (
            estudiante.id_persona,
            estudiante.estado,
            estudiante.fecha_ingreso,
            estudiante.fecha_retiro,
            estudiante.activo,
            estudiante.id_estudiante,
        ),
    )
    conn.commit()


def cambiar_estado(id_estudiante: int, estado: str, fecha_retiro: str | None = None) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE estudiante SET estado = ?, fecha_retiro = ? WHERE id_estudiante = ?",
        (estado, fecha_retiro, id_estudiante),
    )
    conn.commit()


def soft_delete(id_estudiante: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE estudiante SET activo = 0 WHERE id_estudiante = ?",
        (id_estudiante,),
    )
    conn.commit()


def buscar_paginado(q: str = "", activo: int | None = 1, estado=None, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    where = []
    params = []
    if activo is not None:
        where.append("e.activo = ?")
        params.append(activo)
    if estado is not None:
        if isinstance(estado, (list, tuple)):
            placeholders = ",".join("?" * len(estado))
            where.append(f"e.estado IN ({placeholders})")
            params.extend(estado)
        else:
            where.append("e.estado = ?")
            params.append(estado)
    if q:
        like = f"%{q}%"
        where.append("(p.dni LIKE ? OR p.nombres LIKE ? OR p.apellidos LIKE ?)")
        params.extend([like, like, like])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    base = f"FROM estudiante e JOIN persona p ON e.id_persona=p.id_persona{where_sql}"
    cnt = fetch_one(f"SELECT COUNT(*) as c {base}", tuple(params))
    total = cnt["c"] if cnt else 0
    rows = fetch_all(f"SELECT e.*, p.dni, p.nombres, p.apellidos, p.fecha_nacimiento, p.sexo, p.telefono, p.correo {base} ORDER BY p.apellidos, p.nombres LIMIT ? OFFSET ?", tuple(params + [limit, offset]))
    return rows, total
