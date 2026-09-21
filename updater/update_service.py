import json
import os
import sys
import shutil
import zipfile
import tempfile
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

from updater.config import (
    GITHUB_API_URL,
    GITHUB_DOWNLOAD_URL,
    FRECUENCIA_VERIFICACION_HORAS,
    APP_EXE_NAME,
    RECORDAR_RECHAZO,
    PREFER_SETUP_FOR_PROGRAMFILES,
)
from utils.constants import __version__

# Archivo para guardar estado del updater
_STATE_DIR = os.path.join(os.path.expanduser("~"), ".academia_futbol")
_STATE_FILE = os.path.join(_STATE_DIR, "updater_state.json")

# Para que la vista pueda mostrar el último error detallado
ultimo_error: str = ""

HEADERS_GITHUB = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "AcademiaFutbol-Updater/1.0",
}
HEADERS_DOWNLOAD = {
    "User-Agent": "AcademiaFutbol-Updater/1.0",
}


def _cargar_estado() -> dict:
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _guardar_estado(estado: dict) -> None:
    os.makedirs(_STATE_DIR, exist_ok=True)
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2)


def _obtener_ruta_app() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(__file__))


def _partes_version(v: str) -> list[int]:
    """Tolerante: ignora 'v', espacios y sufijos ('1.0.7-beta' → [1,0,7])."""
    v = (v or "").strip().lstrip("vV")
    partes = []
    for trozo in v.split("."):
        # corta en el primer no-dígito ("7-beta" → "7", "" → 0)
        m = ""
        for c in trozo.strip():
            if c.isdigit():
                m += c
            else:
                break
        partes.append(int(m) if m else 0)
    return partes or [0]


def comparar_versiones(v_local: str, v_remota: str) -> int:
    partes_local = _partes_version(v_local)
    partes_remota = _partes_version(v_remota)
    for l, r in zip(partes_local, partes_remota):
        if l < r:
            return -1
        if l > r:
            return 1
    if len(partes_local) < len(partes_remota):
        return -1
    if len(partes_local) > len(partes_remota):
        return 1
    return 0


def debe_verificar() -> bool:
    estado = _cargar_estado()
    if not RECORDAR_RECHAZO and estado.get("rechazado_version"):
        return True
    ultima_verificacion = estado.get("ultima_verificacion")
    if not ultima_verificacion:
        return True
    try:
        fecha = datetime.fromisoformat(ultima_verificacion)
        return datetime.now() - fecha > timedelta(hours=FRECUENCIA_VERIFICACION_HORAS)
    except (ValueError, TypeError):
        return True


def es_instalacion_programfiles() -> bool:
    try:
        ruta = _obtener_ruta_app().lower()
        return "program files" in ruta or "program files (x86)" in ruta
    except Exception:
        return False


def verificar_actualizacion() -> dict | None:
    global ultimo_error
    ultimo_error = ""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers=HEADERS_GITHUB,
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                ultimo_error = f"GitHub API respondió {resp.status}"
                return None
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "").lstrip("v")
        if not tag:
            ultimo_error = "Respuesta sin tag_name"
            return None

        if comparar_versiones(__version__, tag) >= 0:
            _fusionar_estado({
                "ultima_verificacion": datetime.now().isoformat(),
                "ultima_version_verificada": tag,
            })
            return None

        assets = data.get("assets", [])
        zip_url = None
        zip_size = 0
        setup_url = None
        setup_size = 0
        for asset in assets:
            nombre = asset.get("name", "")
            if nombre.endswith(".zip") and "AcademiaFutbol" in nombre:
                zip_url = asset.get("browser_download_url")
                zip_size = asset.get("size", 0)
            elif nombre.lower().endswith(".exe") and "setup" in nombre.lower():
                setup_url = asset.get("browser_download_url")
                setup_size = asset.get("size", 0)

        if not zip_url:
            zip_url = f"{GITHUB_DOWNLOAD_URL}/v{tag}/AcademiaFutbol-v{tag}.zip"
        if not setup_url:
            setup_url = f"{GITHUB_DOWNLOAD_URL}/v{tag}/AcademiaFutbol-Setup-{tag}.exe"

        en_programfiles = es_instalacion_programfiles()
        usar_setup = PREFER_SETUP_FOR_PROGRAMFILES and en_programfiles and setup_url
        tipo = "setup" if usar_setup else "zip"
        url_principal = setup_url if usar_setup else zip_url
        tam_principal = setup_size if usar_setup else zip_size

        return {
            "version": tag,
            "nombre": data.get("name", f"v{tag}"),
            "descripcion": data.get("body", "Sin descripción"),
            "url_descarga": url_principal,
            "url_zip": zip_url,
            "url_setup": setup_url,
            "tipo": tipo,
            "tamano": tam_principal,
            "tamano_zip": zip_size,
            "tamano_setup": setup_size,
            "en_programfiles": en_programfiles,
            "fecha": data.get("published_at", ""),
        }

    except urllib.error.HTTPError as e:
        ultimo_error = f"HTTP {e.code}: {e.reason} ({GITHUB_API_URL})"
        return None
    except urllib.error.URLError as e:
        ultimo_error = f"Sin conexión: {e.reason}"
        return None
    except Exception as e:
        ultimo_error = f"Error verificación: {e}"
        return None


def _fusionar_estado(nuevo: dict) -> None:
    """Mezcla claves nuevas sobre el estado existente (antes se sobrescribía
    todo el archivo y se perdían p. ej. 'rechazado_version' o 'setup_pendiente')."""
    estado = _cargar_estado()
    estado.update(nuevo or {})
    _guardar_estado(estado)


def registrar_verificacion() -> None:
    _fusionar_estado({"ultima_verificacion": datetime.now().isoformat()})


def registrar_rechazo(version: str) -> None:
    estado = _cargar_estado()
    estado["rechazado_version"] = version
    estado["ultima_verificacion"] = datetime.now().isoformat()
    _guardar_estado(estado)


def _formatear_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f} KB"
    return f"{n/1024/1024:.1f} MB"


class _DescargaCancelada(Exception):
    pass


def descargar_y_actualizar(url_descarga: str, callback_progreso=None,
                           debe_cancelar=None) -> bool:
    """
    Descarga ZIP o Setup.exe streaming con progreso.
    ZIP: extrae sobre ruta_app (preserva db/config)
    Setup EXE: descarga y lanza instalador silencioso (pide UAC si Program Files)
    debe_cancelar: callable opcional sin args → True aborta la descarga cuanto
    antes, limpia el temporal y retorna False (antes Cancelar no detenía el hilo).
    """
    global ultimo_error
    ultimo_error = ""
    ruta_temp = None
    es_setup = url_descarga.lower().endswith(".exe")
    try:
        req = urllib.request.Request(url_descarga, headers=HEADERS_DOWNLOAD)
        intentos = 2
        last_exc = None
        ruta_descarga = None
        for intento in range(intentos):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    if resp.status not in (200, 206):
                        raise urllib.error.HTTPError(url_descarga, resp.status, resp.reason or "Error", resp.headers, None)
                    total = int(resp.headers.get("Content-Length", 0) or 0)
                    ruta_temp = tempfile.mkdtemp(prefix="academia_update_")
                    nombre_arch = "Setup-Update.exe" if es_setup else "update.zip"
                    ruta_descarga = os.path.join(ruta_temp, nombre_arch)

                    bytes_read = 0
                    inicio = time.time()
                    ultimo_update = inicio
                    ultimo_bytes = 0

                    with open(ruta_descarga, "wb") as out:
                        while True:
                            if debe_cancelar is not None:
                                try:
                                    if debe_cancelar():
                                        raise _DescargaCancelada()
                                except _DescargaCancelada:
                                    raise
                                except Exception:
                                    pass
                            chunk = resp.read(8192 * 4)
                            if not chunk:
                                break
                            out.write(chunk)
                            bytes_read += len(chunk)
                            ahora = time.time()
                            if callback_progreso and (ahora - ultimo_update > 0.15 or bytes_read - ultimo_bytes > 256 * 1024):
                                transcurrido = ahora - inicio
                                velocidad = bytes_read / transcurrido if transcurrido > 0 else 0
                                try:
                                    try:
                                        callback_progreso(bytes_read, total, velocidad)
                                    except TypeError:
                                        callback_progreso(bytes_read, total)
                                except Exception:
                                    pass
                                ultimo_update = ahora
                                ultimo_bytes = bytes_read

                    if callback_progreso:
                        try:
                            callback_progreso(bytes_read, total or bytes_read, 0)
                        except TypeError:
                            try:
                                callback_progreso(bytes_read, total or bytes_read)
                            except Exception:
                                pass
                    if es_setup:
                        if bytes_read < 1024 * 1024:
                            raise ValueError("Setup descargado muy pequeño, descarga incompleta")
                    else:
                        if not zipfile.is_zipfile(ruta_descarga):
                            raise ValueError("El archivo descargado no es un ZIP válido (descarga incompleta o URL incorrecta)")
                    if total and bytes_read != total:
                        raise ValueError(
                            f"Descarga truncada: {bytes_read}/{total} bytes")
                    break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                    ConnectionError, OSError, ValueError) as e:
                # ValueError = truncado o ZIP inválido: también reintenta una vez
                last_exc = e
                if intento < intentos - 1:
                    time.sleep(1.2)
                    continue
                raise
        else:
            if last_exc:
                raise last_exc

        if es_setup:
            try:
                import subprocess
                _fusionar_estado({"setup_pendiente": ruta_descarga, "setup_version": url_descarga})
                try:
                    os.startfile(ruta_descarga)  # type: ignore[attr-defined]
                except Exception:
                    subprocess.Popen([ruta_descarga, "/SILENT", "/SUPPRESSMSGBOXES", "/NOCANCEL", "/CLOSEAPPLICATIONS"], shell=False)
                return True
            except Exception as e:
                ultimo_error = f"No se pudo lanzar instalador: {e} (ejecute manualmente {ruta_descarga})"
                return False

        # --- extracción ZIP ---
        ruta_app = _obtener_ruta_app()
        archivos_bloqueados: list[str] = []
        ruta_zip = ruta_descarga

        with zipfile.ZipFile(ruta_zip, "r") as zf:
            nombres = zf.namelist()
            for nombre in nombres:
                if nombre.endswith("/"):
                    continue
                lower = nombre.lower()
                if lower in ("config.ini", "config_visual.json"):
                    continue
                if lower.startswith("database/academia.db") or lower.startswith("database\\academia.db"):
                    continue
                if lower.startswith("database/") and lower.endswith(".db"):
                    continue
                if lower.startswith("logs/") or lower.startswith("logs\\"):
                    continue
                if lower.startswith("backups/") or lower.startswith("backups\\"):
                    continue
                destino = os.path.join(ruta_app, nombre)
                # normalizar separadores zip (siempre /)
                destino = os.path.normpath(destino)
                # seguridad: no salir de ruta_app (zip-slip; exige separador)
                base = os.path.normpath(ruta_app)
                if destino != base and not destino.startswith(base + os.sep):
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                try:
                    with zf.open(nombre) as src, open(destino, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                except PermissionError as e:
                    # EXE en ejecución en Windows → no se puede sobrescribir
                    archivos_bloqueados.append(nombre)
                    continue
                except OSError as e:
                    # disco lleno u otro
                    raise OSError(f"No se pudo escribir {nombre}: {e}") from e

        if archivos_bloqueados:
            # Si solo es el EXE principal, instruir reinicio manual
            ultimo_error = (
                f"Algunos archivos estaban en uso ({', '.join(archivos_bloqueados[:3])}). "
                "Cierre la app y use el instalador Setup para actualizar."
                if any("academiafutbol.exe" in x.lower() for x in archivos_bloqueados)
                else f"Archivos bloqueados: {', '.join(archivos_bloqueados)}"
            )
            # consideramos fallo parcial, pero no borramos temp para debug
            return False

        shutil.rmtree(ruta_temp, ignore_errors=True)
        ruta_temp = None

        _fusionar_estado({
            "ultima_verificacion": datetime.now().isoformat(),
            "actualizado_version": __version__,
            "rechazado_version": "",
        })

        return True

    except _DescargaCancelada:
        ultimo_error = "Descarga cancelada por el usuario."
        return False
    except urllib.error.HTTPError as e:
        ultimo_error = f"HTTP {e.code} {e.reason} al descargar (¿Release sin ZIP? Verifique que el Release tenga AcademiaFutbol-v*.zip adjunto)"
        return False
    except urllib.error.URLError as e:
        ultimo_error = f"Error de red: {e.reason}. Verifique internet / firewall / proxy."
        return False
    except TimeoutError:
        ultimo_error = "Tiempo agotado (timeout 60s). Internet lenta o GitHub no responde. Reintente."
        return False
    except zipfile.BadZipFile:
        ultimo_error = "ZIP corrupto (descarga incompleta). Reintente con mejor conexión."
        return False
    except OSError as e:
        ultimo_error = f"Error de disco/permisos: {e} (¿sin espacio o antivirus bloqueando?)"
        return False
    except Exception as e:
        ultimo_error = f"Error inesperado: {e}"
        return False
    finally:
        if ruta_temp and os.path.isdir(ruta_temp):
            try:
                shutil.rmtree(ruta_temp, ignore_errors=True)
            except Exception:
                pass


def descargar_setup_y_ejecutar(url_setup: str, callback_progreso=None) -> bool:
    return descargar_y_actualizar(url_setup, callback_progreso=callback_progreso)


def reiniciar_app() -> None:
    try:
        estado = _cargar_estado()
        setup = estado.get("setup_pendiente")
        if setup and os.path.isfile(setup):
            try:
                import subprocess
                subprocess.Popen([setup, "/SILENT", "/SUPPRESSMSGBOXES", "/NOCANCEL", "/CLOSEAPPLICATIONS"], shell=False)
            except Exception:
                try:
                    os.startfile(setup)  # type: ignore[attr-defined]
                except Exception:
                    pass
            estado.pop("setup_pendiente", None)
            _guardar_estado(estado)
            sys.exit(0)
    except Exception:
        pass
    ruta_app = _obtener_ruta_app()
    exe_path = os.path.join(ruta_app, APP_EXE_NAME)
    if os.path.exists(exe_path):
        try:
            os.startfile(exe_path)  # type: ignore[attr-defined]
        except AttributeError:
            import subprocess
            subprocess.Popen([exe_path], cwd=ruta_app)
    sys.exit(0)


def verificar_manual() -> dict | None:
    return verificar_actualizacion()
