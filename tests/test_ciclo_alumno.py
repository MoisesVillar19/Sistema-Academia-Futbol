"""Ciclo de vida: Activos → Inactivos → Activar (solo ADMIN, sin borrado físico)."""
import pytest

pytestmark = pytest.mark.ui


def test_filtro_inactivos_vacio_y_lleno(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    from controllers import estudiante_controller
    id_est = crear_estudiante()
    vista = crear_vista(EstudianteView)
    vista.filtro_estado.set("Inactivos")
    vista._on_busqueda_cambiar()
    assert "Total: 0" in vista.label_status.cget("text")
    ok, _ = estudiante_controller.desactivar_estudiante(id_est)
    assert ok
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text")


def test_desactivar_requiere_admin(usuario_secretaria, crear_estudiante):
    from controllers import estudiante_controller
    id_est = crear_estudiante()
    ok, msg = estudiante_controller.desactivar_estudiante(id_est)
    assert ok is False and "administrador" in msg.lower()
    ok, _ = estudiante_controller.reactivar_estudiante(id_est)
    assert ok is False


def test_reactivar_revierte(crear_estudiante, usuario_admin):
    from controllers import estudiante_controller
    id_est = crear_estudiante()
    assert estudiante_controller.desactivar_estudiante(id_est)[0] is True
    assert estudiante_controller.reactivar_estudiante(id_est)[0] is True
    assert estudiante_controller.reactivar_estudiante(id_est)[0] is False
    from repositories import estudiante_repository
    assert estudiante_repository.obtener_por_id(id_est)["activo"] == 1


def test_boton_activar_solo_inactivos(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    from controllers import estudiante_controller
    id_est = crear_estudiante(nombres="Ciclo", apellidos="Inactivo")
    estudiante_controller.desactivar_estudiante(id_est)
    vista = crear_vista(EstudianteView)
    vista.filtro_estado.set("Inactivos")
    vista._on_busqueda_cambiar()
    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()

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

    todo = _textos(vista.scroll_estudiantes)
    assert "Activar" in todo and "INACTIVO" in todo
