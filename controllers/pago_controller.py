from services import pago_service, cuota_service, matricula_service
from utils.validators import validate_metodo_pago


def registrar_pago(data: dict) -> tuple[bool, str, int | None]:
    if not data.get("id_cuota"):
        return False, "La cuota es obligatoria", None

    try:
        monto = float(data.get("monto_pagado", 0))
        if monto <= 0:
            return False, "El monto debe ser mayor a 0", None
        data["monto_pagado"] = monto
    except (ValueError, TypeError):
        return False, "Monto no válido", None

    metodo = data.get("metodo_pago", "")
    if not validate_metodo_pago(metodo):
        return False, "Método de pago no válido. Use EFECTIVO, YAPE, PLIN o TRANSFERENCIA", None

    return pago_service.registrar_pago(data)


def obtener_pago(id_pago: int) -> dict | None:
    return pago_service.obtener_pago(id_pago)


def obtener_detalles_por_pago(id_pago: int) -> list[dict]:
    return pago_service.obtener_detalles_por_pago(id_pago)


def listar_pagos(limit: int = 100, offset: int = 0) -> list[dict]:
    return pago_service.listar_pagos(limit=limit, offset=offset)


def listar_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return pago_service.listar_por_fecha(fecha_inicio, fecha_fin)


def listar_por_estudiante(id_estudiante: int) -> list[dict]:
    return pago_service.listar_por_estudiante(id_estudiante)


def obtener_ingresos_por_fecha(fecha_inicio: str, fecha_fin: str) -> float:
    return pago_service.obtener_ingresos_por_fecha(fecha_inicio, fecha_fin)


def contar_pagos_por_fecha(fecha_inicio: str, fecha_fin: str) -> int:
    return pago_service.contar_pagos_por_fecha(fecha_inicio, fecha_fin)


def listar_matriculas_activas() -> list[dict]:
    return matricula_service.listar_matriculas_activas()


def obtener_cuotas_vencidas() -> list[dict]:
    return cuota_service.obtener_vencidas()


def obtener_cuotas_pendientes(id_matricula: int) -> list[dict]:
    return cuota_service.obtener_cuotas_pendientes(id_matricula)


def listar_cuotas_por_cobrar(limit: int = 200) -> list[dict]:
    """Cuotas con saldo para la pestaña Mensualidades de Cobros."""
    return cuota_service.obtener_por_cobrar(limit)


def obtener_cuotas_por_vencer(dias: int = 3) -> list[dict]:
    return cuota_service.obtener_por_vencer(dias)


def buscar_por_texto(texto: str) -> list[dict]:
    from repositories import pago_repository
    return pago_repository.buscar_por_texto(texto)
