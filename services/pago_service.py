import sqlite3

from repositories import pago_repository, detalle_pago_repository
from models.pago import Pago
from services import auditoria_service, cuota_service
from database.connection import transaccion
from utils.constants import (
    METODO_EFECTIVO,
    METODO_YAPE,
    METODO_PLIN,
    METODO_TRANSFERENCIA,
    CUOTA_PAGADO,
)
from utils.helpers import generate_receipt_number
from utils.dates import get_today
from utils.logger import logger

METODOS_VALIDOS = (METODO_EFECTIVO, METODO_YAPE, METODO_PLIN, METODO_TRANSFERENCIA)


def registrar_pago(data: dict) -> tuple[bool, str, int | None]:
    id_usuario = data.get("id_usuario")
    id_cuota = data.get("id_cuota")
    monto_pagado = data.get("monto_pagado", 0)
    metodo_pago = data.get("metodo_pago", "")

    if not id_usuario:
        return False, "Usuario no identificado", None
    if not id_cuota:
        return False, "La cuota es obligatoria", None
    if monto_pagado <= 0:
        return False, "El monto debe ser mayor a 0", None
    if metodo_pago not in METODOS_VALIDOS:
        return False, "Método de pago no válido", None
    # RN-042: comprobante obligatorio si no es EFECTIVO
    if metodo_pago != METODO_EFECTIVO:
        comp = (data.get("comprobante_path") or "").strip() if data.get("comprobante_path") else ""
        if not comp:
            return False, "Suba comprobante para YAPE/PLIN/TRANSFERENCIA (RN-042)", None

    from repositories import cuota_repository
    cuota = cuota_repository.obtener_por_id(id_cuota)
    if not cuota:
        return False, "Cuota no encontrada", None
    if cuota["estado"] == CUOTA_PAGADO:
        return False, "Esta cuota ya está pagada completamente", None
    if monto_pagado > cuota["saldo"]:
        return False, f"El monto excede el saldo pendiente de S/{cuota['saldo']:.2f}", None

    numero_recibo = generate_receipt_number()

    # Fase 3: centralizar comprobante (R-{recibo}.ext); si falla, se guarda
    # la ruta original igual (mejor que descartarla como antes de Fase 0).
    comprobante = (data.get("comprobante_path") or "").strip()
    if comprobante:
        try:
            import os
            import shutil
            from utils.constants import COMPROBANTES_DIR
            from utils.imagenes import extension_real
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            dest = os.path.join(
                COMPROBANTES_DIR, f"{numero_recibo}{extension_real(comprobante)}")
            shutil.copy2(comprobante, dest)
            comprobante = dest
        except Exception as e:
            logger.warning(f"No se pudo centralizar comprobante {comprobante}: {e}")

    pago = Pago(
        id_usuario=id_usuario,
        numero_recibo=numero_recibo,
        fecha_pago=(str(data.get("fecha_pago") or "").strip() or get_today()),
        monto_total=monto_pagado,
        metodo_pago=metodo_pago,
        observacion=data.get("observacion", ""),
        comprobante_path=comprobante,
    )

    with transaccion():
        id_pago = None
        for _ in range(3):
            try:
                id_pago = pago_repository.insertar(pago)
                break
            except sqlite3.IntegrityError:
                # Colision improbable de numero_recibo: regenerar y reintentar
                pago.numero_recibo = generate_receipt_number()
        if id_pago is None:
            return False, "No se pudo generar un numero de recibo unico", None

        detalle_pago_repository.insertar(id_pago, id_cuota, monto_pagado)

        cuota_service.actualizar_pago(id_cuota, monto_pagado)

        auditoria_service.registrar_insert(
            id_usuario=id_usuario,
            tabla="pago",
            id_registro=id_pago,
            valores_nuevos=f"recibo={pago.numero_recibo}, monto=S/{monto_pagado:.2f}, metodo={metodo_pago}",
        )

    logger.info(f"Pago registrado: recibo={numero_recibo}, monto=S/{monto_pagado:.2f}")
    return True, f"Pago registrado. Recibo: {numero_recibo}", id_pago


def obtener_pago(id_pago: int) -> dict | None:
    return pago_repository.obtener_por_id(id_pago)


def obtener_detalles_por_pago(id_pago: int) -> list[dict]:
    return detalle_pago_repository.obtener_por_pago(id_pago)


def listar_pagos(limit: int = 100, offset: int = 0) -> list[dict]:
    return pago_repository.obtener_todos(limit=limit, offset=offset)


def listar_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return pago_repository.obtener_por_fecha(fecha_inicio, fecha_fin)


def listar_por_estudiante(id_estudiante: int) -> list[dict]:
    return pago_repository.obtener_por_estudiante(id_estudiante)


def obtener_ingresos_por_fecha(fecha_inicio: str, fecha_fin: str) -> float:
    return pago_repository.sumar_por_fecha(fecha_inicio, fecha_fin)


def contar_pagos_por_fecha(fecha_inicio: str, fecha_fin: str) -> int:
    return pago_repository.contar_por_fecha(fecha_inicio, fecha_fin)
