from services import tarifa_service, auth_service


def _get_id_usuario() -> int:
    return auth_service.id_usuario_sesion_or_system()


def _requerir_tarifas() -> tuple[bool, str]:
    if not auth_service.tiene_permiso("tarifas"):
        return False, "Sin permiso para gestionar tarifas"
    return True, ""


def crear_tarifa(data: dict) -> tuple[bool, str, int | None]:
    permitido, msg = _requerir_tarifas()
    if not permitido:
        return False, msg, None
    return tarifa_service.crear_tarifa(data)


def editar_tarifa(id_tarifa: int, data: dict) -> tuple[bool, str]:
    permitido, msg = _requerir_tarifas()
    if not permitido:
        return False, msg
    return tarifa_service.editar_tarifa(id_tarifa, data)


def obtener_tarifa(id_tarifa: int) -> dict | None:
    return tarifa_service.obtener_tarifa(id_tarifa)


def listar_tarifas_activas(tipo: str | None = None) -> list[dict]:
    return tarifa_service.listar_tarifas_activas(tipo=tipo)


def listar_por_categoria(id_categoria: int) -> list[dict]:
    return tarifa_service.listar_tarifas_por_categoria(id_categoria)


def desactivar_tarifa(id_tarifa: int) -> tuple[bool, str]:
    permitido, msg = _requerir_tarifas()
    if not permitido:
        return False, msg
    return tarifa_service.editar_tarifa(id_tarifa, {"activo": 0})


def activar_tarifa(id_tarifa: int) -> tuple[bool, str]:
    permitido, msg = _requerir_tarifas()
    if not permitido:
        return False, msg
    return tarifa_service.activar_tarifa(id_tarifa)


def eliminar_tarifa(id_tarifa: int) -> tuple[bool, str]:
    permitido, msg = _requerir_tarifas()
    if not permitido:
        return False, msg
    return tarifa_service.eliminar_tarifa(id_tarifa)


def listar_tarifas_inactivas() -> list[dict]:
    return tarifa_service.listar_tarifas_inactivas()
