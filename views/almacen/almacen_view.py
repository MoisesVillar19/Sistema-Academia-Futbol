"""Fase 6b: Almacén (solo ADMIN). Compras + Movimientos + Historial, sin ventas."""
from views.inventario.inventario_view import InventarioView


class AlmacenView(InventarioView):
    def __init__(self, parent):
        super().__init__(parent, canal="ALMACEN")
