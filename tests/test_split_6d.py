"""Fase 6d: vocabulario Excel en empaque (COSTO X UNIDAD / COSTO TOTAL / COSTO VENTA)."""
import pytest

pytestmark = pytest.mark.ui

from views.inventario.inventario_view import InventarioView
from controllers import inventario_controller


def _vista_nueva(crear_vista):
    vista = crear_vista(InventarioView)
    vista._nuevo_producto()
    return vista


def test_unidad_muestra_costo_unitario(crear_vista, usuario_admin, ctk_root):
    vista = _vista_nueva(crear_vista)
    ctk_root.update_idletasks()
    assert vista.row_unit.winfo_ismapped()
    assert not vista.row_total.winfo_ismapped()


def test_caja_muestra_costo_total(crear_vista, usuario_admin, ctk_root):
    vista = _vista_nueva(crear_vista)
    vista.combo_empaque.set("Caja x12")
    vista._on_empaque_change("Caja x12")
    ctk_root.update_idletasks()
    assert vista.row_total.winfo_ismapped()
    assert not vista.row_unit.winfo_ismapped()


def _id_cat():
    cats = inventario_controller.listar_categorias()
    return cats[0]["id_categoria_producto"]


def test_guardar_unidad_usa_unitario(crear_vista, usuario_admin):
    vista = _vista_nueva(crear_vista)
    vista.combo_categoria.set(
        next(n for n, i in vista._categorias_map.items() if i == _id_cat()))
    vista.entry_nombre.insert(0, "Unidad QA 6d")
    vista.entry_unitario.insert(0, "3.50")
    vista.entry_precio_venta.insert(0, "5.00")
    vista._guardar_producto()
    from repositories import producto_repository
    prods = [p for p in producto_repository.obtener_todos() if p["nombre"] == "Unidad QA 6d"]
    assert prods and float(prods[0]["precio_compra"]) == 3.50


def test_guardar_caja_calcula_unitario(crear_vista, usuario_admin):
    vista = _vista_nueva(crear_vista)
    vista.combo_empaque.set("Personalizado")
    vista._on_empaque_change("Personalizado")
    vista.combo_categoria.set(
        next(n for n, i in vista._categorias_map.items() if i == _id_cat()))
    vista.entry_nombre.insert(0, "Caja QA 6d")
    vista.entry_cant_caja.insert(0, "10")
    vista.entry_precio_total.insert(0, "25.00")
    vista.entry_precio_venta.insert(0, "4.00")
    vista._guardar_producto()
    from repositories import producto_repository
    prods = [p for p in producto_repository.obtener_todos() if p["nombre"] == "Caja QA 6d"]
    assert prods and float(prods[0]["precio_compra"]) == 2.50
