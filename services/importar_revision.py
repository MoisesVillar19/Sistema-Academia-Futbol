"""E2: revisión PREVIA a ejecutar, con opciones explícitas por hallazgo.

Nada se adivina en silencio: cada hallazgo trae opciones y la ejecución
exige una resolución por hallazgo (omitir, provisional, corregir...).
Las resoluciones viajan como {hallazgo_id: opcion_id} y el ejecutor las aplica.
"""
import re

OPC_OMITIR = "omitir"
OPC_PROVISIONAL = "provisional"
OPC_CORREGIR = "corregir"

_OPCIONES_BASE = [{"id": OPC_OMITIR, "label": "Omitir fila"}]


def _hid(tipo: str, idx: int, codigo: str) -> str:
    return f"{tipo}:{idx}:{codigo}"


def _dni_de(fila: dict, mapeo: dict | None) -> str:
    from services import importar_service
    mapping = mapeo or importar_service.MAPEO_CAMPOS
    for na, ns in mapping.items():
        if ns == "dni" and na in fila:
            return str(fila[na] or "").strip()
    for na in fila:
        if str(na).upper() == "DNI":
            return str(fila[na] or "").strip()
    return ""


def revisar_estudiantes(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Hallazgos estructurados. Códigos: FALTA_DNI, DNI_INVALIDO, DNI_DUPLICADO,
    FECHA_INVALIDA, SEXO_INVALIDO, OTRO."""
    from services import importar_service
    from repositories import persona_repository
    hallazgos = []
    vistos = set()
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila(fila, idx, mapeo):
            if "es obligatorio" in err and "DNI" in err:
                codigo, opciones = "FALTA_DNI", [
                    {"id": OPC_PROVISIONAL, "label": "Generar DNI provisional"},
                    {"id": OPC_OMITIR, "label": "Omitir fila"}]
            elif "inválido" in err and ("DNI" in err or "Carnet" in err):
                codigo, opciones = "DNI_INVALIDO", list(_OPCIONES_BASE)
            elif "Fecha_Nacimiento" in err:
                codigo, opciones = "FECHA_INVALIDA", list(_OPCIONES_BASE)
            elif "Sexo" in err:
                codigo, opciones = "SEXO_INVALIDO", list(_OPCIONES_BASE)
            else:
                codigo, opciones = "OTRO", list(_OPCIONES_BASE)
            hallazgos.append({
                "id": _hid("est", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": opciones, "default": opciones[0]["id"],
            })
        dni = _dni_de(fila, mapeo).replace(" ", "")
        if dni:
            if dni in vistos:
                hallazgos.append({
                    "id": _hid("est", idx, "DNI_DUPLICADO"), "fila": idx,
                    "codigo": "DNI_DUPLICADO",
                    "mensaje": f"Fila {idx}: DNI duplicado en el archivo",
                    "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                })
            vistos.add(dni)
            if persona_repository.existe_dni(dni):
                hallazgos.append({
                    "id": _hid("est", idx, "DNI_DUPLICADO"), "fila": idx,
                    "codigo": "DNI_DUPLICADO",
                    "mensaje": f"Fila {idx}: DNI {dni} ya registrado en el sistema",
                    "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                })
    return hallazgos


def revisar_tienda(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Códigos: FALTA_NOMBRE, NUMERO_INVALIDO, VENDIDAS_MAYOR, QUEDAN_MAL, DUPLICADO."""
    from services import importar_service
    hallazgos = []
    vistos = set()
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila_tienda(fila, idx, mapeo):
            if "PRODUCTOS es obligatorio" in err:
                codigo, opciones = "FALTA_NOMBRE", list(_OPCIONES_BASE)
            elif "QUEDAN" in err:
                codigo, opciones = "QUEDAN_MAL", [
                    {"id": OPC_CORREGIR, "label": "Corregir QUEDAN (= CANT−VEND)"},
                    {"id": OPC_OMITIR, "label": "Omitir fila"}]
            elif "duplicado" in err:
                codigo, opciones = "DUPLICADO", list(_OPCIONES_BASE)
            else:
                codigo, opciones = "NUMERO_INVALIDO", list(_OPCIONES_BASE)
            hallazgos.append({
                "id": _hid("tie", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": opciones, "default": opciones[0]["id"],
            })
        mapping = mapeo or importar_service.MAPEO_TIENDA
        nombre = ""
        for na, ns in mapping.items():
            if ns == "nombre" and na in fila:
                nombre = str(fila[na]).strip().lower()
        if nombre:
            if nombre in vistos:
                hallazgos.append({
                    "id": _hid("tie", idx, "DUPLICADO"), "fila": idx,
                    "codigo": "DUPLICADO",
                    "mensaje": f"Fila {idx}: producto duplicado en el archivo",
                    "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                })
            vistos.add(nombre)
    return hallazgos


def revisar(tipo: str, filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    if tipo == "Tienda":
        return revisar_tienda(filas, mapeo)
    return revisar_estudiantes(filas, mapeo)


def siguiente_dni_provisional() -> str:
    from repositories import persona_repository
    n = 90000001
    while persona_repository.existe_dni(str(n)):
        n += 1
    return str(n)


def _columna(fila: dict, mapeo: dict | None, sys_nombres: tuple,
             fallback_upper: tuple) -> str | None:
    """Nombre real de la columna en la fila para un campo sys (o None)."""
    mapping = mapeo or {}
    for na, ns in mapping.items():
        if ns in sys_nombres and na in fila:
            return na
    for na in fila:
        if str(na).upper().replace(" ", "_") in fallback_upper:
            return na
    return None


def aplicar_resoluciones(tipo: str, filas: list[dict], mapeo: dict | None,
                         resoluciones: dict) -> tuple[list[dict], list[str]]:
    """Aplica {hallazgo_id: opcion}. Retorna (filas_efectivas, notas).

    omitir → saca la fila; provisional → inyecta DNI; corregir → recalcula QUEDAN.
    """
    from services import importar_service
    mapping = mapeo or (importar_service.MAPEO_TIENDA if tipo == "Tienda"
                        else importar_service.MAPEO_CAMPOS)
    omitidas: set[int] = set()
    notas: list[str] = []
    filas = [dict(f) for f in filas]
    provisionales_usados: set[str] = set()
    for hid, opcion in (resoluciones or {}).items():
        try:
            _t, idx_s, _cod = hid.split(":", 2)
            idx = int(idx_s) - 1
        except (ValueError, AttributeError):
            continue
        if not 0 <= idx < len(filas):
            continue
        if opcion == OPC_OMITIR:
            omitidas.add(idx)
        elif opcion == OPC_PROVISIONAL and tipo == "Estudiantes":
            from repositories import persona_repository
            col = _columna(filas[idx], mapping, ("dni",), ("DNI",))
            dni = siguiente_dni_provisional()
            while dni in provisionales_usados or persona_repository.existe_dni(dni):
                dni = str(int(dni) + 1)
            provisionales_usados.add(dni)
            if col is None:
                filas[idx]["DNI"] = dni
            else:
                filas[idx][col] = dni
            notas.append(f"Fila {idx + 1}: DNI provisional {dni}")
        elif opcion == OPC_CORREGIR and tipo == "Tienda":
            f = filas[idx]
            col_q = _columna(f, mapping, ("quedan",), ("QUEDAN",))
            col_c = _columna(f, mapping, ("cantidad",), ("CANTIDAD",))
            col_v = _columna(f, mapping, ("vendidas",),
                             ("VENDIDAS", "CANTIDAD_VENDIDO", "CANTIDAD_VENDIDAS",
                              "UNIDADES_VENDIDAS", "VENDIDO"))
            try:
                cant = importar_service._numi(f.get(col_c, 0)) if col_c else 0
                vend = importar_service._numi(f.get(col_v, 0)) if col_v else 0
                if col_q is None:
                    f["QUEDAN"] = cant - vend
                else:
                    f[col_q] = cant - vend
                notas.append(f"Fila {idx + 1}: QUEDAN corregido a {cant - vend}")
            except Exception:
                omitidas.add(idx)
    efectivas = [f for i, f in enumerate(filas) if i not in omitidas]
    if omitidas:
        notas.append(f"{len(omitidas)} fila(s) omitidas por decisión del usuario")
    return efectivas, notas
