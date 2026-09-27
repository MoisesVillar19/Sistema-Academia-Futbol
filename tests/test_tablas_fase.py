"""E4b: toggles y tablas (Morosos, Tarifas/Becas)."""
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
            for h in x.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(w)
    return " ".join(out)


def test_morosos_tabla(crear_vista, usuario_admin, crear_matricula):
    from views.pagos.pago_view import PagoView
    from services import cuota_service
    m = crear_matricula()
    cuotas = cuota_service.obtener_cuotas_por_matricula(m["id_matricula"])
    from repositories import cuota_repository
    from models.cuota import Cuota
    c = cuotas[0]
    cuota_repository.actualizar(Cuota(**{**c, "fecha_vencimiento": "2020-01-01"}))
    cuota_service.actualizar_estados_vencidos()
    vista = crear_vista(PagoView)
    vista.tabview.set("Morosos")
    vista._cargar_morosos()
    vista.update_idletasks()
    todo = _textos(vista.scroll_morosos)
    assert "Saldo" in todo


def test_tarifas_toggle(crear_vista, usuario_admin):
    from views.tarifas.tarifa_view import TarifaView
    vista = crear_vista(TarifaView)
    vista.update_idletasks()
    assert vista.seg_vista.get() == "Tabla"
    todo = _textos(vista.scroll)
    assert "Monto" in todo
    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()


def test_becas_toggle(crear_vista, usuario_admin):
    from views.tarifas.tarifa_view import TarifaView
    vista = crear_vista(TarifaView)
    vista.tabview.set("Becas")
    vista.update_idletasks()
    todo = _textos(vista.scroll_becas)
    assert "Tipo" in todo and "Valor" in todo
    vista._on_vista_becas_cambiar("Cards")
    vista.update_idletasks()
