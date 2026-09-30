"""Estudiantes: el toggle Cards/Tabla debe quedar visible (filtros en 2 filas)."""
import pytest

pytestmark = pytest.mark.ui


def test_toggle_visible_en_segunda_fila(crear_vista, usuario_admin, ctk_root):
    from views.estudiantes.estudiante_view import EstudianteView
    vista = crear_vista(EstudianteView)
    vista.pack(fill="both", expand=True)
    vista.update_idletasks()
    ctk_root.update()
    seg = vista.seg_vista
    assert seg.winfo_exists()
    # No comparte fila con el filtro de estado: está en la 2da línea
    assert seg.master is not vista.filtro_estado.master
    # Tiene ancho real (no colapsado fuera de pantalla)
    assert seg.winfo_width() > 50, f"toggle sin ancho visible: {seg.winfo_width()}"
    # Y sigue funcionando
    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()
    assert vista._vista_modo == "Cards"
