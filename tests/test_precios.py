"""Fase 4: precios Excel (express lee tarifa, presets de beca, uniforme 70)."""
import pytest

pytestmark = pytest.mark.ui

from services import matricula_service
from repositories import tarifa_repository, producto_repository
from database.connection import fetch_one


def test_express_default_lee_tarifa_inscripcion():
    # seed fresco: Inscripción = 150
    assert matricula_service.monto_express_nuevo_default() == 150.0
    ok, msg, ids = matricula_service.matricula_express({
        "tipo": "NUEVO", "nombres": "Precio", "apellidos": "Defecto",
        "dni": "71717174", "metodo_pago": "EFECTIVO",
    })
    assert ok, msg
    from repositories import matricula_repository
    assert float(matricula_repository.obtener_por_id(ids["id_matricula"])["monto_pactado"]) == 150.0


def test_express_default_sigue_cambios_tarifa():
    from database.connection import get_connection
    conn = get_connection()
    row = fetch_one("SELECT id_tarifa FROM tarifa WHERE nombre = 'Inscripción' LIMIT 1")
    conn.execute("UPDATE tarifa SET monto = 200 WHERE id_tarifa = ?", (row["id_tarifa"],))
    conn.commit()
    assert matricula_service.monto_express_nuevo_default() == 200.0
    # monto explícito sigue mandando
    ok, msg, ids = matricula_service.matricula_express({
        "tipo": "NUEVO", "nombres": "Precio", "apellidos": "Explicito",
        "dni": "71717175", "monto": "99.00", "metodo_pago": "EFECTIVO",
    })
    assert ok, msg
    from repositories import matricula_repository
    assert float(matricula_repository.obtener_por_id(ids["id_matricula"])["monto_pactado"]) == 99.0


def test_uniforme_seed_70_y_editable():
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    assert prod is not None
    assert float(prod["precio_venta"]) == 70.0
    # editable (Fase 6 lo moverá a Tienda; el service ya lo permite)
    from services import inventario_service
    ok, _ = inventario_service.editar_producto(prod["id_producto"], {"precio_venta": 75.0})
    assert ok
    assert float(producto_repository.obtener_por_codigo("CAMISETA-ENT")["precio_venta"]) == 75.0


def test_preset_media_beca_aplica(crear_estudiante, obtener_tarifa):
    from repositories import cuota_repository
    media = fetch_one("SELECT id_beca FROM beca WHERE nombre = '1/2 BECA'")
    completa = fetch_one("SELECT id_beca FROM beca WHERE nombre = 'BECA COMPLETA'")
    assert media and completa
    id_tarifa, _ = obtener_tarifa(monto=120.0)
    ok, _, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": 120.0, "dia_vencimiento": 5,
        "becas": [{"id_beca": media["id_beca"]}],
    })
    assert ok
    cuotas = cuota_repository.obtener_por_matricula(id_mat)
    assert cuotas
    assert float(cuotas[0]["monto_total"]) == 70.0  # 120 - 50 fijo
    ok, _, id_mat2 = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": 120.0, "dia_vencimiento": 5,
        "becas": [{"id_beca": completa["id_beca"]}],
    })
    assert ok
    cuotas2 = cuota_repository.obtener_por_matricula(id_mat2)
    assert float(cuotas2[0]["monto_total"]) == 0.0  # 100%


def test_vista_express_muestra_default(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    assert "150" in vista.label_exp_panel.cget("text")
    assert vista.entry_exp_monto.get() == "150.00"
