from repositories import egreso_repository
from models.egreso import Egreso
from services import auditoria_service
from utils.logger import logger
from utils.validators import validate_not_empty

CONCEPTOS_VALIDOS = ("PROFESOR", "PERSONAL", "CAMPEONATO_FIJO", "ARBITRAJE", "VIATICOS")


def registrar_egreso(data: dict) -> tuple[bool, str, int | None]:
    concepto = data.get("concepto", "").strip().upper()
    monto = data.get("monto")
    fecha = data.get("fecha")
    if concepto not in CONCEPTOS_VALIDOS:
        return False, f"Concepto no válido. Permitidos: {', '.join(CONCEPTOS_VALIDOS)}", None
    try:
        monto_f = float(monto)
        if monto_f <= 0:
            return False, "Monto debe ser mayor a 0", None
    except (ValueError, TypeError) as e:
        logger.warning(f"Egreso monto inválido: {monto} ({e})")
        return False, "Monto inválido", None
    err = validate_not_empty(fecha, "Fecha")
    if err:
        return False, err, None
    id_usuario = data.get("id_usuario") or auditoria_service.id_usuario_sesion()
    comprobante = data.get("comprobante_path")
    # validar comprobante si se proporciona
    if comprobante and not isinstance(comprobante, str):
        comprobante = str(comprobante)
    egreso = Egreso(
        concepto=concepto,
        monto=round(monto_f, 2),
        fecha=fecha,
        responsable=data.get("responsable", ""),
        id_usuario=id_usuario,
        observacion=data.get("observacion", ""),
        comprobante_path=comprobante,
        id_tarifa=data.get("id_tarifa"),
    )
    id_egreso = egreso_repository.insertar(egreso)
    auditoria_service.registrar_insert(id_usuario, "egreso", id_egreso, f"concepto={concepto}, monto={monto_f}, comprobante={bool(comprobante)}")
    logger.info(f"Egreso registrado: {concepto} {monto_f} comprobante={bool(comprobante)}")
    return True, "Egreso registrado correctamente", id_egreso


def listar_egresos(fecha_inicio: str | None = None, fecha_fin: str | None = None) -> list[dict]:
    return egreso_repository.obtener_todos(fecha_inicio, fecha_fin)


def eliminar_egreso(id_egreso: int) -> tuple[bool, str]:
    e = egreso_repository.obtener_por_id(id_egreso)
    if not e:
        return False, "Egreso no encontrado"
    egreso_repository.soft_delete(id_egreso)
    auditoria_service.registrar_desactivacion(auditoria_service.id_usuario_sesion_or_system(), "egreso", id_egreso, "activo=1", "activo=0")
    return True, "Egreso eliminado"


def editar_egreso(id_egreso: int, data: dict) -> tuple[bool, str]:
    e = egreso_repository.obtener_por_id(id_egreso)
    if not e:
        return False, "Egreso no encontrado"
    concepto = (data.get("concepto") or e["concepto"]).strip().upper()
    if concepto not in CONCEPTOS_VALIDOS:
        return False, f"Concepto no válido. Permitidos: {', '.join(CONCEPTOS_VALIDOS)}"
    try:
        monto_f = float(data.get("monto", e["monto"]))
        if monto_f <= 0:
            return False, "Monto debe ser mayor a 0"
    except Exception:
        return False, "Monto inválido"
    from database.connection import get_connection
    from utils.dates import get_now
    conn = get_connection()
    conn.execute(
        "UPDATE egreso SET concepto=?, monto=?, fecha=?, responsable=?, observacion=?, comprobante_path=?, id_usuario=? WHERE id_egreso=?",
        (concepto, round(monto_f,2), data.get("fecha", e["fecha"]), data.get("responsable", e.get("responsable","")), data.get("observacion", e.get("observacion","")), data.get("comprobante_path", e.get("comprobante_path","")), data.get("id_usuario") or auditoria_service.id_usuario_sesion_or_system(), id_egreso),
    )
    if "id_tarifa" in data:
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(egreso)").fetchall()]
            if "id_tarifa" in cols:
                conn.execute("UPDATE egreso SET id_tarifa=? WHERE id_egreso=?", (data.get("id_tarifa"), id_egreso))
        except Exception as e:
            from utils.logger import logger
            logger.warning(f"Egreso {id_egreso}: no se pudo vincular tarifa: {e}")
    conn.commit()
    auditoria_service.registrar_update(auditoria_service.id_usuario_sesion_or_system(), "egreso", id_egreso, f"concepto={e['concepto']}", f"concepto={concepto}, monto={monto_f}")
    return True, "Egreso actualizado"


def reporte_ingresos_vs_egresos(fecha_inicio: str, fecha_fin: str) -> dict:
    from repositories import venta_repository, pago_repository
    ingresos_ventas = venta_repository.sumar_por_periodo(fecha_inicio, fecha_fin)
    ingresos_pagos = pago_repository.sumar_por_fecha(fecha_inicio, fecha_fin) if hasattr(pago_repository, "sumar_por_fecha") else 0
    egresos = egreso_repository.sumar_por_periodo(fecha_inicio, fecha_fin)
    total_ingresos = round(ingresos_ventas + ingresos_pagos, 2)
    neto = round(total_ingresos - egresos, 2)
    return {"ingresos_ventas": ingresos_ventas, "ingresos_pagos": ingresos_pagos, "total_ingresos": total_ingresos, "egresos": egresos, "neto": neto}
