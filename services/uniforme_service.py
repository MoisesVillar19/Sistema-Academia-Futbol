"""Lógica de uniformes: tipos ENT/COM y tallas disponibles por stock."""
from utils.logger import logger

CODIGO_POR_TIPO = {"ENT": "CAMISETA-ENT", "COM": "UNIFORME-COM"}
NOMBRE_POR_TIPO = {"ENT": "Camiseta Entrenamiento", "COM": "Uniforme Competencia"}
PRECIO_UNIFORME_REF = 70.0


def producto_uniforme(tipo: str) -> dict | None:
    """Producto del uniforme ENT/COM, o None si no existe."""
    from repositories import producto_repository
    codigo = CODIGO_POR_TIPO.get(str(tipo or "").upper())
    if not codigo:
        return None
    try:
        return producto_repository.obtener_por_codigo(codigo)
    except Exception:
        return None


def asegurar_producto(tipo: str) -> tuple[bool, str, int | None]:
    """Único asegurador de producto uniforme (antes triplicado).

    Busca por código; si falta lo crea (primera categoría, precio ref 70,
    stock 0, id_tipo_uniforme best-effort). Misma conducta para venta
    manual, importación uniforme e historial.
    """
    from repositories import producto_repository
    from services import inventario_service
    tipo = str(tipo or "").upper()
    codigo = CODIGO_POR_TIPO.get(tipo)
    if not codigo:
        return False, "Tipo debe ser COM o ENT", None
    try:
        prod = producto_repository.obtener_por_codigo(codigo)
    except Exception:
        prod = None
    if prod:
        return True, "OK", prod["id_producto"]
    try:
        cats = inventario_service.listar_categorias()
    except Exception:
        cats = []
    if not cats:
        return False, "Sin categorías de producto para crear el uniforme", None
    id_tipo = None
    try:
        from controllers import tipo_uniforme_controller
        for t in tipo_uniforme_controller.listar_tipos():
            nombre = str(t.get("nombre", "")).upper()
            if ("ENTRENAMIENTO" in nombre and tipo == "ENT") or \
               ("COMPETENCIA" in nombre and tipo == "COM"):
                id_tipo = t["id_tipo_uniforme"]
                break
    except Exception:
        pass
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": NOMBRE_POR_TIPO[tipo], "codigo": codigo,
        "canal": "TIENDITA", "tipo_empaque": "Unidad",
        "precio_venta": PRECIO_UNIFORME_REF,
        "id_tipo_uniforme": id_tipo, "stock_inicial": 0,
    })
    if not ok or not id_prod:
        return False, f"No se pudo crear producto {codigo}: {msg}", None
    return True, "OK", id_prod


def productos_uniforme() -> list[dict]:
    """Los 2 productos uniforme con sus tallas y stock (para la tab Productos)."""
    from repositories import producto_variante_repository, stock_almacen_repository
    from repositories import almacen_repository
    out = []
    for tipo in ("ENT", "COM"):
        prod = producto_uniforme(tipo)
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
        out.append({"tipo": tipo, "producto": prod, "tallas": tallas})
    return out


def agregar_talla(tipo: str, talla_codigo: str, stock: int = 0,
                  id_usuario: int = 1) -> tuple[bool, str]:
    """Crea la variante de talla del uniforme con stock inicial."""
    from repositories import producto_variante_repository, stock_almacen_repository
    from repositories import almacen_repository, talla_repository
    from models.producto_variante import ProductoVariante
    ok, msg, id_prod = asegurar_producto(tipo)
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
    sku = f"{CODIGO_POR_TIPO[str(tipo).upper()]}-{talla_codigo}"
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
            auditoria_service.id_usuario_sesion_or_system(),
            "producto_variante", id_var,
            f"producto={id_prod}, talla={talla_codigo}, stock={stock}")
    except Exception as e:
        logger.error(f"agregar_talla fallo: {e}")
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
