"""Cards estáticas: sin cambio visual en hover (evita parpadeo/blancos en scroll)."""
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
        c._hover_enter() if hasattr(c, "_hover_enter") else None
        c.update_idletasks()
        # Estática: el hover NO debe alterar borde ni ancho
        assert c.cget("border_color") == normal
        assert c.cget("border_width") == 1
    finally:
        card.destroy()


def test_aplicar_hover_no_revienta(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import aplicar_hover_borde
    card = ctk.CTkFrame(ctk_root)
    card.pack()
    try:
        aplicar_hover_borde(card)
        normal = card.cget("border_color")
        card.event_generate("<Enter>")
        card.event_generate("<Leave>")
        card.update_idletasks()
        # Estática: ni los eventos ni los ganchos alteran el borde
        assert card.cget("border_color") == normal
        card._hover_enter()
        card._hover_leave()
        card.update_idletasks()
        assert card.cget("border_color") == normal
    finally:
        card.destroy()


def test_bind_click_unico_dispara_una_vez(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import bind_click_unico
    cont = ctk.CTkFrame(ctk_root)
    cont.pack()
    try:
        card = ctk.CTkFrame(cont)
        card.pack()
        lbl = ctk.CTkLabel(card, text="hola")
        lbl.pack()
        llamadas = []
        bind_click_unico(card, lambda: llamadas.append(1))
        card.update_idletasks()

        class _Ev:
            serial = 424242

        # mismo evento físico invocado en 2 niveles → 1 solo disparo
        card._click_unico(_Ev())
        lbl._click_unico(_Ev())
        # otro evento físico → dispara de nuevo
        otro = _Ev()
        otro.serial = 777
        lbl._click_unico(otro)
        assert len(llamadas) == 2, llamadas
    finally:
        cont.destroy()


def test_dashboard_cards_con_hover(crear_vista, usuario_admin):
    from views.dashboard.dashboard_view import DashboardView
    vista = crear_vista(DashboardView)
    vista.update_idletasks()
