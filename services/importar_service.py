from services import persona_service, estudiante_service, apoderado_service, auditoria_service
from repositories import persona_repository, apoderado_repository, estudiante_apoderado_repository
from utils.logger import logger
from utils.validators import validate_dni, validate_documento


CAMPOS_OBLIGATORIOS_ESTUDIANTE = ["DNI", "Nombres", "Apellidos"]
CAMPOS_OPCIONALES_ESTUDIANTE = [
    "Fecha_Nacimiento", "Sexo", "Telefono", "Correo",
    "Tipo_Documento", "Direccion",
]
CAMPOS_APODERADO = [
    "DNI_Apoderado", "Nombres_Apoderado", "Apellidos_Apoderado",
    "Parentesco", "Telefono_Apoderado", "Direccion_Apoderado",
    "Tipo_Documento_Apoderado",
]

MAPEO_CAMPOS = {
    "DNI": "dni",
    "Nombres": "nombres",
    "Apellidos": "apellidos",
    "Fecha_Nacimiento": "fecha_nacimiento",
    "Sexo": "sexo",
    "Telefono": "telefono",
    "Correo": "correo",
    "Tipo_Documento": "tipo_documento",
    "Direccion": "direccion",
    "DNI_Apoderado": "dni_apoderado",
    "Nombres_Apoderado": "nombres_apoderado",
    "Apellidos_Apoderado": "apellidos_apoderado",
    "Parentesco": "parentesco",
    "Telefono_Apoderado": "telefono_apoderado",
    "Direccion_Apoderado": "direccion_apoderado",
    "Tipo_Documento_Apoderado": "tipo_documento_apoderado",
}


def validar_fila(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_CAMPOS

    campos_invertidos = {v: k for k, v in mapping.items()}

    for campo_requerido in CAMPOS_OBLIGATORIOS_ESTUDIANTE:
        campo_archivo = None
        for nombre_archivo, nombre_sys in mapping.items():
            if nombre_sys == campo_requerido.lower() and nombre_archivo in fila:
                campo_archivo = nombre_archivo
                break

        if campo_archivo is None:
            for nombre_archivo in fila:
                if nombre_archivo.upper() == campo_requerido.upper():
                    campo_archivo = nombre_archivo
                    break

        valor = fila.get(campo_archivo, "") if campo_archivo else ""
        if not valor or valor.strip() == "":
            errores.append(f"Fila {idx}: {campo_requerido} es obligatorio")

    dni_raw = None
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "dni" and nombre_archivo in fila:
            dni_raw = fila[nombre_archivo]
            break
    if dni_raw is None:
        for nombre_archivo in fila:
            if nombre_archivo.upper() == "DNI":
                dni_raw = fila[nombre_archivo]
                break

    if dni_raw:
        dni_limpio = dni_raw.replace(" ", "")
        if not validate_dni(dni_limpio):
            tipo_doc = None
            for nombre_archivo, nombre_sys in mapping.items():
                if nombre_sys == "tipo_documento" and nombre_archivo in fila:
                    tipo_doc = fila[nombre_archivo]
                    break
            if tipo_doc is None:
                for nombre_archivo in fila:
                    if nombre_archivo.upper() == "TIPO_DOCUMENTO":
                        tipo_doc = fila[nombre_archivo]
                        break

            if tipo_doc and tipo_doc.upper() == "CARNET":
                from utils.validators import validate_carnet
                if not validate_carnet(dni_limpio):
                    errores.append(f"Fila {idx}: Carnet de Extranjería inválido (9 dígitos)")
            else:
                errores.append(f"Fila {idx}: DNI inválido (8 dígitos)")

    sexo = None
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "sexo" and nombre_archivo in fila:
            sexo = fila[nombre_archivo]
            break
    if sexo is None:
        for nombre_archivo in fila:
            if nombre_archivo.upper() == "SEXO":
                sexo = fila[nombre_archivo]
                break

    if sexo and sexo.strip():
        sexo_val = sexo.strip().upper()
        if sexo_val not in ("M", "F"):
            errores.append(f"Fila {idx}: Sexo debe ser M o F")

    return errores


def validar_filas(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    todos_errores = []
    dnis_vistos = set()

    for idx, fila in enumerate(filas, 1):
        errores = validar_fila(fila, idx, mapeo)
        todos_errores.extend(errores)

        dni = None
        mapping = mapeo or MAPEO_CAMPOS
        for nombre_archivo, nombre_sys in mapping.items():
            if nombre_sys == "dni" and nombre_archivo in fila:
                dni = fila[nombre_archivo]
                break
        if dni is None:
            for nombre_archivo in fila:
                if nombre_archivo.upper() == "DNI":
                    dni = fila[nombre_archivo]
                    break

        if dni:
            dni_limpio = dni.replace(" ", "")
            if dni_limpio in dnis_vistos:
                todos_errores.append(f"Fila {idx}: DNI duplicado en el archivo")
            dnis_vistos.add(dni_limpio)

            if persona_repository.existe_dni(dni_limpio):
                todos_errores.append(f"Fila {idx}: DNI {dni_limpio} ya registrado en el sistema")

    if todos_errores:
        return False, f"{len(todos_errores)} errores encontrados", todos_errores

    return True, "Validación correcta", []


def importar_estudiantes(filas: list[dict], id_usuario: int = 1,
                         mapeo: dict | None = None) -> tuple[bool, str, dict]:
    from database.connection import transaccion

    resultados = {
        "estudiantes_creados": 0,
        "apoderados_creados": 0,
        "asociaciones_creadas": 0,
        "errores": [],
        "detalles": [],
    }

    mapping = mapeo or MAPEO_CAMPOS

    for idx, fila in enumerate(filas, 1):
        try:
            # Cada fila es atomica: si falla a mitad, se revierte completa.
            with transaccion():
                res = _importar_fila(fila, mapping, id_usuario)

            resultados["estudiantes_creados"] += res["estudiantes"]
            resultados["apoderados_creados"] += res["apoderados"]
            resultados["asociaciones_creadas"] += res["asociaciones"]
            if res["detalle"]:
                resultados["detalles"].append(f"Fila {idx}: {res['detalle']}")

        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            # Limpieza: el detalle ya va a resultados (UI); al log solo resumen
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Error al importar fila {idx}: {e}")

    total = resultados["estudiantes_creados"]
    n_err = len(resultados["errores"])
    if total > 0 or n_err:
        logger.info(
            f"Importación completada: {total} estudiantes, "
            f"{resultados['apoderados_creados']} apoderados, {n_err} errores"
        )

    return True, f"{total} estudiantes importados", resultados


class ErrorFilaImportacion(Exception):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


def _importar_fila(fila: dict, mapping: dict, id_usuario: int) -> dict:
    """Procesa una fila del archivo. Lanza ErrorFilaImportacion ante un fallo
    de negocio para provocar el rollback atomico de la fila."""
    res = {"estudiantes": 0, "apoderados": 0, "asociaciones": 0, "detalle": ""}

    data_estudiante = {}
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_archivo in fila and nombre_sys in (
            "dni", "nombres", "apellidos", "fecha_nacimiento",
            "sexo", "telefono", "correo", "tipo_documento", "direccion"
        ):
            data_estudiante[nombre_sys] = fila[nombre_archivo]

    exito_est, msg_est, id_estudiante = estudiante_service.crear_estudiante(
        data_estudiante, id_usuario
    )
    if not exito_est:
        raise ErrorFilaImportacion(msg_est)

    res["estudiantes"] = 1
    res["detalle"] = f"Estudiante {data_estudiante.get('dni', '')} creado"

    data_apoderado = {}
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_archivo in fila and nombre_sys in (
            "dni_apoderado", "nombres_apoderado", "apellidos_apoderado",
            "parentesco", "telefono_apoderado", "direccion_apoderado",
            "tipo_documento_apoderado"
        ):
            data_apoderado[nombre_sys] = fila[nombre_archivo]

    if data_apoderado.get("dni_apoderado"):
        apoderado_data = {
            "dni": data_apoderado.get("dni_apoderado", ""),
            "nombres": data_apoderado.get("nombres_apoderado", ""),
            "apellidos": data_apoderado.get("apellidos_apoderado", ""),
            "parentesco": data_apoderado.get("parentesco", ""),
            "telefono": data_apoderado.get("telefono_apoderado", ""),
            "direccion": data_apoderado.get("direccion_apoderado", ""),
            "tipo_documento": data_apoderado.get("tipo_documento_apoderado", "DNI"),
        }
        exito_ap, msg_ap, id_apoderado = apoderado_service.crear_apoderado(
            apoderado_data, id_usuario
        )

        if not exito_ap:
            raise ErrorFilaImportacion(f"Apoderado - {msg_ap}")

        res["apoderados"] = 1

        exito_asc, msg_asc = estudiante_service.asociar_apoderado(
            id_estudiante, id_apoderado, es_principal=True, id_usuario=id_usuario
        )
        if not exito_asc:
            raise ErrorFilaImportacion(f"Asociación - {msg_asc}")
        res["asociaciones"] = 1

    return res


def obtener_campos_disponibles() -> list[str]:
    return list(MAPEO_CAMPOS.keys())


def obtener_campos_obligatorios() -> list[str]:
    return CAMPOS_OBLIGATORIOS_ESTUDIANTE.copy()


def obtener_campos_apoderado() -> list[str]:
    return CAMPOS_APODERADO.copy()
