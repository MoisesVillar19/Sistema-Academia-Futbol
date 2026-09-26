from repositories import estudiante_repository, persona_repository, estudiante_apoderado_repository
from models.estudiante import Estudiante
from models.persona import Persona
from services import auditoria_service, apoderado_service
from database.connection import transaccion
from utils.constants import STATUS_ACTIVO, STATUS_RETIRADO, STATUS_REINGRESANTE
from utils.dates import get_today
from utils.logger import logger


def crear_estudiante(data: dict, id_usuario: int = 1) -> tuple[bool, str, int | None]:
    # RN-041 foto_path flexible, RN-051 es_nuevo
    foto_path = data.get("foto_path")
    dni = data.get("dni", "")
    es_nuevo = 1 if data.get("es_nuevo") in (1, "1", True, "true", "True") else 0

    if not dni:
        return False, "El DNI es obligatorio", None

    persona = persona_repository.obtener_por_dni(dni)
    if persona:
        id_persona = persona["id_persona"]
        existente = estudiante_repository.obtener_por_persona(id_persona)
        if existente:
            return False, "Esta persona ya es estudiante", None
    else:
        nombres = data.get("nombres", "")
        apellidos = data.get("apellidos", "")
        if not nombres or not apellidos:
            return False, "Nombres y apellidos son obligatorios para nueva persona", None

    estudiante = Estudiante(
        id_persona=0,
        estado=STATUS_ACTIVO,
        fecha_ingreso=get_today(),
        foto_path=foto_path,
        fecha_matricula=data.get("fecha_matricula", get_today()),
        es_nuevo=es_nuevo,
    )

    with transaccion():
        if persona:
            id_persona = persona["id_persona"]
        else:
            persona_obj = Persona(
                dni=dni,
                tipo_documento=data.get("tipo_documento", "DNI"),
                nombres=data.get("nombres", ""),
                apellidos=data.get("apellidos", ""),
                fecha_nacimiento=data.get("fecha_nacimiento", ""),
                sexo=data.get("sexo", ""),
                direccion=data.get("direccion", ""),
                telefono=data.get("telefono", ""),
                correo=data.get("correo", ""),
            )
            id_persona = persona_repository.insertar(persona_obj)

        estudiante.id_persona = id_persona
        id_estudiante = estudiante_repository.insertar(estudiante)
        # Si hay foto_path, actualizar (estudiante_repository soporta foto_path)
        if foto_path:
            try:
                estudiante_repository.actualizar_foto(id_estudiante, foto_path)
            except Exception:
                pass

        auditoria_service.registrar_insert(
            id_usuario=id_usuario,
            tabla="estudiante",
            id_registro=id_estudiante,
            valores_nuevos=f"dni={dni}, estado={STATUS_ACTIVO}",
        )

    logger.info(f"Estudiante creado: DNI={dni}")
    return True, "Estudiante registrado correctamente", id_estudiante


def editar_estudiante(id_estudiante: int, data: dict) -> tuple[bool, str]:
    estudiante = estudiante_repository.obtener_por_id(id_estudiante)
    if not estudiante:
        return False, "Estudiante no encontrado"

    persona = persona_repository.obtener_por_id(estudiante["id_persona"])
    if persona:
        dni = data.get("dni", persona["dni"])
        if persona_repository.existe_dni(dni, exclude_id=estudiante["id_persona"]):
            return False, "El DNI ya está registrado por otra persona"

        persona_obj = Persona(
            id_persona=estudiante["id_persona"],
            dni=dni,
            nombres=data.get("nombres", persona["nombres"]),
            apellidos=data.get("apellidos", persona["apellidos"]),
            fecha_nacimiento=data.get("fecha_nacimiento", persona["fecha_nacimiento"] or ""),
            sexo=data.get("sexo", persona["sexo"] or ""),
            direccion=data.get("direccion", persona["direccion"] or ""),
            telefono=data.get("telefono", persona["telefono"] or ""),
            correo=data.get("correo", persona["correo"] or ""),
            activo=persona["activo"],
        )
        persona_repository.actualizar(persona_obj)

        auditoria_service.registrar_update(
            id_usuario=auditoria_service.id_usuario_sesion(),
            tabla="persona",
            id_registro=estudiante["id_persona"],
            valores_anteriores=f"dni={persona['dni']}, nombres={persona['nombres']}, apellidos={persona['apellidos']}",
            valores_nuevos=f"dni={dni}, nombres={persona_obj.nombres}, apellidos={persona_obj.apellidos}",
        )

    # RN-041: actualizar foto si se envía (flexible, opcional)
    foto_path = data.get("foto_path")
    if foto_path:
        try:
            estudiante_repository.actualizar_foto(id_estudiante, foto_path)
            auditoria_service.registrar_update(
                id_usuario=auditoria_service.id_usuario_sesion(),
                tabla="estudiante",
                id_registro=id_estudiante,
                valores_anteriores=f"foto_path={estudiante.get('foto_path','')}",
                valores_nuevos=f"foto_path={foto_path}",
            )
        except Exception as e:
            logger.warning(f"No se pudo actualizar foto: {e}")

    return True, "Estudiante actualizado correctamente"


def registrar_retiro(id_estudiante: int, id_usuario: int = 1,
                     fecha: str | None = None) -> tuple[bool, str]:
    from repositories import matricula_repository

    estudiante = estudiante_repository.obtener_por_id(id_estudiante)
    if not estudiante:
        return False, "Estudiante no encontrado"

    if estudiante["estado"] == STATUS_RETIRADO:
        return False, "El estudiante ya está retirado"

    estudiante_repository.cambiar_estado(
        id_estudiante, STATUS_RETIRADO, (fecha or "").strip() or get_today())

    # Cerrar las matriculas activas para permitir una nueva matricula al reingresar
    for m in matricula_repository.obtener_por_estudiante(id_estudiante):
        if m["estado"] == STATUS_ACTIVO:
            matricula_repository.cambiar_estado(m["id_matricula"], STATUS_RETIRADO)
            auditoria_service.registrar_update(
                id_usuario=id_usuario,
                tabla="matricula",
                id_registro=m["id_matricula"],
                valores_anteriores=f"estado={STATUS_ACTIVO}",
                valores_nuevos=f"estado={STATUS_RETIRADO}",
            )

    auditoria_service.registrar_update(
        id_usuario=id_usuario,
        tabla="estudiante",
        id_registro=id_estudiante,
        valores_anteriores=f"estado={estudiante['estado']}",
        valores_nuevos=f"estado={STATUS_RETIRADO}",
    )

    logger.info(f"Estudiante retirado: ID={id_estudiante}")
    return True, "Retiro registrado correctamente"


def registrar_reingreso(id_estudiante: int, id_usuario: int = 1) -> tuple[bool, str]:
    estudiante = estudiante_repository.obtener_por_id(id_estudiante)
    if not estudiante:
        return False, "Estudiante no encontrado"

    if estudiante["estado"] != STATUS_RETIRADO:
        return False, "Solo pueden reingresar estudiantes retirados"

    estudiante_repository.cambiar_estado(id_estudiante, STATUS_REINGRESANTE)

    auditoria_service.registrar_update(
        id_usuario=id_usuario,
        tabla="estudiante",
        id_registro=id_estudiante,
        valores_anteriores=f"estado={STATUS_RETIRADO}",
        valores_nuevos=f"estado={STATUS_REINGRESANTE}",
    )

    logger.info(f"Estudiante reingreso: ID={id_estudiante}")
    return True, "Reingreso registrado correctamente"


def desactivar_estudiante(id_estudiante: int, id_usuario: int = 1) -> tuple[bool, str]:
    """Soft delete del estudiante (activo=0) con registro de auditoria."""
    estudiante = estudiante_repository.obtener_por_id(id_estudiante)
    if not estudiante:
        return False, "Estudiante no encontrado"

    if estudiante["activo"] == 0:
        return False, "El estudiante ya está desactivado"

    estudiante_repository.soft_delete(id_estudiante)

    auditoria_service.registrar_desactivacion(
        id_usuario=id_usuario,
        tabla="estudiante",
        id_registro=id_estudiante,
        valores_anteriores="activo=1",
        valores_nuevos="activo=0",
    )

    logger.info(f"Estudiante desactivado: ID={id_estudiante}")
    return True, "Estudiante desactivado correctamente"


def asociar_apoderado(id_estudiante: int, id_apoderado: int,
                      es_principal: bool = False, id_usuario: int = 1) -> tuple[bool, str]:
    return apoderado_service.asociar_a_estudiante(
        id_estudiante, id_apoderado, es_principal, id_usuario
    )


def desasociar_apoderado(id_estudiante: int, id_apoderado: int,
                         id_usuario: int = 1) -> tuple[bool, str]:
    return apoderado_service.desasociar_de_estudiante(id_estudiante, id_apoderado)


def listar_estudiantes(activo: int | None = None, estado: str | None = None) -> list[dict]:
    return estudiante_repository.obtener_todos(activo=activo, estado=estado)


def obtener_estudiante(id_estudiante: int) -> dict | None:
    return estudiante_repository.obtener_por_id_con_persona(id_estudiante)


def obtener_apoderados_por_estudiante(id_estudiante: int) -> list[dict]:
    return estudiante_apoderado_repository.obtener_por_estudiante(id_estudiante)


def tiene_apoderado_principal(id_estudiante: int) -> bool:
    return estudiante_apoderado_repository.tiene_principal(id_estudiante)
