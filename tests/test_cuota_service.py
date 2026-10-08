from services import cuota_service, matricula_service
from repositories import persona_repository, estudiante_repository
from models.persona import Persona
from models.estudiante import Estudiante
from models.tarifa import Tarifa
from database.connection import fetch_one
from utils.dates import get_today


_counter = 0

def _crear_estudiante_con_matricula():
    """Helper: crea persona, estudiante y matrícula. Retorna (id_estudiante, id_matricula)."""
    global _counter
    _counter += 1
    dni = f"770000{_counter:04d}"

    persona = Persona(
        id_persona=None, dni=dni, nombres="Test", apellidos="Cuota",
        fecha_nacimiento="2000-01-01", sexo="M", direccion="", telefono="", correo=""
    )
    id_persona = persona_repository.insertar(persona)

    estudiante = Estudiante(
        id_estudiante=None, id_persona=id_persona, estado="ACTIVO",
        fecha_ingreso=get_today(), fecha_retiro=None
    )
    id_estudiante = estudiante_repository.insertar(estudiante)

    from repositories.tarifa_repository import obtener_activas, insertar as insertar_tarifa
    tarifas = obtener_activas()
    if tarifas:
        id_tarifa = tarifas[0]["id_tarifa"]
    else:
        cat = fetch_one("SELECT id_categoria FROM categoria LIMIT 1")
        if not cat:
            return None, None
        tarifa = Tarifa(
            id_categoria=cat["id_categoria"],
            nombre="Tarifa Test",
            monto=200.0,
        )
        id_tarifa = insertar_tarifa(tarifa)

    exito, msg, id_matricula = matricula_service.crear_matricula({
        "id_estudiante": id_estudiante,
        "id_tarifa": id_tarifa,
        "monto_pactado": 200.0,
        "dia_vencimiento": 15,
    })
    if exito:
        return id_estudiante, id_matricula
    return id_estudiante, None


# --- Tests ---

def test_crear_cuota():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )
    assert id_cuota is not None
    assert id_cuota > 0


def test_crear_cuota_detalle():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=150.0,
        fecha_vencimiento="2026-09-15",
        periodo="2026-09"
    )

    cuota = cuota_service.obtener_cuota(id_cuota) if hasattr(cuota_service, 'obtener_cuota') else None
    from repositories import cuota_repository
    cuota = cuota_repository.obtener_por_id(id_cuota)

    assert cuota is not None
    assert cuota["monto_total"] == 150.0
    assert cuota["saldo"] == 150.0
    assert cuota["estado"] == "PENDIENTE"
    assert cuota["monto_pagado"] == 0


def test_actualizar_pago():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=200.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    exito, msg = cuota_service.actualizar_pago(id_cuota, 50.0)
    assert exito is True
    assert "50" in msg or "Saldo" in msg

    from repositories import cuota_repository
    cuota = cuota_repository.obtener_por_id(id_cuota)
    assert cuota["monto_pagado"] == 50.0
    assert cuota["saldo"] == 150.0
    assert cuota["estado"] == "PARCIAL"


def test_actualizar_pago_total():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    exito, msg = cuota_service.actualizar_pago(id_cuota, 100.0)
    assert exito is True

    from repositories import cuota_repository
    cuota = cuota_repository.obtener_por_id(id_cuota)
    assert cuota["monto_pagado"] == 100.0
    assert cuota["saldo"] == 0
    assert cuota["estado"] == "PAGADO"


def test_actualizar_pago_excede_saldo():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    exito, msg = cuota_service.actualizar_pago(id_cuota, 150.0)
    assert exito is False
    assert "excede" in msg.lower()


def test_actualizar_pago_cuota_no_existe():
    exito, msg = cuota_service.actualizar_pago(99999, 50.0)
    assert exito is False
    assert "no encontrada" in msg.lower() or "no existe" in msg.lower()


def test_contar_por_estado():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    total = cuota_service.contar_por_estado("PENDIENTE")
    assert total >= 1


def test_obtener_cuotas_por_matricula():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    cuotas = cuota_service.obtener_cuotas_por_matricula(id_mat)
    assert isinstance(cuotas, list)
    assert len(cuotas) >= 1


def test_obtener_cuotas_pendientes():
    id_est, id_mat = _crear_estudiante_con_matricula()
    assert id_mat is not None

    cuota_service.crear_cuota(
        id_matricula=id_mat,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )

    cuotas = cuota_service.obtener_cuotas_pendientes(id_mat)
    assert isinstance(cuotas, list)
    assert len(cuotas) >= 1
    for cuota in cuotas:
        assert cuota["estado"] in ("PENDIENTE", "PARCIAL", "VENCIDO")


def test_obtener_vencidas():
    result = cuota_service.obtener_vencidas()
    assert isinstance(result, list)


def test_obtener_por_vencer():
    result = cuota_service.obtener_por_vencer(dias=7)
    assert isinstance(result, list)


def test_editar_cuota_corrige_monto_y_recalcula_saldo():
    from repositories import cuota_repository
    id_est, id_mat = _crear_estudiante_con_matricula()
    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat, monto_total=100.0,
        fecha_vencimiento='2026-08-15', periodo='2026-08')
    ok, msg = cuota_service.editar_cuota(id_cuota, {'monto_total': 150.0})
    assert ok, msg
    c = cuota_repository.obtener_por_id(id_cuota)
    assert c['monto_total'] == 150.0 and c['saldo'] == 150.0


def test_editar_cuota_rechaza_total_menor_a_pagado():
    from repositories import cuota_repository
    id_est, id_mat = _crear_estudiante_con_matricula()
    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat, monto_total=100.0,
        fecha_vencimiento='2026-08-15', periodo='2026-08')
    cuota_service.actualizar_pago(id_cuota, 40.0)
    ok, msg = cuota_service.editar_cuota(id_cuota, {'monto_total': 30.0})
    assert not ok and 'pagado' in msg.lower()
    ok, msg = cuota_service.editar_cuota(
        id_cuota, {'monto_total': 120.0, 'estado': 'PARCIAL'})
    assert ok, msg
    c = cuota_repository.obtener_por_id(id_cuota)
    assert c['saldo'] == 80.0 and c['estado'] == 'PARCIAL'


def test_editar_cuota_fecha_invalida():
    id_est, id_mat = _crear_estudiante_con_matricula()
    id_cuota = cuota_service.crear_cuota(
        id_matricula=id_mat, monto_total=100.0,
        fecha_vencimiento='2026-08-15', periodo='2026-08')
    ok, _ = cuota_service.editar_cuota(id_cuota, {'fecha_vencimiento': 'no-fecha'})
    assert not ok
