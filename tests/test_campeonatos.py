"""Pestaña Campeonatos: inscripcion por division + resumen + arbitraje vinculado."""
import pytest

pytestmark = pytest.mark.ui

from controllers import venta_controller, egreso_controller, tarifa_controller


def _tarifa_camp():
    tarifas = tarifa_controller.listar_tarifas_activas(tipo="CAMPEONATO")
    assert tarifas
    return tarifas[0]


def test_egreso_con_division(usuario_admin):
    t = _tarifa_camp()
    exito, msg, eid = egreso_controller.registrar_egreso({
        "concepto": "ARBITRAJE", "monto": 45.0, "fecha": "2026-09-01",
        "responsable": "Arbitro QA", "id_tarifa": t["id_tarifa"],
    })
    assert exito is True, msg
    from repositories import egreso_repository
    e = egreso_repository.obtener_por_id(eid)
    assert e["id_tarifa"] == t["id_tarifa"]


def test_resumen_campeonatos(usuario_admin, crear_matricula):
    from controllers import venta_controller as vc
    t = _tarifa_camp()
    exito, msg, _ = vc.registrar_venta({
        "tipo_venta": "CAMPEONATO", "metodo_pago": "EFECTIVO",
        "items": [], "id_tarifa": t["id_tarifa"], "monto_total": 150.0,
    })
    assert exito is True, msg
    exito, msg, _ = egreso_controller.registrar_egreso({
        "concepto": "ARBITRAJE", "monto": 50.0, "fecha": "2026-09-02",
        "id_tarifa": t["id_tarifa"],
    })
    assert exito is True, msg
    resumen = vc.resumen_campeonatos()
    fila = next(r for r in resumen if r["tarifa"]["id_tarifa"] == t["id_tarifa"])
    assert fila["ventas"] >= 1
    assert fila["recaudado"] >= 150.0
    assert fila["arbitraje"] >= 50.0
    assert fila["neto"] == round(fila["recaudado"] - fila["arbitraje"], 2)


def test_campeonato_inscribe_estudiante(usuario_admin, crear_estudiante):
    from controllers import venta_controller as vc
    t = _tarifa_camp()
    id_est = crear_estudiante()
    exito, msg, vid = vc.registrar_venta({
        "id_estudiante": id_est, "tipo_venta": "CAMPEONATO", "metodo_pago": "YAPE",
        "items": [], "id_tarifa": t["id_tarifa"], "monto_total": 150.0,
    })
    assert exito is True, msg
    resumen = vc.resumen_campeonatos()
    fila = next(r for r in resumen if r["tarifa"]["id_tarifa"] == t["id_tarifa"])
    assert fila["inscritos"] >= 1


def test_tab_campeonatos_render(crear_vista, usuario_admin):
    from views.campeonatos.campeonato_view import CampeonatoView
    vista = crear_vista(CampeonatoView)
    assert vista.winfo_exists()
