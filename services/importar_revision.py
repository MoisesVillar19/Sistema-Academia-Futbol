"""E2: revisión PREVIA a ejecutar, con opciones explícitas por hallazgo.

Nada se adivina en silencio: cada hallazgo trae opciones y la ejecución
exige una resolución por hallazgo (omitir, provisional, corregir...).
Las resoluciones viajan como {hallazgo_id: opcion_id} y el ejecutor las aplica.
"""
import re

OPC_OMITIR = "omitir"
OPC_PROVISIONAL = "provisional"
OPC_CORREGIR = "corregir"
OPC_SIN_BECA = "sin_beca"
OPC_ACTUALIZAR = "actualizar"
OPC_CREAR_BECA = "crear_beca"

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
            elif "INICIO" in err:
                codigo, opciones = "INICIO_INVALIDO", list(_OPCIONES_BASE)
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
                # Si el DNI es de la MISMA persona (nombre coincide), se
                # puede actualizar en vez de solo omitir (re-importe con DNIs).
                misma = False
                try:
                    per = persona_repository.obtener_por_dni(dni)
                    nom_f, ape_f = importar_service._nombres_de_fila(
                        fila, mapeo or importar_service.MAPEO_CAMPOS)
                    if per and nom_f and ape_f:
                        misma = (importar_service._nombre_key(
                            per.get("nombres", ""), per.get("apellidos", ""))
                            == importar_service._nombre_key(nom_f, ape_f))
                except Exception:
                    pass
                if misma:
                    hallazgos.append({
                        "id": _hid("est", idx, "DNI_DUPLICADO"), "fila": idx,
                        "codigo": "DNI_DUPLICADO",
                        "mensaje": f"Fila {idx}: DNI {dni} ya registrado (misma persona)",
                        "opciones": [
                            {"id": OPC_ACTUALIZAR, "label": "Actualizar datos"},
                            {"id": OPC_OMITIR, "label": "Omitir fila"}],
                        "default": OPC_ACTUALIZAR,
                    })
                else:
                    hallazgos.append({
                        "id": _hid("est", idx, "DNI_DUPLICADO"), "fila": idx,
                        "codigo": "DNI_DUPLICADO",
                        "mensaje": f"Fila {idx}: DNI {dni} ya registrado en el sistema",
                        "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                    })
        beca = _beca_de(fila, mapeo)
        if beca and importar_service._beca_id_por_nombre(beca) is None:
            opciones = [
                {"id": OPC_OMITIR, "label": "Omitir fila"},
                {"id": OPC_SIN_BECA, "label": "Sin beca (solo estudiante)"},
            ]
            if importar_service._inferir_beca(beca) is not None:
                opciones.append({"id": OPC_CREAR_BECA, "label": "Crear beca"})
            hallazgos.append({
                "id": _hid("est", idx, "BECA_NO_EXISTE"), "fila": idx,
                "codigo": "BECA_NO_EXISTE",
                "mensaje": f"Fila {idx}: beca '{beca}' no existe en el sistema",
                "opciones": opciones,
                "default": OPC_SIN_BECA,
            })
        # Re-importe idempotente: mismo Nombres+Apellidos ya registrado.
        # Actualizar no duplica: corrige datos + crea matrícula si no tiene.
        nom, ape = importar_service._nombres_de_fila(
            fila, mapeo or importar_service.MAPEO_CAMPOS)
        if nom and ape and importar_service._buscar_estudiante_por_nombre(nom, ape):
            hallazgos.append({
                "id": _hid("est", idx, "YA_EXISTE"), "fila": idx,
                "codigo": "YA_EXISTE",
                "mensaje": f"Fila {idx}: {nom} {ape} ya registrado (re-importe)",
                "opciones": [
                    {"id": OPC_ACTUALIZAR, "label": "Actualizar datos"},
                    {"id": OPC_OMITIR, "label": "Omitir fila"}],
                "default": OPC_ACTUALIZAR,
            })
    return hallazgos


def _beca_de(fila: dict, mapeo: dict | None) -> str:
    from services import importar_service
    mapping = mapeo or importar_service.MAPEO_CAMPOS
    for na, ns in mapping.items():
        if ns == "beca" and na in fila:
            return str(fila[na] or "").strip()
    for na in fila:
        if str(na).upper() == "BECA":
            return str(fila[na] or "").strip()
    return ""


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
    if tipo == "Productos":
        return revisar_productos(filas, mapeo)
    if tipo == "Compras":
        return revisar_compras(filas, mapeo)
    if tipo == "Pagos":
        return revisar_pagos(filas, mapeo)
    if tipo == "Uniformes":
        return revisar_uniformes(filas, mapeo)
    return revisar_estudiantes(filas, mapeo)


def _nombre_prod_de(fila: dict, mapeo: dict | None, mapping: dict) -> str:
    for na, ns in mapping.items():
        if ns == "nombre" and na in fila:
            return str(fila[na] or "").strip()
    for na in fila:
        if str(na).upper().replace(" ", "_") in ("PRODUCTO", "PRODUCTOS"):
            return str(fila[na] or "").strip()
    return ""


def revisar_productos(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Códigos: FALTA_NOMBRE, NUMERO_INVALIDO, DUPLICADO.
    Existente en BD no es hallazgo (se informa sin cambios, como Tienda)."""
    from services import importar_service
    mapping = mapeo or importar_service.MAPEO_PRODUCTOS
    hallazgos = []
    vistos = set()
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila_productos(fila, idx, mapeo):
            codigo = "FALTA_NOMBRE" if "es obligatorio" in err else "NUMERO_INVALIDO"
            hallazgos.append({
                "id": _hid("pro", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
        nombre = _nombre_prod_de(fila, mapeo, mapping).lower()
        if nombre:
            if nombre in vistos:
                hallazgos.append({
                    "id": _hid("pro", idx, "DUPLICADO"), "fila": idx,
                    "codigo": "DUPLICADO",
                    "mensaje": f"Fila {idx}: producto duplicado en el archivo",
                    "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                })
            vistos.add(nombre)
    return hallazgos


def revisar_compras(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Códigos: FALTA_NOMBRE, CANTIDAD_INVALIDA, TOTAL_INVALIDO, METODO_INVALIDO.
    Sin control de duplicados: varias compras del mismo producto son válidas."""
    from services import importar_service
    hallazgos = []
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila_compras(fila, idx, mapeo):
            if "es obligatorio" in err:
                codigo = "FALTA_NOMBRE"
            elif "CANTIDAD" in err:
                codigo = "CANTIDAD_INVALIDA"
            elif "METODO" in err:
                codigo = "METODO_INVALIDO"
            else:
                codigo = "TOTAL_INVALIDO"
            hallazgos.append({
                "id": _hid("com", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
    return hallazgos


def revisar_pagos(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Códigos: FALTA_DATO, DATO_INVALIDO, DNI_NO_EXISTE, PERIODO_INVALIDO,
    CUOTA_NO_ENCONTRADA, CUOTA_YA_PAGADA, CUOTA_AMBIGUA, MONTO_EXCEDE.
    La cuota se localiza en vivo (DNI+PERIODO); el saldo se valida aquí."""
    from services import importar_service
    from repositories import cuota_repository
    mapping = mapeo or importar_service.MAPEO_PAGOS
    hallazgos = []
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila_pagos(fila, idx, mapeo):
            if "es obligatorio" in err:
                codigo = "FALTA_DATO"
            elif "PERIODO" in err:
                codigo = "PERIODO_INVALIDO"
            elif "METODO" in err:
                codigo = "DATO_INVALIDO"
            elif "DNI" in err:
                codigo = "DATO_INVALIDO"
            else:
                codigo = "DATO_INVALIDO"
            hallazgos.append({
                "id": _hid("pag", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
        dni = str(importar_service._campo_generico(fila, mapping, "dni") or "").strip()
        periodo = str(importar_service._campo_generico(fila, mapping, "periodo") or "").strip()
        monto = importar_service._numf(importar_service._campo_generico(fila, mapping, "monto"))
        if not dni or not periodo or not (monto == monto and monto > 0):
            continue  # ya reportado arriba
        id_cuota, codigo, msg = importar_service._localizar_cuota(dni, periodo)
        if id_cuota is None:
            hallazgos.append({
                "id": _hid("pag", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": f"Fila {idx}: {msg}",
                "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
        elif monto > (cuota_repository.obtener_por_id(id_cuota) or {}).get("saldo", 0):
            hallazgos.append({
                "id": _hid("pag", idx, "MONTO_EXCEDE"), "fila": idx,
                "codigo": "MONTO_EXCEDE",
                "mensaje": f"Fila {idx}: MONTO S/{monto:.2f} excede el saldo de la cuota",
                "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
    return hallazgos


def revisar_uniformes(filas: list[dict], mapeo: dict | None = None) -> list[dict]:
    """Códigos: FALTA_DATO, TIPO_INVALIDO, FECHA_INVALIDA, DATO_INVALIDO,
    DNI_NO_EXISTE. El estudiante debe existir (DNI real). Todo [omitir]."""
    from services import importar_service
    mapping = mapeo or importar_service.MAPEO_UNIFORMES
    hallazgos = []
    for idx, fila in enumerate(filas, 1):
        for err in importar_service.validar_fila_uniformes(fila, idx, mapeo):
            if "es obligatorio" in err:
                codigo = "FALTA_DATO"
            elif "TIPO" in err:
                codigo = "TIPO_INVALIDO"
            elif "FECHA" in err:
                codigo = "FECHA_INVALIDA"
            else:
                codigo = "DATO_INVALIDO"
            hallazgos.append({
                "id": _hid("uni", idx, codigo), "fila": idx, "codigo": codigo,
                "mensaje": err, "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
            })
        dni = str(importar_service._campo_generico(fila, mapping, "dni") or "").strip()
        if dni and dni.isdigit() and len(dni) in (8, 9):
            _id, motivo = importar_service._estudiante_por_dni(dni)
            if _id is None:
                hallazgos.append({
                    "id": _hid("uni", idx, "DNI_NO_EXISTE"), "fila": idx,
                    "codigo": "DNI_NO_EXISTE",
                    "mensaje": f"Fila {idx}: {motivo}",
                    "opciones": list(_OPCIONES_BASE), "default": OPC_OMITIR,
                })
    return hallazgos


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

    omitir → saca la fila; provisional → inyecta DNI; corregir → recalcula QUEDAN;
    sin_beca → vacía BECA (el estudiante entra sin matrícula);
    actualizar → marca la fila para corregir datos en vez de duplicar;
    crear_beca → crea la beca inferida y la conserva en la fila.
    """
    from services import importar_service
    _por_tipo = {
        "Tienda": importar_service.MAPEO_TIENDA,
        "Productos": importar_service.MAPEO_PRODUCTOS,
        "Compras": importar_service.MAPEO_COMPRAS,
        "Pagos": importar_service.MAPEO_PAGOS,
        "Uniformes": importar_service.MAPEO_UNIFORMES,
    }
    mapping = mapeo or _por_tipo.get(tipo, importar_service.MAPEO_CAMPOS)
    omitidas: set[int] = set()
    notas: list[str] = []
    filas = [dict(f) for f in filas]
    provisionales_usados: set[str] = set()
    # Las filas a actualizar conservan su DNI: el provisional solo aplica a
    # filas nuevas. Pre-escaneo porque el dict no garantiza orden.
    actualizar_idx: set[int] = set()
    for hid, opcion in (resoluciones or {}).items():
        if opcion == OPC_ACTUALIZAR:
            try:
                _t, idx_s, _cod = hid.split(":", 2)
                idx = int(idx_s) - 1
                if 0 <= idx < len(filas):
                    actualizar_idx.add(idx)
            except (ValueError, AttributeError):
                pass
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
        elif opcion == OPC_ACTUALIZAR and tipo == "Estudiantes":
            filas[idx]["_actualizar"] = 1
            notas.append(f"Fila {idx + 1}: se actualizará el registro existente")
        elif opcion == OPC_SIN_BECA and tipo == "Estudiantes":
            col = _columna(filas[idx], mapping, ("beca",), ("BECA",))
            if col is not None:
                filas[idx][col] = ""
            filas[idx]["_sin_matricula"] = 1
            notas.append(f"Fila {idx + 1}: entra sin beca (sin matrícula)")
        elif opcion == OPC_CREAR_BECA and tipo == "Estudiantes":
            col = _columna(filas[idx], mapping, ("beca",), ("BECA",))
            nombre_beca = str(filas[idx].get(col, "") if col else "").strip()
            bid, detalle = importar_service._crear_beca_inferida(nombre_beca)
            if bid is None:
                if col is not None:
                    filas[idx][col] = ""
                filas[idx]["_sin_matricula"] = 1
                notas.append(f"Fila {idx + 1}: no se pudo crear beca ({detalle}); entra sin beca")
            else:
                notas.append(f"Fila {idx + 1}: beca {detalle}")
        elif opcion == OPC_PROVISIONAL and tipo == "Estudiantes":
            if idx in actualizar_idx:
                continue  # la fila se actualiza: no se inyecta DNI nuevo
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
