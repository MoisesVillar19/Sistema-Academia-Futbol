"""Tests de la regla de multiples becas segun CONFIGURACION (RN-012)."""
from services import beca_service, configuracion_service, matricula_service
from repositories import cuota_repository, matricula_beca_repository


def _crear_beca(nombre, tipo="PORCENTAJE", valor=10):
    exito, msg, id_beca = beca_service.crear_beca({
        "nombre": nombre, "tipo": tipo, "valor": valor,
    })
    assert exito, msg
    return id_beca


def test_multiples_becas_permitidas_por_defecto(obtener_tarifa, crear_estudiante):
    id_tarifa, _ = obtener_tarifa(monto=200.0)
    b1 = _crear_beca("Hermanos", valor=10)
    b2 = _crear_beca("Pronto pago", valor=5)

    exito, msg, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(),
        "id_tarifa": id_tarifa,
        "becas": [{"id_beca": b1}, {"id_beca": b2}],
    })
    assert exito is True, msg

    # 200 - 10% - 5% = 171
    cuota = cuota_repository.obtener_por_matricula(id_mat)[0]
    assert cuota["monto_total"] == 171.0


def test_una_sola_beca_cuando_config_lo_prohibe(obtener_tarifa, crear_estudiante):
    configuracion_service.actualizar_configuracion({"permitir_multiples_becas": 0})
    id_tarifa, _ = obtener_tarifa(monto=200.0)
    b1 = _crear_beca("Beca A", valor=20)
    b2 = _crear_beca("Beca B", valor=10)

    exito, msg, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(),
        "id_tarifa": id_tarifa,
        "becas": [{"id_beca": b1}, {"id_beca": b2}],
    })
    assert exito is False
    assert "múltiples becas" in msg.lower() or "multiples becas" in msg.lower()


def test_segunda_beca_prohibida_por_config(obtener_tarifa, crear_matricula):
    """Regression RN-012: la segunda beca debe rechazarse si config lo prohibe."""
    configuracion_service.actualizar_configuracion({"permitir_multiples_becas": 0})
    ids = crear_matricula()
    b1 = _crear_beca("Primera", valor=10)
    b2 = _crear_beca("Segunda", valor=15)

    exito, msg = matricula_service.asignar_beca(ids["id_matricula"], b1)
    assert exito is True, msg

    exito, msg = matricula_service.asignar_beca(ids["id_matricula"], b2)
    assert exito is False


def test_asignar_primera_beca_siempre_permitida(obtener_tarifa, crear_matricula):
    configuracion_service.actualizar_configuracion({"permitir_multiples_becas": 0})
    ids = crear_matricula()
    nueva = _crear_beca("Unica", valor=15)

    exito, msg = matricula_service.asignar_beca(ids["id_matricula"], nueva)
    assert exito is True, msg


def test_beca_monto_fijo_descuenta(obtener_tarifa, crear_estudiante):
    id_tarifa, _ = obtener_tarifa(monto=200.0)
    b = _crear_beca("Descuento fijo", tipo="MONTO_FIJO", valor=50)

    exito, msg, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(),
        "id_tarifa": id_tarifa,
        "becas": [{"id_beca": b}],
    })
    assert exito

    cuota = cuota_repository.obtener_por_matricula(id_mat)[0]
    assert cuota["monto_total"] == 150.0


def test_desasignar_beca(obtener_tarifa, crear_matricula):
    ids = crear_matricula()
    b = _crear_beca("Temporal", valor=10)

    assert matricula_service.asignar_beca(ids["id_matricula"], b)[0] is True
    exito, msg = matricula_service.desasignar_beca(ids["id_matricula"], b)
    assert exito is True

    activas = [x for x in matricula_beca_repository.obtener_por_matricula(ids["id_matricula"])
               if x.get("activo", 1)]
    assert len(activas) == 0


def test_asignar_beca_inexistente_rechazada(crear_matricula):
    ids = crear_matricula()
    exito, msg = matricula_service.asignar_beca(ids["id_matricula"], 99999)
    assert exito is False

def test_beca_crud_admin(usuario_admin):
    from controllers import beca_controller
    exito, msg, bid = beca_controller.crear_beca(
        {"nombre": "Beca QA", "tipo": "PORCENTAJE", "valor": 15, "observacion": "t"})
    assert exito is True, msg
    assert any(b["id_beca"] == bid for b in beca_controller.listar_becas())
    exito, msg = beca_controller.editar_beca(bid, {"valor": 20})
    assert exito is True, msg
    exito, msg = beca_controller.desactivar_beca(bid)
    assert exito is True, msg
    assert all(b["id_beca"] != bid for b in beca_controller.listar_becas())
    assert any(b["id_beca"] == bid for b in beca_controller.listar_todas())
    exito, msg = beca_controller.activar_beca(bid)
    assert exito is True, msg
    assert any(b["id_beca"] == bid for b in beca_controller.listar_becas())


def test_beca_secretaria_gestiona_con_permiso_tarifas(usuario_secretaria):
    from controllers import beca_controller
    exito, _, bid = beca_controller.crear_beca(
        {"nombre": "X", "tipo": "PORCENTAJE", "valor": 5})
    assert exito is True
    exito, _ = beca_controller.desactivar_beca(bid)
    assert exito is True


def test_beca_sin_permiso_tarifas_rechazada(usuario_admin):
    from controllers import beca_controller, usuario_controller
    from services import usuario_service, auth_service
    exito, _, bid = beca_controller.crear_beca(
        {"nombre": "Y", "tipo": "PORCENTAJE", "valor": 5})
    assert exito is True
    exito, msg = usuario_controller.guardar_permisos_rol(
        "SECRETARIA", ["dashboard", "pagos"])
    assert exito is True
    exito, temp, _ = usuario_service.crear_usuario(
        {"dni": "90909090", "nombres": "S", "apellidos": "T"}, "sec_sin_tar", "SECRETARIA")
    assert exito, temp
    auth_service.logout()
    assert auth_service.login("sec_sin_tar", temp) is not None
    assert auth_service.tiene_permiso("tarifas") is False
    exito, _ = beca_controller.desactivar_beca(bid)
    assert exito is False
    exito, _, _ = beca_controller.crear_beca(
        {"nombre": "Z", "tipo": "PORCENTAJE", "valor": 5})
    assert exito is False


def test_beca_validaciones(usuario_admin):
    from controllers import beca_controller
    exito, _, _ = beca_controller.crear_beca({"nombre": "", "tipo": "PORCENTAJE", "valor": 5})
    assert exito is False
    exito, _, _ = beca_controller.crear_beca({"nombre": "X", "tipo": "RARO", "valor": 5})
    assert exito is False
    exito, _, _ = beca_controller.crear_beca({"nombre": "X", "tipo": "PORCENTAJE", "valor": 0})
    assert exito is False
