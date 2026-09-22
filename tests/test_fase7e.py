"""Fase 7e: auditoría cards, fin de conceptos, acceso filtrado a Tarifas."""
import pytest

pytestmark = pytest.mark.ui


def _textos(w):
    out = []
    vistos = set()

    def _rec(x):
        try:
            key = str(x)
        except Exception:
            return
        if key in vistos:
            return
        vistos.add(key)
        try:
            t = x.cget("text")
            if t:
                out.append(str(t))
        except Exception:
            pass
        try:
            hijos = x.winfo_children()
        except Exception:
            return
        for h in hijos:
            _rec(h)

    _rec(w)
    return " ".join(out)


def test_auditoria_cards(crear_vista, usuario_admin):
    from views.auditoria.auditoria_view import AuditoriaView
    vista = crear_vista(AuditoriaView)
    vista.update_idletasks()
    todo = _textos(vista)
    assert "Fecha" in todo and "LOGIN" in todo
    assert "Ver" in todo


def test_conceptos_fuera_de_config(crear_vista, usuario_admin):
    from views.configuracion.configuracion_view import ConfiguracionView
    vista = crear_vista(ConfiguracionView)
    vista.update_idletasks()
    assert "Conceptos Flexibles" not in _textos(vista)


def test_conceptos_fuera_de_matricula(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    assert not hasattr(vista, "combo_concepto")


def test_service_ignora_id_concepto(crear_estudiante, obtener_tarifa):
    from services import matricula_service
    id_tarifa, monto = obtener_tarifa(monto=130.0)
    ok, _, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": 130.0, "dia_vencimiento": 5, "id_concepto": 999999,
    })
    assert ok
    from repositories import matricula_repository
    assert float(matricula_repository.obtener_por_id(id_mat)["monto_pactado"]) == 130.0


def test_tarifas_tab_y_filtro(crear_vista, usuario_admin):
    from views.tarifas.tarifa_view import TarifaView
    vista = crear_vista(TarifaView)
    vista2 = None
    try:
        import customtkinter as ctk
        vista2 = TarifaView(vista.master, tab_inicial="Becas", filtro_tipo="ACADEMIA")
        vista2.pack(fill="both", expand=True)
        vista.update_idletasks()
        assert vista2.tabview.get() == "Becas"
        assert vista2._filtro_tipo == "ACADEMIA"
        vista2.tabview.set("Tarifas")
        vista.update_idletasks()
        todo = _textos(vista2)
        assert "[SERVICIO]" not in todo and "[CAMPEONATO]" not in todo
    finally:
        try:
            if vista2 is not None:
                vista2.destroy()
        except Exception:
            pass


def test_evento_abrir_tarifas_inofensivo():
    from utils import event_bus
    event_bus.publish("abrir_tarifas", tab="Tarifas", tipo="ACADEMIA")
