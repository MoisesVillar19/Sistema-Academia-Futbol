import os
import sys

# ── Detección de entorno ────────────────────────────────────────
_FROZEN = getattr(sys, "frozen", False)

if _FROZEN:
    # Ejecutable PyInstaller: rutas relativas al .exe
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Código fuente: rutas relativas al proyecto
    APP_DIR = os.path.dirname(os.path.dirname(__file__))

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) if not _FROZEN else os.path.join(os.path.dirname(sys.executable), "_internal")

# ── Versión ─────────────────────────────────────────────────────
def _leer_version() -> str:
    # En PyInstaller, VERSION está en _internal/
    if _FROZEN:
        version_file = os.path.join(BASE_DIR, "VERSION")
    else:
        version_file = os.path.join(APP_DIR, "VERSION")
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

__version__ = _leer_version()

def _obtener_ruta_backup() -> str:
    # LOCALAPPDATA (escribible en Program Files)
    local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if local:
        try:
            cand = os.path.join(local, "AcademiaFutbol", "backups")
            os.makedirs(cand, exist_ok=True)
            return cand
        except Exception:
            pass
    return os.path.join(APP_DIR, "backups")


def _resolver_config_visual_path() -> str:
    """Ruta escribible para config_visual.json (LOCALAPPDATA -> APP_DIR)."""
    local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if local:
        cand_dir = os.path.join(local, "AcademiaFutbol")
        try:
            os.makedirs(cand_dir, exist_ok=True)
            # si existe en APP_DIR y no en LOCALAPPDATA, migrar
            legacy = os.path.join(APP_DIR, "config_visual.json")
            cand = os.path.join(cand_dir, "config_visual.json")
            if os.path.isfile(legacy) and not os.path.isfile(cand):
                try:
                    import shutil
                    shutil.copy2(legacy, cand)
                except Exception:
                    pass
            return cand
        except Exception:
            pass
    return os.path.join(APP_DIR, "config_visual.json")


CONFIG_VISUAL_PATH = _resolver_config_visual_path()


BACKUP_DIR = _obtener_ruta_backup()

# ── Base de datos (red LAN o local, sin OneDrive) ────────────────
# Orden: config.ini (setup_red.bat o picker) → LOCALAPPDATA (frozen) o
# APP_DIR/database (dev). OneDrive eliminado a propósito (permisos).
def _leer_config_ini(clave: str, seccion: str = "database") -> str | None:
    for base in (APP_DIR, os.path.join(APP_DIR, "_internal") if _FROZEN else APP_DIR):
        ini = os.path.join(base, "config.ini")
        if os.path.isfile(ini):
            try:
                import configparser
                cp = configparser.ConfigParser()
                cp.read(ini, encoding="utf-8")
                if cp.has_option(seccion, clave):
                    v = cp.get(seccion, clave).strip()
                    if v:
                        return v
            except Exception:
                pass
    return None

DB_NAME = os.getenv("DB_NAME", "academia.db")

def _resolver_db_path() -> str:
    p = _leer_config_ini("path", "database") or os.getenv("DB_PATH")
    if p:
        return p if os.path.isabs(p) else os.path.join(APP_DIR, p)
    if _FROZEN:
        # Instalado sin config: base local escribible (setup_red la mueve al share)
        local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if local:
            return os.path.join(local, "AcademiaFutbol", DB_NAME)
    return os.path.join(APP_DIR, "database", DB_NAME)

DB_PATH = _resolver_db_path()

# Carpetas centralizadas (fotos/comprobantes): config.ini o caída local
def _resolver_dir(clave: str, fallback: str) -> str:
    p = _leer_config_ini(clave, "rutas") or _leer_config_ini("dir", clave)
    if p:
        return p if os.path.isabs(p) else os.path.join(APP_DIR, p)
    if _FROZEN:
        local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if local:
            return os.path.join(local, "AcademiaFutbol", fallback)
    return os.path.join(APP_DIR, fallback)

FOTOS_DIR = _resolver_dir("fotos", "fotos")
COMPROBANTES_DIR = _resolver_dir("comprobantes", "comprobantes")

ROLE_ADMIN = "ADMIN"
ROLE_SECRETARIA = "SECRETARIA"
# Legacy roles kept for migration compatibility (will be mapped to SECRETARIA on startup)
ROLE_CAJA = "CAJA"
ROLE_INVENTARIO = "INVENTARIO"
ROLES_VALIDOS = (ROLE_ADMIN, ROLE_SECRETARIA)
ROLES_LEGACY = (ROLE_CAJA, ROLE_INVENTARIO)
# Matriz permisos por rol (para sidebar y gates) — v2.1 secretaria con más libertad
# Es el DEFAULT inicial: el ADMIN puede editarla (tabla rol_permiso) sin tocar código.
MODULOS_SISTEMA = ("dashboard", "estudiantes", "matriculas", "pagos", "ventas",
                   "inventario", "tiendita", "almacen", "reportes", "egresos", "importar", "usuarios",
                   "tarifas", "auditoria", "configuracion", "catalogos", "respaldo")
# Bloque D: `catalogos` = secciones 7-10 de Configuración (categorías edad,
# tipos uniforme, conceptos, apariencia). SECRETARIA lo tiene por defecto;
# `configuracion` (secciones 1-6 + guardar) sigue solo ADMIN.
# Fase 0 v2: `tiendita` (SECRETARIA) y `almacen` (solo ADMIN). `inventario` se
# mantiene hasta Fase 6 (rewire del menú), luego sale de defaults.
# La migración es el seed idempotente de create_db (INSERT OR IGNORE).
PERMISOS_ROL = {
    ROLE_ADMIN: set(MODULOS_SISTEMA),
    ROLE_SECRETARIA: {"dashboard", "estudiantes", "matriculas", "pagos", "ventas", "inventario", "tiendita", "reportes", "egresos", "respaldo", "tarifas", "catalogos"},
}

STATUS_ACTIVO = "ACTIVO"
STATUS_RETIRADO = "RETIRADO"
STATUS_REINGRESANTE = "REINGRESANTE"

CUOTA_PENDIENTE = "PENDIENTE"
CUOTA_PARCIAL = "PARCIAL"
CUOTA_PAGADO = "PAGADO"
CUOTA_VENCIDO = "VENCIDO"

METODO_EFECTIVO = "EFECTIVO"
METODO_YAPE = "YAPE"
METODO_PLIN = "PLIN"
METODO_TRANSFERENCIA = "TRANSFERENCIA"

TIPO_BECA_PORCENTAJE = "PORCENTAJE"
TIPO_BECA_MONTO_FIJO = "MONTO_FIJO"

TIPO_MOVIMIENTO_ENTRADA = "ENTRADA"
TIPO_MOVIMIENTO_SALIDA = "SALIDA"
TIPO_MOVIMIENTO_AJUSTE = "AJUSTE"

TIPO_USO_CONSUMO_INTERNO = "CONSUMO_INTERNO"
TIPO_USO_VENTA = "VENTA"

CATEGORIA_INICIAL = [
    ("3-5", 3, 5),
    ("6-8", 6, 8),
    ("9-12", 9, 12),
    ("13-15", 13, 15),
    ("16-18", 16, 18),
]

CATEGORIA_PRODUCTO_INICIAL = [
    "INSUMO_DEPORTIVO",
    "INSUMO_ALIMENTO",
]

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Credencial inicial documentada (igual que DEFAULT_ADMIN_PASS).
# Se guarda hasheada (bcrypt) en CONFIGURACION.pin_emergencia; el codigo
# nunca la compara en texto plano.
PIN_EMERGENCIA_DEFECTO = "roncalli2026"


# Re-export para imports existentes
__all__ = ["APP_DIR", "BASE_DIR", "DB_PATH", "DB_NAME", "FOTOS_DIR", "COMPROBANTES_DIR", "BACKUP_DIR", "CONFIG_VISUAL_PATH"]
