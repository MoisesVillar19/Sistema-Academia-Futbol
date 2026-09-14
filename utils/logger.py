import logging
import os
import sys
import tempfile
from logging.handlers import RotatingFileHandler


def _resolver_log_dir() -> str:
    """Resuelve directorio de logs escribible (LOCALAPPDATA -> APP_DIR -> temp)."""
    candidatos: list[str] = []
    try:
        from utils.constants import APP_DIR
        # LOCALAPPDATA es escribible aun en Program Files
        local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if local:
            candidatos.append(os.path.join(local, "AcademiaFutbol", "logs"))
        candidatos.append(os.path.join(APP_DIR, "logs"))
    except Exception:
        pass
    # fallback si import falló (caso _internal)
    if not candidatos:
        try:
            base = os.path.dirname(os.path.dirname(__file__))
            candidatos.append(os.path.join(base, "logs"))
        except Exception:
            pass
    # última instancia temp
    candidatos.append(os.path.join(tempfile.gettempdir(), "AcademiaFutbol", "logs"))

    for cand in candidatos:
        try:
            os.makedirs(cand, exist_ok=True)
            # prueba de escritura real (Program Files falla aquí)
            test = os.path.join(cand, ".write_test")
            with open(test, "w", encoding="utf-8") as f:
                f.write("ok")
            try:
                os.remove(test)
            except Exception:
                pass
            return cand
        except (PermissionError, OSError):
            continue
        except Exception:
            continue
    # si todo falla, usar temp
    cand = os.path.join(tempfile.gettempdir(), "AcademiaFutbol", "logs")
    os.makedirs(cand, exist_ok=True)
    return cand


LOG_DIR = _resolver_log_dir()


def setup_logger(name: str = "academia") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    try:
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, "academia.log"),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
    except (PermissionError, OSError) as e:
        # fallback: solo consola si ni siquiera LOG_DIR es escribible
        import sys
        print(f"[logger] No se pudo crear log file en {LOG_DIR}: {e}", file=sys.stderr)
        file_handler = None

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if file_handler is not None:
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
