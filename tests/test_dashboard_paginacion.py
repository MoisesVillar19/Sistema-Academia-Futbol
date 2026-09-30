"""Dashboard: tablas de detalle paginadas (no cortadas en 30)."""
import pytest

pytestmark = pytest.mark.ui


def test_tabla_cards_pagina(crear_vista, usuario_admin, ctk_root):
    import customtkinter as ctk
    from views.dashboard.dashboard_view import crear_tabla_cards
    cont = ctk.CTkFrame(ctk_root)
    cont.pack()
    try:
        filas = [[f"Est {i}", f"DNI{i}", f"S/{i}.00"] for i in range(65)]
        crear_tabla_cards(cont, [("E", 150), ("D", 80), ("S", 80)], filas)
        ctk_root.update_idletasks()

        def _textos(w):
            out = []
            try:
                t = w.cget("text")
                if t:
                    out.append(str(t))
            except Exception:
                pass
            for ch in w.winfo_children():
                out += _textos(ch)
            return out

        todo = " ".join(_textos(cont))
        assert "Página 1 de 3" in todo, todo
        assert "Est 0" in todo and "Est 64" not in todo
        # avanzar a página 2
        for w in cont.winfo_children():
            for ch in w.winfo_children():
                for b in ch.winfo_children():
                    try:
                        if b.cget("text") == ">":
                            b.invoke()
                    except Exception:
                        pass
        ctk_root.update_idletasks()
        todo2 = " ".join(_textos(cont))
        assert "Página 2 de 3" in todo2, todo2
        assert "Est 30" in todo2 and "Est 0" not in todo2
    finally:
        cont.destroy()


def test_tabla_corta_sin_barra(crear_vista, usuario_admin, ctk_root):
    import customtkinter as ctk
    from views.dashboard.dashboard_view import crear_tabla_cards
    cont = ctk.CTkFrame(ctk_root)
    cont.pack()
    try:
        crear_tabla_cards(cont, [("E", 150)], [["a"], ["b"]])
        ctk_root.update_idletasks()

        def _textos(w):
            out = []
            try:
                t = w.cget("text")
                if t:
                    out.append(str(t))
            except Exception:
                pass
            for ch in w.winfo_children():
                out += _textos(ch)
            return out

        assert "Página" not in " ".join(_textos(cont))
    finally:
        cont.destroy()
