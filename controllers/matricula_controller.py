from services import matricula_service, tarifa_service, beca_service, cuota_service, categoria_service, auth_service
from utils.validators import validate_not_empty
from utils.dates import calculate_age


def _get_id_usuario() -> int:
    return auth_service.id_usuario_sesion_or_system()


def matricula_express(data: dict) -> tuple[bool, str, dict | None]:
    return matricula_service.matricula_express(data, id_usuario=_get_id_usuario())


def monto_express_default() -> float:
    return matricula_service.monto_express_nuevo_default()


def crear_matricula(data: dict) -> tuple[bool, str, int | None]:
    if not data.get("id_estudiante"):
        return False, "El estudiante es obligatorio", None
    if not data.get("id_tarifa"):
        return False, "La tarifa es obligatoria", None

    monto_pactado = data.get("monto_pactado")
    if monto_pactado is not None and monto_pactado != "":
        try:
            monto_pactado = float(monto_pactado)
            if monto_pactado < 0:
                return False, "El monto pactado no puede ser negativo", None
        except (ValueError, TypeError):
            return False, "El monto pactado no es válido", None
        data["monto_pactado"] = monto_pactado
    else:
        data["monto_pactado"] = None

    dia_venc = data.get("dia_vencimiento", 1)
    try:
        dia_venc = int(dia_venc)
        if not (1 <= dia_venc <= 31):
            return False, "El día de vencimiento debe ser entre 1 y 31", None
    except (ValueError, TypeError):
        return False, "Día de vencimiento no válido", None
    data["dia_vencimiento"] = dia_venc

    # productos configurables: validar ids y cantidad
    productos = data.get("productos", [])
    if productos:
        for p in productos:
            if not p.get("id_producto"):
                return False, "Producto inválido en selección", None
            try:
                cant = int(p.get("cantidad", 0))
                if cant <= 0:
                    return False, "Cantidad de producto debe ser >0", None
                p["cantidad"] = cant
            except (ValueError, TypeError):
                return False, "Cantidad de producto no válida", None

    return matricula_service.crear_matricula(data, id_usuario=_get_id_usuario())


def obtener_matricula(id_matricula: int) -> dict | None:
    return matricula_service.obtener_matricula(id_matricula)


def obtener_por_estudiante(id_estudiante: int) -> list[dict]:
    return matricula_service.obtener_por_estudiante(id_estudiante)


def listar_matriculas_activas() -> list[dict]:
    return matricula_service.listar_matriculas_activas()


def asignar_beca(id_matricula: int, id_beca: int,
                 observacion: str = "") -> tuple[bool, str]:
    return matricula_service.asignar_beca(id_matricula, id_beca, observacion)


def desasignar_beca(id_matricula: int, id_beca: int) -> tuple[bool, str]:
    return matricula_service.desasignar_beca(id_matricula, id_beca)


def obtener_becas_por_matricula(id_matricula: int) -> list[dict]:
    return matricula_service.obtener_becas_por_matricula(id_matricula)


def listar_tarifas_activas(tipo: str | None = None) -> list[dict]:
    return tarifa_service.listar_tarifas_activas(tipo=tipo)


def listar_becas() -> list[dict]:
    return beca_service.listar_becas(activo=1)


def obtener_cuotas_por_matricula(id_matricula: int) -> list[dict]:
    return cuota_service.obtener_cuotas_por_matricula(id_matricula)


def obtener_tarifa_sugerida_por_edad(fecha_nacimiento: str) -> int | None:
    edad = calculate_age(fecha_nacimiento)
    if edad <= 0:
        return None
    cat = categoria_service.obtener_categoria_por_edad(edad)
    if not cat:
        return None
    tarifas = tarifa_service.listar_tarifas_activas()
    for t in tarifas:
        if t["id_categoria"] == cat["id_categoria"]:
            return t["id_tarifa"]
    return None
