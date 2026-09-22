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
