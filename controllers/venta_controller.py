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


def listar_ventas(fecha_inicio: str | None = None, fecha_fin: str | None = None, tipo_venta: str | None = None,
                  anio: int | None = None, meses: list[int] | None = None,
                  orden: str | None = None) -> list[dict]:
    return venta_service.listar_ventas(fecha_inicio, fecha_fin, tipo_venta, anio, meses, orden)


def editar_venta(id_venta: int, data: dict) -> tuple[bool, str]:
    """Edición acotada de venta (fecha/método/comprobante)."""
    return venta_service.editar_venta(id_venta, data)


CODIGOS_UNIFORME = {
    "ENT": ("CAMISETA-ENT", "Camiseta Entrenamiento", "UNIFORME"),
    "COM": ("UNIFORME-COM", "Uniforme Competencia", "TIENDA"),
}
PRECIO_UNIFORME_REF = 70.0


def _asegurar_producto_uniforme(tipo: str) -> tuple[bool, str, int | None]:
    """Delega en el asegurador único (uniforme_service)."""
    from services import uniforme_service
    return uniforme_service.asegurar_producto(tipo)


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
    id_variante = None
    if data.get("id_variante"):
        try:
            id_variante = int(data["id_variante"])
        except (TypeError, ValueError):
            return False, "Talla no válida", None
        # La precompra también alimenta el stock de la talla (la venta lo
        # descuenta dentro de la transacción; neto 0 como el stock global).
        try:
            from repositories import almacen_repository, stock_almacen_repository
            alm = almacen_repository.obtener_por_nombre("Principal")
            stock_almacen_repository.upsert_stock(
                id_prod, id_variante, alm["id_almacen"] if alm else 1, None, 1)
        except Exception:
            pass
    _codigo, _nombre, tipo_venta = CODIGOS_UNIFORME[tipo]
    item = {"id_producto": id_prod, "cantidad": 1, "precio_unitario": precio}
    if id_variante:
        item["id_variante"] = id_variante
    return registrar_venta({
        "id_estudiante": data["id_estudiante"], "id_usuario": id_usuario,
        "tipo_venta": tipo_venta, "metodo_pago": metodo,
        "items": [item],
        "monto_total": precio, "fecha_venta": fecha,
    })


def obtener_venta(id_venta: int) -> dict | None:
    return venta_service.obtener_venta(id_venta)


def listar_uniformes(limit: int = 200, anio: int | None = None,
                     meses: list[int] | None = None,
                     orden: str | None = None) -> list[dict]:
    return venta_service.listar_uniformes(limit, anio, meses, orden)


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
