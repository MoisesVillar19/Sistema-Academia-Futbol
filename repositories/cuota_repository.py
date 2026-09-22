from database.connection import get_connection, fetch_one, fetch_all
from models.cuota import Cuota
from utils.dates import get_now


def insertar(cuota: Cuota) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO cuota
           (id_matricula, periodo, fecha_vencimiento, monto_total,
            monto_pagado, monto_mora, saldo, estado, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cuota.id_matricula,
            cuota.periodo,
            cuota.fecha_vencimiento,
            cuota.monto_total,
            cuota.monto_pagado,
            cuota.monto_mora,
            cuota.saldo,
            cuota.estado,
            cuota.activo,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def obtener_por_id(id_cuota: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM cuota WHERE id_cuota = ?",
        (id_cuota,),
    )


def obtener_por_matricula(id_matricula: int) -> list[dict]:
    return fetch_all(
        """SELECT * FROM cuota
           WHERE id_matricula = ?
           ORDER BY fecha_vencimiento""",
        (id_matricula,),
    )


def obtener_pendientes_por_matricula(id_matricula: int) -> list[dict]:
    return fetch_all(
        """SELECT * FROM cuota
           WHERE id_matricula = ? AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
           ORDER BY fecha_vencimiento""",
        (id_matricula,),
    )


def obtener_todas_pendientes() -> list[dict]:
    return fetch_all(
        """SELECT cu.*, p.nombres, p.apellidos, p.dni
           FROM cuota cu
           JOIN matricula m ON cu.id_matricula = m.id_matricula
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE cu.estado IN ('PENDIENTE', 'PARCIAL')
           AND cu.activo = 1
           ORDER BY cu.fecha_vencimiento""",
    )


def actualizar(cuota: Cuota) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE cuota SET
           id_matricula = ?, periodo = ?, fecha_vencimiento = ?,
           monto_total = ?, monto_pagado = ?, monto_mora = ?,
           saldo = ?, estado = ?, activo = ?
           WHERE id_cuota = ?""",
        (
            cuota.id_matricula,
            cuota.periodo,
            cuota.fecha_vencimiento,
            cuota.monto_total,
            cuota.monto_pagado,
            cuota.monto_mora,
            cuota.saldo,
            cuota.estado,
            cuota.activo,
            cuota.id_cuota,
        ),
    )
    conn.commit()


def obtener_por_anio(year: int) -> list[dict]:
    """Fase 7d: cuotas del año con estudiante (grilla anual estilo Excel)."""
    return fetch_all(
        """SELECT cu.*, p.nombres, p.apellidos, p.dni, e.id_estudiante
           FROM cuota cu
           JOIN matricula m ON cu.id_matricula = m.id_matricula
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE cu.activo = 1 AND substr(cu.fecha_vencimiento, 1, 4) = ?
           ORDER BY p.apellidos, p.nombres, cu.fecha_vencimiento""",
        (str(year),),
    )


def contar_por_estado(estado: str) -> int:
    row = fetch_one(
        "SELECT COUNT(*) as total FROM cuota WHERE estado = ? AND activo = 1",
        (estado,),
    )
    return row["total"] if row else 0


def obtener_vencidas() -> list[dict]:
    from utils.dates import get_today
    today = get_today()
    return fetch_all(
        """SELECT cu.*, p.nombres, p.apellidos, p.dni
           FROM cuota cu
           JOIN matricula m ON cu.id_matricula = m.id_matricula
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE cu.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
           AND cu.fecha_vencimiento < ?
           AND cu.activo = 1
           ORDER BY cu.fecha_vencimiento""",
        (today,),
    )


def obtener_por_vencer(dias: int = 3) -> list[dict]:
    from utils.dates import get_today
    from datetime import datetime, timedelta
    today = datetime.strptime(get_today(), "%Y-%m-%d")
    fecha_limite = (today + timedelta(days=dias)).strftime("%Y-%m-%d")
    today_str = get_today()
    return fetch_all(
        """SELECT cu.*, p.nombres, p.apellidos, p.dni
           FROM cuota cu
           JOIN matricula m ON cu.id_matricula = m.id_matricula
           JOIN estudiante e ON m.id_estudiante = e.id_estudiante
           JOIN persona p ON e.id_persona = p.id_persona
           WHERE cu.estado IN ('PENDIENTE', 'PARCIAL')
           AND cu.fecha_vencimiento BETWEEN ? AND ?
           AND cu.activo = 1
           ORDER BY cu.fecha_vencimiento""",
        (today_str, fecha_limite),
    )
