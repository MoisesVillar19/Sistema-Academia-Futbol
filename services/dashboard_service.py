from services import cuota_service, pago_service, inventario_service
from repositories import estudiante_repository, matricula_repository
from utils.dates import get_today
from datetime import datetime, timedelta


def obtener_indicadores() -> dict:
    cuota_service.actualizar_estados_vencidos()

    alumnos_activos = estudiante_repository.obtener_todos(activo=1)
    total_activos = len(alumnos_activos)

    cuotas_vencidas = cuota_service.obtener_vencidas()
    total_vencidas = len(cuotas_vencidas)
    monto_vencido = sum(c.get("saldo", 0) for c in cuotas_vencidas)

    config = _obtener_configuracion()
    dias_por_vencer = config.get("dias_por_vencer", 3) if config else 3
    cuotas_por_vencer = cuota_service.obtener_por_vencer(dias_por_vencer)
    total_por_vencer = len(cuotas_por_vencer)
    monto_por_vencer = sum(c.get("saldo", 0) for c in cuotas_por_vencer)

    today = get_today()
    pagos_hoy = pago_service.contar_pagos_por_fecha(today, today)
    ingresos_hoy = pago_service.obtener_ingresos_por_fecha(today, today)

    fecha_inicio_mes = today[:7] + "-01"
    ultimo_dia = _ultimo_dia_mes(today)
    fecha_fin_mes = f"{today[:7]}-{ultimo_dia:02d}"
    ingresos_mes = pago_service.obtener_ingresos_por_fecha(fecha_inicio_mes, fecha_fin_mes)

    # v2 flexible: ventas + egresos + nuevos vs antiguos (robusto, no silencioso)
    from utils.logger import logger as _log
    try:
        from repositories import venta_repository, egreso_repository
        ingresos_ventas_mes = venta_repository.sumar_por_periodo(fecha_inicio_mes, fecha_fin_mes)
        egresos_mes = egreso_repository.sumar_por_periodo(fecha_inicio_mes, fecha_fin_mes)
    except Exception as e:
        _log.warning(f"Dashboard ventas/egresos fallo: {e}")
        ingresos_ventas_mes = None
        egresos_mes = None
    try:
        # v2.1: nuevos = es_nuevo=1 en el mes (RN-051)
        # NOTA: no re-importar estudiante_repository aquí (UnboundLocalError:
        # el import lo convierte en variable local y rompe el uso de línea 10).
        # Se usa el import top-level del módulo.
        try:
            nuevos_mes = estudiante_repository.contar_por_es_nuevo(1, fecha_inicio_mes, fecha_fin_mes)
        except Exception:
            from database.connection import fetch_all
            rows = fetch_all("SELECT COUNT(*) as c FROM estudiante WHERE es_nuevo=1 AND fecha_ingreso BETWEEN ? AND ? AND activo=1", (fecha_inicio_mes, fecha_fin_mes))
            nuevos_mes = rows[0]["c"] if rows and rows[0]["c"] is not None else 0
        matriculas_mes = matricula_repository.contar_por_mes(fecha_inicio_mes, fecha_fin_mes)
        antiguos_mes = max(0, matriculas_mes - nuevos_mes)
    except Exception as e:
        _log.warning(f"Dashboard nuevos/antiguos fallo: {e}")
        nuevos_mes = 0
        matriculas_mes = matricula_repository.contar_por_mes(fecha_inicio_mes, fecha_fin_mes)
        antiguos_mes = max(0, matriculas_mes - nuevos_mes)

    # MoM (mes anterior vs actual) para ingresos
    try:
        from datetime import datetime
        dt = datetime.strptime(fecha_inicio_mes, "%Y-%m-%d")
        # mes anterior
        if dt.month == 1:
            prev_dt = dt.replace(year=dt.year-1, month=12, day=1)
        else:
            prev_dt = dt.replace(month=dt.month-1, day=1)
        prev_ini = prev_dt.strftime("%Y-%m-%d")
        # ultimo dia mes anterior
        import calendar
        prev_fin = f"{prev_dt.strftime('%Y-%m')}-{calendar.monthrange(prev_dt.year, prev_dt.month)[1]:02d}"
        ingresos_mes_prev = pago_service.obtener_ingresos_por_fecha(prev_ini, prev_fin)
        try:
            ventas_prev = venta_repository.sumar_por_periodo(prev_ini, prev_fin)
        except Exception:
            ventas_prev = 0
        total_prev = (ingresos_mes_prev or 0) + (ventas_prev or 0)
        total_actual = (ingresos_mes or 0) + (ingresos_ventas_mes or 0)
        mom = round((total_actual - total_prev) / total_prev * 100, 1) if total_prev else 0
    except Exception as e:
        _log.warning(f"MoM fallo: {e}")
        mom = 0
        total_prev = 0

    total_ingresos_mes = round((ingresos_mes or 0) + (ingresos_ventas_mes or 0), 2) if ingresos_ventas_mes is not None else None
    neto_mes = round((total_ingresos_mes or 0) - (egresos_mes or 0), 2) if egresos_mes is not None and total_ingresos_mes is not None else None

    productos_bajo_stock = inventario_service.obtener_bajo_stock()
    total_bajo_stock = len(productos_bajo_stock)
    # si ventas/egresos fallaron, dejar None para que UI muestre —
    if ingresos_ventas_mes is None or egresos_mes is None or total_ingresos_mes is None:
        logger = _log
        # ya logueado arriba

    return {
        "alumnos_activos": total_activos,
        "cuotas_vencidas": total_vencidas,
        "monto_vencido": monto_vencido,
        "cuotas_por_vencer": total_por_vencer,
        "monto_por_vencer": monto_por_vencer,
        "pagos_hoy": pagos_hoy,
        "ingresos_hoy": ingresos_hoy,
        "ingresos_mes": ingresos_mes,
        "ingresos_ventas_mes": ingresos_ventas_mes,
        "total_ingresos_mes": total_ingresos_mes,
        "egresos_mes": egresos_mes,
        "neto_mes": neto_mes,
        "mom_ingresos": mom,
        "ingresos_mes_prev": total_prev,
        "nuevos_mes": nuevos_mes,
        "antiguos_mes": antiguos_mes,
        "stock_bajo": total_bajo_stock,
        "productos_bajo_stock": productos_bajo_stock,
        "matriculas_mes": matriculas_mes,
    }


def listar_alumnos_activos() -> list[dict]:
    return estudiante_repository.obtener_todos(activo=1)


def listar_cuotas_vencidas() -> list[dict]:
    return cuota_service.obtener_vencidas()


def listar_cuotas_por_vencer() -> list[dict]:
    config = _obtener_configuracion()
    dias = config.get("dias_por_vencer", 3) if config else 3
    return cuota_service.obtener_por_vencer(dias)


def listar_pagos_hoy() -> list[dict]:
    today = get_today()
    return pago_service.listar_por_fecha(today, today)


def listar_monto_vencido() -> list[dict]:
    return cuota_service.obtener_vencidas()


def listar_monto_por_vencer() -> list[dict]:
    config = _obtener_configuracion()
    dias = config.get("dias_por_vencer", 3) if config else 3
    return cuota_service.obtener_por_vencer(dias)


def listar_stock_bajo() -> list[dict]:
    return inventario_service.obtener_bajo_stock()


def obtener_ingresos_por_dia_mes() -> list[dict]:
    today = get_today()
    fecha_inicio_mes = today[:7] + "-01"
    ultimo_dia = _ultimo_dia_mes(today)
    fecha_fin_mes = f"{today[:7]}-{ultimo_dia:02d}"

    pagos = pago_service.listar_por_fecha(fecha_inicio_mes, fecha_fin_mes)

    ingresos_por_dia = {}
    for pago in pagos:
        dia = pago.get("fecha_pago", "")[:10]
        if dia:
            if dia not in ingresos_por_dia:
                ingresos_por_dia[dia] = 0
            ingresos_por_dia[dia] += pago.get("monto_total", 0)

    resultado = []
    for dia in sorted(ingresos_por_dia.keys()):
        resultado.append({"dia": dia, "monto": ingresos_por_dia[dia]})

    return resultado


def contar_matriculas_mes() -> int:
    ini, fin = _rango_mes_actual()
    return matricula_repository.contar_por_mes(ini, fin)


def _rango_mes_actual() -> tuple:
    today = get_today()
    fecha_inicio_mes = today[:7] + "-01"
    ultimo_dia = _ultimo_dia_mes(today)
    return fecha_inicio_mes, f"{today[:7]}-{ultimo_dia:02d}"


def listar_nuevos_mes() -> list[dict]:
    ini, fin = _rango_mes_actual()
    return estudiante_repository.listar_nuevos_por_periodo(ini, fin)


def listar_antiguos_mes() -> list[dict]:
    ini, fin = _rango_mes_actual()
    return matricula_repository.listar_antiguos_por_mes(ini, fin)


def listar_matriculas_mes() -> list[dict]:
    ini, fin = _rango_mes_actual()
    return matricula_repository.listar_por_mes(ini, fin)


def resumen_dinero() -> dict:
    """Cards de dinero del mes: compras/ventas/ganancias por Yape/Efectivo.

    Ganancia de ventas = Σ cant × (precio_unit − costo vigente). Aproximación
    documentada (no costo histórico por venta).
    """
    from repositories import movimiento_inventario_repository, venta_repository
    ini, fin = _rango_mes_actual()
    compras = {r["metodo"]: float(r["total"] or 0)
               for r in movimiento_inventario_repository.sumar_compras_por_metodo(ini, fin)}
    ventas = {r["metodo"]: float(r["total"] or 0)
              for r in venta_repository.ventas_por_metodo(ini, fin)}
    gan = {r["metodo"]: float(r["ganancia"] or 0)
           for r in venta_repository.ganancia_por_metodo(ini, fin)}
    cy, ce = round(compras.get("YAPE", 0), 2), round(compras.get("EFECTIVO", 0), 2)
    vy, ve = round(ventas.get("YAPE", 0), 2), round(ventas.get("EFECTIVO", 0), 2)
    gy, ge = round(gan.get("YAPE", 0), 2), round(gan.get("EFECTIVO", 0), 2)
    return {"compras_yape": cy, "compras_efectivo": ce,
            "ventas_yape": vy, "ventas_efectivo": ve,
            "ganancia_yape": gy, "ganancia_efectivo": ge,
            "ganancia_total": round(gy + ge, 2),
            "mes": ini[:7]}


def listar_compras_mes() -> list[dict]:
    from repositories import movimiento_inventario_repository
    ini, fin = _rango_mes_actual()
    return movimiento_inventario_repository.obtener_compras_con_metodo(ini, fin)


def listar_ventas_dinero_mes() -> list[dict]:
    from repositories import venta_repository
    ini, fin = _rango_mes_actual()
    return [v for v in venta_repository.obtener_todos(ini, fin)
            if (v.get("metodo_pago") in ("YAPE", "EFECTIVO"))]


def listar_ganancias_mes() -> list[dict]:
    from repositories import venta_repository
    ini, fin = _rango_mes_actual()
    return venta_repository.detalle_ganancia_por_venta(ini, fin)


def comparativa_mensual() -> dict:
    """Actual vs anterior día por día (pagos + ventas). Para la vista MoM real."""
    from datetime import datetime
    import calendar
    from repositories import venta_repository
    ini_a, fin_a = _rango_mes_actual()
    dt = datetime.strptime(ini_a, "%Y-%m-%d")
    if dt.month == 1:
        prev_dt = dt.replace(year=dt.year - 1, month=12, day=1)
    else:
        prev_dt = dt.replace(month=dt.month - 1, day=1)
    prev_ini = prev_dt.strftime("%Y-%m-%d")
    prev_fin = f"{prev_dt.strftime('%Y-%m')}-{calendar.monthrange(prev_dt.year, prev_dt.month)[1]:02d}"

    def _por_dia(pagos, ventas):
        agg: dict = {}
        for p in pagos:
            dia = (p.get("fecha_pago", "") or "")[:10]
            if dia:
                agg[dia] = agg.get(dia, 0) + (p.get("monto_total", 0) or 0)
        for v in ventas:
            dia = (v.get("fecha_venta", "") or "")[:10]
            if dia:
                agg[dia] = agg.get(dia, 0) + (v.get("monto_total", 0) or 0)
        return agg

    pagos_a = pago_service.listar_por_fecha(ini_a, fin_a)
    pagos_p = pago_service.listar_por_fecha(prev_ini, prev_fin)
    try:
        ventas_a = venta_repository.obtener_todos(ini_a, fin_a)
    except Exception:
        ventas_a = []
    try:
        ventas_p = venta_repository.obtener_todos(prev_ini, prev_fin)
    except Exception:
        ventas_p = []
    agg_a, agg_p = _por_dia(pagos_a, ventas_a), _por_dia(pagos_p, ventas_p)
    n_dias = max(calendar.monthrange(dt.year, dt.month)[1],
                 calendar.monthrange(prev_dt.year, prev_dt.month)[1])
    etiquetas, serie_a, serie_p = [], [], []
    for d in range(1, n_dias + 1):
        etiquetas.append(f"{d:02d}")
        serie_a.append(round(agg_a.get(f"{ini_a[:7]}-{d:02d}", 0), 2))
        serie_p.append(round(agg_p.get(f"{prev_ini[:7]}-{d:02d}", 0), 2))
    total_a = round(sum(serie_a), 2)
    total_p = round(sum(serie_p), 2)
    delta = round((total_a - total_p) / total_p * 100, 1) if total_p else 0
    return {
        "etiquetas": etiquetas,
        "actual": serie_a,
        "anterior": serie_p,
        "mes_actual": ini_a[:7],
        "mes_anterior": prev_ini[:7],
        "total_actual": total_a,
        "total_anterior": total_p,
        "delta_pct": delta,
    }


def _obtener_configuracion():
    from repositories import configuracion_repository
    return configuracion_repository.obtener_configuracion()


def _ultimo_dia_mes(fecha_str: str) -> int:
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        if fecha.month == 12:
            siguiente = fecha.replace(year=fecha.year + 1, month=1, day=1)
        else:
            siguiente = fecha.replace(month=fecha.month + 1, day=1)
        ultimo = siguiente - timedelta(days=1)
        return ultimo.day
    except ValueError:
        return 30
