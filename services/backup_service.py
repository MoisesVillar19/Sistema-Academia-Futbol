import glob
import os
from datetime import datetime

from database.backup import create_backup
from services import auditoria_service, configuracion_service
from utils.logger import logger


def _ruta_escribible(ruta: str) -> bool:
    """Prueba escritura real (detecta share caído o sin permisos)."""
    try:
        os.makedirs(ruta, exist_ok=True)
        test = os.path.join(ruta, ".write_test")
        with open(test, "w", encoding="utf-8") as f:
            f.write("ok")
        try:
            os.remove(test)
        except Exception:
            pass
        return True
    except Exception:
        return False


def _resolver_ruta_backup() -> str:
    """Resuelve la carpeta de respaldos desde CONFIGURACION.ruta_backup (RN-029).

    Rutas relativas se interpretan respecto al directorio de la aplicacion.
    Si no hay configuracion, usa la carpeta detectada por defecto.
    Fallback (red): si el destino central no es escribible (servidor
    apagado/sin permisos), usa la carpeta local y lo advierte en el log,
    para que cada PC conserve su última foto útil.
    """
    from utils.constants import APP_DIR, BACKUP_DIR
    ruta = configuracion_service.obtener_valor("ruta_backup")
    if not ruta or not str(ruta).strip():
        return BACKUP_DIR
    ruta = str(ruta).strip()
    if not os.path.isabs(ruta):
        ruta = os.path.join(APP_DIR, ruta)
    if _ruta_escribible(ruta):
        return ruta
    logger.warning(f"Backup central inaccesible, usando local: {ruta} -> {BACKUP_DIR}")
    return BACKUP_DIR


def crear_backup(id_usuario: int | None = None) -> tuple[bool, str, str | None]:
    """Crea un respaldo de la BD y lo registra en auditoria (RN-030)."""
    try:
        destino = _resolver_ruta_backup()
        ruta_respaldo = create_backup(custom_path=destino)
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        return False, f"Error al crear el respaldo: {e}", None

    auditoria_service.registrar_log(
        id_usuario=id_usuario or auditoria_service.id_usuario_sesion(),
        tabla_afectada="sistema",
        id_registro=0,
        accion="BACKUP",
        valor_nuevo=ruta_respaldo,
    )
    logger.info(f"Backup creado: {ruta_respaldo}")
    msg = "Respaldo creado correctamente"
    try:
        from utils.constants import APP_DIR
        cfg = str(configuracion_service.obtener_valor("ruta_backup") or "").strip()
        cfg_abs = cfg if os.path.isabs(cfg) else (os.path.join(APP_DIR, cfg) if cfg else "")
        if cfg_abs and os.path.abspath(destino) != os.path.abspath(cfg_abs):
            msg += " (copia LOCAL: destino central inaccesible)"
    except Exception:
        pass
    return True, msg, ruta_respaldo


def dias_desde_ultimo_backup() -> float | None:
    """Dias transcurridos desde el respaldo mas reciente (None si nunca hubo)."""
    destino = _resolver_ruta_backup()
    archivos = glob.glob(os.path.join(destino, "academia_*.db"))
    if not archivos:
        return None
    ultimo_mtime = max(os.path.getmtime(a) for a in archivos)
    delta = datetime.now() - datetime.fromtimestamp(ultimo_mtime)
    return delta.total_seconds() / 86400


def listar_backups() -> list[dict]:
    """Lista backups con fecha UTC-5, tamaño y hash corto."""
    import hashlib
    destino = _resolver_ruta_backup()
    archivos = glob.glob(os.path.join(destino, "academia_*.db"))
    lista = []
    for f in sorted(archivos, key=lambda x: os.path.getmtime(x), reverse=True):
        try:
            st = os.stat(f)
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    h.update(chunk)
            lista.append({"ruta": f, "fecha": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M (UTC-5)"), "tamano_mb": round(st.st_size/1024/1024,2), "hash": h.hexdigest()[:8]})
        except Exception:
            lista.append({"ruta": f, "fecha": "", "tamano_mb": 0, "hash": ""})
    return lista

def verificar_backup(ruta: str) -> tuple[bool, str]:
    """Verifica que el backup sea legible y no corrupto (cabecera SQLite)."""
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master LIMIT 1")
        cur.fetchone()
        conn.close()
        return True, "Backup verificado correctamente"
    except Exception as e:
        return False, f"Backup corrupto: {e}"

LOCK_RESTORE_NOMBRE = ".restore_lock"
LOCK_RESTORE_TIMEOUT_SEG = 30 * 60


def _info_pc() -> dict:
    import socket
    try:
        pc = socket.gethostname()
    except Exception:
        pc = "?"
    try:
        usuario = (auditoria_service.id_usuario_sesion() and
                   f"id={auditoria_service.id_usuario_sesion()}") or "?"
    except Exception:
        usuario = "?"
    return {"pc": pc, "usuario": usuario, "pid": os.getpid()}


def hay_restauracion_en_curso() -> tuple[bool, dict | None]:
    """Detecta lock de otra PC (con expiración anti-zombi)."""
    import json
    import time
    lock = os.path.join(_resolver_ruta_backup(), LOCK_RESTORE_NOMBRE)
    try:
        with open(lock, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception:
        return False, None
    try:
        edad = time.time() - float(info.get("ts", 0))
    except Exception:
        edad = LOCK_RESTORE_TIMEOUT_SEG + 1
    if edad < LOCK_RESTORE_TIMEOUT_SEG:
        return True, info
    try:
        os.remove(lock)  # rancio: liberar
    except Exception:
        pass
    return False, None


def adquirir_lock_restore() -> tuple[bool, str]:
    import json
    import time
    ocupado, info = hay_restauracion_en_curso()
    if ocupado:
        quien = f"{info.get('pc','?')} ({info.get('usuario','?')})" if info else "otra PC"
        return False, (f"Otra PC está restaurando ({quien}). "
                       "Pida que cierren la app e intente de nuevo.")
    try:
        datos = _info_pc()
        datos["ts"] = time.time()
        with open(os.path.join(_resolver_ruta_backup(), LOCK_RESTORE_NOMBRE),
                  "w", encoding="utf-8") as f:
            json.dump(datos, f)
        return True, ""
    except Exception as e:
        return False, f"No se pudo coordinar: {e}"


def liberar_lock_restore() -> None:
    try:
        os.remove(os.path.join(_resolver_ruta_backup(), LOCK_RESTORE_NOMBRE))
    except Exception:
        pass


def restaurar_backup(ruta: str, pin: str) -> tuple[bool, str]:
    """Restaura con PIN de emergencia, cierra conexión y copia.

    Coordinación multi-PC: adquiere lock en la carpeta de backups para
    que dos PCs no restauren a la vez; se libera siempre (finally).
    """
    from services import configuracion_service
    from utils.security import verify_password
    pin_hash = configuracion_service.obtener_valor("pin_emergencia")
    if not pin_hash or not verify_password(pin, pin_hash):
        return False, "PIN incorrecto"
    ok, msg = adquirir_lock_restore()
    if not ok:
        return False, msg
    try:
        from database.connection import close_connection
        from database.restore import restore_backup
        close_connection()
        restore_backup(ruta)
        auditoria_service.registrar_log(auditoria_service.id_usuario_sesion(), "sistema", 0, "RESTORE", valor_nuevo=ruta)
        return True, "Restauración completada. Reinicie la app."
    except Exception as e:
        logger.error(f"Restore fallo: {e}")
        return False, str(e)
    finally:
        liberar_lock_restore()

def rotar_backups(dias: int = 30) -> int:
    """Borra backups con más de N días, retorna cantidad borradas."""
    import time
    destino = _resolver_ruta_backup()
    archivos = glob.glob(os.path.join(destino, "academia_*.db"))
    borrados = 0
    limite = time.time() - dias*86400
    for f in archivos:
        try:
            if os.path.getmtime(f) < limite:
                os.remove(f)
                borrados += 1
        except Exception:
            pass
    if borrados:
        logger.info(f"Rotación backups: {borrados} borrados >{dias}d")
        try:
            auditoria_service.registrar_log(
                id_usuario=auditoria_service.id_usuario_sesion(),
                tabla_afectada="sistema", id_registro=0, accion="ROTAR_BACKUPS",
                valor_nuevo=f"{borrados} respaldo(s) >{dias}d eliminados de {destino}")
        except Exception:
            pass
    return borrados

def verificar_backup_automatico() -> tuple[bool, str]:
    """Respeta CONFIGURACION.backup_automatico y frecuencia_backup (RN-030).

    Retorna (True, msg) solo cuando se creo un respaldo nuevo.
    """
    config = configuracion_service.obtener_configuracion() or {}
    if not config.get("backup_automatico", 0):
        return False, "Backup automático deshabilitado"

    try:
        frecuencia = max(int(config.get("frecuencia_backup", 7) or 7), 1)
    except (ValueError, TypeError):
        frecuencia = 7

    dias = dias_desde_ultimo_backup()
    if dias is not None and dias < frecuencia:
        return False, f"Último respaldo hace {dias:.1f} días (frecuencia: {frecuencia})"

    exito, msg, _ = crear_backup()
    return exito, msg
