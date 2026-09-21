"""Bloque B (plan inventario UX): toggle Cards/Tabla, filtro categoria, stock readonly."""
import pytest

pytestmark = pytest.mark.ui

from views.inventario.inventario_view import InventarioView
from controllers import inventario_controller


def _crear_producto(nombre, categoria, **extra):
    cats = inventario_controller.listar_categorias()
    id_cat = next((c["id_categoria_producto"] for c in cats if c["nombre"] == categoria), None)
    if id_cat is None:
        ok, _, id_cat = inventario_controller.crear_categoria({"nombre": categoria})
        assert ok
    data = {"nombre": nombre, "id_categoria_producto": id_cat, "tipo_uso": "VENTA"}
    data.update(extra)
    ok, _, id_prod = inventario_controller.crear_producto(data)
    assert ok
    return id_prod


def _textos(vista):
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

    _rec(vista.scroll_productos)
    return textos


def test_toggle_renderiza_ambas_vistas(crear_vista, usuario_admin):
    _crear_producto("Toggle QA", "CatToggle")
    vista = crear_vista(InventarioView)

    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    textos = _textos(vista)
    for esperado in ("Código", "Gan.%", "Total inv."):
        assert esperado in textos, f"falta columna {esperado} en modo Tabla"
    assert "Toggle QA" in " ".join(textos)

    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()
    assert "Toggle QA" in " ".join(_textos(vista))


def test_filtro_por_categoria(crear_vista, usuario_admin):
    _crear_producto("FiltroA QA", "CatA")
    _crear_producto("FiltroB QA", "CatB")
    vista = crear_vista(InventarioView)
    vista.update_idletasks()

    id_cat_a = inventario_controller.listar_categorias()
    id_a = next(c["id_categoria_producto"] for c in id_cat_a if c["nombre"] == "CatA")
    vista._filtro_categoria_id = id_a
    vista._cargar_paginado()
    vista.update_idletasks()
    textos = " ".join(_textos(vista))
    assert "FiltroA QA" in textos
    assert "FiltroB QA" not in textos


def test_editar_muestra_stock_solo_lectura(crear_vista, usuario_admin):
    id_prod = _crear_producto("StockRO QA", "CatRO")
    vista = crear_vista(InventarioView)
    prod = inventario_controller.obtener_producto(id_prod)
    vista._editar_producto(prod)
    vista.update_idletasks()
    assert "solo lectura" in vista.label_stock_readonly.cget("text")
    assert vista.entry_stock_inicial.cget("state") == "disabled"

    vista._nuevo_producto()
    assert vista.entry_stock_inicial.cget("state") == "normal"


def test_compra_suma_stock():
    id_prod = _crear_producto("CompraSuma QA", "CatCompra")
    antes = inventario_controller.obtener_producto(id_prod)["stock_actual"]
    ok, _, _ = inventario_controller.registrar_compra({
        "id_producto": id_prod, "cantidad": 5, "monto_total": "50.00",
        "metodo_pago": "EFECTIVO", "motivo": "Compra a proveedor",
    })
    assert ok
    despues = inventario_controller.obtener_producto(id_prod)["stock_actual"]
    assert despues == antes + 5
