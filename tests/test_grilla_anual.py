"""Fase 7d: grilla anual de cuotas estilo Excel."""
import pytest

pytestmark = pytest.mark.ui

from services import cuota_service, pago_service
from utils.dates import get_today


def test_grilla_muestra_pendiente_y_pagado(crear_matricula, usuario_admin):
    from repositories import cuota_repository
    m = crear_matricula()
    cuotas = cuota_repository.obtener_por_matricula(m["id_matricula"])
    assert cuotas
    anio = int(get_today()[:4])
    filas = cuota_service.grilla_anual(anio)
    assert len(filas) >= 1
    fila = filas[0]
    mes = int(cuotas[0]["fecha_vencimiento"][5:7])
    assert fila["meses"][mes]["estado"] in ("PENDIENTE", "VENCIDO", "PARCIAL")
    # pagar todo → X
    saldo = float(cuotas[0]["saldo"])
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": saldo, "metodo_pago": "EFECTIVO"})
    assert ok
    filas = cuota_service.grilla_anual(anio)
    assert filas[0]["meses"][mes]["estado"] == "PAGADO"


def test_grilla_parcial_muestra_saldo(crear_matricula, usuario_admin):
    from repositories import cuota_repository
    m = crear_matricula(monto_pactado=200.0)
    cuotas = cuota_repository.obtener_por_matricula(m["id_matricula"])
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": 50.0, "metodo_pago": "EFECTIVO"})
    assert ok
    anio = int(get_today()[:4])
    filas = cuota_service.grilla_anual(anio)
    mes = int(cuotas[0]["fecha_vencimiento"][5:7])
    celda = filas[0]["meses"][mes]
    assert celda["estado"] == "PARCIAL"
    assert celda["saldo"] == 150.0


def test_tab_grilla_en_vista(crear_vista, usuario_admin, crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    crear_matricula()
    vista = crear_vista(MatriculaView)
    vista.update_idletasks()
    assert vista.tab_grilla.winfo_exists()
    assert "X=cancelado" in vista.label_grilla_status.cget("text")
