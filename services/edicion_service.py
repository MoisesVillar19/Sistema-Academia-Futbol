"""Edición exclusiva (v1.2.3): una sola PC hace edición masiva a la vez.

Importaciones y restauraciones son las escrituras largas que truncaron la BD
en red (caso 2026-10-10). Con la bandera activa por otra PC, esos flujos se
RECHAZAN con mensaje claro; cobros, ventas, matrículas y consultas nunca se
bloquean. Stale: expira a las 2h (cierre brusco del dueño).
"""
import os
import socket
from datetime import datetime, timedelta

from database.connection import fetch_one, get_connection
from utils.logger import logger

STALE_MINUTOS = 120


def _pc_actual() -> str:
    return (os.environ.get("COMPUTERNAME")
            or os.environ.get("HOSTNAME")
            or socket.gethostname() or "PC").strip()


def _usuario_actual() -> str:
    try:
        from services import auth_service
        u = auth_service.obtener_usuario_actual() or {}
        return str(u.get("username", "") or "")
    except Exception:
        return ""


def _ahora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _es_stale(desde: str) -> bool:
    try:
        dt = datetime.fromisoformat(str(desde or ""))
    except ValueError:
        return True
    return datetime.now() - dt > timedelta(minutes=STALE_MINUTOS)


def estado() -> dict:
    """{activo, pc, username, motivo, desde}. Stale se auto-libera."""
    try:
        row = fetch_one("SELECT * FROM edicion_exclusiva WHERE id_edicion = 1")
    except Exception:
        return {"activo": 0}
    if not row or not row.get("activo"):
        return {"activo": 0}
    if _es_stale(row.get("desde", "")):
        try:
            liberar(forzado=True)
        except Exception:
            pass
        return {"activo": 0}
    return {"activo": 1, "pc": row.get("pc", ""), "username": row.get("username", ""),
            "motivo": row.get("motivo", ""), "desde": row.get("desde", "")}


def _soy_yo(st: dict) -> bool:
    return bool(st.get("activo")) and st.get("pc") == _pc_actual() \
        and st.get("username") == _usuario_actual()


def es_mia() -> bool:
    """True si esta PC/usuario tiene la edición exclusiva."""
    try:
        return _soy_yo(estado())
    except Exception:
        return False


def activar(motivo: str = "edición masiva") -> tuple[bool, str]:
    """Toma la edición exclusiva (solo ADMIN). Idempotente si ya la tengo."""
    from services import auth_service
    if not auth_service.es_admin():
        return False, "Solo ADMIN puede activar la edición exclusiva"
    st = estado()
    if st.get("activo"):
        if _soy_yo(st):
            return True, "Ya tienes la edición exclusiva"
        return False, (f"Edición exclusiva activa en {st.get('pc')} "
                       f"por {st.get('username')} desde {st.get('desde')} "
                       f"({st.get('motivo')}). Espera a que la libere.")
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO edicion_exclusiva (id_edicion, activo, pc, username, motivo, desde)
               VALUES (1, 1, ?, ?, ?, ?)
               ON CONFLICT(id_edicion) DO UPDATE SET
                 activo=1, pc=excluded.pc, username=excluded.username,
                 motivo=excluded.motivo, desde=excluded.desde""",
            (_pc_actual(), _usuario_actual(), (motivo or "")[:120], _ahora_iso()),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"activar edicion exclusiva fallo: {e}")
        return False, "No se pudo activar la edición exclusiva"
    try:
        from services import auditoria_service
        auditoria_service.registrar_insert(
            auditoria_service.id_usuario_sesion(),
            "edicion_exclusiva", 1, f"activada por {_usuario_actual()}@{_pc_actual()}: {motivo}")
    except Exception:
        pass
    return True, f"Edición exclusiva activada ({motivo}). Libérala al terminar."


def liberar(forzado: bool = False) -> tuple[bool, str]:
    """Libera la bandera. Solo el dueño o ADMIN (forzado = stale/auto)."""
    st = estado()
    if not st.get("activo"):
        return True, "No había edición exclusiva activa"
    if not forzado:
        from services import auth_service
        if not _soy_yo(st) and not auth_service.es_admin():
            return False, "Solo quien la activó (o ADMIN) puede liberarla"
    try:
        conn = get_connection()
        conn.execute("UPDATE edicion_exclusiva SET activo = 0 WHERE id_edicion = 1")
        conn.commit()
    except Exception as e:
        logger.error(f"liberar edicion exclusiva fallo: {e}")
        return False, "No se pudo liberar la edición exclusiva"
    try:
        from services import auditoria_service
        auditoria_service.registrar_update(
            auditoria_service.id_usuario_sesion(), "edicion_exclusiva", 1,
            "activo=1", "activo=0")
    except Exception:
        pass
    return True, "Edición exclusiva liberada"


def exigir_libre(operacion: str = "esta operación") -> tuple[bool, str]:
    """Guardián para importaciones/restauraciones. (True, '') si puedo seguir."""
    st = estado()
    if not st.get("activo") or _soy_yo(st):
        return True, ""
    return False, (f"No se puede iniciar {operacion}: edición exclusiva activa "
                    f"en {st.get('pc')} por {st.get('username')} "
                    f"({st.get('motivo')}). Avísale que la libere.")


def descripcion_estado() -> str:
    st = estado()
    if not st.get("activo"):
        return "Edición masiva: libre"
    marca = " (tuya)" if _soy_yo(st) else ""
    return (f"Edición exclusiva{marca}: {st.get('pc')} / {st.get('username')} "
            f"desde {st.get('desde')} ({st.get('motivo')})")
