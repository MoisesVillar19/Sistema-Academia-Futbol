"""Vista Uniformes separada: instancia, lista y registro."""
import pytest

pytestmark = pytest.mark.ui


def test_vista_instancia_y_lista(crear_vista, usuario_admin):
    from views.uniformes.uniforme_view import UniformesView
    vista = crear_vista(UniformesView)
    vista.pack(fill="both", expand=True)
    vista.update_idletasks()
    assert "Total: 0" in vista.label_status.cget("text")


def test_registrar_venta_com(crear_vista, usuario_admin, crear_estudiante,
                             monkeypatch):
    import tkinter.messagebox as mb
    monkeypatch.setattr(mb, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: None)
    from views.uniformes.uniforme_view import UniformesView
    crear_estudiante(dni="12345678", nombres="Uni", apellidos="Forme")
    vista = crear_vista(UniformesView)
    vista.update_idletasks()
    vista.entry_dni.insert(0, "12345678")
    vista.combo_tipo.set("COM")
    vista.entry_monto.insert(0, "30.00")
    vista.entry_fecha.insert(0, "2026-05-15")
    vista._registrar()
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text"), \
        vista.label_form_status.cget("text")


def test_registrar_rechaza_sin_dni(crear_vista, usuario_admin):
    from views.uniformes.uniforme_view import UniformesView
    vista = crear_vista(UniformesView)
    vista.update_idletasks()
    vista.entry_monto.insert(0, "30.00")
    vista._registrar()
    vista.update_idletasks()
    assert "DNI" in vista.label_form_status.cget("text")


def test_sidebar_tiene_uniformes(crear_vista, usuario_admin, ctk_root):
    from utils.constants import PERMISOS_ROL
    assert "uniformes" in PERMISOS_ROL["SECRETARIA"]
    assert "uniformes" in PERMISOS_ROL["ADMIN"]
