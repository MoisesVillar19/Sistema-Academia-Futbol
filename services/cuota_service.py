import calendar
from datetime import datetime, timedelta

from repositories import cuota_repository
from models.cuota import Cuota
from services import auditoria_service
from utils.constants import (
    CUOTA_PENDIENTE,
    CUOTA_PARCIAL,
    CUOTA_PAGADO,
    CUOTA_VENCIDO,
)
from utils.dates import get_today
from utils.logger import logger


def _fecha_vencimiento_valida(periodo: str, dia: int) -> str:
    """Construye la fecha de vencimiento ajustando el dia al ultimo del mes.

    Evita fechas invalidas como 2026-02-30 cuando dia_vencimiento > 28.
    """
    anio, mes = int(periodo[:4]), int(periodo[5:7])
    dia_valido = min(int(dia), calendar.monthrange(anio, mes)[1])
    return f"{periodo}-{dia_valido:02d}"


def crear_cuota(id_matricula: int, monto_total: float, fecha_vencimiento: str,
               periodo: str) -> int:
    cuota = Cuota(
        id_matricula=id_matricula,
        periodo=periodo,
        fecha_vencimiento=fecha_vencimiento,
        monto_total=monto_total,
        monto_pagado=0,
        saldo=monto_total,
        estado=CUOTA_PENDIENTE,
    )
    return cuota_repository.insertar(cuota)


def generar_siguiente_cuota(id_matricula: int, monto_base: float,
                            dia_vencimiento: int) -> tuple[bool, str, int | None]:
    cuotas = cuota_repository.obtener_por_matricula(id_matricula)

    if cuotas:
        ultimo_periodo = cuotas[-1]["periodo"]
        try:
            fecha = datetime.strptime(ultimo_periodo, "%Y-%m")
            nueva_fecha = fecha + timedelta(days=32)
            siguiente_periodo = nueva_fecha.strftime("%Y-%m")
        except ValueError:
            siguiente_periodo = get_today()[:7]

        periodos_existentes = {c["periodo"] for c in cuotas}
        if siguiente_periodo in periodos_existentes:
            return False, f"Ya existe una cuota para el periodo {siguiente_periodo}", None
    else:
        siguiente_periodo = get_today()[:7]

    fecha_venc = _fecha_vencimiento_valida(siguiente_periodo, dia_vencimiento)

    id_cuota = crear_cuota(
        id_matricula=id_matricula,
        monto_total=monto_base,
        fecha_vencimiento=fecha_venc,
        periodo=siguiente_periodo,
    )

    return True, "Cuota generada correctamente", id_cuota


def actualizar_pago(id_cuota: int, monto_pagado: float) -> tuple[bool, str]:
    cuota = cuota_repository.obtener_por_id(id_cuota)
    if not cuota:
        return False, "Cuota no encontrada"

    nuevo_monto_pagado = round(cuota["monto_pagado"] + monto_pagado, 2)
    nuevo_saldo = round(cuota["monto_total"] - nuevo_monto_pagado, 2)

    if nuevo_saldo < 0:
        return False, "El monto excede el saldo pendiente"

    if nuevo_saldo == 0:
        estado = CUOTA_PAGADO
    elif nuevo_monto_pagado > 0:
        estado = CUOTA_PARCIAL
    else:
        estado = CUOTA_PENDIENTE

    cuota_obj = Cuota(
        id_cuota=id_cuota,
        id_matricula=cuota["id_matricula"],
        periodo=cuota["periodo"],
        fecha_vencimiento=cuota["fecha_vencimiento"],
        monto_total=cuota["monto_total"],
        monto_pagado=nuevo_monto_pagado,
        saldo=nuevo_saldo,
        estado=estado,
        monto_mora=cuota.get("monto_mora", 0),
        activo=cuota["activo"],
    )
    cuota_repository.actualizar(cuota_obj)

    auditoria_service.registrar_update(
        id_usuario=auditoria_service.id_usuario_sesion(),
        tabla="cuota",
        id_registro=id_cuota,
        valores_anteriores=f"pagado={cuota['monto_pagado']}, saldo={cuota['saldo']}, estado={cuota['estado']}",
        valores_nuevos=f"pagado={nuevo_monto_pagado}, saldo={nuevo_saldo}, estado={estado}",
    )

    if estado == CUOTA_PAGADO:
        _generar_siguiente_cuota_automatica(cuota)

    return True, f"Pago registrado. Saldo: S/{nuevo_saldo:.2f}"


def _generar_siguiente_cuota_automatica(cuota_pagada: dict) -> None:
    """RN-014: al cancelar una cuota se genera la del mes siguiente.

    Usa como monto base el monto original de la cuota pagada (sin mora).
    No falla si ya existe la cuota del periodo siguiente.
    """
    from repositories import matricula_repository

    matricula = matricula_repository.obtener_por_id(cuota_pagada["id_matricula"])
    if not matricula or not matricula.get("activo", 1):
        return

    monto_base = round(
        (cuota_pagada.get("monto_total") or 0) - (cuota_pagada.get("monto_mora") or 0), 2
    )
    generar_siguiente_cuota(
        id_matricula=cuota_pagada["id_matricula"],
        monto_base=monto_base,
        dia_vencimiento=matricula.get("dia_vencimiento", 1),
    )


def actualizar_estados_vencidos() -> int:
    """Marca cuotas vencidas y aplica mora segun CONFIGURACION (PORCENTAJE o MONTO_FIJO).

    Mantiene la invarianta saldo = monto_total - monto_pagado: la mora se suma
    tambien a monto_total. Solo escribe cuando hay un cambio real.
    """
    from services import configuracion_service
    today = get_today()
    cuotas = cuota_repository.obtener_todas_pendientes()

    mora_habilitada = configuracion_service.esta_mora_habilitada()
    tipo_mora = configuracion_service.obtener_tipo_mora()
    porcentaje_mora = configuracion_service.obtener_porcentaje_mora()
    monto_fijo_mora = configuracion_service.obtener_monto_fijo_mora()
    id_usuario = auditoria_service.id_usuario_sesion()

    actualizadas = 0
    for cuota in cuotas:
        vencida = cuota["fecha_vencimiento"] < today and cuota["saldo"] > 0
        ya_vencida = cuota["estado"] == CUOTA_VENCIDO

        mora_actual = cuota.get("monto_mora", 0) or 0
        nueva_mora = mora_actual

        if mora_habilitada and vencida and not ya_vencida and mora_actual == 0:
            base = round(cuota["monto_total"] - cuota["monto_pagado"], 2)
            if tipo_mora == "MONTO_FIJO":
                nueva_mora = round(monto_fijo_mora, 2) if monto_fijo_mora > 0 else 0
            elif porcentaje_mora > 0:
                nueva_mora = round(base * porcentaje_mora / 100, 2)

        nuevo_estado = CUOTA_VENCIDO if vencida else cuota["estado"]

        if nueva_mora == mora_actual and nuevo_estado == cuota["estado"]:
            continue

        nuevo_total = round(cuota["monto_total"] + (nueva_mora - mora_actual), 2)
        nuevo_saldo = round(nuevo_total - cuota["monto_pagado"], 2)

        cuota_obj = Cuota(
            id_cuota=cuota["id_cuota"],
            id_matricula=cuota["id_matricula"],
            periodo=cuota["periodo"],
            fecha_vencimiento=cuota["fecha_vencimiento"],
            monto_total=nuevo_total,
            monto_pagado=cuota["monto_pagado"],
            monto_mora=nueva_mora,
            saldo=nuevo_saldo,
            estado=nuevo_estado,
            activo=cuota["activo"],
        )
        cuota_repository.actualizar(cuota_obj)
        actualizadas += 1

        auditoria_service.registrar_update(
            id_usuario=id_usuario,
            tabla="cuota",
            id_registro=cuota["id_cuota"],
            valores_anteriores=f"saldo={cuota['saldo']}, mora={mora_actual}, estado={cuota['estado']}",
            valores_nuevos=f"saldo={nuevo_saldo}, mora={nueva_mora}, estado={nuevo_estado}",
        )

    return actualizadas


def obtener_cuotas_por_matricula(id_matricula: int) -> list[dict]:
    return cuota_repository.obtener_por_matricula(id_matricula)


def obtener_cuotas_pendientes(id_matricula: int) -> list[dict]:
    return cuota_repository.obtener_pendientes_por_matricula(id_matricula)


def contar_por_estado(estado: str) -> int:
    return cuota_repository.contar_por_estado(estado)


def obtener_vencidas() -> list[dict]:
    return cuota_repository.obtener_vencidas()


def obtener_por_vencer(dias: int | None = None) -> list[dict]:
    from services import configuracion_service
    if dias is None:
        dias = configuracion_service.obtener_dias_por_vencer()
    return cuota_repository.obtener_por_vencer(dias)


MESES_GRILLA = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                "JUL", "AGO", "SET", "OCT", "NOV", "DIC"]

_PRIORIDAD_ESTADO = {"VENCIDO": 0, "PARCIAL": 1, "PENDIENTE": 2, "PAGADO": 3}


def grilla_anual(year: int) -> list[dict]:
    """Fase 7d: una fila por estudiante con estado por mes (estilo Excel
    RELACIÓN DE ALUMNOS: X=CANCELADO/PAGADO, monto=ADELANTO/PARCIAL)."""
    filas: dict = {}
    for c in cuota_repository.obtener_por_anio(year):
        eid = c.get("id_estudiante")
        if eid not in filas:
            filas[eid] = {
                "id_estudiante": eid,
                "nombre": f"{c.get('nombres', '')} {c.get('apellidos', '')}".strip(),
                "dni": c.get("dni", ""),
                "meses": {},
            }
        try:
            mes = int(str(c.get("fecha_vencimiento", ""))[5:7])
        except (ValueError, TypeError):
            continue
        if not 1 <= mes <= 12:
            continue
        estado = c.get("estado", "PENDIENTE")
        try:
            saldo = float(c.get("saldo", 0) or 0)
        except (TypeError, ValueError):
            saldo = 0.0
        actual = filas[eid]["meses"].get(mes)
        if actual is None or _PRIORIDAD_ESTADO.get(estado, 9) < _PRIORIDAD_ESTADO.get(actual.get("estado"), 9):
            filas[eid]["meses"][mes] = {"estado": estado, "saldo": saldo}
    return sorted(filas.values(), key=lambda f: f["nombre"])
