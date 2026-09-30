from services import venta_service, auth_service


def registrar_venta(data: dict) -> tuple[bool, str, int | None]:
    if not auth_service.esta_logueado():
        return False, "Sesión requerida", None
    if not data.get("id_usuario"):
        data["id_usuario"] = auth_service.id_usuario_sesion_or_system()
    ok, msg, vid = venta_service.registrar_venta(data)
    if ok:
        try:
            from utils import event_bus
            event_bus.publish("producto_actualizado")
        except Exception:
            pass
    return ok, msg, vid


def listar_ventas(fecha_inicio: str | None = None, fecha_fin: str | None = None, tipo_venta: str | None = None) -> list[dict]:
    return venta_service.listar_ventas(fecha_inicio, fecha_fin, tipo_venta)


CODIGOS_UNIFORME = {
    "ENT": ("CAMISETA-ENT", "Camiseta Entrenamiento", "UNIFORME"),
    "COM": ("UNIFORME-COM", "Uniforme Competencia", "TIENDA"),
}
PRECIO_UNIFORME_REF = 70.0


def _asegurar_producto_uniforme(tipo: str) -> tuple[bool, str, int | None]:
    """Producto COM/ENT por código; lo crea si falta (primera categoría)."""
    from services import inventario_service
    from repositories import producto_repository
    codigo, nombre, _tv = CODIGOS_UNIFORME[tipo]
    prod = producto_repository.obtener_por_codigo(codigo)
    if prod:
        return True, "OK", prod["id_producto"]
    try:
        cats = inventario_service.listar_categorias()
    except Exception:
        cats = []
    if not cats:
        return False, "Sin categorías de producto para crear el uniforme", None
    ok, msg, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre, "codigo": codigo, "canal": "TIENDITA",
        "tipo_empaque": "Unidad", "precio_venta": PRECIO_UNIFORME_REF,
        "stock_inicial": 0,
    })
    if not ok:
        return False, msg, None
    return True, "OK", id_prod


def registrar_venta_uniforme(data: dict) -> tuple[bool, str, int | None]:
    """Venta de uniforme con stock asegurado (pre-compra si falta).

    data: id_estudiante, tipo (COM/ENT), fecha_venta, metodo_pago (def EFECTIVO).
    El monto sale del precio_venta del producto. Nunca bloquea por stock.
    """
    from services import inventario_service
    if not auth_service.esta_logueado():
        return False, "Sesión requerida", None
    id_usuario = data.get("id_usuario") or auth_service.id_usuario_sesion_or_system()
    tipo = str(data.get("tipo", "") or "").strip().upper()
    if tipo not in CODIGOS_UNIFORME:
        return False, "Tipo debe ser COM o ENT", None
    if not data.get("id_estudiante"):
        return False, "El estudiante es obligatorio", None
    metodo = str(data.get("metodo_pago", "") or "EFECTIVO").strip().upper()
    fecha = str(data.get("fecha_venta", "") or "").strip() or None
    ok, msg, id_prod = _asegurar_producto_uniforme(tipo)
    if not ok:
        return False, msg, None
    try:
        from repositories import producto_repository
        prod = producto_repository.obtener_por_id(id_prod)
        precio = float(prod.get("precio_venta") or prod.get("precio") or 0)
    except Exception:
        return False, "No se pudo leer el precio del uniforme", None
    if precio <= 0:
        return False, "El uniforme no tiene precio de venta configurado", None
    ok_c, msg_c, _ = inventario_service.registrar_compra({
        "id_producto": id_prod, "cantidad": 1, "monto_total": precio,
        "metodo_pago": "EFECTIVO", "motivo": "Stock p/venta de uniforme",
        "fecha_movimiento": fecha, "id_usuario": id_usuario,
    })
    if not ok_c:
        return False, msg_c, None
    _codigo, _nombre, tipo_venta = CODIGOS_UNIFORME[tipo]
    return registrar_venta({
        "id_estudiante": data["id_estudiante"], "id_usuario": id_usuario,
        "tipo_venta": tipo_venta, "metodo_pago": metodo,
        "items": [{"id_producto": id_prod, "cantidad": 1,
                   "precio_unitario": precio}],
        "monto_total": precio, "fecha_venta": fecha,
    })


def obtener_venta(id_venta: int) -> dict | None:
    return venta_service.obtener_venta(id_venta)


def resumen_campeonatos() -> list[dict]:
    """Por división (tarifa CAMPEONATO): inscritos, ventas, recaudado,
    arbitraje vinculado (egresos con id_tarifa) y neto."""
    from services import tarifa_service, egreso_service
    tarifas = tarifa_service.listar_tarifas_activas(tipo="CAMPEONATO")
    ventas = venta_service.listar_ventas(tipo_venta="CAMPEONATO")
    try:
        egresos = egreso_service.listar_egresos()
    except Exception as e:
        from utils.logger import logger
        logger.warning(f"resumen_campeonatos sin egresos (arbitraje=0): {e}")
        egresos = []
    out = []
    for t in tarifas:
        tid = t["id_tarifa"]
        vs = [v for v in ventas if v.get("id_tarifa") == tid]
        inscritos = {v.get("id_estudiante") for v in vs if v.get("id_estudiante")}
        recaudado = round(sum((v.get("monto_total", 0) or 0) for v in vs), 2)
        arb = [e for e in egresos
               if e.get("id_tarifa") == tid and (e.get("concepto") in ("ARBITRAJE", "CAMPEONATO_FIJO"))]
        arbitraje = round(sum((e.get("monto", 0) or 0) for e in arb), 2)
        out.append({"tarifa": t, "inscritos": len(inscritos),
                    "ventas": len(vs), "recaudado": recaudado,
                    "arbitraje": arbitraje, "neto": round(recaudado - arbitraje, 2)})
    return out
