from repositories import configuracion_repository
from models.configuracion import Configuracion
from services import auditoria_service
from utils.logger import logger


def obtener_configuracion() -> dict | None:
    return configuracion_repository.obtener_configuracion()


def actualizar_configuracion(data: dict) -> tuple[bool, str]:
    config = configuracion_repository.obtener_configuracion()
    if not config:
        return False, "Configuración no encontrada"

    config_obj = Configuracion(
        id_configuracion=config["id_configuracion"],
        nombre_academia=data.get("nombre_academia", config.get("nombre_academia", "")),
        direccion=data.get("direccion", config.get("direccion", "")),
        telefono=data.get("telefono", config.get("telefono", "")),
        correo=data.get("correo", config.get("correo", "")),
        mora_habilitada=data.get("mora_habilitada", config.get("mora_habilitada", 0)),
        tipo_mora=data.get("tipo_mora", config.get("tipo_mora", "PORCENTAJE")),
        porcentaje_mora=data.get("porcentaje_mora", config.get("porcentaje_mora", 0)),
        monto_mora=data.get("monto_mora", config.get("monto_mora", 0)),
        dias_por_vencer=data.get("dias_por_vencer", config.get("dias_por_vencer", 3)),
        permitir_multiples_becas=data.get("permitir_multiples_becas",
                                          config.get("permitir_multiples_becas", 1)),
        backup_automatico=data.get("backup_automatico", config.get("backup_automatico", 1)),
        frecuencia_backup=data.get("frecuencia_backup", config.get("frecuencia_backup", 7)),
        ruta_backup=data.get("ruta_backup", config.get("ruta_backup", "backups/")),
        correo_onedrive=data.get("correo_onedrive", config.get("correo_onedrive", "")),
        pin_emergencia=config.get("pin_emergencia", ""),
        precio_inscripcion=data.get("precio_inscripcion", config.get("precio_inscripcion", 100)),
        precio_mensualidad=data.get("precio_mensualidad", config.get("precio_mensualidad", 100)),
        precio_uniforme=data.get("precio_uniforme", config.get("precio_uniforme", 20)),
        precio_reingreso=data.get("precio_reingreso", config.get("precio_reingreso", 100)),
        tasa_campeonato=data.get("tasa_campeonato", config.get("tasa_campeonato", 15)),
        arbitraje_por_equipo=data.get("arbitraje_por_equipo", config.get("arbitraje_por_equipo", 15)),
        pago_profesor=data.get("pago_profesor", config.get("pago_profesor", 200)),
        frecuencia_profesores=data.get("frecuencia_profesores", config.get("frecuencia_profesores", "MENSUAL")),
        frecuencia_profesores_dias=data.get("frecuencia_profesores_dias", config.get("frecuencia_profesores_dias", 30)),
    )

    if config_obj.frecuencia_profesores not in FRECUENCIAS_PROFESORES:
        return False, "Frecuencia de pago a profesores no válida (MENSUAL/QUINCENAL/PERSONALIZADA)"

    configuracion_repository.actualizar(config_obj)

    auditoria_service.registrar_update(
        id_usuario=auditoria_service.id_usuario_sesion(),
        tabla="configuracion",
        id_registro=config["id_configuracion"],
        valores_anteriores=f"mora_habilitada={config.get('mora_habilitada', 0)}, porcentaje_mora={config.get('porcentaje_mora', 0)}, dias_por_vencer={config.get('dias_por_vencer', 3)}",
        valores_nuevos=f"mora_habilitada={config_obj.mora_habilitada}, porcentaje_mora={config_obj.porcentaje_mora}, dias_por_vencer={config_obj.dias_por_vencer}, precio_inscripcion={config_obj.precio_inscripcion}, precio_mensualidad={config_obj.precio_mensualidad}",
    )

    logger.info("Configuración actualizada")
    return True, "Configuración actualizada correctamente"


def obtener_dias_por_vencer() -> int:
    config = obtener_configuracion()
    return config.get("dias_por_vencer", 3) if config else 3


def esta_mora_habilitada() -> bool:
    config = obtener_configuracion()
    return bool(config.get("mora_habilitada", 0)) if config else False


def obtener_porcentaje_mora() -> float:
    config = obtener_configuracion()
    return config.get("porcentaje_mora", 0) if config else 0


def permite_multiples_becas() -> bool:
    config = obtener_configuracion()
    return bool(config.get("permitir_multiples_becas", 1)) if config else True


def obtener_valor(clave: str):
    """Retorna el valor crudo de una columna de CONFIGURACION (o None si no existe)."""
    config = obtener_configuracion()
    return config.get(clave) if config else None


def obtener_tipo_mora() -> str:
    config = obtener_configuracion()
    return (config.get("tipo_mora") or "PORCENTAJE") if config else "PORCENTAJE"


def obtener_monto_fijo_mora() -> float:
    config = obtener_configuracion()
    return float(config.get("monto_mora", 0) or 0) if config else 0.0


FRECUENCIAS_PROFESORES = ("MENSUAL", "QUINCENAL", "PERSONALIZADA")


def obtener_frecuencia_profesores() -> tuple[str, int]:
    """(frecuencia, dias): MENSUAL=30, QUINCENAL=15, PERSONALIZADA=dias config."""
    config = obtener_configuracion() or {}
    frec = str(config.get("frecuencia_profesores", "MENSUAL") or "MENSUAL").upper()
    if frec not in FRECUENCIAS_PROFESORES:
        frec = "MENSUAL"
    if frec == "QUINCENAL":
        return frec, 15
    if frec == "PERSONALIZADA":
        try:
            dias = max(int(config.get("frecuencia_profesores_dias", 30) or 30), 1)
        except (TypeError, ValueError):
            dias = 30
        return frec, dias
    return frec, 30
