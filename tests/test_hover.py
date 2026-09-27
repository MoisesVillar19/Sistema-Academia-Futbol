"""Hover en cards: feedback de borde sin parpadeo (sin reflow)."""
import pytest

pytestmark = pytest.mark.ui


def test_card_hover_cambia_borde(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import crear_card_interactiva
    card = ctk.CTkFrame(ctk_root)
    card.pack()
    try:
        c = crear_card_interactiva(card)
        c.update_idletasks()
        normal = c.cget("border_color")
        c._hover_enter()
        c.update_idletasks()
        assert c.cget("border_color") != normal
        assert c.cget("border_width") == 1  # mismo ancho: sin reflow
        c.configure(border_color=normal)
    finally:
        card.destroy()


def test_aplicar_hover_no_revienta(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import aplicar_hover_borde
    card = ctk.CTkFrame(ctk_root)
    card.pack()
    try:
        aplicar_hover_borde(card)
        card.event_generate("<Enter>")
        card.event_generate("<Leave>")
        card.update_idletasks()
    finally:
        card.destroy()


def test_dashboard_cards_con_hover(crear_vista, usuario_admin):
    from views.dashboard.dashboard_view import DashboardView
    vista = crear_vista(DashboardView)
    vista.update_idletasks()
