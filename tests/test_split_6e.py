"""Fase 6e: event_bus real + ventas por categoría."""
import pytest

pytestmark = pytest.mark.ui

from utils import event_bus
from controllers import inventario_controller
from services import inventario_service


def _bus_handlers(nombre):
    return list(event_bus._default_bus._handlers.get(nombre, []))


def test_publish_en_crud():
    recibidos = []
    h = lambda *a, **k: recibidos.append(1)
    event_bus.subscribe("producto_actualizado", h)
    try:
        cats = inventario_controller.listar_categorias()
        ok, _, id_prod = inventario_controller.crear_producto({
            "id_categoria_producto": cats[0]["id_categoria_producto"],
            "nombre": "Pub QA 6e", "canal": "TIENDITA",
        })
        assert ok
        assert recibidos, "crear_producto no publicó"
        ok, _ = inventario_controller.editar_producto(id_prod, {"nombre": "Pub QA 6e B"})
        assert ok and len(recibidos) >= 2
        ok, _, _ = inventario_controller.registrar_compra({
            "id_producto": id_prod, "cantidad": 2, "monto_total": "4.00",
            "metodo_pago": "EFECTIVO",
        })
        assert ok and len(recibidos) >= 3
    finally:
        event_bus.unsubscribe("producto_actualizado", h)


def test_venta_combo_se_refresca(crear_vista, usuario_admin):
    from views.ventas.venta_view import VentaView
    vista = crear_vista(VentaView)
    assert "Refresco QA 6e" not in " ".join(vista._productos_map.keys())
    cats = inventario_controller.listar_categorias()
    inventario_controller.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "Refresco QA 6e", "canal": "TIENDITA",
    })
    vista._recargar_productos()
    assert "Refresco QA 6e" in " ".join(vista._productos_map.keys())


def test_matricula_extras_se_refrescan(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    cats = inventario_controller.listar_categorias()
    inventario_controller.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "Extra Refresco 6e", "canal": "TIENDITA",
    })
    vista._recargar_productos()
    assert any(p["nombre"] == "Extra Refresco 6e" for p in vista._productos_disponibles)


def test_ventas_filtro_categoria(crear_vista, usuario_admin):
    from views.ventas.venta_view import VentaView
    inventario_controller.crear_categoria({"nombre": "CatV6eA"})
    inventario_controller.crear_categoria({"nombre": "CatV6eB"})
    cats = {c["nombre"]: c["id_categoria_producto"]
            for c in inventario_controller.listar_categorias()}
    inventario_service.crear_producto({
        "id_categoria_producto": cats["CatV6eA"], "nombre": "ProdCatA 6e",
        "canal": "TIENDITA"})
    inventario_service.crear_producto({
        "id_categoria_producto": cats["CatV6eB"], "nombre": "ProdCatB 6e",
        "canal": "TIENDITA"})
    vista = crear_vista(VentaView)
    vista._on_filtro_categoria("CatV6eA")
    combos = " ".join(vista._productos_map.keys())
    assert "ProdCatA 6e" in combos
    assert "ProdCatB 6e" not in combos
    vista._on_filtro_categoria("Todas")


def test_sin_suscriptores_zombi(crear_vista, usuario_admin, ctk_root):
    from views.ventas.venta_view import VentaView
    from views.tiendita.tiendita_view import TienditaView
    n_antes = len(_bus_handlers("producto_actualizado"))
    v1 = crear_vista(VentaView)
    v2 = crear_vista(TienditaView)
    ctk_root.update_idletasks()
    assert len(_bus_handlers("producto_actualizado")) > n_antes
    v1.destroy()
    v2.destroy()
    ctk_root.update_idletasks()
    assert len(_bus_handlers("producto_actualizado")) == n_antes
