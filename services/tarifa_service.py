from repositories import tarifa_repository
from models.tarifa import Tarifa
from services import auditoria_service
from utils.dates import get_today
from utils.logger import logger


def crear_tarifa(data: dict) -> tuple[bool, str, int | None]:
    nombre = data.get("nombre", "")
    monto = data.get("monto", 0)
    id_categoria = data.get("id_categoria")

    if not nombre:
        return False, "El nombre es obligatorio", None
    if not id_categoria:
        return False, "La categoría es obligatoria", None
    if monto <= 0:
        return False, "El monto debe ser mayor a 0", None

    tarifa = Tarifa(
        id_categoria=id_categoria,
        nombre=nombre,
        monto=monto,
        descripcion=data.get("descripcion", ""),
        observaciones=data.get("observaciones", ""),
        fecha_vigencia_desde=data.get("fecha_vigencia_desde", ""),
        fecha_vigencia_hasta=data.get("fecha_vigencia_hasta", ""),
    )

    id_tarifa = tarifa_repository.insertar(tarifa)

    auditoria_service.registrar_insert(
        id_usuario=1,
        tabla="tarifa",
        id_registro=id_tarifa,
        valores_nuevos=f"nombre={nombre}, monto={monto}",
    )

    logger.info(f"Tarifa creada: {nombre} - S/{monto}")
    return True, "Tarifa creada correctamente", id_tarifa


def editar_tarifa(id_tarifa: int, data: dict) -> tuple[bool, str]:
    tarifa = tarifa_repository.obtener_por_id(id_tarifa)
    if not tarifa:
        return False, "Tarifa no encontrada"

    tarifa_obj = Tarifa(
        id_tarifa=id_tarifa,
        id_categoria=data.get("id_categoria", tarifa["id_categoria"]),
        nombre=data.get("nombre", tarifa["nombre"]),
        monto=data.get("monto", tarifa["monto"]),
        descripcion=data.get("descripcion", tarifa.get("descripcion", "")),
        observaciones=data.get("observaciones", tarifa.get("observaciones", "")),
        fecha_vigencia_desde=data.get("fecha_vigencia_desde", tarifa.get("fecha_vigencia_desde", "")),
        fecha_vigencia_hasta=data.get("fecha_vigencia_hasta", tarifa.get("fecha_vigencia_hasta", "")),
        activo=data.get("activo", tarifa["activo"]),
    )
    tarifa_repository.actualizar(tarifa_obj)
    auditoria_service.registrar_update(
        id_usuario=1,
        tabla="tarifa",
        id_registro=id_tarifa,
        valores_anteriores=f"nombre={tarifa['nombre']}, monto={tarifa['monto']}",
        valores_nuevos=f"nombre={tarifa_obj.nombre}, monto={tarifa_obj.monto}",
    )

    nuevo_activo = data.get("activo", tarifa["activo"])
    if nuevo_activo != tarifa["activo"]:
        if nuevo_activo == 0:
            auditoria_service.registrar_desactivacion(
                id_usuario=1,
                tabla="tarifa",
                id_registro=id_tarifa,
                valores_anteriores=f"activo=1",
                valores_nuevos=f"activo=0",
            )
            logger.info(f"Tarifa desactivada: {tarifa['nombre']} (id={id_tarifa})")
        else:
            auditoria_service.registrar_update(
                id_usuario=1,
                tabla="tarifa",
                id_registro=id_tarifa,
                valores_anteriores="activo=0",
                valores_nuevos="activo=1",
            )
            logger.info(f"Tarifa activada: {tarifa['nombre']} (id={id_tarifa})")

    return True, "Tarifa actualizada correctamente"


def obtener_tarifa(id_tarifa: int) -> dict | None:
    return tarifa_repository.obtener_por_id(id_tarifa)


def listar_tarifas_por_categoria(id_categoria: int) -> list[dict]:
    return tarifa_repository.obtener_por_categoria(id_categoria)


def listar_tarifas_activas(tipo: str | None = None) -> list[dict]:
    return tarifa_repository.obtener_activas(tipo=tipo)


def obtener_tarifa_vigente(tipo: str, fecha: str) -> dict | None:
    """Obtiene la tarifa vigente para un tipo en una fecha dada."""
    return tarifa_repository.obtener_vigente(tipo, fecha)


def listar_tarifas_inactivas() -> list[dict]:
    return tarifa_repository.obtener_inactivas()


def activar_tarifa(id_tarifa: int) -> tuple[bool, str]:
    tarifa = tarifa_repository.obtener_por_id(id_tarifa)
    if not tarifa:
        return False, "Tarifa no encontrada"
    if tarifa["activo"]:
        return False, "La tarifa ya está activa"

    tarifa_obj = Tarifa(
        id_tarifa=id_tarifa,
        id_categoria=tarifa["id_categoria"],
        nombre=tarifa["nombre"],
        monto=tarifa["monto"],
        descripcion=tarifa.get("descripcion", ""),
        observaciones=tarifa.get("observaciones", ""),
        activo=1,
    )
    tarifa_repository.actualizar(tarifa_obj)

    auditoria_service.registrar_update(
        id_usuario=1,
        tabla="tarifa",
        id_registro=id_tarifa,
        valores_anteriores="activo=0",
        valores_nuevos="activo=1",
    )

    logger.info(f"Tarifa activada: {tarifa['nombre']} (id={id_tarifa})")
    return True, "Tarifa activada correctamente"


def eliminar_tarifa(id_tarifa: int, id_usuario: int = 1) -> tuple[bool, str]:
    """Soft delete: nunca se borra fisicamente la tarifa (regla RN-028)."""
    tarifa = tarifa_repository.obtener_por_id(id_tarifa)
    if not tarifa:
        return False, "Tarifa no encontrada"

    if tarifa["activo"] == 0:
        return False, "La tarifa ya está desactivada"

    uso = tarifa_repository.contar_matriculas_por_tarifa(id_tarifa)
    if uso > 0:
        return False, (
            f"No se puede eliminar: la tarifa tiene {uso} matrícula(s) activa(s). "
            "Desactívela en su lugar."
        )

    tarifa_repository.soft_delete(id_tarifa)

    auditoria_service.registrar_desactivacion(
        id_usuario=id_usuario,
        tabla="tarifa",
        id_registro=id_tarifa,
        valores_anteriores=f"nombre={tarifa['nombre']}, monto={tarifa['monto']}, activo=1",
        valores_nuevos="activo=0",
    )

    logger.info(f"Tarifa desactivada (soft delete): {tarifa['nombre']} (id={id_tarifa})")
    return True, "Tarifa eliminada correctamente"
