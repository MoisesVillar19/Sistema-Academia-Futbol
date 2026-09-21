"""Bloque D (plan inventario UX): modulo catalogos + config granular."""
import pytest

pytestmark = pytest.mark.ui

from controllers import configuracion_controller, usuario_controller
from services import auth_service


def _login_secretaria():
    from services import usuario_service
    ok, temp, _ = usuario_service.crear_usuario(
        {"dni": "66666666", "nombres": "Sec", "apellidos": "Catalogo"},
        "sec_catalogo", "SECRETARIA",
    )
    assert ok, temp
    auth_service.logout()
    assert auth_service.login("sec_catalogo", temp) is not None


def _textos(widget):
    textos = []

    def _rec(w):
        try:
            t = w.cget("text")
            if t:
                textos.append(str(t))
        except Exception:
            pass
        try:
            for h in w.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(widget)
    return textos


def test_gates_secretaria_con_catalogos_por_defecto(usuario_admin):
    auth_service.logout()
    _login_secretaria()
    assert configuracion_controller.puede_ver() is True
    assert configuracion_controller.puede_editar_globales() is False
    assert configuracion_controller.puede_acceder() is False
    # globales siguen protegidos aunque tenga catalogos
    ok, _ = configuracion_controller.actualizar_configuracion({"nombre_academia": "Hack"})
    assert ok is False


def test_gates_secretaria_sin_catalogos_denegado(usuario_admin):
    ok, _ = usuario_controller.guardar_permisos_rol(
        "SECRETARIA", ["dashboard", "estudiantes"])
    assert ok
    auth_service.logout()
    _login_secretaria()
    assert auth_service.tiene_permiso("catalogos") is False
    assert configuracion_controller.puede_ver() is False


def test_gates_admin_todo(usuario_admin):
    assert configuracion_controller.puede_ver() is True
    assert configuracion_controller.puede_editar_globales() is True


def test_render_solo_catalogos_para_secretaria(crear_vista, usuario_admin):
    auth_service.logout()
    _login_secretaria()
    from views.configuracion.configuracion_view import ConfiguracionView
    vista = crear_vista(ConfiguracionView)
    vista.update_idletasks()
    textos = " ".join(_textos(vista))
    assert "Acceso denegado" not in textos
    # catálogos visibles (7-10)
    for esperado in ("Categorías de Edad", "Tipos de Uniforme", "Conceptos Flexibles", "Apariencia Visual"):
        assert esperado in textos, f"falta sección catálogo: {esperado}"
    assert "CATÁLOGOS" in textos
    # globales ocultas + sin Guardar global
    assert "Información General" not in textos
    assert "Respaldo y OneDrive" not in textos
    assert "Guardar Cambios" not in textos
    assert "Guardar apariencia" in textos


def test_render_completo_para_admin(crear_vista, usuario_admin):
    from views.configuracion.configuracion_view import ConfiguracionView
    vista = crear_vista(ConfiguracionView)
    vista.update_idletasks()
    textos = " ".join(_textos(vista))
    assert "Información General" in textos
    assert "Categorías de Edad" in textos
    assert "Guardar Cambios" in textos


def test_matriz_guarda_modulo_nuevo(usuario_admin):
    ok, msg = usuario_controller.guardar_permisos_rol(
        "SECRETARIA", ["dashboard", "catalogos"])
    assert ok, msg
    assert "catalogos" in usuario_controller.listar_permisos_rol("SECRETARIA")
    ok, _ = usuario_controller.guardar_permisos_rol("SECRETARIA", ["dashboard", "noexiste"])
    assert ok is False
