"""Fase 7a: helper crear_tabla_densa."""
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
    return out


def test_tabla_densa_header_y_filas(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import crear_tabla_densa
    cont = ctk.CTkFrame(ctk_root)
    cont.pack()
    try:
        crear_tabla_densa(
            cont, [("Código", 90), ("Nombre", 150)],
            [["A-1", "Uno"], ["A-2", ("Dos", {"text_color": "red"})]],
            detalles=[None, lambda f: ctk.CTkLabel(f, text="DETALLE-2").pack()],
        )
        ctk_root.update_idletasks()
        todo = " ".join(_textos(cont))
        for esperado in ("Código", "Nombre", "A-1", "Uno", "A-2", "Dos", "▾"):
            assert esperado in todo, esperado
    finally:
        cont.destroy()


def test_tabla_densa_toggle(ctk_root):
    import customtkinter as ctk
    from utils.ui_helpers import crear_tabla_densa
    cont = ctk.CTkFrame(ctk_root)
    cont.pack()
    try:
        crear_tabla_densa(
            cont, [("X", 60)],
            [["a"]],
            detalles=[lambda f: ctk.CTkLabel(f, text="SECRETO").pack()],
        )
        ctk_root.update_idletasks()
        btns = [w for w in cont.winfo_children() if "ctkframe" in str(w.winfo_class()).lower()]

        def _botones(x):
            out = []
            try:
                import customtkinter as _c
                if isinstance(x, _c.CTkButton) and x.cget("text") in ("▾", "▴"):
                    out.append(x)
            except Exception:
                pass
            try:
                for h in x.winfo_children():
                    out.extend(_botones(h))
            except Exception:
                pass
            return out

        toggle = _botones(cont)[0]
        toggle.invoke()
        ctk_root.update_idletasks()
        assert "SECRETO" in " ".join(_textos(cont))
        assert toggle.cget("text") == "▴"
    finally:
        cont.destroy()
