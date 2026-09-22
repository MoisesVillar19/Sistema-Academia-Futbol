"""Fase 6c: categorías de producto en Configuración."""
import pytest

pytestmark = pytest.mark.ui

from controllers import inventario_controller


def test_categoria_producto_crud():
    ok, _, id_cat = inventario_controller.crear_categoria({"nombre": "Cat6c"})
    assert ok
    ok, _ = inventario_controller.editar_categoria(id_cat, {"nombre": "Cat6cB"})
    assert ok
    cats = inventario_controller.listar_categorias(activo=1)
    assert any(c["nombre"] == "Cat6cB" for c in cats)
    ok, _ = inventario_controller.desactivar_categoria(id_cat)
    assert ok
    cats = inventario_controller.listar_categorias(activo=1)
    assert not any(c["id_categoria_producto"] == id_cat for c in cats)
    ok, _ = inventario_controller.desactivar_categoria(999999)
    assert ok is False


def test_config_muestra_categorias_producto(crear_vista, usuario_admin):
    from views.configuracion.configuracion_view import ConfiguracionView
    inventario_controller.crear_categoria({"nombre": "Cat6cUI"})
    vista = crear_vista(ConfiguracionView)
    vista.update_idletasks()
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

    _rec(vista)
    todo = " ".join(textos)
    assert "Categorías de Productos" in todo
    assert "Cat6cUI" in todo
