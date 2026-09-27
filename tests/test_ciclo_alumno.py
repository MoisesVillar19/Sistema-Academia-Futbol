"""Ciclo único: Activos → Retirar (archiva) → Reingreso (reactiva). Sin borrado físico."""
import pytest

pytestmark = pytest.mark.ui


def test_retiro_archiva_y_reingreso_reactiva(crear_estudiante):
    from controllers import estudiante_controller
    from repositories import estudiante_repository
    id_est = crear_estudiante()
    assert estudiante_controller.registrar_retiro(id_est)[0] is True
    est = estudiante_repository.obtener_por_id(id_est)
    assert est["estado"] == "RETIRADO" and est["activo"] == 0
    assert estudiante_controller.registrar_retiro(id_est)[0] is False
    assert estudiante_controller.registrar_reingreso(id_est)[0] is True
    est = estudiante_repository.obtener_por_id(id_est)
    assert est["estado"] == "REINGRESANTE" and est["activo"] == 1


def test_reingreso_sin_retiro_rechazado(crear_estudiante):
    from controllers import estudiante_controller
    id_est = crear_estudiante()
    assert estudiante_controller.registrar_reingreso(id_est)[0] is False


def test_filtro_inactivos(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    from controllers import estudiante_controller
    id_est = crear_estudiante()
    vista = crear_vista(EstudianteView)
    vista.filtro_estado.set("Inactivos")
    vista._on_busqueda_cambiar()
    assert "Total: 0" in vista.label_status.cget("text")
    assert estudiante_controller.registrar_retiro(id_est)[0] is True
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text")


def test_botones_ciclo(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    from controllers import estudiante_controller
    id_est = crear_estudiante(nombres="Ciclo", apellidos="Unico")
    vista = crear_vista(EstudianteView)
    vista._on_busqueda_cambiar()
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

    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()
    assert "Retirar" in _textos(vista.scroll_estudiantes)
    assert "Desactivar" not in _textos(vista.scroll_estudiantes)
    estudiante_controller.registrar_retiro(id_est)
    vista.filtro_estado.set("Inactivos")
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    todo = _textos(vista.scroll_estudiantes)
    assert "Reingreso" in todo and "INACTIVO" in todo
    assert "Desactivar" not in todo and "Activar" not in todo
