"""Fase 6b: Tiendita (SECRETARIA+ADMIN). Compras + Ventas + Ganancias, sin movimientos."""
import customtkinter as ctk

from views.inventario.inventario_view import InventarioView


class TienditaView(InventarioView):
    # Uniformes COM/ENT viven en su sección propia (no en Tiendita).
    CODIGOS_EXCLUIDOS = ("UNIFORME-COM", "CAMISETA-ENT")

    def __init__(self, parent):
        super().__init__(parent, canal="TIENDITA")
        self._excluir_codigos = self.CODIGOS_EXCLUIDOS
        self._cargar_paginado()
        try:
            from services import auth_service
            if auth_service.tiene_permiso("ventas"):
                self._agregar_tab_ventas()
        except Exception:
            self._agregar_tab_ventas()
        self._agregar_tab_ganancias()

    def _agregar_tab_ganancias(self):
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo, crear_tabla_densa
        from widgets.date_picker import DatePicker
        try:
            self.tab_ganancias = self.tabview.add("Ganancias")
            self._tabs["Ganancias"] = self.tab_ganancias
        except Exception:
            return
        sec = crear_seccion(
            self.tab_ganancias, titulo="Balance de Tienda", icono="📊",
            descripcion="PRODUCTOS, COSTO TOTAL/X UNIDAD/VENTA, YAPE/EFECTIVO, "
                        "VENDIDAS, QUEDAN y GANANCIA (costo vigente).",
            nro=1)
        barra = ctk.CTkFrame(sec, fg_color="transparent")
        barra.pack(fill="x", padx=10, pady=(0, 8))
        self.date_gan_ini = DatePicker(barra, label_text="Desde:", default="start_of_month")
        self.date_gan_ini.pack(side="left", padx=5)
        self.date_gan_fin = DatePicker(barra, label_text="Hasta:", default="today")
        self.date_gan_fin.pack(side="left", padx=5)
        self.seg_gan_metodo = ctk.CTkSegmentedButton(
            barra, values=["Todas", "YAPE", "EFECTIVO"],
            command=lambda v: self._cargar_ganancias())
        try:
            self.seg_gan_metodo.set("Todas")
        except Exception:
            pass
        self.seg_gan_metodo.pack(side="left", padx=5)
        crear_boton_interactivo(barra, text="Actualizar", width=110,
                                command=self._cargar_ganancias, fg_color="#7C3AED").pack(side="left")
        self.scroll_ganancias = ctk.CTkScrollableFrame(self.tab_ganancias)
        self.scroll_ganancias.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_ganancias = ctk.CTkLabel(self.tab_ganancias, text="", font=ctk.CTkFont(size=12))
        self.label_ganancias.pack(pady=3)
        self._cargar_ganancias()

    def _cargar_ganancias(self):
        from services import reporte_service
        for w in self.scroll_ganancias.winfo_children():
            w.destroy()
        desde = self.date_gan_ini.get() or "2000-01-01"
        hasta = self.date_gan_fin.get() or "2100-12-31"
        metodo = self.seg_gan_metodo.get()
        filas, totales = reporte_service.balance_tienda(desde, hasta)
        from utils.ui_helpers import crear_tabla_densa
        cols = [("Productos", 170), ("Cantidad", 70), ("Costo Total", 85),
                ("Costo x Und.", 85), ("Costo Venta", 85), ("Yape", 80),
                ("Efectivo", 80), ("Vendidas", 70), ("Quedan", 60), ("Ganancia", 85)]
        datos = []
        for f in filas:
            yape = f["yape"] if metodo in ("Todas", "YAPE") else 0.0
            efec = f["efectivo"] if metodo in ("Todas", "EFECTIVO") else 0.0
            datos.append([
                f["nombre"], f["cantidad"], f"S/{f['costo_total']:.2f}",
                f"S/{f['costo_unitario']:.2f}", f"S/{f['costo_venta']:.2f}",
                f"S/{yape:.2f}", f"S/{efec:.2f}", f["vendidas"], f["quedan"],
                (f"S/{f['ganancia']:.2f}", {"weight": "bold",
                 "text_color": "green" if f["ganancia"] >= 0 else "red"}),
            ])
        datos.append(["TOTAL", totales["cantidad"], f"S/{totales['costo_total']:.2f}",
                      "", "", f"S/{totales['yape']:.2f}", f"S/{totales['efectivo']:.2f}",
                      totales["vendidas"], totales["quedan"],
                      (f"S/{totales['ganancia']:.2f}", {"weight": "bold"})])
        crear_tabla_densa(self.scroll_ganancias, cols, datos, cap=200)
        self.label_ganancias.configure(
            text=f"Ganancia del período: S/{totales['ganancia']:.2f} • "
                 f"Vendido: S/{totales['yape'] + totales['efectivo']:.2f}")

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
