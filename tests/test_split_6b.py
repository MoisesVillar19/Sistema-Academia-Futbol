"""Fase 6b: vistas Tiendita/Almacén estancas + menú por rol."""
import pytest

pytestmark = pytest.mark.ui

from views.tiendita.tiendita_view import TienditaView
from views.almacen.almacen_view import AlmacenView
from views.inventario.inventario_view import InventarioView
from services import inventario_service


def _prod(nombre, canal):
    cats = inventario_service.listar_categorias()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": nombre, "canal": canal, "precio_venta": 10.0,
    })
    assert ok
    return id_prod


def _tabs(vista):
    return list(vista._tabs.keys())


def test_tiendita_tabs_y_filtro(crear_vista, usuario_admin):
    id_t = _prod("T6b", "TIENDITA")
    id_a = _prod("A6b", "ALMACEN")
    vista = crear_vista(TienditaView)
    assert _tabs(vista) == ["Productos", "Registrar Producto", "Registrar Compra", "Ventas"]
    assert vista.tab_movimiento is None and vista.tab_historial is None
    vista.update_idletasks()
    ids = {p["id_producto"] for p in
           [v for v in inventario_service.listar_por_canal("TIENDITA")]}
    assert id_t in ids
    combos = " ".join(vista._productos_compra_map.keys())
    assert "T6b" in combos and "A6b" not in combos
    # form bloqueado a TIENDITA
    vista._nuevo_producto()
    assert vista.combo_tipo_uso.get() == "TIENDITA"
    assert vista.combo_tipo_uso.cget("state") == "disabled"


def test_almacen_tabs_y_filtro(crear_vista, usuario_admin):
    id_t = _prod("T6b2", "TIENDITA")
    id_a = _prod("A6b2", "ALMACEN")
    vista = crear_vista(AlmacenView)
    assert "Movimiento" in _tabs(vista) and "Historial" in _tabs(vista)
    assert "Ventas" not in _tabs(vista)
    combos = " ".join(vista._productos_compra_map.keys())
    assert "A6b2" in combos and "T6b2" not in combos


def test_legacy_inventario_intacto(crear_vista, usuario_admin):
    vista = crear_vista(InventarioView)
    assert "Categorías" in _tabs(vista) and "Movimiento" in _tabs(vista)


def test_roles_tiendita_almacen(usuario_admin):
    from services import auth_service
    assert auth_service.tiene_permiso("tiendita") is True
    assert auth_service.tiene_permiso("almacen") is True


def test_secretaria_solo_tiendita(usuario_secretaria):
    from services import auth_service
    assert auth_service.tiene_permiso("tiendita") is True
    assert auth_service.tiene_permiso("almacen") is False


def test_venta_solo_tiendita(crear_vista, usuario_admin):
    from views.ventas.venta_view import VentaView
    _prod("TV6b", "TIENDITA")
    _prod("AV6b", "ALMACEN")
    vista = crear_vista(VentaView)
    combos = " ".join(vista._productos_map.keys())
    assert "TV6b" in combos and "AV6b" not in combos
