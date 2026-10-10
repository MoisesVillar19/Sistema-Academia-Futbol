"""Lógica de uniformes: N tipos dinámicos (`tipo_uniforme`) + tallas con stock.

v1.2.1: se elimina el hardcode ENT/COM. Todo tipo de uniforme ACTIVO con
producto vinculado (`producto.id_tipo_uniforme`) es vendible. Las claves
legacy "ENT"/"COM" se conservan por compatibilidad (historial, importador,
regalo RN-051 que sigue siendo solo Entrenamiento).
"""
import re
import unicodedata

from utils.logger import logger

# Códigos legacy (compatibilidad histórica).
CODIGO_POR_TIPO = {"ENT": "CAMISETA-ENT", "COM": "UNIFORME-COM"}
NOMBRE_POR_TIPO = {"ENT": "Camiseta Entrenamiento", "COM": "Uniforme Competencia"}
PRECIO_UNIFORME_REF = 70.0


def _norm(texto) -> str:
    """Normaliza para comparar: mayúsculas, sin tildes, espacios simples."""
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Z0-9]+", " ", t.upper()).strip()
    return re.sub(r"\s+", " ", t)


def codigo_para_nombre(nombre: str) -> str:
    """Slug único de producto para un tipo: UNI-XXX (sufijo -2, -3 si choca).

    Se descarta un "UNIFORME" inicial ("Uniforme Arquero" → UNI-ARQUERO).
    """
    from repositories import producto_repository
    tokens = [t for t in _norm(nombre).split(" ") if t]
    if len(tokens) > 1 and tokens[0] == "UNIFORME":
        tokens = tokens[1:]
    base = re.sub(r"[^A-Z0-9]+", "-", " ".join(tokens)).strip("-")
    base = f"UNI-{base}"[:30].rstrip("-") or "UNI-TIPO"
    codigo = base
    n = 2
    while producto_repository.existe_codigo(codigo):
        codigo = f"{base}-{n}"[:30]
        n += 1
    return codigo


def _clave_legacy(nombre_tipo: str, codigo: str | None) -> str | None:
    """'ENT'/'COM' solo por código legacy o nombre exacto seed; si no, None.

    Sin adivinanza por substring: un tipo nuevo "Uniforme Competencia
    Reserva" NO debe colapsar a la clave COM.
    """
    cod = (codigo or "").upper()
    if cod == "CAMISETA-ENT":
        return "ENT"
    if cod == "UNIFORME-COM":
        return "COM"
    return None


# Nombres seed legacy → código (fallback solo para BD sin vínculo id_tipo).
_LEGACY_POR_NOMBRE_EXACTO = {
    "UNIFORME ENTRENAMIENTO": "CAMISETA-ENT",
    "UNIFORME COMPETENCIA": "UNIFORME-COM",
}

# Alias legacy → (clave, código, nombre canónico). Para tipos legacy aún
# sin producto (el seed solo trae CAMISETA-ENT; UNIFORME-COM nace a demanda).
_LEGACY_ALIAS = {
    "ENT": ("ENT", "CAMISETA-ENT", "Camiseta Entrenamiento"),
    "ENTRENAMIENTO": ("ENT", "CAMISETA-ENT", "Camiseta Entrenamiento"),
    "ENTRENO": ("ENT", "CAMISETA-ENT", "Camiseta Entrenamiento"),
    "COM": ("COM", "UNIFORME-COM", "Uniforme Competencia"),
    "COMP": ("COM", "UNIFORME-COM", "Uniforme Competencia"),
    "COMPETENCIA": ("COM", "UNIFORME-COM", "Uniforme Competencia"),
}


def tipos_vendibles() -> list[dict]:
    """Tipos activos con producto activo vinculado, listos para vender.

    Cada entrada: {clave, nombre, codigo, id_tipo_uniforme, id_producto,
    tipo_venta}. Legacy ENT/COM primero (compat), resto por nombre.
    """
    from repositories import producto_repository
    try:
        from services import tipo_uniforme_service
        tipos = tipo_uniforme_service.listar_tipos(activo=1) or []
    except Exception:
        tipos = []
    legacy, nuevos = [], []
    for t in tipos:
        id_tipo = t.get("id_tipo_uniforme")
        prod = None
        try:
            prod = producto_repository.obtener_por_tipo_uniforme(id_tipo)
        except Exception:
            prod = None
        codigo = (prod or {}).get("codigo") if prod else None
        if not prod:
            # Fallback legacy exacto: producto creado antes del vínculo
            # id_tipo (solo nombres seed exactos, sin substring).
            fb = _LEGACY_POR_NOMBRE_EXACTO.get(_norm(t.get("nombre", "")))
            if fb:
                try:
                    prod = producto_repository.obtener_por_codigo(fb)
                except Exception:
                    prod = None
                codigo = fb if prod else None
        if not prod or (prod.get("activo", 1) == 0):
            continue
        clave = _clave_legacy(t.get("nombre", ""), codigo) or str(t.get("nombre", "")).strip()
        entrada = {
            "clave": clave,
            "nombre": t.get("nombre", ""),
            "codigo": codigo or prod.get("codigo"),
            "id_tipo_uniforme": id_tipo,
            "id_producto": prod.get("id_producto"),
            "tipo_venta": "UNIFORME" if clave == "ENT" else "TIENDA",
        }
        (legacy if clave in ("ENT", "COM") else nuevos).append(entrada)
    nuevos.sort(key=lambda e: _norm(e["nombre"]))
    return legacy + nuevos


def tipos_sin_producto() -> list[dict]:
    """Tipos activos aún sin producto (para el diálogo '+ Nuevo producto')."""
    from repositories import producto_repository
    try:
        from services import tipo_uniforme_service
        tipos = tipo_uniforme_service.listar_tipos(activo=1) or []
    except Exception:
        return []
    out = []
    for t in tipos:
        try:
            prod = producto_repository.obtener_por_tipo_uniforme(t.get("id_tipo_uniforme"))
        except Exception:
            prod = None
        if not prod:
            out.append(t)
    return out


def resolver_tipo(ref: str) -> dict | None:
    """Resuelve clave/código/nombre de tipo a entrada de `tipos_vendibles()`."""
    clave = _norm(ref).replace(" ", "")
    for e in tipos_vendibles():
        if _norm(e["clave"]).replace(" ", "") == clave:
            return e
        if (e.get("codigo") or "").upper() == str(ref or "").strip().upper():
            return e
        if _norm(e["nombre"]).replace(" ", "") == clave:
            return e
    return None


def es_producto_uniforme(prod) -> bool:
    """True si el producto (dict o id) pertenece a Uniformes (independencia)."""
    try:
        if isinstance(prod, dict):
            return prod.get("id_tipo_uniforme") is not None
        from repositories import producto_repository
        p = producto_repository.obtener_por_id(int(prod))
        return bool(p and p.get("id_tipo_uniforme") is not None)
    except Exception:
        return False


def producto_uniforme(tipo: str) -> dict | None:
    """Producto del tipo indicado (clave legacy o nombre), o None."""
    from repositories import producto_repository
    e = resolver_tipo(tipo)
    if e:
        try:
            return producto_repository.obtener_por_id(e["id_producto"])
        except Exception:
            return None
    # Fallback legacy directo por código (BD sin vínculo).
    codigo = CODIGO_POR_TIPO.get(str(tipo or "").upper())
    if not codigo:
        return None
    try:
        return producto_repository.obtener_por_codigo(codigo)
    except Exception:
        return None


def asegurar_producto(tipo: str) -> tuple[bool, str, int | None]:
    """Asegurador único de producto uniforme (venta manual, importación,
    historial, tallas). Crea el producto si falta (precio ref, stock 0,
    vinculado al tipo)."""
    from repositories import producto_repository
    from services import inventario_service
    e = resolver_tipo(tipo)
    if e:
        try:
            prod = producto_repository.obtener_por_id(e["id_producto"])
        except Exception:
            prod = None
        if prod and prod.get("activo", 1) != 0:
            return True, "OK", prod["id_producto"]
    else:
        # Alias legacy (COM/ENT y variantes) con tipo aún sin producto.
        alias = _LEGACY_ALIAS.get(_norm(tipo).replace(" ", ""))
        if alias:
            return _asegurar_legacy(alias)
        # ¿Es un tipo_uniforme existente aún sin producto? Se crea al vuelo.
        creado = _asegurar_producto_de_tipo(tipo)
        if creado[0]:
            return creado
        validos = ", ".join(x["clave"] for x in tipos_vendibles()) or "—"
        return False, f"Tipo de uniforme no válido ({tipo}). Válidos: {validos}", None
    try:
        cats = inventario_service.listar_categorias()
    except Exception:
        cats = []
    if not cats:
        return False, "Sin categorías de producto para crear el uniforme", None
    # e resolvió pero sin producto activo: reactivar si existe inactivo.
    try:
        viejo = producto_repository.obtener_por_codigo(e.get("codigo") or "")
    except Exception:
        viejo = None
    if viejo and viejo.get("activo", 1) == 0:
        try:
            producto_repository.reactivar(viejo["id_producto"])
            return True, "OK", viejo["id_producto"]
        except Exception as exc:
            logger.error(f"reactivar uniforme fallo: {exc}")
            return False, "No se pudo reactivar el producto", None
    clave = e["clave"]
    if clave in CODIGO_POR_TIPO:
        codigo = CODIGO_POR_TIPO[clave]
        nombre = NOMBRE_POR_TIPO[clave]
    else:
        codigo = codigo_para_nombre(e["nombre"])
        nombre = e["nombre"]
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre, "codigo": codigo,
        "canal": "TIENDITA", "tipo_empaque": "Unidad",
        "precio_venta": PRECIO_UNIFORME_REF,
        "id_tipo_uniforme": e["id_tipo_uniforme"], "stock_inicial": 0,
    })
    if not ok or not id_prod:
        return False, f"No se pudo crear producto {codigo}: {msg}", None
    return True, "OK", id_prod


def _asegurar_legacy(alias: tuple[str, str, str]) -> tuple[bool, str, int | None]:
    """Crea el producto legacy (código fijo + vínculo best-effort al tipo)."""
    from repositories import producto_repository
    from services import inventario_service
    clave, codigo, nombre = alias
    try:
        prod = producto_repository.obtener_por_codigo(codigo)
    except Exception:
        prod = None
    if prod and prod.get("activo", 1) != 0:
        return True, "OK", prod["id_producto"]
    try:
        cats = inventario_service.listar_categorias()
    except Exception:
        cats = []
    if not cats:
        return False, "Sin categorías de producto para crear el uniforme", None
    id_tipo = None
    try:
        from services import tipo_uniforme_service
        objetivo = "ENTRENAMIENTO" if clave == "ENT" else "COMPETENCIA"
        for t in tipo_uniforme_service.listar_tipos() or []:
            if _norm(t.get("nombre", "")) == f"UNIFORME {objetivo}":
                id_tipo = t["id_tipo_uniforme"]
                break
        if id_tipo is None:
            for t in tipo_uniforme_service.listar_tipos() or []:
                if objetivo in _norm(t.get("nombre", "")):
                    id_tipo = t["id_tipo_uniforme"]
                    break
    except Exception:
        pass
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": NOMBRE_POR_TIPO[clave], "codigo": codigo,
        "canal": "TIENDITA", "tipo_empaque": "Unidad",
        "precio_venta": PRECIO_UNIFORME_REF,
        "id_tipo_uniforme": id_tipo, "stock_inicial": 0,
    })
    if not ok or not id_prod:
        return False, f"No se pudo crear producto {codigo}: {msg}", None
    return True, "OK", id_prod


def _asegurar_producto_de_tipo(ref: str) -> tuple[bool, str, int | None]:
    """Si `ref` es un tipo_uniforme existente sin producto, lo crea."""
    from services import tipo_uniforme_service
    try:
        tipos = tipo_uniforme_service.listar_tipos(activo=1) or []
    except Exception:
        return False, "sin tipos", None
    objetivo = _norm(ref).replace(" ", "")
    for t in tipos:
        if _norm(t.get("nombre", "")).replace(" ", "") == objetivo:
            e = {
                "clave": str(t.get("nombre", "")).strip(),
                "nombre": t.get("nombre", ""),
                "codigo": None,
                "id_tipo_uniforme": t.get("id_tipo_uniforme"),
                "id_producto": None,
                "tipo_venta": "TIENDA",
            }
            from services import inventario_service
            try:
                cats = inventario_service.listar_categorias()
            except Exception:
                cats = []
            if not cats:
                return False, "Sin categorías de producto para crear el uniforme", None
            codigo = codigo_para_nombre(e["nombre"])
            ok, msg, id_prod = inventario_service.crear_producto({
                "id_categoria_producto": cats[0]["id_categoria_producto"],
                "nombre": e["nombre"], "codigo": codigo,
                "canal": "TIENDITA", "tipo_empaque": "Unidad",
                "precio_venta": PRECIO_UNIFORME_REF,
                "id_tipo_uniforme": e["id_tipo_uniforme"], "stock_inicial": 0,
            })
            if not ok or not id_prod:
                return False, f"No se pudo crear producto {codigo}: {msg}", None
            return True, "OK", id_prod
    return False, "no es tipo", None


def crear_producto_uniforme(nombre_tipo: str, precio_venta: float = PRECIO_UNIFORME_REF,
                            stock_inicial: int = 0,
                            id_usuario: int = 1) -> tuple[bool, str, int | None]:
    """CRUD Uniformes: crea tipo (si no existe) + producto vinculado.

    Usado por el diálogo '+ Nuevo producto' de Uniformes. Todo queda
    en Uniformes: no requiere pasar por Configuración ni Almacén.
    """
    from services import tipo_uniforme_service, inventario_service
    nombre_tipo = str(nombre_tipo or "").strip()
    if not nombre_tipo:
        return False, "Nombre del uniforme requerido", None
    if _norm(nombre_tipo).replace(" ", "") in ("COM", "ENT"):
        return False, "Nombre reservado: use los tipos legacy COM/ENT", None
    try:
        precio_venta = float(precio_venta)
        assert precio_venta > 0
    except (ValueError, TypeError, AssertionError):
        return False, "Precio de venta no válido", None
    try:
        stock_inicial = max(int(stock_inicial or 0), 0)
    except (ValueError, TypeError):
        return False, "Stock no válido", None
    try:
        tipos = tipo_uniforme_service.listar_tipos() or []
    except Exception:
        tipos = []
    id_tipo = None
    for t in tipos:
        if _norm(t.get("nombre", "")) == _norm(nombre_tipo):
            if (t.get("activo", 1) == 0):
                return False, f"El tipo '{t['nombre']}' está desactivado", None
            id_tipo = t["id_tipo_uniforme"]
            nombre_tipo = t["nombre"]
            break
    if id_tipo is None:
        ok, msg, id_tipo = tipo_uniforme_service.crear_tipo_uniforme({"nombre": nombre_tipo})
        if not ok:
            return False, msg, None
    from repositories import producto_repository
    try:
        existente = producto_repository.obtener_por_tipo_uniforme(id_tipo)
    except Exception:
        existente = None
    if existente and existente.get("activo", 1) != 0:
        return False, f"El tipo '{nombre_tipo}' ya tiene producto ({existente.get('codigo')})", None
    try:
        inactivo = producto_repository.obtener_por_tipo_uniforme(
            id_tipo, solo_activos=False)
    except Exception:
        inactivo = None
    if inactivo and inactivo.get("activo", 1) == 0:
        # Reactivar en vez de duplicar (mismo tipo, nuevo precio).
        try:
            producto_repository.reactivar(inactivo["id_producto"])
            from services import inventario_service as _inv
            _inv.editar_producto(inactivo["id_producto"], {"precio_venta": precio_venta})
            return True, f"Uniforme '{nombre_tipo}' reactivado ({inactivo.get('codigo')})", inactivo["id_producto"]
        except Exception as exc:
            logger.error(f"reactivar producto uniforme fallo: {exc}")
            return False, "No se pudo reactivar el producto", None
    try:
        cats = inventario_service.listar_categorias()
    except Exception:
        cats = []
    if not cats:
        return False, "Sin categorías de producto para crear el uniforme", None
    codigo = codigo_para_nombre(nombre_tipo)
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre_tipo, "codigo": codigo,
        "canal": "TIENDITA", "tipo_empaque": "Unidad",
        "precio_venta": precio_venta, "precio_compra": precio_venta,
        "id_tipo_uniforme": id_tipo, "stock_inicial": stock_inicial,
        "motivo_compra": "Stock inicial uniforme", "id_usuario": id_usuario,
    })
    if not ok or not id_prod:
        return False, f"No se pudo crear producto {codigo}: {msg}", None
    try:
        from services import auditoria_service
        auditoria_service.registrar_insert(
            auditoria_service.id_usuario_sesion(),
            "producto", id_prod,
            f"uniforme nuevo tipo={nombre_tipo}, codigo={codigo}, precio={precio_venta}")
    except Exception:
        pass
    return True, f"Uniforme '{nombre_tipo}' creado ({codigo})", id_prod


def desactivar_producto_uniforme(id_producto: int) -> tuple[bool, str]:
    """Soft delete de producto de uniforme (el tipo se conserva e historia)."""
    from repositories import producto_repository
    try:
        prod = producto_repository.obtener_por_id(int(id_producto))
    except (TypeError, ValueError):
        return False, "Producto no válido"
    if not prod:
        return False, "Producto no encontrado"
    if not es_producto_uniforme(prod):
        return False, "No es un producto de uniforme"
    try:
        producto_repository.soft_delete(int(id_producto))
        from services import auditoria_service
        auditoria_service.registrar_desactivacion(
            auditoria_service.id_usuario_sesion(),
            "producto", int(id_producto), "activo=1", "activo=0")
    except Exception as e:
        logger.error(f"desactivar_producto_uniforme fallo: {e}")
        return False, "No se pudo desactivar el producto"
    return True, f"Producto '{prod.get('nombre')}' desactivado"


def productos_uniforme() -> list[dict]:
    """Productos de uniforme con tallas y stock (tab Productos, N tipos)."""
    from repositories import producto_variante_repository, stock_almacen_repository
    from repositories import almacen_repository, producto_repository
    out = []
    for e in tipos_vendibles():
        try:
            prod = producto_repository.obtener_por_id(e["id_producto"])
        except Exception:
            prod = None
        if not prod:
            continue
        try:
            variantes = producto_variante_repository.obtener_por_producto(
                prod["id_producto"]) or []
        except Exception:
            variantes = []
        try:
            alm = almacen_repository.obtener_por_nombre("Principal")
            alm_id = alm["id_almacen"] if alm else 1
        except Exception:
            alm_id = 1
        tallas = []
        for v in variantes:
            try:
                sa = stock_almacen_repository.obtener(
                    prod["id_producto"], v["id_variante"], alm_id, None)
                stock = int((sa or {}).get("stock", 0) or 0)
            except Exception:
                stock = 0
            tallas.append({"id_variante": v["id_variante"],
                           "talla": v.get("talla_codigo") or v.get("sku") or "?",
                           "stock": stock})
        out.append({"tipo": e["clave"], "nombre": e["nombre"],
                    "producto": prod, "tallas": tallas})
    return out


def agregar_talla(tipo: str, talla_codigo: str, stock: int = 0,
                  id_usuario: int = 1) -> tuple[bool, str]:
    """Crea la variante de talla del uniforme con stock inicial."""
    from repositories import producto_variante_repository, stock_almacen_repository
    from repositories import almacen_repository, talla_repository
    from models.producto_variante import ProductoVariante
    e = resolver_tipo(tipo)
    if not e:
        return False, f"Tipo de uniforme no válido ({tipo})"
    ok, msg, id_prod = asegurar_producto(e["clave"])
    if not ok:
        return False, msg
    talla_codigo = str(talla_codigo or "").strip().upper()
    if not talla_codigo:
        return False, "Talla requerida"
    try:
        t = talla_repository.obtener_por_codigo(talla_codigo)
    except Exception:
        t = None
    if not t:
        return False, f"Talla '{talla_codigo}' no existe en el catálogo"
    try:
        stock = max(int(stock or 0), 0)
    except (TypeError, ValueError):
        return False, "Stock no válido"
    sku = f"{e['codigo']}-{talla_codigo}"
    try:
        if producto_variante_repository.existe_sku(sku):
            return False, f"La talla {talla_codigo} ya existe para este uniforme"
        var = ProductoVariante(id_producto=id_prod, id_talla=t["id_talla"],
                               sku=sku, stock_minimo=0, activo=1)
        id_var = producto_variante_repository.insertar(var)
        if stock > 0:
            alm = almacen_repository.obtener_por_nombre("Principal")
            stock_almacen_repository.upsert_stock(
                id_prod, id_var, alm["id_almacen"] if alm else 1, None, stock)
        from services import auditoria_service
        auditoria_service.registrar_insert(
            auditoria_service.id_usuario_sesion(),
            "producto_variante", id_var,
            f"producto={id_prod}, talla={talla_codigo}, stock={stock}")
    except Exception as exc:
        logger.error(f"agregar_talla fallo: {exc}")
        return False, "No se pudo crear la talla"
    return True, f"Talla {talla_codigo} creada con stock {stock}"


def tallas_disponibles(tipo: str) -> list[dict]:
    """Variantes con stock > 0 del uniforme indicado.

    Retorna [{id_variante, talla, stock}]. Si el producto no tiene
    variantes, retorna [] (venta sin talla).
    """
    from repositories import producto_variante_repository, stock_almacen_repository
    from repositories import almacen_repository
    prod = producto_uniforme(tipo)
    if not prod:
        return []
    try:
        variantes = producto_variante_repository.obtener_por_producto(
            prod["id_producto"]) or []
    except Exception:
        return []
    if not variantes:
        return []
    try:
        alm = almacen_repository.obtener_por_nombre("Principal")
        alm_id = alm["id_almacen"] if alm else 1
    except Exception:
        alm_id = 1
    out = []
    for v in variantes:
        try:
            sa = stock_almacen_repository.obtener(
                prod["id_producto"], v["id_variante"], alm_id, None)
            stock = int((sa or {}).get("stock", 0) or 0)
        except Exception:
            stock = 0
        if stock > 0:
            out.append({
                "id_variante": v["id_variante"],
                "talla": v.get("talla_codigo") or v.get("sku") or "?",
                "stock": stock,
            })
    return out
