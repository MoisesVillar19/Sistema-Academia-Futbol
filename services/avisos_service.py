"""Fase 1: notificaciones por módulo (sin toast invasivo).

Cada aviso: {codigo, modulo, texto, cantidad, severidad}.
Severidades: 'alta' (rojo), 'media' (naranja), 'info' (morado).
"""

from repositories import pago_repository
from services import cuota_service, inventario_service
from utils.logger import logger


def _sin_apoderado_principal() -> list[dict]:
    from services import matricula_service, estudiante_service
    pendientes = []
    try:
        mats = matricula_service.listar_matriculas_activas()
    except Exception as e:
        logger.warning(f"Avisos sin-apoderado no disponible: {e}")
        return []
    for m in mats:
        try:
            apods = estudiante_service.obtener_apoderados_por_estudiante(
                m.get("id_estudiante"))
        except Exception:
            continue
        if not any(a.get("es_principal") for a in apods):
            pendientes.append(m)
    return pendientes


def obtener_avisos() -> list[dict]:
    avisos = []
    try:
        n_comp = len(pago_repository.obtener_sin_comprobante(limit=1000))
    except Exception as e:
        logger.warning(f"Aviso comprobantes no disponible: {e}")
        n_comp = 0
    if n_comp:
        avisos.append({
            "codigo": "comprobantes",
            "modulo": "pagos",
            "texto": f"{n_comp} pago(s) con comprobante pendiente",
            "cantidad": n_comp,
            "severidad": "alta",
        })
    try:
        vencidas = cuota_service.obtener_vencidas()
    except Exception:
        vencidas = []
    if vencidas:
        avisos.append({
            "codigo": "vencidas",
            "modulo": "pagos",
            "texto": f"{len(vencidas)} cuota(s) vencida(s)",
            "cantidad": len(vencidas),
            "severidad": "alta",
        })
    try:
        por_vencer = cuota_service.obtener_por_vencer()
    except Exception:
        por_vencer = []
    if por_vencer:
        avisos.append({
            "codigo": "por_vencer",
            "modulo": "pagos",
            "texto": f"{len(por_vencer)} cuota(s) por vencer",
            "cantidad": len(por_vencer),
            "severidad": "media",
        })
    try:
        bajo = inventario_service.obtener_bajo_stock()
    except Exception:
        bajo = []
    if bajo:
        avisos.append({
            "codigo": "stock_bajo",
            "modulo": "inventario",
            "texto": f"{len(bajo)} producto(s) con stock bajo",
            "cantidad": len(bajo),
            "severidad": "media",
        })
    sin_apod = _sin_apoderado_principal()
    if sin_apod:
        avisos.append({
            "codigo": "sin_apoderado",
            "modulo": "matriculas",
            "texto": f"{len(sin_apod)} matrícula(s) sin apoderado principal",
            "cantidad": len(sin_apod),
            "severidad": "media",
        })
    return avisos


def avisos_por_modulo(modulo: str) -> list[dict]:
    return [a for a in obtener_avisos() if a["modulo"] == modulo]


def listar_pagos_sin_comprobante(limit: int = 200) -> list[dict]:
    return pago_repository.obtener_sin_comprobante(limit=limit)


def listar_matriculas_sin_apoderado() -> list[dict]:
    return _sin_apoderado_principal()
