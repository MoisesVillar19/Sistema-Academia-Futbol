"""Fase 7c: dashboard por bloques colapsables."""
import pytest

pytestmark = pytest.mark.ui


def _textos(w):
    out = []

    def _rec(x):
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


def test_bloques_presentes(crear_vista, usuario_admin):
    from views.dashboard.dashboard_view import DashboardView
    vista = crear_vista(DashboardView)
    vista.update_idletasks()
    todo = _textos(vista)
    for bloque in ("Academia", "Dinero", "Tienda", "Almac"):
        assert bloque in todo, bloque
    # cards clave siguen existiendo
    for card in ("Alumnos Activos", "Neto Mes", "Stock Bajo", "Pagos Hoy"):
        assert card in todo, card


def test_bloque_colapsa(crear_vista, usuario_admin):
    import customtkinter as ctk
    from views.dashboard.dashboard_view import DashboardView
    vista = crear_vista(DashboardView)
    vista.update_idletasks()

    def _botones(x):
        out = []
        try:
            if isinstance(x, ctk.CTkButton) and x.cget("text") in ("▾", "▸"):
                out.append(x)
        except Exception:
            pass
        try:
            for h in x.winfo_children():
                out.extend(_botones(h))
        except Exception:
            pass
        return out

    botones = _botones(vista)
    assert botones, "sin toggles de bloque"
    assert all(b.cget("text") == "▾" for b in botones)
    botones[0].invoke()
    vista.update_idletasks()
    assert botones[0].cget("text") == "▸"
