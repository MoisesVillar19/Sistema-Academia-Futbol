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
                ok, msg, id_prod = inventario_service.crear_producto({
                    "id_categoria_producto": id_cat, "nombre": nombre,
                    "canal": "TIENDITA", "tipo_empaque": "Unidad",
                    "precio_compra_total": total if total > 0 else None,
                    "precio_venta": venta_pv, "stock_inicial": 0,
                })
                if not ok:
                    raise ErrorFilaImportacion(msg)
                resultados["productos_creados"] += 1
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
    cols = {_norm_cab(c) for c in columnas}
    claves = {"PRODUCTOS", "CANTIDAD", "COSTO_TOTAL", "COSTO_VENTA"}
    hits = claves & cols
    if hits:
        return True, f"columnas tienda ({', '.join(sorted(hits))})"
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
