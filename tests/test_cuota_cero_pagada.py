"""G1: cuota con monto 0 nace/recaculada PAGADA (beca completa)."""
from repositories import cuota_repository


def test_crear_cuota_cero_es_pagada(crear_matricula):
    from services import cuota_service
    m = crear_matricula()
    id_c = cuota_service.crear_cuota(m["id_matricula"], 0, "2026-09-01", "2026-09")
    c = cuota_repository.obtener_por_id(id_c)
    assert c["estado"] == "PAGADO" and c["saldo"] == 0
    # fuera de vencidas y pinta X
    assert all(x["id_cuota"] != id_c for x in cuota_repository.obtener_vencidas())


def test_recalcula_a_cero_paga(crear_matricula):
    from services import matricula_service
    from repositories import beca_repository, cuota_repository
    from models.beca import Beca
    m = crear_matricula(monto_pactado=100.0)
    bid = beca_repository.insertar(Beca(nombre="Completa QA", tipo="PORCENTAJE",
                                        valor=100.0, activo=1))
    ok, _ = matricula_service.asignar_beca(m["id_matricula"], bid, "QA")
    assert ok
    cuotas = cuota_repository.obtener_por_matricula(m["id_matricula"])
    assert cuotas and all(c["saldo"] == 0 and c["estado"] == "PAGADO" for c in cuotas), cuotas


def test_cuota_normal_sigue_pendiente(crear_matricula):
    from services import cuota_service
    from repositories import cuota_repository
    m = crear_matricula()
    id_c = cuota_service.crear_cuota(m["id_matricula"], 100.0, "2026-09-01", "2026-09")
    assert cuota_repository.obtener_por_id(id_c)["estado"] == "PENDIENTE"
