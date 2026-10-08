import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil, os
from controllers import venta_controller
from controllers import inventario_controller
from utils.constants import COMPROBANTES_DIR


class VentaView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._productos_map = {}
        self._comprobante_tmp = None
        self._filtro_categoria_id = None
        self._crear_widgets()
        self._cargar_productos()
        self._cargar_ventas()
        # Fase 6e: refrescar combo cuando cambian productos en Tiendita
        from utils import event_bus
        self._bus_handler = lambda *a, **k: self.after(200, lambda: self._recargar_productos())
        event_bus.subscribe("producto_actualizado", self._bus_handler)

    def destroy(self):
        try:
            from utils import event_bus
            if hasattr(self, "_bus_handler"):
                event_bus.unsubscribe("producto_actualizado", self._bus_handler)
        except Exception:
            pass
        super().destroy()

    def _recargar_productos(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        try:
            self._cargar_productos()
        except Exception:
            pass

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_lista = self.tabview.add("Ventas")
        self.tab_form = self.tabview.add("Registrar Venta")
        self._crear_tab_lista()
        self._crear_tab_form()

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_lista, titulo="Ventas", icono="🛒",
            descripcion="Uniformes / Tienda. Clic en ▾ Ver detalle para producto, cantidades y comprobante.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_ventas,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))
        # Fase 7b: toggle Cards/Tabla
        self._vista_modo = "Tabla"
        self.seg_vista = ctk.CTkSegmentedButton(
            sec, values=["Cards", "Tabla"], command=self._on_vista_cambiar)
        try:
            self.seg_vista.set("Tabla")
        except Exception:
            pass
        self.seg_vista.pack(anchor="e", padx=10, pady=(0, 8))
        crear_nota(sec, "Tip: cada tarjeta se expande inline con el detalle completo.")
        from widgets.periodo_filter import PeriodoFilter
        self.periodo_ventas = PeriodoFilter(sec, on_change=self._on_periodo_ventas)
        self.periodo_ventas.pack(fill="x", padx=10, pady=(0, 8))
        self.scroll = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_lista_status = ctk.CTkLabel(self.tab_lista, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_lista_status.pack(pady=3)

    def _crear_tab_form(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        sec1 = crear_seccion(scroll, titulo="Producto y tipo", icono="🛒",
                             descripcion="Uniforme/Tienda por producto con stock.",
                             nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(cuerpo1, text="Producto *").pack(anchor="w")
        self.combo_producto = ctk.CTkComboBox(cuerpo1, width=400, values=["Cargando..."])
        self.combo_producto.pack(anchor="w", pady=3)
        # Fase 6e: filtro por categoría (insumos, vestimenta, etc.)
        self.seg_categoria = ctk.CTkSegmentedButton(
            cuerpo1, values=["Todas"], command=self._on_filtro_categoria)
        try:
            self.seg_categoria.set("Todas")
        except Exception:
            pass
        self.seg_categoria.pack(anchor="w", pady=3)
        self._categorias_venta_map = {"Todas": None}
        self._reconstruir_filtro_categorias()
        ctk.CTkLabel(cuerpo1, text="Cantidad *").pack(anchor="w")
        self.entry_cant = ctk.CTkEntry(cuerpo1, width=150, placeholder_text="1")
        self.entry_cant.pack(anchor="w", pady=3)
        self.entry_cant.insert(0, "1")
        ctk.CTkLabel(cuerpo1, text="Tipo venta").pack(anchor="w")
        self.combo_tipo = ctk.CTkComboBox(cuerpo1, width=200, values=["UNIFORME","TIENDA"], command=self._on_tipo_changed)
        self.combo_tipo.set("UNIFORME")
        self.combo_tipo.pack(anchor="w", pady=3)
        sec2 = crear_seccion(scroll, titulo="Pago y comprobante", icono="💵",
                             descripcion="Método, estudiante opcional y comprobante si no es efectivo.", nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(cuerpo2, text="Método pago").pack(anchor="w")
        self.combo_metodo = ctk.CTkComboBox(cuerpo2, width=200, values=["EFECTIVO","YAPE","PLIN","TRANSFERENCIA"])
        self.combo_metodo.set("EFECTIVO")
        self.combo_metodo.pack(anchor="w", pady=3)
        from widgets.date_picker import DatePicker
        self.date_venta = DatePicker(cuerpo2, label_text="Fecha de venta:", default="today")
        self.date_venta.pack(anchor="w", pady=3)
        ctk.CTkLabel(cuerpo2, text="ID Estudiante (opcional, para reingreso/inscripción)").pack(anchor="w")
        self.entry_est = ctk.CTkEntry(cuerpo2, width=200, placeholder_text="ID estudiante")
        self.entry_est.pack(anchor="w", pady=3)
        self.btn_comprobante = ctk.CTkButton(cuerpo2, text="Subir comprobante (YAPE/PLIN)", width=200, command=self._elegir_comprobante)
        self.btn_comprobante.pack(anchor="w", pady=5)
        self.label_comp = ctk.CTkLabel(cuerpo2, text="Sin comprobante", text_color="gray")
        self.label_comp.pack(anchor="w")
        crear_nota(sec2, "Campeonatos se gestionan en el módulo Campeonatos (menú FINANZAS).")
        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_status = ctk.CTkLabel(footer, text="")
        self.label_status.pack(anchor="w", padx=10, pady=(8, 2))
        crear_boton_interactivo(footer, text="Registrar Venta", width=150, command=self._registrar,
                                fg_color="#7C3AED").pack(anchor="w", padx=10, pady=(2, 8))

    def _cargar_productos(self):
        # Fase 6b: ventas solo Tiendita (guard también en venta_service)
        try:
            prods = inventario_controller.listar_por_canal("TIENDITA", activo=1)
        except Exception:
            prods = [p for p in inventario_controller.listar_productos(activo=1)
                     if p.get("canal") == "TIENDITA"]
        cat_id = getattr(self, "_filtro_categoria_id", None)
        if cat_id is not None:
            prods = [p for p in prods if p.get("id_categoria_producto") == cat_id]
        nombres = [f"{p['codigo']} - {p['nombre']} (S/{p.get('precio_venta', p.get('precio',0)):.2f} stock:{p['stock_actual']})" for p in prods]
        self.combo_producto.configure(values=nombres if nombres else ["Sin productos"])
        self._productos_map = {n: p for n,p in zip(nombres, prods)}

    def _on_filtro_categoria(self, valor):
        self._filtro_categoria_id = self._categorias_venta_map.get(valor)
        self._cargar_productos()

    def _reconstruir_filtro_categorias(self):
        try:
            cats = inventario_controller.listar_categorias(activo=1)
        except Exception:
            cats = []
        nombres = [c["nombre"] for c in cats]
        self._categorias_venta_map = {"Todas": None}
        self._categorias_venta_map.update(
            {c["nombre"]: c["id_categoria_producto"] for c in cats})
        try:
            self.seg_categoria.configure(values=["Todas"] + nombres)
            actual = next((k for k, v in self._categorias_venta_map.items()
                           if v == self._filtro_categoria_id), "Todas")
            self._filtro_categoria_id = self._categorias_venta_map[actual]
            self.seg_categoria.set(actual)
        except Exception:
            pass

    def _on_periodo_ventas(self, filtro):
        self._filtro_ventas = filtro
        self._cargar_ventas()

    def _cargar_ventas(self):
        from utils.ui_helpers import crear_lista_vacia
        for w in self.scroll.winfo_children():
            w.destroy()
        fp = getattr(self, "_filtro_ventas", None)
        if fp:
            ventas = venta_controller.listar_ventas(
                anio=fp.get("anio"), meses=fp.get("meses"), orden=fp.get("orden"))
        else:
            ventas = venta_controller.listar_ventas()
        if hasattr(self, "label_lista_status"):
            try:
                total = sum(v.get("monto_total", 0) for v in ventas)
                self.label_lista_status.configure(text=f"Total: {len(ventas)} venta(s) • S/{total:.2f}")
            except Exception:
                self.label_lista_status.configure(text=f"Total: {len(ventas)} venta(s)")
        if not ventas:
            crear_lista_vacia(self.scroll, "No hay ventas", "Registra la primera en la pestaña Registrar Venta")
            return
        if getattr(self, "_vista_modo", "Cards") == "Tabla":
            self._render_tabla_ventas(ventas)
        else:
            for v in ventas:
                self._crear_card_venta(self.scroll, v)

    def _crear_card_venta(self, scroll, v):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle
        card = crear_card_interactiva(scroll)
        card.pack(fill="x", padx=6, pady=4)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)
        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        try:
            titulo = f"{v['tipo_venta']} - {v['numero_recibo']} - S/{v['monto_total']:.2f} - {v['metodo_pago']}"
        except Exception:
            titulo = f"{v.get('tipo_venta','')} - {v.get('numero_recibo','')} - S/{v.get('monto_total',0)} - {v.get('metodo_pago','')}"
        ctk.CTkLabel(info, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#1F0A33").pack(anchor="w")
        ctk.CTkLabel(info, text=f"Fecha: {v.get('fecha_venta','')} | Comp: {v.get('comprobante_path','')}", text_color="#6B5B7B", font=ctk.CTkFont(size=12)).pack(anchor="w")
        badge = ctk.CTkFrame(top, fg_color="#F3E8FF", corner_radius=8)
        badge.pack(side="right", padx=10)
        try:
            ctk.CTkLabel(badge, text=f"S/{v.get('monto_total',0):.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#7C3AED").pack(padx=10, pady=6)
        except Exception:
            pass

        toggle_btn, _, _ = agregar_detalle_expandible(
            card, lambda frame, _v=v: self._poblar_detalle_venta(frame, _v))
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    @staticmethod
    def _poblar_detalle_venta(frame, v):
        from utils.ui_helpers import linea_detalle
        linea_detalle(frame, "ID venta", v.get("id_venta"))
        linea_detalle(frame, "Recibo", v.get("numero_recibo"))
        linea_detalle(frame, "Tipo", v.get("tipo_venta"))
        linea_detalle(frame, "División", v.get("tarifa_nombre") or v.get("id_tarifa"))
        linea_detalle(frame, "Producto", v.get("producto_nombre") or v.get("nombre_producto"))
        linea_detalle(frame, "Cantidad", v.get("cantidad"))
        linea_detalle(frame, "Precio unit.", v.get("precio_unitario") or v.get("precio"))
        linea_detalle(frame, "Método pago", v.get("metodo_pago"))
        linea_detalle(frame, "Estudiante", v.get("estudiante_nombre") or v.get("id_estudiante") or v.get("estudiante"))
        linea_detalle(frame, "Comprobante", v.get("comprobante_path"))
        linea_detalle(frame, "Fecha", v.get("fecha_venta"))

    def _on_vista_cambiar(self, valor):
        self._vista_modo = valor
        self._cargar_ventas()

    def _render_tabla_ventas(self, ventas):
        from utils.ui_helpers import crear_tabla_densa
        cols = [("Recibo", 110), ("Tipo", 110), ("Monto", 90),
                ("Método", 110), ("Fecha", 100)]
        filas, dets = [], []
        for v in ventas:
            filas.append([
                str(v.get("numero_recibo", "")),
                str(v.get("tipo_venta", "")),
                (f"S/{v.get('monto_total', 0):.2f}", {"weight": "bold"}),
                str(v.get("metodo_pago", "")),
                str(v.get("fecha_venta", "")),
            ])
            dets.append(lambda frame, _v=v: self._poblar_detalle_venta(frame, _v))
        crear_tabla_densa(self.scroll, cols, filas, dets, cap=50)

    def _elegir_comprobante(self):
        from tkinter import messagebox
        from utils.imagenes import validar_imagen
        path = filedialog.askopenfilename(filetypes=[("Imagen","*.jpg *.jpeg *.png"),("Todos","*.*")])
        if path:
            ok, msg = validar_imagen(path, max_mb=5)
            if not ok:
                messagebox.showerror("Comprobante no válido", msg)
                self.label_status.configure(text=f"❌ {msg}", text_color="red")
                return
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            self._comprobante_tmp = path
            self.label_comp.configure(text=os.path.basename(path))

    def _on_tipo_changed(self, selection):
        pass

    def _registrar(self):
        tipo = self.combo_tipo.get()
        comprobante_path = None
        if self._comprobante_tmp:
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            comprobante_path = self._comprobante_tmp
        id_est = self.entry_est.get().strip()
        try:
            id_est = int(id_est) if id_est else None
        except ValueError:
            id_est = None
        sel = self.combo_producto.get()
        prod = self._productos_map.get(sel)
        if not prod:
            self.label_status.configure(text="Seleccione producto", text_color="red")
            return
        try:
            cant = int(self.entry_cant.get().strip() or "1")
            if cant <= 0:
                raise ValueError
        except ValueError:
            self.label_status.configure(text="Cantidad inválida", text_color="red")
            return
        data = {
            "id_estudiante": id_est,
            "tipo_venta": tipo,
            "metodo_pago": self.combo_metodo.get(),
            "items": [{"id_producto": prod["id_producto"], "cantidad": cant}],
            "comprobante_path": comprobante_path,
            "fecha_venta": self.date_venta.get() or None,
        }
        from widgets.loading_dialog import con_indicador_ocupado
        exito, msg, vid = con_indicador_ocupado(
            self, "Guardando venta...",
            lambda: venta_controller.registrar_venta(data))
        if exito and comprobante_path and vid:
            # copiar a central con recibo (conserva extensión real)
            try:
                import glob
                from utils.imagenes import extension_real
                # el service ya generó recibo, obtener venta para nombre
                v = venta_controller.obtener_venta(vid)
                if v:
                    dest = os.path.join(COMPROBANTES_DIR, f"{v['numero_recibo']}{extension_real(comprobante_path)}")
                    shutil.copy2(comprobante_path, dest)
            except Exception:
                pass
            self._comprobante_tmp = None
            self.label_comp.configure(text="Sin comprobante")
        self.label_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self._cargar_productos()
            self._cargar_ventas()
