"""Bloque C (plan inventario UX): MiPerfil para todos + categoria sin botones cortados."""
import pytest

pytestmark = pytest.mark.ui


def _textos_botones(widget):
    import customtkinter as ctk
    encontrados = []

    def _rec(w):
        try:
            if isinstance(w, ctk.CTkButton):
                encontrados.append(w.cget("text"))
        except Exception:
            pass
        try:
            for h in w.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(widget)
    return encontrados


def test_miperfil_visible_para_admin_y_secretaria(ctk_root, usuario_admin):
    from views.usuarios.usuario_view import MiPerfilDialog

    dlg = MiPerfilDialog(ctk_root)
    ctk_root.update_idletasks()
    try:
        assert dlg.winfo_exists()
        botones = _textos_botones(dlg)
        assert "Guardar" in botones and "Cancelar" in botones
        assert dlg.entry_actual.winfo_exists()
    finally:
        dlg.destroy()


def test_miperfil_visible_para_secretaria(ctk_root, usuario_secretaria):
    from views.usuarios.usuario_view import MiPerfilDialog

    dlg = MiPerfilDialog(ctk_root)
    ctk_root.update_idletasks()
    try:
        assert dlg.winfo_exists()
        botones = _textos_botones(dlg)
        assert "Guardar" in botones and "Cancelar" in botones
    finally:
        dlg.destroy()


def test_miperfil_cambia_clave(usuario_secretaria):
    from controllers import login_controller
    from services import auth_service

    # validaciones
    ok, msg = login_controller.cambiar_password("clave-mal", "nueva123", "nueva123")
    assert ok is False
    ok, _ = login_controller.cambiar_password("x", "corta", "corta")
    assert ok is False

    # la fixture deja la temporal en el servicio; recuperarla es interno:
    # camino válido = actual correcta. Usamos el flujo real con PIN-free:
    # primero obtenemos la temporal creando otro usuario no es viable;
    # en su lugar verificamos que con la clave de sesión actual funciona.
    # La clave temporal de la fixture no se expone: probamos rechazo de
    # confirmación distinta y longitud mínima (ya cubierto) + éxito real
    # re-logueando con cambio directo del servicio.
    from utils.security import hash_password
    from repositories import usuario_repository
    usuario = usuario_repository.obtener_por_username("secretaria_test")
    usuario_repository.cambiar_password(usuario["id_usuario"], hash_password("actual123"))
    auth_service.logout()
    assert auth_service.login("secretaria_test", "actual123") is not None

    ok, msg = login_controller.cambiar_password("actual123", "nueva123", "nueva123")
    assert ok is True, msg
    auth_service.logout()
    assert auth_service.login("secretaria_test", "nueva123") is not None


def test_categoria_dialog_muestra_ambos_botones(crear_vista, usuario_admin):
    from views.configuracion.configuracion_view import ConfiguracionView

    vista = crear_vista(ConfiguracionView)
    vista._nueva_categoria()
    vista.update_idletasks()
    try:
        toplevels = [w for w in vista.winfo_children() if w.winfo_class() == "Toplevel"]
        assert toplevels, "no se abrió el diálogo de categoría"
        dlg = toplevels[0]
        assert "360x520" in dlg.geometry()
        botones = _textos_botones(dlg)
        assert "Guardar" in botones and "Cancelar" in botones
        import customtkinter as ctk

        def _hay_scroll(w):
            try:
                if isinstance(w, ctk.CTkScrollableFrame):
                    return True
            except Exception:
                pass
            try:
                return any(_hay_scroll(h) for h in w.winfo_children())
            except Exception:
                return False

        assert _hay_scroll(dlg), "contenido de categoría debe ser scrolleable"
    finally:
        for w in list(vista.winfo_children()):
            try:
                if w.winfo_class() == "Toplevel":
                    w.destroy()
            except Exception:
                pass
