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


def test_agregar_talla_y_listar_productos(usuario_admin):
    from services import uniforme_service
    ok, msg = uniforme_service.agregar_talla("ENT", "L", 4)
    if not ok:
        assert "ya existe" in msg  # otro test la creó antes
    else:
        ok2, _ = uniforme_service.agregar_talla("ENT", "L", 1)
        assert not ok2, "talla duplicada debe rechazarse"
    grupos = uniforme_service.productos_uniforme()
    ent = next(g for g in grupos if g["tipo"] == "ENT")
    assert any(t["talla"] == "L" for t in ent["tallas"])
    ok, msg = uniforme_service.agregar_talla("ENT", "XX", 1)
    assert not ok, "talla inexistente en catálogo debe rechazarse"


def test_tab_productos_en_vista(crear_vista, usuario_admin):
    from views.uniformes.uniforme_view import UniformesView
    vista = crear_vista(UniformesView)
    vista.update_idletasks()
    assert vista.tab_productos.winfo_exists()
    assert "producto(s)" in vista.label_prod_status.cget("text")
