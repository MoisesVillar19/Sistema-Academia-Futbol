"""Fase 1 + E3: notificaciones por módulo (sin toast invasivo).

Cada aviso: {codigo, modulo, texto, cantidad, severidad, ir}.
ir = {"modulo": <destino>, "params": {...}} para el evento "abrir_modulo".
Omitidos (tabla aviso_omitido) se excluyen; ver omitir_aviso().
Severidades: 'alta' (rojo), 'media' (naranja), 'info' (morado).
"""

from repositories import pago_repository, aviso_repository
from services import cuota_service, inventario_service
from utils.logger import logger


def _omitido(codigo: str, origen_tipo: str = "", origen_id: int = 0) -> bool:
    try:
        return aviso_repository.esta_omitido(codigo, origen_tipo, origen_id)
    except Exception:
        return False


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


_AVISOS_CACHE: list[dict] = []
_AVISOS_TS = 0.0
_AVISOS_TTL_SEG = 60


def obtener_avisos() -> list[dict]:
    """Cacheado 60s: los banners de cada módulo lo piden al abrir."""
    global _AVISOS_CACHE, _AVISOS_TS
    import time
    ahora = time.time()
    if _AVISOS_CACHE and ahora - _AVISOS_TS < _AVISOS_TTL_SEG:
        return [dict(a) for a in _AVISOS_CACHE]
    avisos = _calcular_avisos()
    _AVISOS_CACHE = [dict(a) for a in avisos]
    _AVISOS_TS = ahora
    return avisos


def invalidar_cache_avisos() -> None:
    global _AVISOS_CACHE, _AVISOS_TS
    _AVISOS_CACHE = []
    _AVISOS_TS = 0.0


def _calcular_avisos() -> list[dict]:
    avisos = []
    try:
        n_comp = len(pago_repository.obtener_sin_comprobante(limit=1000))
    except Exception as e:
        logger.warning(f"Aviso comprobantes no disponible: {e}")
        n_comp = 0
    if n_comp and not _omitido("comprobantes"):
        avisos.append({
            "codigo": "comprobantes",
            "modulo": "pagos",
            "texto": f"{n_comp} pago(s) con comprobante pendiente",
            "cantidad": n_comp,
            "severidad": "alta",
            "ir": {"modulo": "pagos", "params": {"filtro": "pendientes"}},
        })
    try:
        vencidas = cuota_service.obtener_vencidas()
    except Exception:
        vencidas = []
    if vencidas and not _omitido("vencidas"):
        avisos.append({
            "codigo": "vencidas",
            "modulo": "pagos",
            "texto": f"{len(vencidas)} cuota(s) vencida(s)",
            "cantidad": len(vencidas),
            "severidad": "alta",
            "ir": {"modulo": "pagos", "params": {"tab": "Morosos"}},
        })
    try:
        por_vencer = cuota_service.obtener_por_vencer()
    except Exception:
        por_vencer = []
    if por_vencer and not _omitido("por_vencer"):
        avisos.append({
            "codigo": "por_vencer",
            "modulo": "pagos",
            "texto": f"{len(por_vencer)} cuota(s) por vencer",
            "cantidad": len(por_vencer),
            "severidad": "media",
            "ir": {"modulo": "pagos", "params": {"tab": "Morosos"}},
        })
    try:
        bajo = inventario_service.obtener_bajo_stock()
    except Exception:
        bajo = []
    bajo = [p for p in bajo
            if not _omitido("stock_bajo", "producto", p.get("id_producto", 0))]
    if bajo and not _omitido("stock_bajo"):
        avisos.append({
            "codigo": "stock_bajo",
            "modulo": "inventario",
            "texto": f"{len(bajo)} producto(s) con stock bajo",
            "cantidad": len(bajo),
            "severidad": "media",
            "ir": {"modulo": "tiendita", "params": {}},
        })
    sin_apod = [m for m in _sin_apoderado_principal()
                if not _omitido("sin_apoderado", "matricula", m.get("id_matricula", 0))]
    if sin_apod and not _omitido("sin_apoderado"):
        avisos.append({
            "codigo": "sin_apoderado",
            "modulo": "matriculas",
            "texto": f"{len(sin_apod)} matrícula(s) sin apoderado principal",
            "cantidad": len(sin_apod),
            "severidad": "media",
            "ir": {"modulo": "matriculas", "params": {}},
        })
    avisos.extend(_avisos_pago_profesores())
    return avisos


def _avisos_pago_profesores() -> list[dict]:
    """Recordatorio de pago a profesores según frecuencia configurada.

    Sin tabla nueva: usa el último egreso PROFESOR por responsable.
    """
    from datetime import datetime
    from repositories import egreso_repository
    from services import configuracion_service
    try:
        frec, dias = configuracion_service.obtener_frecuencia_profesores()
    except Exception:
        frec, dias = "MENSUAL", 30
    try:
        filas = egreso_repository.ultimo_por_responsable("PROFESOR")
    except Exception as e:
        logger.warning(f"Aviso pago profesores no disponible: {e}")
        return []
    hoy = datetime.now().date()
    avisos = []
    if not filas:
        if not _omitido("pago_profesores"):
            avisos.append({
                "codigo": "pago_profesores",
                "modulo": "egresos",
                "texto": "Sin pagos a profesores registrados (frecuencia: "
                         f"{frec.lower()})",
                "cantidad": 0,
                "severidad": "media",
                "ir": {"modulo": "egresos", "params": {"tab": "Profesores"}},
            })
        return avisos
    for f in filas:
        resp = (f.get("responsable") or "").strip() or "profesor"
        try:
            ultima = datetime.strptime(str(f.get("ultima_fecha", ""))[:10], "%Y-%m-%d").date()
            atraso = (hoy - ultima).days
        except (ValueError, TypeError):
            continue
        if atraso >= dias and not _omitido("pago_profesores", "responsable", resp):
            avisos.append({
                "codigo": "pago_profesores",
                "modulo": "egresos",
                "texto": f"Pago a {resp} pendiente (último hace {atraso} días)",
                "cantidad": atraso,
                "severidad": "media",
                "ir": {"modulo": "egresos", "params": {"tab": "Profesores"}},
            })
    return avisos


def avisos_por_modulo(modulo: str) -> list[dict]:
    return [a for a in obtener_avisos() if a["modulo"] == modulo]


def listar_pagos_sin_comprobante(limit: int = 200) -> list[dict]:
    rows = pago_repository.obtener_sin_comprobante(limit=limit)
    return [r for r in rows
            if not _omitido("comprobantes", "pago", r.get("id_pago", 0))]


def listar_matriculas_sin_apoderado() -> list[dict]:
    return [m for m in _sin_apoderado_principal()
            if not _omitido("sin_apoderado", "matricula", m.get("id_matricula", 0))]


def listar_bajo_stock() -> list[dict]:
    try:
        rows = inventario_service.obtener_bajo_stock()
    except Exception:
        return []
    return [p for p in rows
            if not _omitido("stock_bajo", "producto", p.get("id_producto", 0))]


def omitir_aviso(codigo: str, motivo: str, origen_tipo: str = "",
                 origen_id: int = 0, id_usuario: int | None = None) -> None:
    aviso_repository.omitir(codigo, origen_tipo, origen_id, motivo, id_usuario)
    invalidar_cache_avisos()
    try:
        from services import auditoria_service
        auditoria_service.registrar_log(
            id_usuario if id_usuario is not None else auditoria_service.id_usuario_sesion(),
            "aviso_omitido", origen_id, "OMITIR_AVISO",
            "", f"{codigo}/{origen_tipo}:{motivo}")
    except Exception:
        pass


def reactivar_aviso(codigo: str, origen_tipo: str = "",
                    origen_id: int = 0) -> None:
    aviso_repository.reactivar(codigo, origen_tipo, origen_id)
    invalidar_cache_avisos()
    try:
        from services import auditoria_service
        auditoria_service.registrar_log(
            auditoria_service.id_usuario_sesion(),
            "aviso_omitido", origen_id, "REACTIVAR_AVISO",
            "", f"{codigo}/{origen_tipo}")
    except Exception:
        pass


def listar_omitidos() -> list[dict]:
    try:
        return aviso_repository.listar_omitidos()
    except Exception as e:
        logger.warning(f"Avisos omitidos no disponibles: {e}")
        return []
