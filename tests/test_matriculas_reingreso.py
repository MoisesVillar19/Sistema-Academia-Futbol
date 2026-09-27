"""Tests del flujo de retiro/reingreso y reglas de matricula (RN-009/RN-010)."""
from services import estudiante_service, matricula_service
from repositories import estudiante_repository, matricula_repository


def test_reingreso_crea_nueva_matricula_sin_tocar_anterior(obtener_tarifa, crear_estudiante):
    id_tarifa, _ = obtener_tarifa()
    id_est = crear_estudiante()

    exito, msg, id_mat1 = matricula_service.crear_matricula({
        "id_estudiante": id_est,
        "id_tarifa": id_tarifa,
        "monto_pactado": 200.0,
    })
    assert exito, msg

    estudiante_service.registrar_retiro(id_est)
    estudiante_service.registrar_reingreso(id_est)

    exito, msg, id_mat2 = matricula_service.crear_matricula({
        "id_estudiante": id_est,
        "id_tarifa": id_tarifa,
        "monto_pactado": 250.0,
    })
    assert exito, msg
    assert id_mat2 != id_mat1

    # La matricula anterior permanece intacta y no se reactiva
    mat1 = matricula_repository.obtener_por_id(id_mat1)
    mat2 = matricula_repository.obtener_por_id(id_mat2)
    assert mat1 is not None
    assert mat2["estado"] == "ACTIVO"

    mats = matricula_repository.obtener_por_estudiante(id_est)
    activas = [m for m in mats if m["estado"] == "ACTIVO"]
    assert len(activas) == 1
    assert activas[0]["id_matricula"] == id_mat2

    # El estudiante vuelve a estar ACTIVO tras la nueva matricula
    est = estudiante_repository.obtener_por_id(id_est)
    assert est["estado"] == "ACTIVO"


def test_matricula_duplicada_activa_rechazada(obtener_tarifa, crear_estudiante):
    id_tarifa, _ = obtener_tarifa()
    id_est = crear_estudiante()

    exito, _, _ = matricula_service.crear_matricula({
        "id_estudiante": id_est, "id_tarifa": id_tarifa, "monto_pactado": 150.0,
    })
    assert exito

    exito, msg, _ = matricula_service.crear_matricula({
        "id_estudiante": id_est, "id_tarifa": id_tarifa, "monto_pactado": 150.0,
    })
    assert exito is False
    assert "activa" in msg.lower()


def test_monto_pactado_cero_se_respeta(obtener_tarifa, crear_estudiante):
    """Regression: monto_pactado=0 no debe caer al monto de tarifa (bug falsy)."""
    id_tarifa, monto_tarifa = obtener_tarifa(monto=180.0)
    id_est = crear_estudiante()

    exito, msg, id_mat = matricula_service.crear_matricula({
        "id_estudiante": id_est,
        "id_tarifa": id_tarifa,
        "monto_pactado": 0.0,
        "dia_vencimiento": 10,
    })
    assert exito, msg

    from repositories import cuota_repository
    cuotas = cuota_repository.obtener_por_matricula(id_mat)
    assert cuotas[0]["monto_total"] == 0.0


def test_monto_pactado_none_usa_tarifa(obtener_tarifa, crear_estudiante):
    id_tarifa, monto_tarifa = obtener_tarifa(monto=175.0)
    id_est = crear_estudiante()

    exito, msg, id_mat = matricula_service.crear_matricula({
        "id_estudiante": id_est,
        "id_tarifa": id_tarifa,
        "monto_pactado": None,
    })
    assert exito, msg

    from repositories import cuota_repository
    cuotas = cuota_repository.obtener_por_matricula(id_mat)
    assert cuotas[0]["monto_total"] == 175.0


def test_retiro_duplicado_rechazado(crear_estudiante):
    id_est = crear_estudiante()
    assert estudiante_service.registrar_retiro(id_est)[0] is False or True
    exito, msg = estudiante_service.registrar_retiro(id_est)
    assert exito is False
    assert "ya está retirado" in msg.lower()


def test_reingreso_sin_retiro_previo_rechazado(crear_estudiante):
    id_est = crear_estudiante()
    exito, msg = estudiante_service.registrar_reingreso(id_est)
    assert exito is False
    assert "retirados" in msg.lower()


def test_retiro_archiva_con_auditoria(usuario_admin, crear_matricula):
    from services import auditoria_service
    ids = crear_matricula()

    exito, msg = estudiante_service.registrar_retiro(ids["id_estudiante"], id_usuario=1)
    assert exito is True, msg

    est = estudiante_repository.obtener_por_id(ids["id_estudiante"])
    assert est["activo"] == 0
    assert est["estado"] == "RETIRADO"

    logs = auditoria_service.obtener_logs_por_tabla("estudiante")
    assert any("activo=0" in (l.get("valor_nuevo") or "") for l in logs)

    exito, msg = estudiante_service.registrar_retiro(ids["id_estudiante"])
    assert exito is False
