from services import importar_service
from services import auth_service
from utils.csv_parser import parse_csv, obtener_columnas_csv
from utils.excel_parser import parse_excel, obtener_hojas_excel, obtener_columnas_excel
from controllers import login_controller
from utils.logger import logger


def puede_acceder() -> bool:
    return login_controller.es_admin()


def cargar_archivo(ruta_archivo: str, hoja: str | None = None) -> tuple[bool, str, list[dict]]:
    extension = ruta_archivo.rsplit(".", 1)[-1].lower() if "." in ruta_archivo else ""

    if extension == "csv":
        return parse_csv(ruta_archivo)
    elif extension in ("xlsx", "xls"):
        return parse_excel(ruta_archivo, hoja)
    else:
        return False, "Formato no soportado. Use CSV o XLSX", []


def obtener_hojas(ruta_archivo: str) -> tuple[bool, str, list[str]]:
    extension = ruta_archivo.rsplit(".", 1)[-1].lower() if "." in ruta_archivo else ""

    if extension in ("xlsx", "xls"):
        return obtener_hojas_excel(ruta_archivo)

    return True, "OK", [""]


def obtener_columnas(ruta_archivo: str, hoja: str | None = None) -> tuple[bool, str, list[str]]:
    extension = ruta_archivo.rsplit(".", 1)[-1].lower() if "." in ruta_archivo else ""

    if extension == "csv":
        return obtener_columnas_csv(ruta_archivo)
    elif extension in ("xlsx", "xls"):
        return obtener_columnas_excel(ruta_archivo, hoja)

    return False, "Formato no soportado", []


TIPOS_IMPORTACION = ("Estudiantes", "Tienda")


def validar_datos(filas: list[dict], mapeo: dict | None = None,
                  tipo: str = "Estudiantes") -> tuple[bool, str, list[str]]:
    if not filas:
        return False, "No hay datos para validar", []
    if tipo == "Tienda":
        return importar_service.validar_filas_tienda(filas, mapeo)
    return importar_service.validar_filas(filas, mapeo)


def ejecutar_importacion(filas: list[dict], mapeo: dict | None = None,
                         tipo: str = "Estudiantes") -> tuple[bool, str, dict]:
    if not filas:
        return False, "No hay datos para importar", {}

    id_usuario = auth_service.id_usuario_sesion_or_system()
    if tipo == "Tienda":
        return importar_service.importar_tienda(filas, id_usuario, mapeo)
    return importar_service.importar_estudiantes(filas, id_usuario, mapeo)


def obtener_campos_sistema(tipo: str = "Estudiantes") -> list[str]:
    if tipo == "Tienda":
        return list(importar_service.MAPEO_TIENDA.keys())
    return importar_service.obtener_campos_disponibles()


def obtener_campos_obligatorios(tipo: str = "Estudiantes") -> list[str]:
    if tipo == "Tienda":
        return importar_service.CAMPOS_OBLIGATORIOS_TIENDA.copy()
    return importar_service.obtener_campos_obligatorios()


def obtener_campos_apoderado() -> list[str]:
    return importar_service.obtener_campos_apoderado()
