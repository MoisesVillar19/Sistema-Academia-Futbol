"""Usuarios: tabla por defecto + cards con hover de raíz."""
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


def test_tabla_por_defecto(crear_vista, usuario_admin):
    from views.usuarios.usuario_view import UsuarioView
    vista = crear_vista(UsuarioView)
    vista.update_idletasks()
    assert vista.seg_vista.get() == "Tabla"
    todo = _textos(vista.scroll_frame)
    assert "Usuario" in todo and "Rol" in todo and "admin" in todo


def test_cards_con_hover(crear_vista, usuario_admin):
    from views.usuarios.usuario_view import UsuarioView
    vista = crear_vista(UsuarioView)
    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()
    assert "admin" in _textos(vista.scroll_frame)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
