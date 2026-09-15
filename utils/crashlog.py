"""Diagnóstico anti-muerte-muda: ningún arranque vuelve a fallar en silencio.

- error_log.txt siempre escribible (LOCALAPPDATA -> temp).
- faulthandler: vuelca hasta crashes nativos (C) con traceback.
- sys.excepthook + threading.excepthook: tracebacks de callbacks Tk e hilos.
- registrar_fase(): marca cada etapa del arranque para ubicar muertes tempranas.
"""
import faulthandler
import os
import sys
import tempfile
import threading
import traceback
from datetime import datetime

_NOMBRE_ARCHIVO = "error_log.txt"
_instalado = False


def ruta_error_log() -> str:
    local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    candidatos = []
    if local:
        candidatos.append(os.path.join(local, "AcademiaFutbol", _NOMBRE_ARCHIVO))
    candidatos.append(os.path.join(tempfile.gettempdir(), "AcademiaFutbol", _NOMBRE_ARCHIVO))
    for ruta in candidatos:
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "a", encoding="utf-8"):
                pass
            return ruta
        except Exception:
            continue
    return os.path.join(tempfile.gettempdir(), _NOMBRE_ARCHIVO)


def _escribir(titulo: str, detalle: str) -> str:
    ruta = ruta_error_log()
    try:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n{datetime.now():%Y-%m-%d %H:%M:%S} | {titulo}\n{detalle}\n")
    except Exception:
        pass
    return ruta


def registrar_fase(nombre: str) -> None:
    _escribir("FASE", nombre)


def _hook_excepcion(tipo, valor, tb) -> None:
    ruta = _escribir("EXCEPCION NO CAPTURADA",
                     "".join(traceback.format_exception(tipo, valor, tb)))
    try:
        from utils.logger import logger
        logger.error(f"Excepción no capturada (ver {ruta}): {valor}")
    except Exception:
        pass
    try:
        sys.__excepthook__(tipo, valor, tb)
    except Exception:
        pass


def _hook_hilos(args) -> None:
    _escribir("EXCEPCION EN HILO",
              "".join(traceback.format_exception(args.exc_type, args.exc_value,
                                                 args.exc_traceback)))


_fd_faulthandler = None


def instalar() -> str:
    """Instala hooks y faulthandler. Idempotente. Retorna ruta del log."""
    global _instalado, _fd_faulthandler
    ruta = ruta_error_log()
    try:
        # el fd debe quedar ABIERTO (faulthandler escribe en crashes duros)
        _fd_faulthandler = open(ruta, "a", encoding="utf-8")
        faulthandler.enable(file=_fd_faulthandler)
    except Exception:
        pass
    try:
        sys.excepthook = _hook_excepcion
    except Exception:
        pass
    try:
        threading.excepthook = _hook_hilos
    except Exception:
        pass
    _instalado = True
    return ruta
