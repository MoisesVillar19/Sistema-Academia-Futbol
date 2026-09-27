"""Tests adicionales del servicio de estudiantes: listado y edicion."""
from services import estudiante_service
from repositories import persona_repository


def test_crear_y_obtener_estudiante_con_persona(crear_persona):
    id_persona = crear_persona(dni="61111222", nombres="Carlos", apellidos="Rojas")
    exito, msg, id_est = estudiante_service.crear_estudiante({
        "dni": "61111222",
    })
    assert exito is True

    est = estudiante_service.obtener_estudiante(id_est)
    assert est is not None
    assert est["id_persona"] == id_persona
    assert est["estado"] == "ACTIVO"


def test_listar_filtros_activo(crear_estudiante):
    id_est1 = crear_estudiante()
    crear_estudiante()
    estudiante_service.registrar_retiro(id_est1)

    activos = estudiante_service.listar_estudiantes(activo=1)
    inactivos = estudiante_service.listar_estudiantes(activo=0)

    assert all(e["activo"] == 1 for e in activos)
    assert any(e["id_estudiante"] == id_est1 for e in inactivos)


def test_listar_filtro_estado(crear_estudiante):
    id_retirado = crear_estudiante()
    estudiante_service.registrar_retiro(id_retirado)

    retirados = estudiante_service.listar_estudiantes(estado="RETIRADO")
    assert any(e["id_estudiante"] == id_retirado for e in retirados)


def test_editar_estudiante_persiste_cambios(crear_estudiante):
    id_est = crear_estudiante(dni="62222333", nombres="NombreOriginal")

    exito, msg = estudiante_service.editar_estudiante(id_est, {"nombres": "NombreEditado"})
    assert exito is True, msg

    est = estudiante_service.obtener_estudiante(id_est)
    persona = persona_repository.obtener_por_id(est["id_persona"])
    assert persona["nombres"] == "NombreEditado"


def test_editar_estudiante_registra_auditoria(usuario_admin, crear_estudiante):
    from services import auditoria_service
    id_est = crear_estudiante()

    estudiante_service.editar_estudiante(id_est, {"nombres": "Auditado"})

    logs = auditoria_service.obtener_logs_por_tabla("persona")
    assert any(l["accion"] == "UPDATE" for l in logs)


def test_editar_dni_duplicado_rechazado(crear_estudiante):
    crear_estudiante(dni="63333444")
    id_est2 = crear_estudiante(dni="64444555")

    est2 = estudiante_service.obtener_estudiante(id_est2)
    exito, msg = estudiante_service.editar_estudiante(id_est2, {"dni": "63333444"})
    assert exito is False
    assert "ya está registrado" in msg.lower()

    persona = persona_repository.obtener_por_id(est2["id_persona"])
    assert persona["dni"] == "64444555"
