from services import persona_service, estudiante_service, apoderado_service, auditoria_service
from repositories import persona_repository, apoderado_repository, estudiante_apoderado_repository
from utils.logger import logger
from utils.validators import validate_dni, validate_documento


CAMPOS_OBLIGATORIOS_ESTUDIANTE = ["DNI", "Nombres", "Apellidos"]

# INICIO vacío (CSV) → 15 de mayo 2026 (nunca la fecha actual de carga).
FECHA_INICIO_DEFAULT = "2026-05-15"


def _normalizar_inicio_csv(raw) -> str:
    """INICIO del CSV → ISO AAAA-MM-DD o ''.

    Acepta ISO, 'dd/C.M' (= enero) e 'INICIO dd/mm' (reglas del historial).
    """
    txt = str(raw or "").strip()
    if not txt:
        return ""
    try:
        from services.importar_historial import parse_inicio
        ini, _rein, _ret = parse_inicio(txt)
        if ini:
            return ini[:10]
    except Exception:
        pass
    try:
        from utils.dates import parse_date
        if parse_date(txt[:10]) is not None:
            return txt[:10]
    except Exception:
        pass
    return ""


def _inicio_de_fila(fila: dict, mapping: dict) -> str:
    """INICIO normalizado o default 15-may (nunca hoy)."""
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "fecha_ingreso" and nombre_archivo in fila:
            norm = _normalizar_inicio_csv(fila[nombre_archivo])
            if norm:
                return norm
            break
    else:
        for nombre_archivo in fila:
            if nombre_archivo.upper() == "INICIO":
                norm = _normalizar_inicio_csv(fila[nombre_archivo])
                if norm:
                    return norm
                break
    return FECHA_INICIO_DEFAULT


def _trae_inicio(fila: dict, mapping: dict) -> str:
    """INICIO explícito normalizado o '' (sin default): para decidir si
    corresponde re-tarifear (vacío = sin información, no tocar tarifa)."""
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "fecha_ingreso" and nombre_archivo in fila:
            return _normalizar_inicio_csv(fila[nombre_archivo])
    for nombre_archivo in fila:
        if nombre_archivo.upper() == "INICIO":
            return _normalizar_inicio_csv(fila[nombre_archivo])
    return ""


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
    "BECA": "beca",
    "INICIO": "fecha_ingreso",
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

    # Fix: Fecha_Nacimiento nunca se validaba (llegaba basura a BD)
    fecha_nac = None
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "fecha_nacimiento" and nombre_archivo in fila:
            fecha_nac = fila[nombre_archivo]
            break
    if fecha_nac is None:
        for nombre_archivo in fila:
            if nombre_archivo.upper() == "FECHA_NACIMIENTO":
                fecha_nac = fila[nombre_archivo]
                break
    if fecha_nac and str(fecha_nac).strip():
        from utils.dates import parse_date
        if parse_date(str(fecha_nac).strip()) is None:
            errores.append(f"Fila {idx}: Fecha_Nacimiento debe ser AAAA-MM-DD")

    # INICIO = inicio de clases → fecha_ingreso (referencia de vencimientos).
    # Acepta ISO, 'dd/C.M' (= enero) e 'INICIO dd/mm'; vacío = default 15-may.
    inicio_raw = None
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "fecha_ingreso" and nombre_archivo in fila:
            inicio_raw = fila[nombre_archivo]
            break
    if inicio_raw is None:
        for nombre_archivo in fila:
            if nombre_archivo.upper() == "INICIO":
                inicio_raw = fila[nombre_archivo]
                break
    if inicio_raw and str(inicio_raw).strip():
        if not _normalizar_inicio_csv(inicio_raw):
            errores.append(f"Fila {idx}: INICIO debe ser AAAA-MM-DD, C.M o INICIO dd/mm")

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
        "matriculas": 0,
        "becas": 0,
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
            resultados["matriculas"] += res.get("matriculas", 0)
            resultados["becas"] += res.get("becas", 0)
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

    # Re-importe idempotente: la Revisión marcó la fila como _actualizar
    # (YA_EXISTE por Nombres+Apellidos). Si sigue existiendo, se actualiza;
    # si se borró entre revisión y ejecución, se crea normal.
    if fila.get("_actualizar"):
        nom, ape = _nombres_de_fila(fila, mapping)
        previo = _buscar_estudiante_por_nombre(nom, ape)
        if previo is not None:
            return _actualizar_fila_existente(fila, mapping, id_usuario, previo)

    data_estudiante = {}
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_archivo in fila and nombre_sys in (
            "dni", "nombres", "apellidos", "fecha_nacimiento",
            "sexo", "telefono", "correo", "tipo_documento", "direccion",
            "fecha_ingreso"
        ):
            data_estudiante[nombre_sys] = fila[nombre_archivo]
    # Normaliza INICIO (C.M→enero) y defaultea a 15-may (nunca hoy).
    data_estudiante["fecha_ingreso"] = _inicio_de_fila(fila, mapping)

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

    # Matrícula para todo importado (beca solo si la fila trae BECA válida).
    _importar_matricula_fila(fila, mapping, id_usuario, id_estudiante,
                             res, _beca_de_fila(fila, mapping))

    return res


def _beca_de_fila(fila: dict, mapping: dict) -> str:
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_sys == "beca" and nombre_archivo in fila:
            return str(fila[nombre_archivo] or "").strip()
    for nombre_archivo in fila:
        if nombre_archivo.upper() == "BECA":
            return str(fila[nombre_archivo] or "").strip()
    return ""


def _actualizar_fila_existente(fila: dict, mapping: dict, id_usuario: int,
                               previo: dict) -> dict:
    """Re-importe: actualiza persona (DNI provisional→real incluido),
    fecha_ingreso y matrícula si no tiene activa. No duplica nada."""
    from repositories import persona_repository, estudiante_repository
    from models.persona import Persona
    from models.estudiante import Estudiante
    res = {"estudiantes": 0, "apoderados": 0, "asociaciones": 0, "detalle": ""}

    data_estudiante = {}
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_archivo in fila and nombre_sys in (
            "dni", "nombres", "apellidos", "fecha_nacimiento",
            "sexo", "telefono", "correo", "tipo_documento", "direccion",
            "fecha_ingreso"
        ):
            data_estudiante[nombre_sys] = fila[nombre_archivo]

    per = persona_repository.obtener_por_dni(previo["dni"])
    if per is None:
        raise ErrorFilaImportacion("El estudiante ya no existe (se borró tras la revisión)")
    nuevo_dni = str(data_estudiante.get("dni", "") or "").strip().replace(" ", "")
    if nuevo_dni and nuevo_dni != per["dni"]:
        if persona_repository.existe_dni(nuevo_dni, exclude_id=per["id_persona"]):
            raise ErrorFilaImportacion(f"DNI {nuevo_dni} ya lo tiene otra persona")
    dni_final = nuevo_dni or per["dni"]
    persona_repository.actualizar(Persona(
        id_persona=per["id_persona"], dni=dni_final,
        tipo_documento=str(data_estudiante.get("tipo_documento", "") or "").strip() or per.get("tipo_documento", "DNI"),
        nombres=per["nombres"], apellidos=per["apellidos"],
        fecha_nacimiento=str(data_estudiante.get("fecha_nacimiento", "") or "").strip() or per.get("fecha_nacimiento", ""),
        sexo=str(data_estudiante.get("sexo", "") or "").strip() or per.get("sexo", ""),
        direccion=str(data_estudiante.get("direccion", "") or "").strip() or per.get("direccion", ""),
        telefono=str(data_estudiante.get("telefono", "") or "").strip() or per.get("telefono", ""),
        correo=str(data_estudiante.get("correo", "") or "").strip() or per.get("correo", ""),
        activo=per.get("activo", 1),
    ))
    est = estudiante_repository.obtener_por_id(previo["id_estudiante"])
    if est is None:
        raise ErrorFilaImportacion("El estudiante ya no existe (se borró tras la revisión)")
    inicio = _normalizar_inicio_csv(data_estudiante.get("fecha_ingreso", ""))
    if inicio:
        try:
            from utils.dates import parse_date
            if parse_date(inicio) is not None:
                estudiante_repository.actualizar(Estudiante(
                    id_estudiante=est["id_estudiante"], id_persona=est["id_persona"],
                    estado=est["estado"], fecha_ingreso=inicio,
                    fecha_retiro=est.get("fecha_retiro"),
                    es_nuevo=est.get("es_nuevo", 0), foto_path=est.get("foto_path"),
                    comprobante_pago_path=est.get("comprobante_pago_path"),
                    fecha_matricula=est.get("fecha_matricula"), activo=est.get("activo", 1),
                ))
        except Exception:
            pass
    res["detalle"] = f"Estudiante {dni_final} actualizado"

    # Apoderado solo si trae DNI y el estudiante no tiene ninguno
    data_apoderado = {}
    for nombre_archivo, nombre_sys in mapping.items():
        if nombre_archivo in fila and nombre_sys in (
            "dni_apoderado", "nombres_apoderado", "apellidos_apoderado",
            "parentesco", "telefono_apoderado", "direccion_apoderado",
            "tipo_documento_apoderado"
        ):
            data_apoderado[nombre_sys] = fila[nombre_archivo]
    if data_apoderado.get("dni_apoderado"):
        try:
            _tiene = False
            try:
                from controllers import estudiante_controller
                _tiene = bool(estudiante_controller.obtener_apoderados_por_estudiante(
                    previo["id_estudiante"]))
            except Exception:
                pass
            if not _tiene:
                apoderado_data = {
                    "dni": data_apoderado.get("dni_apoderado", ""),
                    "nombres": data_apoderado.get("nombres_apoderado", ""),
                    "apellidos": data_apoderado.get("apellidos_apoderado", ""),
                    "parentesco": data_apoderado.get("parentesco", ""),
                    "telefono": data_apoderado.get("telefono_apoderado", ""),
                    "direccion": data_apoderado.get("direccion_apoderado", ""),
                    "tipo_documento": data_apoderado.get("tipo_documento_apoderado", "DNI"),
                }
                exito_ap, _m, id_ap = apoderado_service.crear_apoderado(
                    apoderado_data, id_usuario)
                if exito_ap:
                    estudiante_service.asociar_apoderado(
                        previo["id_estudiante"], id_ap, es_principal=True,
                        id_usuario=id_usuario)
                    res["apoderados"] = 1
                    res["asociaciones"] = 1
        except Exception:
            pass

    beca_nombre = _beca_de_fila(fila, mapping)
    _importar_matricula_fila(fila, mapping, id_usuario, previo["id_estudiante"],
                             res, beca_nombre)
    # Re-tarifa por era solo si la fila trae INICIO explícito.
    ini_exp = _trae_inicio(fila, mapping)
    if ini_exp and res.get("id_matricula"):
        res["detalle"] += _aplicar_tarifa_era(res["id_matricula"], ini_exp)
    return res


def _beca_id_por_nombre(nombre: str) -> int | None:
    """Beca activa por nombre (insensible a mayúsculas/espacios) + sinónimos
    del Excel (MEDIA/1-2 → 1/2 BECA; COMPLETA/ENTERA → BECA COMPLETA)."""
    import unicodedata
    from repositories import beca_repository

    def _norm_beca(t):
        t = "".join(c for c in unicodedata.normalize("NFD", str(t or "").strip().upper())
                    if unicodedata.category(c) != "Mn")
        return " ".join(t.split())
    objetivo = _norm_beca(nombre)
    sinonimos = {
        "MEDIA BECA": "1/2 BECA", "BECA MEDIA": "1/2 BECA", "1-2 BECA": "1/2 BECA",
        "1/2 DE BECA": "1/2 BECA", "MITAD DE BECA": "1/2 BECA", "MITAD BECA": "1/2 BECA",
        "BECA COMPLETA": "BECA COMPLETA", "COMPLETA": "BECA COMPLETA",
        "BECA ENTERA": "BECA COMPLETA", "ENTERA": "BECA COMPLETA",
        "BECA 100": "BECA COMPLETA", "100% BECA": "BECA COMPLETA",
    }
    objetivo = sinonimos.get(objetivo, objetivo)
    for b in beca_repository.obtener_todas():
        if not b.get("activo", 1):
            continue
        if _norm_beca(b.get("nombre", "")) == objetivo:
            return b["id_beca"]
    return None


def _inferir_beca(nombre: str) -> tuple[str, str, float] | None:
    """Infiere (nombre_canonico, tipo, valor) para auto-crear becas.
    MEDIA/1-2 → MONTO_FIJO 50; COMPLETA/ENTERA → PORCENTAJE 100;
    con número → MONTO_FIJO ese valor. None si no se puede inferir."""
    import re
    import unicodedata

    def _norm(t):
        t = "".join(c for c in unicodedata.normalize("NFD", str(t or "").strip().upper())
                    if unicodedata.category(c) != "Mn")
        return " ".join(t.split())
    t = _norm(nombre)
    if not t:
        return None
    if any(k in t for k in ("COMPLETA", "ENTERA", "100", "TOTAL")):
        return t.title(), "PORCENTAJE", 100.0
    if any(k in t for k in ("MEDIA", "MITAD", "1-2", "1/2", "50")):
        return t.title(), "MONTO_FIJO", 50.0
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if m:
        try:
            v = float(m.group(1))
            if v > 0:
                return t.title(), "MONTO_FIJO", v
        except (ValueError, TypeError):
            pass
    return None


def _crear_beca_inferida(nombre: str) -> tuple[int | None, str]:
    """Crea la beca si es inferible (reutiliza si ya existe)."""
    from services import beca_service
    existente = _beca_id_por_nombre(nombre)
    if existente:
        return existente, "ya existía"
    inferida = _inferir_beca(nombre)
    if inferida is None:
        return None, "no se pudo inferir tipo/valor"
    nom, tipo, valor = inferida
    try:
        ok, msg, bid = beca_service.crear_beca({
            "nombre": nom, "tipo": tipo, "valor": valor,
            "observacion": "Creada por importación",
        })
    except Exception as e:
        return None, str(e)
    if not ok:
        # carrera/duplicado: reintentar lookup
        bid2 = _beca_id_por_nombre(nom)
        if bid2:
            return bid2, "ya existía"
        return None, msg
    return bid, f"creada ({tipo} {valor:g})"


def _tarifa_para_beca(inicio: str = "") -> dict | None:
    """Mensualidad genérica por era (escala central en cuota_service);
    la crea si falta. Si no, primera ACADEMIA; si no, primera activa."""
    from repositories import tarifa_repository
    from services import cuota_service
    from utils.dates import get_today
    per = (str(inicio or "").strip()[:7]) or get_today()[:7]
    objetivo = cuota_service.monto_mensualidad(per)
    activas = tarifa_repository.obtener_activas()
    acad = [t for t in activas if (t.get("categoria_tipo") or "") == "ACADEMIA"]
    if objetivo:
        for t in acad:
            try:
                if round(float(t.get("monto", 0) or 0), 2) == objetivo:
                    return t
            except (TypeError, ValueError):
                pass
        creada = _asegurar_tarifa_generica(objetivo, activas)
        if creada:
            return creada
    for t in acad:
        return t
    return activas[0] if activas else None


def _asegurar_tarifa_generica(monto: float, activas: list | None = None) -> dict | None:
    """Crea 'Mensualidad {monto}' (primera categoría ACADEMIA) si no existe."""
    from repositories import tarifa_repository, categoria_repository
    from models.tarifa import Tarifa
    from database.connection import fetch_one
    nombre = f"Mensualidad {monto:g}"
    try:
        activas = tarifa_repository.obtener_activas() if activas is None else activas
    except Exception:
        activas = []
    for t in activas:
        if ((t.get("categoria_tipo") or "") == "ACADEMIA"
                and str(t.get("nombre", "")).strip().lower() == nombre.lower()):
            return t
    try:
        cat = fetch_one("SELECT id_categoria FROM categoria "
                        "WHERE tipo = 'ACADEMIA' AND activo = 1 ORDER BY id_categoria LIMIT 1")
    except Exception:
        cat = None
    if not cat:
        return None
    try:
        id_tar = tarifa_repository.insertar(Tarifa(
            id_categoria=cat["id_categoria"], nombre=nombre, monto=monto,
            descripcion="Creada por importación"))
    except Exception as e:
        logger.error(f"No se pudo crear tarifa {nombre}: {e}")
        return None
    for t in tarifa_repository.obtener_activas():
        if t.get("id_tarifa") == id_tar:
            return t
    return None


def _aplicar_tarifa_era(id_matricula: int, inicio: str) -> str:
    """Re-tariféa la matrícula a la era del INICIO (100/120) si difiere.

    Solo cambia id_tarifa (rige futuras cuotas y lo mostrado); las cuotas
    existentes conservan su monto (verdad histórica). Retorna nota o ''.
    """
    from repositories import matricula_repository, tarifa_repository
    from models.matricula import Matricula
    from services import cuota_service
    per = (str(inicio or "").strip())[:7]
    if not per:
        return ""
    try:
        mat = matricula_repository.obtener_por_id(id_matricula)
    except Exception:
        return ""
    if not mat:
        return ""
    try:
        actual = round(float((tarifa_repository.obtener_por_id(
            mat["id_tarifa"]) or {}).get("monto", 0) or 0), 2)
    except Exception:
        return ""
    esperado = round(cuota_service.monto_mensualidad(per), 2)
    if actual == esperado:
        return ""
    nueva = _tarifa_para_beca(per + "-01")
    if not nueva or nueva["id_tarifa"] == mat["id_tarifa"]:
        return ""
    try:
        matricula_repository.actualizar(Matricula(
            id_matricula=mat["id_matricula"], id_estudiante=mat["id_estudiante"],
            id_tarifa=nueva["id_tarifa"], monto_pactado=mat.get("monto_pactado"),
            pago_matricula=mat.get("pago_matricula", "AHORA"),
            monto_matricula=mat.get("monto_matricula", 0),
            fecha_inicio=mat.get("fecha_inicio", ""),
            fecha_fin=mat.get("fecha_fin", ""),
            dia_vencimiento=mat.get("dia_vencimiento", 1),
            tipo=mat.get("tipo"), estado=mat.get("estado", "ACTIVO"),
            activo=mat.get("activo", 1),
        ))
        auditoria_service.registrar_update(
            id_usuario=auditoria_service.id_usuario_sesion(),
            tabla="matricula", id_registro=mat["id_matricula"],
            valores_anteriores=f"id_tarifa={mat['id_tarifa']} (S/{actual:.2f})",
            valores_nuevos=f"id_tarifa={nueva['id_tarifa']} (S/{esperado:.2f}, era {per})",
        )
    except Exception as e:
        logger.error(f"Re-tarifa mat {id_matricula} falló: {e}")
        return ""
    return f" (tarifa actualizada S/{actual:.0f}→S/{esperado:.0f} por era {per})"


def _retrotraer_primera_cuota(id_matricula: int, inicio: str) -> None:
    """INICIO = inicio de clases y referencia de vencimientos: la primera
    cuota (generada con el mes actual) se retrotrae al AAAA-MM del INICIO."""
    from repositories import cuota_repository
    from models.cuota import Cuota
    from services import cuota_service
    per = (str(inicio or "").strip())[:7]
    cuotas = cuota_repository.obtener_por_matricula(id_matricula)
    if not cuotas or cuotas[0].get("periodo") == per:
        return
    c = cuotas[0]
    dia = 1
    try:
        dia = int(str(c.get("fecha_vencimiento", "") or "")[8:10])
    except (ValueError, TypeError):
        pass
    cuota_repository.actualizar(Cuota(
        id_cuota=c["id_cuota"], id_matricula=c["id_matricula"],
        periodo=per,
        fecha_vencimiento=cuota_service._fecha_vencimiento_valida(per, dia),
        monto_total=c["monto_total"], monto_pagado=c.get("monto_pagado", 0),
        monto_mora=c.get("monto_mora", 0), saldo=c.get("saldo", c["monto_total"]),
        estado=c.get("estado", "PENDIENTE"), activo=c.get("activo", 1),
    ))


def _importar_matricula_fila(fila: dict, mapping: dict, id_usuario: int,
                           id_estudiante: int, res: dict, beca_nombre: str = "") -> None:
    """Matrícula para todo importado (INICIO como fecha_inicio); beca solo
    si la fila trae BECA válida. No duplica matrícula activa. Atómico con la fila."""
    from services import matricula_service
    from repositories import matricula_repository
    from utils.dates import get_today
    if fila.get("_sin_matricula"):
        res["detalle"] += " (sin matrícula por decisión de revisión)"
        return
    activas = [m for m in matricula_repository.obtener_por_estudiante(id_estudiante)
               if m.get("estado") == "ACTIVO"]
    if activas:
        res["id_matricula"] = activas[0]["id_matricula"]
        # Re-importe: si trae BECA válida no asignada, se asigna ahora
        # (recalcula cuotas pendientes) en vez de nota manual.
        if beca_nombre:
            id_beca = _beca_id_por_nombre(beca_nombre)
            if id_beca is None:
                res["detalle"] += (f" (BECA {beca_nombre} pendiente de asignar manual: "
                                   "no existe)")
            else:
                try:
                    actuales = [b for b in matricula_service.obtener_becas_por_matricula(
                        activas[0]["id_matricula"]) if b.get("activo", 1)]
                except Exception:
                    actuales = []
                if any(b.get("id_beca") == id_beca for b in actuales):
                    res["detalle"] += " (ya tiene matrícula activa con esa beca)"
                else:
                    ok_b, msg_b = matricula_service.asignar_beca(
                        activas[0]["id_matricula"], id_beca, "Importación")
                    if ok_b:
                        res["becas"] = res.get("becas", 0) + 1
                        res["detalle"] += f" (beca {beca_nombre} asignada a matrícula activa)"
                    else:
                        res["detalle"] += f" (BECA {beca_nombre} pendiente de asignar manual: {msg_b})"
        else:
            res["detalle"] += " (ya tiene matrícula activa, sin cambios)"
        return
    id_beca = None
    if beca_nombre:
        id_beca = _beca_id_por_nombre(beca_nombre)
        if id_beca is None:
            raise ErrorFilaImportacion(f"Beca '{beca_nombre}' no existe en el sistema")
    inicio = _inicio_de_fila(fila, mapping)
    tarifa = _tarifa_para_beca(inicio)
    if tarifa is None:
        res["detalle"] += " (sin tarifa para matricular)"
        return
    dia_venc = 15
    try:
        dia_venc = int(inicio[8:10])
    except (ValueError, TypeError, IndexError):
        pass
    becas = [{"id_beca": id_beca, "observacion": "Importación"}] if id_beca else []
    exito_m, msg_m, id_mat = matricula_service.crear_matricula({
        "id_estudiante": id_estudiante,
        "id_tarifa": tarifa["id_tarifa"],
        "fecha_inicio": inicio,
        "dia_vencimiento": dia_venc,
        "becas": becas,
    }, id_usuario)
    if not exito_m:
        raise ErrorFilaImportacion(f"Matrícula - {msg_m}")
    res["id_matricula"] = id_mat
    _retrotraer_primera_cuota(id_mat, inicio)
    res["matriculas"] = res.get("matriculas", 0) + 1
    if id_beca:
        res["becas"] = res.get("becas", 0) + 1
        res["detalle"] += f" + matrícula con beca {beca_nombre}"
    else:
        res["detalle"] += " + matrícula"


MAPEO_TIENDA = {
    "PRODUCTOS": "nombre",
    "CANTIDAD": "cantidad",
    "COSTO_TOTAL": "costo_total",
    "COSTO_X_UNIDAD": "costo_unitario",
    "COSTO_VENTA": "costo_venta",
    "YAPE": "monto_yape",
    "EFECTIVO": "monto_efectivo",
    "P_YAPE": "monto_yape",
    "P_EFECTIVO": "monto_efectivo",
    "CANTIDAD_VENDIDO": "vendidas",
    "UNIDADES_VENDIDAS": "vendidas",
    "QUEDAN": "quedan",
    "CATEGORIA": "categoria",
    "FECHA": "fecha",
}

CAMPOS_OBLIGATORIOS_TIENDA = ["PRODUCTOS"]


def _numf(valor, defecto=0.0) -> float:
    try:
        txt = str(valor or "").strip().replace("s/", "").replace("S/", "").replace(",", "")
        return float(txt or defecto)
    except (ValueError, TypeError):
        return float("nan")


def _numi(valor, defecto=0) -> int:
    try:
        txt = str(valor or "").strip().replace("s/", "").replace("S/", "")
        if txt == "":
            return defecto
        return int(float(txt))
    except (ValueError, TypeError):
        return -1


def validar_fila_tienda(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_TIENDA

    def _norm(cab):
        return str(cab or "").upper().replace(" ", "_")

    def _campo(*nombres):
        for nombre_archivo, nombre_sys in mapping.items():
            if nombre_sys in nombres and nombre_archivo in fila:
                return fila[nombre_archivo]
        # fallback: cabecera del archivo (con o sin espacios) → sys vía MAPEO
        rev = {_norm(k): v for k, v in mapping.items()}
        for nombre_archivo in fila:
            if rev.get(_norm(nombre_archivo)) in nombres:
                return fila[nombre_archivo]
        # último recurso: la cabecera ya es el nombre sys
        for nombre_archivo in fila:
            if _norm(nombre_archivo) in {n.upper() for n in nombres}:
                return fila[nombre_archivo]
        return ""

    nombre = str(_campo("nombre") or "").strip()
    if not nombre:
        errores.append(f"Fila {idx}: PRODUCTOS es obligatorio")
        return errores
    cantidad = _numi(_campo("cantidad"))
    total = _numf(_campo("costo_total"))
    venta = _numf(_campo("costo_venta"))
    yape = _numf(_campo("monto_yape"))
    efec = _numf(_campo("monto_efectivo"))
    vendidas = _numi(_campo("vendidas"))
    quedan_raw = _campo("quedan")
    for etiqueta, v in (("CANTIDAD", cantidad), ("VENDIDAS", vendidas)):
        if v < 0:
            errores.append(f"Fila {idx}: {etiqueta} debe ser número ≥ 0")
    for etiqueta, v in (("COSTO TOTAL", total), ("COSTO VENTA", venta),
                        ("YAPE", yape), ("EFECTIVO", efec)):
        if v != v or v < 0:  # NaN o negativo
            errores.append(f"Fila {idx}: {etiqueta} debe ser número ≥ 0")
    if not errores and vendidas > cantidad:
        errores.append(f"Fila {idx}: VENDIDAS ({vendidas}) > CANTIDAD ({cantidad})")
    if not errores and cantidad > 0 and total <= 0:
        errores.append(f"Fila {idx}: con CANTIDAD se exige COSTO TOTAL > 0")
    if not errores and str(quedan_raw or "").strip() != "":
        quedan = _numi(quedan_raw)
        if quedan != cantidad - vendidas:
            errores.append(f"Fila {idx}: QUEDAN ({quedan}) ≠ CANTIDAD−VENDIDAS ({cantidad - vendidas})")
    return errores


def validar_filas_tienda(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    todos = []
    vistos = set()
    mapping = mapeo or MAPEO_TIENDA
    for idx, fila in enumerate(filas, 1):
        todos.extend(validar_fila_tienda(fila, idx, mapeo))
        nombre = ""
        for na, ns in mapping.items():
            if ns == "nombre" and na in fila:
                nombre = str(fila[na]).strip().lower()
        if nombre:
            if nombre in vistos:
                todos.append(f"Fila {idx}: producto duplicado en el archivo")
            vistos.add(nombre)
    if todos:
        return False, f"{len(todos)} errores encontrados", todos
    return True, "Validación correcta", []


def _buscar_producto_tienda(nombre: str) -> int | None:
    import unicodedata
    from repositories import producto_repository
    objetivo = "".join(c for c in unicodedata.normalize(
        "NFD", str(nombre or "").strip().upper())
        if unicodedata.category(c) != "Mn")
    objetivo = " ".join(objetivo.split())
    for p in producto_repository.obtener_todos(activo=1):
        if p.get("canal") != "TIENDITA":
            continue
        actual = "".join(c for c in unicodedata.normalize(
            "NFD", str(p.get("nombre", ""))) if unicodedata.category(c) != "Mn")
        if " ".join(actual.upper().split()) == objetivo:
            return p["id_producto"]
    return None


def _asegurar_categoria_tienda(nombre: str) -> int:
    from repositories import categoria_producto_repository
    from models.categoria_producto import CategoriaProducto
    nombre = (nombre or "").strip() or "TIENDA"
    row = categoria_producto_repository.obtener_todas()
    for c in row:
        if c["nombre"].lower() == nombre.lower():
            return c["id_categoria_producto"]
    return categoria_producto_repository.insertar(CategoriaProducto(nombre=nombre))


def importar_tienda(filas: list[dict], id_usuario: int = 1,
                    mapeo: dict | None = None) -> tuple[bool, str, dict]:
    from database.connection import transaccion
    from services import inventario_service, venta_service

    resultados = {"productos_creados": 0, "compras": 0, "ventas": 0,
                  "errores": [], "detalles": []}
    mapping = mapeo or MAPEO_TIENDA

    def _norm(cab):
        return str(cab or "").upper().replace(" ", "_")

    def _campo(fila, *nombres):
        for na, ns in mapping.items():
            if ns in nombres and na in fila:
                return fila[na]
        rev = {_norm(k): v for k, v in mapping.items()}
        for na in fila:
            if rev.get(_norm(na)) in nombres:
                return fila[na]
        for na in fila:
            if _norm(na) in {n.upper() for n in nombres}:
                return fila[na]
        return ""

    for idx, fila in enumerate(filas, 1):
        try:
            with transaccion():
                nombre = str(_campo(fila, "nombre")).strip()
                cantidad = _numi(_campo(fila, "cantidad"))
                total = _numf(_campo(fila, "costo_total"))
                venta_pv = _numf(_campo(fila, "costo_venta"))
                yape = _numf(_campo(fila, "monto_yape"))
                efec = _numf(_campo(fila, "monto_efectivo"))
                vendidas = _numi(_campo(fila, "vendidas"))
                fecha = str(_campo(fila, "fecha") or "").strip() or None
                id_cat = _asegurar_categoria_tienda(str(_campo(fila, "categoria") or ""))
                # reutiliza producto existente (importar varios meses no duplica)
                id_prod = _buscar_producto_tienda(nombre)
                if id_prod is None:
                    ok, msg, id_prod = inventario_service.crear_producto({
                        "id_categoria_producto": id_cat, "nombre": nombre,
                        "canal": "TIENDITA", "tipo_empaque": "Unidad",
                        "precio_compra_total": total if total > 0 else None,
                        "precio_venta": venta_pv, "stock_inicial": 0,
                    })
                    if not ok:
                        raise ErrorFilaImportacion(msg)
                    resultados["productos_creados"] += 1
                else:
                    resultados["detalles"].append(f"Fila {idx}: {nombre} ya existía, se suma movimiento")
                if cantidad > 0 and total > 0:
                    # compra única (método EFECTIVO; el split YAPE/EFECTIVO es de ventas)
                    ok_c, msg_c, _ = inventario_service.registrar_compra({
                        "id_producto": id_prod, "cantidad": cantidad,
                        "monto_total": total, "metodo_pago": "EFECTIVO",
                        "motivo": "Importación balance tienda",
                        "fecha_movimiento": fecha,
                        "id_usuario": id_usuario,
                    })
                    if not ok_c:
                        raise ErrorFilaImportacion(msg_c)
                    resultados["compras"] += 1
                if vendidas > 0:
                    # reparte unidades por método según montos
                    uy = round(yape / venta_pv) if venta_pv > 0 and yape > 0 else 0
                    uy = min(max(uy, 0), vendidas)
                    ue = vendidas - uy
                    partes = ([("YAPE", uy)] if uy else []) + ([("EFECTIVO", ue)] if ue else [])
                    if not partes:
                        partes = [("EFECTIVO", vendidas)]
                    for metodo, cant in partes:
                        ok_v, msg_v, _ = venta_service.registrar_venta({
                            "tipo_venta": "TIENDA", "metodo_pago": metodo,
                            "items": [{"id_producto": id_prod, "cantidad": cant}],
                            "fecha_venta": fecha, "id_usuario": id_usuario,
                        })
                        if not ok_v:
                            raise ErrorFilaImportacion(msg_v)
                        resultados["ventas"] += 1
                resultados["detalles"].append(f"Fila {idx}: {nombre} importado")
        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Importación tienda fila {idx}: {e}")

    total = resultados["productos_creados"]
    n_err = len(resultados["errores"])
    logger.info(f"Importación tienda: {total} productos, "
                f"{resultados['compras']} compras, {resultados['ventas']} ventas, {n_err} errores")
    return True, f"{total} productos importados", resultados


# ── Productos: solo catálogo (sin movimientos de compra/venta) ──────
MAPEO_PRODUCTOS = {
    "PRODUCTO": "nombre",
    "PRODUCTOS": "nombre",
    "CATEGORIA": "categoria",
    "COSTO": "costo_unitario",
    "COSTO_UNITARIO": "costo_unitario",
    "COSTO_X_UNIDAD": "costo_unitario",
    "PRECIO_COMPRA": "costo_unitario",
    "PRECIO_VENTA": "precio_venta",
    "PRECIO": "precio_venta",
}

CAMPOS_OBLIGATORIOS_PRODUCTOS = ["PRODUCTO"]


def _campo_generico(fila: dict, mapping: dict, *nombres):
    """Extrae valor por nombre sys con los 3 fallbacks (igual que tienda)."""
    def _norm(cab):
        return str(cab or "").upper().replace(" ", "_")
    for na, ns in mapping.items():
        if ns in nombres and na in fila:
            return fila[na]
    rev = {_norm(k): v for k, v in mapping.items()}
    for na in fila:
        if rev.get(_norm(na)) in nombres:
            return fila[na]
    for na in fila:
        if _norm(na) in {n.upper() for n in nombres}:
            return fila[na]
    return ""


def validar_fila_productos(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_PRODUCTOS
    nombre = str(_campo_generico(fila, mapping, "nombre") or "").strip()
    if not nombre:
        errores.append(f"Fila {idx}: PRODUCTO es obligatorio")
        return errores
    costo = _numf(_campo_generico(fila, mapping, "costo_unitario"))
    precio = _numf(_campo_generico(fila, mapping, "precio_venta"))
    # vacíos → 0.0 vía _numf (defecto); solo se queja de basura/negativos
    if costo != costo or costo < 0:
        errores.append(f"Fila {idx}: COSTO debe ser número ≥ 0")
    if precio != precio or precio < 0:
        errores.append(f"Fila {idx}: PRECIO_VENTA debe ser número ≥ 0")
    return errores


def validar_filas_productos(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    todos = []
    vistos = set()
    mapping = mapeo or MAPEO_PRODUCTOS
    for idx, fila in enumerate(filas, 1):
        todos.extend(validar_fila_productos(fila, idx, mapeo))
        nombre = ""
        for na, ns in mapping.items():
            if ns == "nombre" and na in fila:
                nombre = str(fila[na]).strip().lower()
        if nombre:
            if nombre in vistos:
                todos.append(f"Fila {idx}: producto duplicado en el archivo")
            vistos.add(nombre)
    if todos:
        return False, f"{len(todos)} errores encontrados", todos
    return True, "Validación correcta", []


def importar_productos(filas: list[dict], id_usuario: int = 1,
                       mapeo: dict | None = None) -> tuple[bool, str, dict]:
    """Crea productos de catálogo (canal TIENDITA, stock 0, sin movimientos)."""
    from database.connection import transaccion
    from services import inventario_service

    resultados = {"productos_creados": 0, "errores": [], "detalles": []}
    mapping = mapeo or MAPEO_PRODUCTOS
    for idx, fila in enumerate(filas, 1):
        try:
            with transaccion():
                nombre = str(_campo_generico(fila, mapping, "nombre")).strip()
                costo = _numf(_campo_generico(fila, mapping, "costo_unitario"))
                precio = _numf(_campo_generico(fila, mapping, "precio_venta"))
                id_cat = _asegurar_categoria_tienda(
                    str(_campo_generico(fila, mapping, "categoria") or ""))
                id_prod = _buscar_producto_tienda(nombre)
                if id_prod is None:
                    ok, msg, _id = inventario_service.crear_producto({
                        "id_categoria_producto": id_cat, "nombre": nombre,
                        "canal": "TIENDITA", "tipo_empaque": "Unidad",
                        "precio_compra": costo if costo > 0 else 0,
                        "precio_venta": precio, "stock_inicial": 0,
                    })
                    if not ok:
                        raise ErrorFilaImportacion(msg)
                    resultados["productos_creados"] += 1
                    resultados["detalles"].append(f"Fila {idx}: {nombre} creado")
                else:
                    resultados["detalles"].append(f"Fila {idx}: {nombre} ya existía, sin cambios")
        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Importación productos fila {idx}: {e}")
    total = resultados["productos_creados"]
    n_err = len(resultados["errores"])
    logger.info(f"Importación productos: {total} creados, {n_err} errores")
    return True, f"{total} productos importados", resultados


# ── Compras: entradas a proveedor (crea el producto si no existe) ────
MAPEO_COMPRAS = {
    "PRODUCTO": "nombre",
    "PRODUCTOS": "nombre",
    "CANTIDAD": "cantidad",
    "COSTO_TOTAL": "costo_total",
    "COSTO_X_UNIDAD": "costo_unitario",
    "COSTO_UNITARIO": "costo_unitario",
    "COSTO": "costo_unitario",
    "METODO": "metodo",
    "FECHA": "fecha",
    "CATEGORIA": "categoria",
}

CAMPOS_OBLIGATORIOS_COMPRAS = ["PRODUCTO", "CANTIDAD"]

METODOS_COMPRA = ("YAPE", "EFECTIVO")


def _total_compra(fila: dict, mapping: dict) -> float:
    """COSTO_TOTAL manda; si no, unitario × cantidad."""
    total = _numf(_campo_generico(fila, mapping, "costo_total"))
    if total == total and total > 0:
        return total
    unit = _numf(_campo_generico(fila, mapping, "costo_unitario"))
    cant = _numi(_campo_generico(fila, mapping, "cantidad"))
    if unit == unit and unit > 0 and cant > 0:
        return round(unit * cant, 2)
    return total  # 0.0 o NaN → la validación lo reporta


def validar_fila_compras(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_COMPRAS
    nombre = str(_campo_generico(fila, mapping, "nombre") or "").strip()
    if not nombre:
        errores.append(f"Fila {idx}: PRODUCTO es obligatorio")
        return errores
    cantidad = _numi(_campo_generico(fila, mapping, "cantidad"))
    if cantidad < 1:
        errores.append(f"Fila {idx}: CANTIDAD debe ser entero ≥ 1")
    total = _total_compra(fila, mapping)
    if total != total or total <= 0:
        errores.append(f"Fila {idx}: COSTO_TOTAL (o unitario × cantidad) debe ser > 0")
    metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper()
    if metodo and metodo not in METODOS_COMPRA:
        errores.append(f"Fila {idx}: METODO debe ser YAPE o EFECTIVO (vacío = EFECTIVO)")
    return errores


def validar_filas_compras(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    # Sin control de duplicados: varias compras del mismo producto son válidas.
    todos = []
    for idx, fila in enumerate(filas, 1):
        todos.extend(validar_fila_compras(fila, idx, mapeo))
    if todos:
        return False, f"{len(todos)} errores encontrados", todos
    return True, "Validación correcta", []


def importar_compras(filas: list[dict], id_usuario: int = 1,
                     mapeo: dict | None = None) -> tuple[bool, str, dict]:
    from database.connection import transaccion
    from services import inventario_service

    resultados = {"productos_creados": 0, "compras": 0, "errores": [], "detalles": []}
    mapping = mapeo or MAPEO_COMPRAS
    for idx, fila in enumerate(filas, 1):
        try:
            with transaccion():
                nombre = str(_campo_generico(fila, mapping, "nombre")).strip()
                cantidad = _numi(_campo_generico(fila, mapping, "cantidad"))
                total = _total_compra(fila, mapping)
                metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper() or "EFECTIVO"
                fecha = str(_campo_generico(fila, mapping, "fecha") or "").strip() or None
                id_cat = _asegurar_categoria_tienda(
                    str(_campo_generico(fila, mapping, "categoria") or ""))
                id_prod = _buscar_producto_tienda(nombre)
                if id_prod is None:
                    ok, msg, id_prod = inventario_service.crear_producto({
                        "id_categoria_producto": id_cat, "nombre": nombre,
                        "canal": "TIENDITA", "tipo_empaque": "Unidad",
                        "precio_venta": 0, "stock_inicial": 0,
                    })
                    if not ok:
                        raise ErrorFilaImportacion(msg)
                    resultados["productos_creados"] += 1
                ok_c, msg_c, _ = inventario_service.registrar_compra({
                    "id_producto": id_prod, "cantidad": cantidad,
                    "monto_total": total, "metodo_pago": metodo,
                    "motivo": "Importación compras",
                    "fecha_movimiento": fecha,
                    "id_usuario": id_usuario,
                })
                if not ok_c:
                    raise ErrorFilaImportacion(msg_c)
                resultados["compras"] += 1
                resultados["detalles"].append(f"Fila {idx}: {nombre} x{cantidad} S/{total:.2f} ({metodo})")
        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Importación compras fila {idx}: {e}")
    n_err = len(resultados["errores"])
    logger.info(f"Importación compras: {resultados['compras']} compras, "
                f"{resultados['productos_creados']} productos creados, {n_err} errores")
    return True, f"{resultados['compras']} compras registradas", resultados


# ── Pagos: DNI + PERIODO localizan la cuota; el monto la imputa ───────
MAPEO_PAGOS = {
    "DNI": "dni",
    "PERIODO": "periodo",
    "MONTO": "monto",
    "METODO": "metodo",
    "FECHA": "fecha",
}

CAMPOS_OBLIGATORIOS_PAGOS = ["DNI", "PERIODO", "MONTO"]


def _normalizar_periodo(raw) -> str | None:
    """Acepta AAAA-MM, AAAA/MM, MM-AAAA, MM/AAAA → AAAA-MM (o None)."""
    import re
    txt = str(raw or "").strip().replace("/", "-")
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", txt)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.fullmatch(r"(\d{1,2})-(\d{4})", txt)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    return None


def _nombre_key(nombres: str, apellidos: str) -> str:
    """Clave de identidad para re-importes (sin tildes, 1 espacio, UPPER)."""
    import unicodedata
    txt = f"{nombres or ''} {apellidos or ''}".strip()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt)
                  if unicodedata.category(c) != "Mn")
    return " ".join(txt.upper().split())


def _nombres_de_fila(fila: dict, mapping: dict) -> tuple[str, str]:
    nom = ape = ""
    for na, ns in mapping.items():
        if na in fila and ns == "nombres":
            nom = str(fila[na] or "")
        elif na in fila and ns == "apellidos":
            ape = str(fila[na] or "")
    if not nom:
        for na in fila:
            if str(na).upper() == "NOMBRES":
                nom = str(fila[na] or "")
    if not ape:
        for na in fila:
            if str(na).upper() == "APELLIDOS":
                ape = str(fila[na] or "")
    return nom.strip(), ape.strip()


def _buscar_estudiante_por_nombre(nombres: str, apellidos: str) -> dict | None:
    from repositories import estudiante_repository
    clave = _nombre_key(nombres, apellidos)
    if not clave:
        return None
    for e in estudiante_repository.obtener_todos():
        if _nombre_key(e.get("nombres", ""), e.get("apellidos", "")) == clave:
            return e
    return None


def _localizar_cuota(dni: str, periodo: str) -> tuple[int | None, str, str]:
    """DNI+PERIODO → id_cuota. Retorna (id_cuota|None, codigo, mensaje).

    Códigos: OK, DNI_NO_EXISTE, CUOTA_NO_ENCONTRADA, CUOTA_YA_PAGADA,
    CUOTA_AMBIGUA (reingresos con mismo periodo en 2 matrículas).
    """
    from repositories import (persona_repository, estudiante_repository,
                              matricula_repository, cuota_repository)
    from utils.constants import CUOTA_PAGADO
    dni = str(dni or "").strip().replace(" ", "")
    per = _normalizar_periodo(periodo)
    if not dni:
        return None, "DNI_NO_EXISTE", "DNI vacío"
    if per is None:
        return None, "PERIODO_INVALIDO", f"PERIODO inválido ({periodo}); use AAAA-MM"
    persona = persona_repository.obtener_por_dni(dni)
    if not persona:
        return None, "DNI_NO_EXISTE", f"DNI {dni} no registrado en el sistema"
    est = estudiante_repository.obtener_por_persona(persona["id_persona"])
    if not est:
        return None, "DNI_NO_EXISTE", f"DNI {dni} no es estudiante"
    candidatas, pagadas = [], 0
    for mat in matricula_repository.obtener_por_estudiante(est["id_estudiante"]):
        for c in cuota_repository.obtener_por_matricula(mat["id_matricula"]):
            if not c.get("activo", 1):
                continue  # anuladas no matchean
            if str(c.get("periodo", "")).strip() == per:
                if c.get("estado") == CUOTA_PAGADO:
                    pagadas += 1
                else:
                    candidatas.append(c)
    if len(candidatas) == 1:
        return candidatas[0]["id_cuota"], "OK", ""
    if len(candidatas) > 1:
        return None, "CUOTA_AMBIGUA", f"DNI {dni} periodo {per}: {len(candidatas)} cuotas pendientes"
    if pagadas:
        return None, "CUOTA_YA_PAGADA", f"DNI {dni} periodo {per}: cuota ya pagada"
    return None, "CUOTA_NO_ENCONTRADA", f"DNI {dni} periodo {per}: sin cuota"


def validar_fila_pagos(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_PAGOS
    dni = str(_campo_generico(fila, mapping, "dni") or "").strip().replace(" ", "")
    periodo = str(_campo_generico(fila, mapping, "periodo") or "").strip()
    monto = _numf(_campo_generico(fila, mapping, "monto"))
    metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper()
    if not dni:
        errores.append(f"Fila {idx}: DNI es obligatorio")
    elif not (dni.isdigit() and len(dni) in (8, 9)):
        errores.append(f"Fila {idx}: DNI inválido (8-9 dígitos)")
    if not periodo:
        errores.append(f"Fila {idx}: PERIODO es obligatorio")
    elif _normalizar_periodo(periodo) is None:
        errores.append(f"Fila {idx}: PERIODO inválido ({periodo}); use AAAA-MM")
    if monto != monto or monto <= 0:
        errores.append(f"Fila {idx}: MONTO debe ser número > 0")
    if metodo:
        from services import pago_service
        if metodo not in pago_service.METODOS_VALIDOS:
            errores.append(f"Fila {idx}: METODO debe ser { '/'.join(pago_service.METODOS_VALIDOS)} (vacío = EFECTIVO)")
    return errores


def validar_filas_pagos(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    # Sin duplicados: un periodo puede pagarse en 2 partes (2 filas).
    todos = []
    for idx, fila in enumerate(filas, 1):
        todos.extend(validar_fila_pagos(fila, idx, mapeo))
    if todos:
        return False, f"{len(todos)} errores encontrados", todos
    return True, "Validación correcta", []


def importar_pagos(filas: list[dict], id_usuario: int = 1,
                   mapeo: dict | None = None) -> tuple[bool, str, dict]:
    from database.connection import transaccion
    from services import pago_service

    resultados = {"pagos": 0, "errores": [], "detalles": []}
    mapping = mapeo or MAPEO_PAGOS
    for idx, fila in enumerate(filas, 1):
        try:
            with transaccion():
                dni = str(_campo_generico(fila, mapping, "dni") or "").strip()
                periodo = str(_campo_generico(fila, mapping, "periodo") or "").strip()
                monto = _numf(_campo_generico(fila, mapping, "monto"))
                metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper() or "EFECTIVO"
                fecha = str(_campo_generico(fila, mapping, "fecha") or "").strip() or None
                id_cuota, codigo, msg = _localizar_cuota(dni, periodo)
                if id_cuota is None:
                    raise ErrorFilaImportacion(msg)
                # RN-042: YAPE/PLIN/TRANSFERENCIA exigen comprobante; en
                # importación se permite sin comprobante (igual que el historial)
                # y el pago queda visible en avisos "comprobante pendiente".
                ok, msg_p, _id = pago_service.registrar_pago({
                    "id_usuario": id_usuario, "id_cuota": id_cuota,
                    "monto_pagado": monto, "metodo_pago": metodo,
                    "fecha_pago": fecha,
                    "permitir_sin_comprobante": metodo != "EFECTIVO",
                })
                if not ok:
                    raise ErrorFilaImportacion(msg_p)
                resultados["pagos"] += 1
                extra = " (sin comprobante: queda en avisos)" if metodo != "EFECTIVO" else ""
                resultados["detalles"].append(
                    f"Fila {idx}: DNI {dni} periodo {_normalizar_periodo(periodo)} S/{monto:.2f}{extra}")
        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Importación pagos fila {idx}: {e}")
    n_err = len(resultados["errores"])
    logger.info(f"Importación pagos: {resultados['pagos']} pagos, {n_err} errores")
    return True, f"{resultados['pagos']} pagos registrados", resultados


# ── Uniformes: 1 fila = 1 pago = 1 venta (adelanto y resto son 2 filas).
# ENT = entrenamiento (Camiseta Entrenamiento, venta UNIFORME);
# COM = competencia (Uniforme Competencia, venta TIENDA, convención del
# historial). Cuotas de campeonato (COM como arancel) van por Ventas
# CAMPEONATO por tarifa, fuera de este tipo. ──────────────────────────
MAPEO_UNIFORMES = {
    "DNI": "dni",
    "TIPO": "tipo",
    "MONTO": "monto",
    "FECHA": "fecha",
    "METODO": "metodo",
}

CAMPOS_OBLIGATORIOS_UNIFORMES = ["DNI", "TIPO", "MONTO"]

PRODUCTOS_UNIFORME = {
    "ENT": ("CAMISETA-ENT", "Camiseta Entrenamiento", "UNIFORME"),
    "COM": ("UNIFORME-COM", "Uniforme Competencia", "TIENDA"),
}
PRECIO_UNIFORME_REF = 70.0


def _normalizar_tipo_uniforme(raw) -> str | None:
    t = str(raw or "").strip().upper()
    if t in ("COM", "COMPETENCIA", "COMP"):
        return "COM"
    if t in ("ENT", "ENTRENAMIENTO", "ENTRENO"):
        return "ENT"
    if t.startswith("COM"):
        return "COM"
    if t.startswith("ENT"):
        return "ENT"
    return None


def _fecha_venta_uniforme(raw) -> str | None:
    """AAAA-MM-DD exacto; AAAA-MM o MM/AAAA → día 01. None si inválido."""
    from utils.dates import parse_date
    txt = str(raw or "").strip().replace("/", "-")
    if not txt:
        return None
    if parse_date(txt[:10]) is not None and len(txt) >= 10:
        return txt[:10]
    per = _normalizar_periodo(txt)
    if per is not None:
        return f"{per}-01"
    return None


def _estudiante_por_dni(dni: str):
    """(id_estudiante,) si el DNI es de un estudiante; si no, (None, motivo)."""
    from repositories import (persona_repository, estudiante_repository)
    dni = str(dni or "").strip().replace(" ", "")
    if not dni:
        return None, "DNI vacío"
    per = persona_repository.obtener_por_dni(dni)
    if not per:
        return None, f"DNI {dni} no registrado en el sistema"
    est = estudiante_repository.obtener_por_persona(per["id_persona"])
    if not est:
        return None, f"DNI {dni} no es estudiante"
    return est["id_estudiante"], ""


def validar_fila_uniformes(fila: dict, idx: int, mapeo: dict | None = None) -> list[str]:
    errores = []
    mapping = mapeo or MAPEO_UNIFORMES
    dni = str(_campo_generico(fila, mapping, "dni") or "").strip().replace(" ", "")
    tipo = _normalizar_tipo_uniforme(_campo_generico(fila, mapping, "tipo"))
    monto = _numf(_campo_generico(fila, mapping, "monto"))
    metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper()
    fecha = _fecha_venta_uniforme(_campo_generico(fila, mapping, "fecha"))
    if not dni:
        errores.append(f"Fila {idx}: DNI es obligatorio")
    elif not (dni.isdigit() and len(dni) in (8, 9)):
        errores.append(f"Fila {idx}: DNI inválido (8-9 dígitos)")
    if tipo is None:
        errores.append(f"Fila {idx}: TIPO debe ser COM o ENT")
    if monto != monto or monto <= 0:
        errores.append(f"Fila {idx}: MONTO debe ser número > 0")
    if metodo:
        from services import venta_service
        if metodo not in venta_service.METODOS_VALIDOS:
            errores.append(f"Fila {idx}: METODO inválido (vacío = EFECTIVO)")
    if str(_campo_generico(fila, mapping, "fecha") or "").strip() and fecha is None:
        errores.append(f"Fila {idx}: FECHA inválida (AAAA-MM-DD o AAAA-MM)")
    return errores


def validar_filas_uniformes(filas: list[dict], mapeo: dict | None = None) -> tuple[bool, str, list[str]]:
    # Sin duplicados: adelanto y resto pueden repetir DNI+TIPO en meses distintos.
    todos = []
    for idx, fila in enumerate(filas, 1):
        todos.extend(validar_fila_uniformes(fila, idx, mapeo))
    if todos:
        return False, f"{len(todos)} errores encontrados", todos
    return True, "Validación correcta", []


def _asegurar_producto_uniforme(tipo: str) -> int:
    """Producto por código (CAMISETA-ENT / UNIFORME-COM); lo crea si falta."""
    from repositories import producto_repository
    from services import inventario_service
    codigo, nombre, _tv = PRODUCTOS_UNIFORME[tipo]
    prod = producto_repository.obtener_por_codigo(codigo)
    if prod:
        return prod["id_producto"]
    cats = inventario_service.listar_categorias()
    id_cat = cats[0]["id_categoria_producto"]
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": nombre, "codigo": codigo,
        "canal": "TIENDITA", "tipo_empaque": "Unidad",
        "precio_venta": PRECIO_UNIFORME_REF, "stock_inicial": 0,
    })
    if not ok or not id_prod:
        raise ErrorFilaImportacion(f"No se pudo crear producto {codigo}: {msg}")
    return id_prod


def importar_uniformes(filas: list[dict], id_usuario: int = 1,
                       mapeo: dict | None = None) -> tuple[bool, str, dict]:
    from database.connection import transaccion
    from services import inventario_service, venta_service
    from utils.dates import get_today

    resultados = {"ventas": 0, "productos_creados": 0, "errores": [], "detalles": []}
    mapping = mapeo or MAPEO_UNIFORMES
    creados_esta_carga: set[str] = set()
    for idx, fila in enumerate(filas, 1):
        try:
            with transaccion():
                dni = str(_campo_generico(fila, mapping, "dni") or "").strip()
                tipo = _normalizar_tipo_uniforme(_campo_generico(fila, mapping, "tipo"))
                monto = _numf(_campo_generico(fila, mapping, "monto"))
                metodo = str(_campo_generico(fila, mapping, "metodo") or "").strip().upper() or "EFECTIVO"
                fecha = _fecha_venta_uniforme(_campo_generico(fila, mapping, "fecha")) or get_today()
                id_est, motivo = _estudiante_por_dni(dni)
                if id_est is None:
                    raise ErrorFilaImportacion(motivo)
                if tipo not in PRODUCTOS_UNIFORME:
                    raise ErrorFilaImportacion("TIPO debe ser COM o ENT")
                codigo, _nom, tipo_venta = PRODUCTOS_UNIFORME[tipo]
                from repositories import producto_repository
                ya = producto_repository.obtener_por_codigo(codigo)
                id_prod = _asegurar_producto_uniforme(tipo)
                if not ya and codigo not in creados_esta_carga:
                    creados_esta_carga.add(codigo)
                    resultados["productos_creados"] += 1
                # stock para la venta histórica (compra a precio ref.)
                ok_c, msg_c, _ = inventario_service.registrar_compra({
                    "id_producto": id_prod, "cantidad": 1,
                    "monto_total": PRECIO_UNIFORME_REF, "metodo_pago": "EFECTIVO",
                    "motivo": "Stock p/venta uniforme importada",
                    "fecha_movimiento": fecha, "id_usuario": id_usuario,
                })
                if not ok_c:
                    raise ErrorFilaImportacion(msg_c)
                ok_v, msg_v, _ = venta_service.registrar_venta({
                    "id_estudiante": id_est, "id_usuario": id_usuario,
                    "tipo_venta": tipo_venta, "metodo_pago": metodo,
                    "items": [{"id_producto": id_prod, "cantidad": 1,
                               "precio_unitario": monto}],
                    "monto_total": monto, "fecha_venta": fecha,
                })
                if not ok_v:
                    raise ErrorFilaImportacion(msg_v)
                resultados["ventas"] += 1
                resultados["detalles"].append(
                    f"Fila {idx}: DNI {dni} {tipo} S/{monto:.2f} ({metodo}) {fecha}")
        except ErrorFilaImportacion as e:
            resultados["errores"].append(f"Fila {idx}: {e.mensaje}")
        except Exception as e:
            resultados["errores"].append(f"Fila {idx}: Error inesperado - {str(e)}")
            logger.debug(f"Importación uniformes fila {idx}: {e}")
    n_err = len(resultados["errores"])
    logger.info(f"Importación uniformes: {resultados['ventas']} ventas, {n_err} errores")
    return True, f"{resultados['ventas']} ventas de uniforme registradas", resultados


def _detectar_uniformes(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    cols = {_norm_cab(c) for c in columnas}
    if {"DNI", "TIPO", "MONTO"} <= cols:
        return True, "columnas uniforme (DNI+tipo+monto)"
    return False, ""


def obtener_campos_disponibles() -> list[str]:
    return list(MAPEO_CAMPOS.keys())


def obtener_campos_obligatorios() -> list[str]:
    return CAMPOS_OBLIGATORIOS_ESTUDIANTE.copy()


def obtener_campos_apoderado() -> list[str]:
    return CAMPOS_APODERADO.copy()


# ── E1: registro unificado de tipos (autodetección; futuros tipos se
# registran aquí sin tocar la UI) ──────────────────────────────────
def _norm_cab(cab) -> str:
    return str(cab or "").upper().replace(" ", "_")


def _detectar_estudiantes(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    cols = {_norm_cab(c) for c in columnas}
    if "DNI" in cols and ("NOMBRES" in cols or "APELLIDOS" in cols):
        return True, "columnas DNI+Nombres"
    return False, ""


def _detectar_tienda(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    # Columnas distintivas: exige al menos una clave de tienda Y una señal
    # de venta (YAPE/EFECTIVO/VENDIDO/QUEDAN). Sin señal de venta, un
    # PRODUCTOS+CANTIDAD+COSTO es Compras y PRODUCTOS+PRECIO es Productos.
    cols = {_norm_cab(c) for c in columnas}
    claves = {"PRODUCTOS", "CANTIDAD", "COSTO_TOTAL", "COSTO_VENTA"}
    hits = claves & cols
    if hits and (SENAL_VENTA & cols):
        return True, f"columnas tienda ({', '.join(sorted(hits))})"
    return False, ""


# Señales de venta (Tienda) y de costo (Compras). Un CSV con PRODUCTOS
# matchea varios detectores a la vez; detectar_tipo exige 1 solo hit.
SENAL_VENTA = {"CANTIDAD_VENDIDO", "UNIDADES_VENDIDAS", "VENDIDO", "YAPE",
               "EFECTIVO", "P_YAPE", "P_EFECTIVO", "QUEDAN"}
SENAL_COSTO = {"COSTO_TOTAL", "COSTO_X_UNIDAD", "COSTO_UNITARIO", "COSTO",
               "COSTO_COMPRA"}
SENAL_PRECIO = {"PRECIO_VENTA", "PRECIO", "COSTO_VENTA"}
COLS_NOMBRE_PROD = {"PRODUCTO", "PRODUCTOS"}


def _detectar_productos(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    # Catálogo: nombre + precio, SIN cantidad, SIN señales de venta y SIN
    # costo total/unitario explícito (eso es Compras). COSTO solo sí vale
    # (es el costo unitario del catálogo).
    cols = {_norm_cab(c) for c in columnas}
    veto = (SENAL_VENTA | (SENAL_COSTO - {"COSTO"})) & cols
    if ((COLS_NOMBRE_PROD & cols) and (SENAL_PRECIO & cols)
            and "CANTIDAD" not in cols and not veto):
        return True, "columnas catálogo producto (nombre+precio)"
    return False, ""


def _detectar_compras(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    # Entradas: nombre + cantidad + costo, SIN señales de venta.
    cols = {_norm_cab(c) for c in columnas}
    if ((COLS_NOMBRE_PROD & cols) and "CANTIDAD" in cols
            and (SENAL_COSTO & cols) and not (SENAL_VENTA & cols)):
        return True, "columnas compra (producto+cantidad+costo)"
    return False, ""


def _detectar_pagos(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    # Pagos de cuotas: DNI + PERIODO + MONTO. Si trae NOMBRES/APELLIDOS
    # también matchea Estudiantes → ambiguo (elegir tipo manual).
    cols = {_norm_cab(c) for c in columnas}
    if {"DNI", "PERIODO", "MONTO"} <= cols:
        return True, "columnas pago (DNI+periodo+monto)"
    return False, ""


HOJAS_HISTORIAL = ("RELACIÓN DE ALUMNOS", "INGRESOS", "VENTA UNIFORME")


def _detectar_historial(columnas: list[str], hojas: list[str]) -> tuple[bool, str]:
    if hojas and all(h in hojas for h in HOJAS_HISTORIAL):
        return True, "hojas RELACIÓN/INGRESOS/VENTA"
    return False, ""


TIPOS_IMPORTACION = {
    "Estudiantes": {
        "descripcion": "DNI, Nombres, Apellidos (+ apoderado opcional).",
        "detectar": _detectar_estudiantes,
        "campos": lambda: list(MAPEO_CAMPOS.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_ESTUDIANTE.copy(),
        "validar": lambda filas, mapeo=None: validar_filas(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_estudiantes(filas, uid, mapeo),
    },
    "Tienda": {
        "descripcion": "PRODUCTOS, CANTIDAD, COSTO TOTAL/VENTA, YAPE, EFECTIVO, VENDIDO, QUEDAN.",
        "detectar": _detectar_tienda,
        "campos": lambda: list(MAPEO_TIENDA.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_TIENDA.copy(),
        "validar": lambda filas, mapeo=None: validar_filas_tienda(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_tienda(filas, uid, mapeo),
    },
    "Historial": {
        "descripcion": "XLSX con hojas RELACIÓN/INGRESOS/VENTA (posicional, sin mapeo).",
        "detectar": _detectar_historial,
        "campos": lambda: [],
        "obligatorios": lambda: [],
        "validar": lambda filas, mapeo=None: (True, "OK", []),
        "ejecutar": None,  # va por importar_historial_excel (ruta directa)
    },
    "Productos": {
        "descripcion": "Catálogo: PRODUCTO, CATEGORIA, COSTO, PRECIO_VENTA (sin movimientos).",
        "detectar": _detectar_productos,
        "campos": lambda: list(MAPEO_PRODUCTOS.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_PRODUCTOS.copy(),
        "validar": lambda filas, mapeo=None: validar_filas_productos(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_productos(filas, uid, mapeo),
    },
    "Compras": {
        "descripcion": "Entradas: PRODUCTO, CANTIDAD, COSTO_TOTAL (o unitario), METODO, FECHA.",
        "detectar": _detectar_compras,
        "campos": lambda: list(MAPEO_COMPRAS.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_COMPRAS.copy(),
        "validar": lambda filas, mapeo=None: validar_filas_compras(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_compras(filas, uid, mapeo),
    },
    "Pagos": {
        "descripcion": "Pagos de cuotas: DNI + PERIODO (AAAA-MM) + MONTO (+ METODO/FECHA).",
        "detectar": _detectar_pagos,
        "campos": lambda: list(MAPEO_PAGOS.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_PAGOS.copy(),
        "validar": lambda filas, mapeo=None: validar_filas_pagos(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_pagos(filas, uid, mapeo),
    },
    "Uniformes": {
        "descripcion": "Ventas de uniforme: DNI + TIPO (COM/ENT) + MONTO + FECHA (+ METODO). 1 fila = 1 venta.",
        "detectar": _detectar_uniformes,
        "campos": lambda: list(MAPEO_UNIFORMES.keys()),
        "obligatorios": lambda: CAMPOS_OBLIGATORIOS_UNIFORMES.copy(),
        "validar": lambda filas, mapeo=None: validar_filas_uniformes(filas, mapeo),
        "ejecutar": lambda filas, uid, mapeo=None: importar_uniformes(filas, uid, mapeo),
    },
}


def detectar_tipo(columnas: list[str], hojas: list[str]) -> tuple[str | None, str]:
    """Retorna (tipo, motivo). None si ambiguo o irreconocible."""
    hits = []
    for nombre, spec in TIPOS_IMPORTACION.items():
        ok, motivo = spec["detectar"](columnas or [], hojas or [])
        if ok:
            hits.append((nombre, motivo))
    if len(hits) == 1:
        return hits[0]
    return None, "ambiguo o irreconocible" if hits else "sin coincidencias"
