from services import dashboard_service


def obtener_indicadores() -> dict:
    return dashboard_service.obtener_indicadores()


def listar_alumnos_activos() -> list[dict]:
    return dashboard_service.listar_alumnos_activos()


def listar_cuotas_vencidas() -> list[dict]:
    return dashboard_service.listar_cuotas_vencidas()


def listar_cuotas_por_vencer() -> list[dict]:
    return dashboard_service.listar_cuotas_por_vencer()


def listar_pagos_hoy() -> list[dict]:
    return dashboard_service.listar_pagos_hoy()


def listar_monto_vencido() -> list[dict]:
    return dashboard_service.listar_monto_vencido()


def listar_monto_por_vencer() -> list[dict]:
    return dashboard_service.listar_monto_por_vencer()


def listar_stock_bajo() -> list[dict]:
    return dashboard_service.listar_stock_bajo()


def obtener_ingresos_por_dia_mes() -> list[dict]:
    return dashboard_service.obtener_ingresos_por_dia_mes()


def contar_matriculas_mes() -> int:
    return dashboard_service.contar_matriculas_mes()


def listar_nuevos_mes() -> list[dict]:
    return dashboard_service.listar_nuevos_mes()


def listar_antiguos_mes() -> list[dict]:
    return dashboard_service.listar_antiguos_mes()


def listar_matriculas_mes() -> list[dict]:
    return dashboard_service.listar_matriculas_mes()


def comparativa_mensual() -> dict:
    return dashboard_service.comparativa_mensual()


def resumen_dinero() -> dict:
    return dashboard_service.resumen_dinero()


def listar_compras_mes() -> list[dict]:
    return dashboard_service.listar_compras_mes()


def listar_ventas_dinero_mes() -> list[dict]:
    return dashboard_service.listar_ventas_dinero_mes()


def listar_ganancias_mes() -> list[dict]:
    return dashboard_service.listar_ganancias_mes()
