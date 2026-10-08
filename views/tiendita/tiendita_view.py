"""Fase 6b: Tiendita (SECRETARIA+ADMIN). Compras + Ventas + Ganancias, sin movimientos."""
import customtkinter as ctk

from views.inventario.inventario_view import InventarioView


class TienditaView(InventarioView):
    # Uniformes COM/ENT viven en su sección propia (no en Tiendita).
    CODIGOS_EXCLUIDOS = ("UNIFORME-COM", "CAMISETA-ENT")

    def __init__(self, parent):
        super().__init__(parent, canal="TIENDITA")
        self._excluir_codigos = self.CODIGOS_EXCLUIDOS
        # Tienda: sin filtro por categoría de insumos (vive en Almacén).
        # Todo lo canal TIENDITA (sin uniformes) se muestra junto.
        try:
            if hasattr(self, "filtro_cat_frame"):
                self.filtro_cat_frame.pack_forget()
        except Exception:
            pass
        self._cargar_paginado()
        self._ventas_lista = False
        self._ganancias_lista = False
        self._venta_embebida = None
        try:
            from services import auth_service
            if auth_service.tiene_permiso("ventas"):
                self._agregar_tab_ventas()
        except Exception:
            self._agregar_tab_ventas()
        self._agregar_tab_ganancias()
        # Ventas y Ganancias son pesadas: se cargan al entrar a la pestaña.
        try:
            self.tabview.configure(command=self._on_tab_tiendita)
        except Exception:
            self._asegurar_tab_ventas()
            self._cargar_ganancias()
            self._ganancias_lista = True

    def _on_tab_tiendita(self):
        try:
            actual = self.tabview.get()
        except Exception:
            actual = ""
        if actual == "Ventas" and not getattr(self, "_ventas_lista", False):
            self._ventas_lista = True
            try:
                for w in list(self.tab_ventas.winfo_children()):
                    w.destroy()
                self.update_idletasks()
            except Exception:
                pass
            self._asegurar_tab_ventas()
        elif actual == "Ganancias" and not getattr(self, "_ganancias_lista", False):
            self._ganancias_lista = True
            try:
                self.label_ganancias.configure(text="Cargando balance...")
                self.update_idletasks()
            except Exception:
                pass
            self._cargar_ganancias()

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
        self.seg_gan_modo = ctk.CTkSegmentedButton(
            barra, values=["Por producto", "Por venta"],
            command=lambda v: self._cargar_ganancias())
        try:
            self.seg_gan_modo.set("Por producto")
        except Exception:
            pass
        self.seg_gan_modo.pack(side="left", padx=5)
        self.entry_gan_prod = ctk.CTkEntry(
            barra, placeholder_text="Filtrar producto...", width=180)
        self.entry_gan_prod.pack(side="left", padx=5)
        self.entry_gan_prod.bind(
            "<KeyRelease>",
            lambda e: self.after(300, self._cargar_ganancias_debounced()))
        crear_boton_interactivo(barra, text="Actualizar", width=110,
                                command=self._cargar_ganancias, fg_color="#7C3AED").pack(side="left")
        from widgets.periodo_filter import PeriodoFilter
        self.periodo_gan = PeriodoFilter(sec, on_change=self._on_periodo_gan,
                                         show_orden=False)
        self.periodo_gan.pack(fill="x", padx=10, pady=(0, 8))
        self.scroll_ganancias = ctk.CTkScrollableFrame(self.tab_ganancias)
        self.scroll_ganancias.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_ganancias = ctk.CTkLabel(self.tab_ganancias, text="Entra a la pestaña para cargar el balance...", font=ctk.CTkFont(size=12))
        self.label_ganancias.pack(pady=3)

    def _on_periodo_gan(self, filtro):
        """PeriodoFilter (año + meses) sincroniza los DatePickers y recarga."""
        try:
            meses = filtro.get("meses", [])
            anio = filtro.get("anio")
            if meses:
                self.date_gan_ini.set(f"{anio}-{min(meses):02d}-01")
                import calendar
                self.date_gan_fin.set(
                    f"{anio}-{max(meses):02d}-{calendar.monthrange(anio, max(meses))[1]:02d}")
                self._cargar_ganancias()
        except Exception:
            pass

    def _cargar_ganancias_debounced(self):
        try:
            if getattr(self, "_gan_after", None):
                self.after_cancel(self._gan_after)
        except Exception:
            pass
        try:
            self._gan_after = self.after(400, self._cargar_ganancias)
        except Exception:
            self._cargar_ganancias()

    def _filtro_prod_gan(self) -> str:
        try:
            return self.entry_gan_prod.get().strip().lower()
        except Exception:
            return ""

    def _cargar_ganancias(self):
        try:
            modo = self.seg_gan_modo.get()
        except Exception:
            modo = "Por producto"
        if modo == "Por venta":
            self._cargar_ganancias_por_venta()
        else:
            self._cargar_ganancias_por_producto()

    def _cargar_ganancias_por_venta(self):
        from controllers import venta_controller
        from repositories import detalle_venta_repository, producto_repository
        from utils.ui_helpers import crear_tabla_densa
        for w in self.scroll_ganancias.winfo_children():
            w.destroy()
        desde = self.date_gan_ini.get() or "2000-01-01"
        hasta = self.date_gan_fin.get() or "2100-12-31"
        try:
            metodo = self.seg_gan_metodo.get()
        except Exception:
            metodo = "Todas"
        qprod = self._filtro_prod_gan()
        try:
            ventas = venta_controller.listar_ventas(fecha_inicio=desde, fecha_fin=hasta)
        except Exception:
            ventas = []
        cols = [("Fecha", 95), ("Recibo", 130), ("Productos", 220),
                ("Cant.", 60), ("Monto", 85), ("Método", 95)]
        filas, dets = [], []
        total = 0.0
        for v in ventas:
            if metodo != "Todas" and v.get("metodo_pago") != metodo:
                continue
            try:
                dets_v = detalle_venta_repository.obtener_por_venta(v["id_venta"])
            except Exception:
                dets_v = []
            nombres, cant = [], 0
            for d in dets_v:
                try:
                    p = producto_repository.obtener_por_id(d["id_producto"])
                    nombre = (p or {}).get("nombre", "")
                except Exception:
                    nombre = ""
                # Tienda: sin uniformes
                if (p or {}).get("codigo") in ("UNIFORME-COM", "CAMISETA-ENT"):
                    continue
                nombres.append(f"{nombre} x{d.get('cantidad', 0)}")
                cant += int(d.get("cantidad", 0) or 0)
            if qprod and qprod not in " ".join(nombres).lower():
                continue
            if not nombres:
                continue
            try:
                monto = float(v.get("monto_total", 0) or 0)
            except (TypeError, ValueError):
                monto = 0.0
            total += monto
            filas.append([
                str(v.get("fecha_venta", "")), str(v.get("numero_recibo", "")),
                "; ".join(nombres), cant, f"S/{monto:.2f}",
                str(v.get("metodo_pago", "")),
            ])
            dets.append(lambda frame, _v=dict(v): self._detalle_venta_gan(frame, _v))
        crear_tabla_densa(self.scroll_ganancias, cols, filas, dets, cap=200)
        self.label_ganancias.configure(
            text=f"{len(filas)} venta(s) • Total período: S/{total:.2f}")

    def _detalle_venta_gan(self, frame, venta):
        from utils.ui_helpers import linea_detalle
        linea_detalle(frame, "Recibo", venta.get("numero_recibo", ""))
        linea_detalle(frame, "Fecha", venta.get("fecha_venta", ""))
        linea_detalle(frame, "Método", venta.get("metodo_pago", ""))
        linea_detalle(frame, "Monto", f"S/{float(venta.get('monto_total', 0) or 0):.2f}")
        from utils.ui_helpers import crear_boton_interactivo
        crear_boton_interactivo(
            frame, text="Editar", width=100,
            command=lambda: self._dialog_editar_venta(venta),
            fg_color="#7C3AED").pack(anchor="w", padx=10, pady=6)

    def _dialog_editar_venta(self, venta):
        from tkinter import messagebox
        from controllers import venta_controller
        top = ctk.CTkToplevel(self)
        top.title(f"Editar venta {venta.get('numero_recibo', '')}")
        top.geometry("420x360")
        try:
            top.transient(self)
        except Exception:
            pass
        cuerpo = ctk.CTkFrame(top, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=12)

        def _fila(etiqueta, valor):
            f = ctk.CTkFrame(cuerpo, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=etiqueta, width=140, anchor="w").pack(side="left")
            e = ctk.CTkEntry(f, width=200)
            e.insert(0, str(valor))
            e.pack(side="left", padx=5)
            return e

        e_fecha = _fila("Fecha (AAAA-MM-DD)", venta.get("fecha_venta", ""))
        f_met = ctk.CTkFrame(cuerpo, fg_color="transparent")
        f_met.pack(fill="x", pady=2)
        ctk.CTkLabel(f_met, text="Método", width=140, anchor="w").pack(side="left")
        cb_met = ctk.CTkComboBox(
            f_met, width=200,
            values=["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA"])
        try:
            cb_met.set(venta.get("metodo_pago", "EFECTIVO"))
        except Exception:
            pass
        cb_met.pack(side="left", padx=5)
        lbl = ctk.CTkLabel(cuerpo, text="", font=ctk.CTkFont(size=12))
        lbl.pack(anchor="w", pady=4)
        ctk.CTkLabel(
            cuerpo, text="Solo fecha, método y comprobante. Ítems y stock no se tocan.",
            font=ctk.CTkFont(size=11), text_color="#6B5B7B",
            wraplength=380, justify="left").pack(anchor="w")

        def guardar():
            ok, msg = venta_controller.editar_venta(venta["id_venta"], {
                "fecha_venta": e_fecha.get().strip(),
                "metodo_pago": cb_met.get(),
            })
            if ok:
                messagebox.showinfo("Venta", msg)
                top.destroy()
                self._cargar_ganancias()
            else:
                lbl.configure(text=f"❌ {msg}", text_color="red")

        btnf = ctk.CTkFrame(cuerpo, fg_color="transparent")
        btnf.pack(pady=10)
        ctk.CTkButton(btnf, text="Cancelar", fg_color="gray",
                      command=top.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Guardar", command=guardar).pack(side="left", padx=5)

    def _cargar_ganancias_por_producto(self):
        from services import reporte_service
        for w in self.scroll_ganancias.winfo_children():
            w.destroy()
        desde = self.date_gan_ini.get() or "2000-01-01"
        hasta = self.date_gan_fin.get() or "2100-12-31"
        metodo = self.seg_gan_metodo.get()
        filas, totales = reporte_service.balance_tienda(desde, hasta)
        qprod = self._filtro_prod_gan()
        if qprod:
            filas = [f for f in filas if qprod in str(f.get("nombre", "")).lower()]
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
        ctk.CTkLabel(self.tab_ventas, text="Entra a la pestaña para cargar las ventas...",
                     text_color="gray").pack(pady=20)

    def _asegurar_tab_ventas(self):
        if getattr(self, "_venta_embebida", None) is not None:
            return
        try:
            from views.ventas.venta_view import VentaView
            self._venta_embebida = VentaView(self.tab_ventas)
            self._venta_embebida.pack(fill="both", expand=True)
            self._ventas_lista = True
        except Exception as e:
            ctk.CTkLabel(self.tab_ventas, text=f"No se pudo cargar Ventas: {e}",
                         text_color="red").pack(pady=20)
