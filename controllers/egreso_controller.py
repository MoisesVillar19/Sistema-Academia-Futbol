from services import egreso_service, auth_service


def registrar_egreso(data: dict) -> tuple[bool, str, int | None]:
    if not auth_service.tiene_permiso("egresos"):
        return False, "No tiene permiso para registrar egresos", None
    if not data.get("id_usuario"):
        data["id_usuario"] = auth_service.id_usuario_sesion_or_system()
    return egreso_service.registrar_egreso(data)


def listar_egresos(fecha_inicio: str | None = None, fecha_fin: str | None = None,
                   anio: int | None = None, meses: list[int] | None = None,
                   orden: str | None = None, conceptos: list[str] | None = None,
                   limit: int | None = None) -> list[dict]:
    if not auth_service.tiene_permiso("egresos"):
        return []
    return egreso_service.listar_egresos(
        fecha_inicio, fecha_fin, anio, meses, orden, conceptos, limit)


def reporte_ingresos_vs_egresos(fecha_inicio: str, fecha_fin: str) -> dict:
    if not auth_service.tiene_permiso("egresos"):
        return {}
    return egreso_service.reporte_ingresos_vs_egresos(fecha_inicio, fecha_fin)


def eliminar_egreso(id_egreso: int) -> tuple[bool, str]:
    if not auth_service.es_admin():
        return False, "Solo ADMIN puede eliminar egresos"
    return egreso_service.eliminar_egreso(id_egreso)
