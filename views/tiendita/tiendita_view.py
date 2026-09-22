"""Fase 6b: Tiendita (SECRETARIA+ADMIN). Compras + Ventas + Ganancias, sin movimientos."""
import customtkinter as ctk

from views.inventario.inventario_view import InventarioView


class TienditaView(InventarioView):
    def __init__(self, parent):
        super().__init__(parent, canal="TIENDITA")
        try:
            from services import auth_service
            if auth_service.tiene_permiso("ventas"):
                self._agregar_tab_ventas()
        except Exception:
            self._agregar_tab_ventas()

    def destroy(self):
        # La VentaView embebida no recibe destroy al destruir el padre
        # (suscriptor zombi al evento); destruirla explícito.
        try:
            if getattr(self, "_venta_embebida", None) is not None:
                self._venta_embebida.destroy()
        except Exception:
            pass
        super().destroy()

    def _agregar_tab_ventas(self):
        self._venta_embebida = None
        try:
            self.tab_ventas = self.tabview.add("Ventas")
            self._tabs["Ventas"] = self.tab_ventas
        except Exception:
            return
        try:
            from views.ventas.venta_view import VentaView
            self._venta_embebida = VentaView(self.tab_ventas)
            self._venta_embebida.pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(self.tab_ventas, text=f"No se pudo cargar Ventas: {e}",
                         text_color="red").pack(pady=20)
