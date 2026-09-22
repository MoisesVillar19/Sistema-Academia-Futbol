import customtkinter as ctk
from controllers import inventario_controller, login_controller
from utils.debounce import Debouncer
from utils import event_bus
from widgets.pagination import PaginationBar


class InventarioView(ctk.CTkFrame):
    # Fase 6b: canal None = vista legacy completa (compat); "TIENDITA" o
    # "ALMACEN" = vista estanca (tabs y listas filtradas, sin cruce).
    CANAL_TITULOS = {None: "Inventario de Productos", "TIENDITA": "Tiendita",
                     "ALMACEN": "Almacén"}

    def __init__(self, parent, canal=None):
        super().__init__(parent, fg_color="transparent")
        self._canal = canal
        self._categorias_map = {}
        self._productos_map = {}
        self._pagina = 1
        self._per_page = 50
        self._total = 0
        self._q_actual = ""
        self._productos_compra_map = {}
        # Bloque B: vista Cards/Tabla + filtro por categoría (None = Todas)
        self._vista_modo = "Cards"
        self._filtro_categoria_id = None
        self._categorias_filtro_map = {}
        self._crear_widgets()
        self._cargar_combo_categorias()
        self._cargar_productos()
        # A1: el combo de compra quedaba en "Cargando..." hasta la primera
        # compra; el de movimiento hasta el primer uso. Cargar al instanciar.
        if self.tab_compra is not None:
            self._cargar_productos_compra()
        if self.tab_movimiento is not None:
            self._cargar_combo_productos()
        self._bus_handler = lambda *a, **kw: self.after(200, lambda: self._recargar_actual())
        event_bus.subscribe("producto_actualizado", self._bus_handler)

    def destroy(self):
        # Sin esto cada visita acumulaba un suscriptor zombi que retenía la
        # vista destruida y disparaba recargas fantasma en cada evento.
        try:
            if hasattr(self, "_bus_handler"):
                event_bus.unsubscribe("producto_actualizado", self._bus_handler)
        except Exception:
            pass
        try:
            if hasattr(self, "_debouncer"):
                self._debouncer.cancel()
        except Exception:
            pass
        super().destroy()

    def _tabs_para_canal(self):
        # Tiendita: sin Movimiento ni Historial (stock vía Compras/Ventas).
        # Almacén: sin Ventas (se agregan en TienditaView aparte).
        if self._canal == "TIENDITA":
            return ["Productos", "Registrar Producto", "Registrar Compra"]
        if self._canal == "ALMACEN":
            return ["Productos", "Registrar Producto", "Registrar Compra",
                    "Movimiento", "Historial"]
        return ["Productos", "Categorías", "Registrar Producto",
                "Registrar Compra", "Movimiento", "Historial"]

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self._tabs = {}
        for nombre in self._tabs_para_canal():
            self._tabs[nombre] = self.tabview.add(nombre)
        self.tab_productos = self._tabs.get("Productos")
        self.tab_categorias = self._tabs.get("Categorías")
        self.tab_form = self._tabs.get("Registrar Producto")
        self.tab_compra = self._tabs.get("Registrar Compra")
        self.tab_movimiento = self._tabs.get("Movimiento")
        self.tab_historial = self._tabs.get("Historial")

        if self.tab_productos is not None:
            self._crear_tab_productos()
        if self.tab_categorias is not None:
            self._crear_tab_categorias()
        if self.tab_form is not None:
            self._crear_tab_formulario()
        if self.tab_compra is not None:
            self._crear_tab_compra()
        if self.tab_movimiento is not None:
            self._crear_tab_movimiento()
        if self.tab_historial is not None:
            self._crear_tab_historial()

    def _crear_tab_productos(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec_titulo = crear_seccion(
            self.tab_productos, titulo=self.CANAL_TITULOS.get(self._canal, "Inventario de Productos"),
            icono="📦",
            descripcion="Stock, precios y movimientos. Clic en ▾ Ver detalle para valorizado, categoría y tallas.",
            nro=1,
        )
        crear_boton_interactivo(sec_titulo, text="+ Nuevo", width=110, command=self._nuevo_producto,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        sec_busq = crear_seccion(
            self.tab_productos, titulo="Búsqueda", icono="🔍",
            descripcion="Busca por nombre o código de producto.",
            nro=2,
        )
        busqueda_frame = ctk.CTkFrame(sec_busq, fg_color="transparent")
        busqueda_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.entry_busqueda = ctk.CTkEntry(
            busqueda_frame, placeholder_text="Buscar por nombre o código...",
            width=250,
        )
        self.entry_busqueda.pack(side="left", padx=5)
        self._debouncer = Debouncer(self, 300)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._debouncer.call(self._on_busqueda_cambiar))
        # B1: toggle Cards/Tabla (modo Excel denso)
        self.seg_vista = ctk.CTkSegmentedButton(
            busqueda_frame, values=["Cards", "Tabla"],
            command=self._on_vista_cambiar,
        )
        self.seg_vista.set("Cards")
        self.seg_vista.pack(side="left", padx=5)
        crear_nota(sec_busq, "Tip: clic en ▾ Ver detalle de cada tarjeta o fila para precios, valorizado y tallas.")
        # B2: filtro por categoría (segmentado Todas + cada una)
        self.filtro_cat_frame = ctk.CTkFrame(sec_busq, fg_color="transparent")
        self.filtro_cat_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._reconstruir_filtro_categorias()
        # B4: nota de objetivo del flujo de stock
        crear_nota(sec_busq, "El stock se mueve en Compras y Movimiento; aquí se consulta y se crean productos.")

        self.scroll_productos = ctk.CTkScrollableFrame(self.tab_productos)
        self.scroll_productos.pack(fill="both", expand=True, padx=5, pady=5)

        self.pagination = PaginationBar(self.tab_productos, on_page_change=self._on_page, per_page=50)
        self.pagination.pack(fill="x", padx=5, pady=4)

        self.label_status = ctk.CTkLabel(self.tab_productos, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status.pack(pady=3)

    def _crear_tab_categorias(self):
        header = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            header, text="Categorías de Productos",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Nueva", width=100,
            command=self._nueva_categoria,
        ).pack(side="right")

        self.scroll_categorias = ctk.CTkScrollableFrame(self.tab_categorias)
        self.scroll_categorias.pack(fill="both", expand=True, padx=5, pady=5)

        self.label_status_cat = ctk.CTkLabel(self.tab_categorias, text="", font=ctk.CTkFont(size=11))
        self.label_status_cat.pack(pady=3)

        self._cargar_categorias()

    def _cargar_categorias(self):
        for widget in self.scroll_categorias.winfo_children():
            widget.destroy()

        categorias = inventario_controller.listar_categorias()

        if not categorias:
            ctk.CTkLabel(
                self.scroll_categorias, text="No hay categorías registradas",
                text_color="gray",
            ).pack(pady=20)
            self.label_status_cat.configure(text="Total: 0")
            return

        for cat in categorias:
            card = ctk.CTkFrame(self.scroll_categorias)
            card.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(
                card, text=cat.get("nombre", ""),
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left", padx=10, pady=8)

            botones = ctk.CTkFrame(card, fg_color="transparent")
            botones.pack(side="right", padx=5, pady=5)

            ctk.CTkButton(
                botones, text="Editar", width=70, height=28,
                command=lambda c=cat: self._editar_categoria(c),
            ).pack(side="left", padx=2)

        self.label_status_cat.configure(text=f"Total: {len(categorias)} categoría(s)")

    def _nueva_categoria(self):
        dialog = ctk.CTkInputDialog(
            text="Nombre de la nueva categoría:", title="Nueva Categoría",
        )
        nombre = dialog.get_input()
        if not nombre:
            return

        exito, msg, _ = inventario_controller.crear_categoria({"nombre": nombre})
        if exito:
            self._cargar_categorias()
            self._cargar_combo_categorias()
        else:
            ctk.CTkLabel(self.scroll_categorias, text=msg, text_color="red").pack(pady=5)

    def _editar_categoria(self, cat):
        dialog = ctk.CTkInputDialog(
            text=f"Nuevo nombre para '{cat['nombre']}':", title="Editar Categoría",
        )
        nombre = dialog.get_input()
        if not nombre:
            return

        exito, msg = inventario_controller.editar_categoria(
            cat["id_categoria_producto"], {"nombre": nombre},
        )
        if exito:
            self._cargar_categorias()
            self._cargar_combo_categorias()

    def _crear_tab_formulario(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec1 = crear_seccion(scroll, titulo="Datos del producto", icono="📦",
                             descripcion="Nombre, categoría y canal. TIENDITA se vende; ALMACEN es solo movimientos.",
                             nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))

        self.label_codigo = ctk.CTkLabel(
            cuerpo1, text="Código: Generando...",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#7C3AED",
        )
        self.label_codigo.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Nombre *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(cuerpo1, placeholder_text="Nombre del producto", width=400)
        self.entry_nombre.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Categoría *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_categoria = ctk.CTkComboBox(cuerpo1, width=300, values=["Cargando..."])
        self.combo_categoria.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Canal", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_tipo_uso = ctk.CTkComboBox(
            cuerpo1, width=200,
            values=["ALMACEN", "TIENDITA"],
        )
        self.combo_tipo_uso.set("ALMACEN")
        self.combo_tipo_uso.pack(anchor="w", pady=(0, 5))

        sec2 = crear_seccion(scroll, titulo="Empaque y precios", icono="💰",
                             descripcion="Unidad: se pide COSTO X UNIDAD. Caja: COSTO TOTAL + cantidad; la app calcula el unitario y la ganancia sola.",
                             nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))

        row0 = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        row0.pack(fill="x", anchor="w", pady=3)
        self._row_empaque = row0

        ctk.CTkLabel(row0, text="Tipo empaque:").pack(side="left")
        self.combo_empaque = ctk.CTkComboBox(
            row0, width=140,
            values=["Unidad", "Caja x12", "Caja x100", "Personalizado"],
            command=lambda v: self._on_empaque_change(v),
        )
        self.combo_empaque.set("Unidad")
        self.combo_empaque.pack(side="left", padx=10)

        self.label_cant_caja = ctk.CTkLabel(row0, text="Cant. por caja:")
        self.entry_cant_caja = ctk.CTkEntry(row0, placeholder_text="1", width=80)
        self.entry_cant_caja.bind("<KeyRelease>", lambda e: self._actualizar_calculo())

        row1 = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        row1.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row1, text="Stock mínimo:").pack(side="left")
        self.entry_stock_min = ctk.CTkEntry(row1, placeholder_text="0", width=100)
        self.entry_stock_min.pack(side="left", padx=10)

        # Fase 6d: vocabulario Excel (COSTO X UNIDAD / COSTO TOTAL / COSTO VENTA)
        self.row_unit = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        ctk.CTkLabel(self.row_unit, text="COSTO X UNIDAD (S/) *:").pack(side="left")
        self.entry_unitario = ctk.CTkEntry(self.row_unit, placeholder_text="0.00", width=100)
        self.entry_unitario.pack(side="left", padx=10)
        self.entry_unitario.bind("<KeyRelease>", lambda e: self._actualizar_calculo())

        self.row_total = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        ctk.CTkLabel(self.row_total, text="COSTO TOTAL (S/) *:").pack(side="left")
        self.entry_precio_total = ctk.CTkEntry(self.row_total, placeholder_text="0.00", width=100)
        self.entry_precio_total.pack(side="left", padx=10)
        self.entry_precio_total.bind("<KeyRelease>", lambda e: self._actualizar_calculo())

        row2 = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        row2.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row2, text="COSTO VENTA x unidad (S/) *:").pack(side="left")
        self.entry_precio_venta = ctk.CTkEntry(row2, placeholder_text="0.00", width=100)
        self.entry_precio_venta.pack(side="left", padx=10)
        self.entry_precio_venta.bind("<KeyRelease>", lambda e: self._actualizar_calculo())
        self._on_empaque_change("Unidad")

        self.label_calculo = ctk.CTkLabel(
            cuerpo2, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#7C3AED",
        )
        self.label_calculo.pack(anchor="w", pady=4)

        rowm = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        rowm.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(rowm, text="Modo compra:").pack(side="left")
        self.combo_modo_compra = ctk.CTkComboBox(rowm, width=140, values=["YAPE", "EFECTIVO"])
        self.combo_modo_compra.set("EFECTIVO")
        self.combo_modo_compra.pack(side="left", padx=10)

        ctk.CTkLabel(rowm, text="Stock inicial (uds):").pack(side="left", padx=(10, 0))
        self.entry_stock_inicial = ctk.CTkEntry(rowm, placeholder_text="0", width=80)
        self.entry_stock_inicial.pack(side="left", padx=10)

        # B3: en Editar el stock es solo-lectura (se mueve en Compras/Movimiento)
        self.label_stock_readonly = ctk.CTkLabel(
            cuerpo2, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#7C3AED",
        )
        self.label_stock_nota = ctk.CTkLabel(
            cuerpo2, text="El stock se mueve en Compras y Movimiento (ENTRADA/SALIDA/AJUSTE), no aquí.",
            font=ctk.CTkFont(size=11), text_color="#6B5B7B",
        )

        sec3 = crear_seccion(scroll, titulo="Variante (opcional)", icono="👕",
                             descripcion="Solo para uniformes: tipo y talla crean variantes con stock propio.", nro=3)
        cuerpo3 = ctk.CTkFrame(sec3, fg_color="transparent")
        cuerpo3.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(cuerpo3, text="Tipo uniforme (opcional)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5,0))
        self.combo_tipo_uniforme = ctk.CTkComboBox(cuerpo3, width=300, values=["Sin tipo"])
        self.combo_tipo_uniforme.set("Sin tipo")
        self.combo_tipo_uniforme.pack(anchor="w", pady=(0, 5))
        self._tipos_uniforme_map = {}

        ctk.CTkLabel(cuerpo3, text="Talla (opcional, para uniformes)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5,0))
        self.combo_talla = ctk.CTkComboBox(cuerpo3, width=200, values=["UNICA", "S", "M", "L", "XL"])
        self.combo_talla.set("UNICA")
        self.combo_talla.pack(anchor="w", pady=(0, 5))

        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_form_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", padx=10, pady=(8, 2))

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=10, pady=(2, 8))

        self.btn_guardar = crear_boton_interactivo(
            btn_frame, text="Guardar", width=120,
            command=self._guardar_producto, fg_color="#7C3AED",
        )
        self.btn_guardar.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=120, fg_color="gray",
            command=lambda: self.tabview.set("Productos"),
        ).pack(side="left", padx=5)

        self._id_producto_editando = None

    def _crear_tab_compra(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_compra)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec = crear_seccion(scroll, titulo="Registrar Compra a proveedor", icono="🧾",
                            descripcion="Suma stock y guarda monto + método (Yape/Efectivo). Alimenta Compras y Ganancias del dashboard.",
                            nro=1)
        cuerpo = ctk.CTkFrame(sec, fg_color="transparent")
        cuerpo.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo, text="Producto *").pack(anchor="w")
        self.combo_producto_compra = ctk.CTkComboBox(cuerpo, width=400, values=["Cargando..."],
                                                    command=self._on_producto_compra)
        self.combo_producto_compra.pack(anchor="w", pady=3)
        self.label_compra_info = ctk.CTkLabel(cuerpo, text="", font=ctk.CTkFont(size=11), text_color="#6B5B7B")
        self.label_compra_info.pack(anchor="w", pady=2)

        row = ctk.CTkFrame(cuerpo, fg_color="transparent")
        row.pack(fill="x", anchor="w", pady=3)
        ctk.CTkLabel(row, text="Cantidad (uds) *").pack(side="left")
        self.entry_compra_cant = ctk.CTkEntry(row, width=100, placeholder_text="0")
        self.entry_compra_cant.pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Monto total pagado (S/) *").pack(side="left", padx=(10, 0))
        self.entry_compra_monto = ctk.CTkEntry(row, width=120, placeholder_text="0.00")
        self.entry_compra_monto.pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Método *").pack(side="left", padx=(10, 0))
        self.combo_compra_metodo = ctk.CTkComboBox(row, width=130, values=["YAPE", "EFECTIVO"])
        self.combo_compra_metodo.set("EFECTIVO")
        self.combo_compra_metodo.pack(side="left", padx=10)

        from widgets.date_picker import DatePicker
        self.date_compra = DatePicker(cuerpo, label_text="Fecha de compra:", default="today")
        self.date_compra.pack(anchor="w", pady=3)

        self.label_compra_status = ctk.CTkLabel(cuerpo, text="", font=ctk.CTkFont(size=12))
        self.label_compra_status.pack(anchor="w", pady=5)

        crear_boton_interactivo(cuerpo, text="Registrar Compra", width=160,
                                command=self._registrar_compra, fg_color="#7C3AED").pack(anchor="w", pady=5)
        crear_nota(sec, "Tip: el monto y el método quedan en el movimiento e historial.")
        self._productos_compra_map = {}

    def _on_producto_compra(self, selection):
        prod = self._productos_compra_map.get(selection)
        if not prod:
            return
        try:
            self.label_compra_info.configure(
                text=f"Stock: {prod.get('stock_actual',0)} • Costo unit. actual: S/{float(prod.get('precio_compra',0) or 0):.2f}")
        except Exception:
            pass

    def _registrar_compra(self):
        prod = self._productos_compra_map.get(self.combo_producto_compra.get())
        if not prod:
            self.label_compra_status.configure(text="Seleccione producto", text_color="red")
            return
        try:
            cant = int(self.entry_compra_cant.get().strip() or "0")
        except ValueError:
            cant = 0
        data = {"id_producto": prod["id_producto"], "cantidad": cant,
                "monto_total": self.entry_compra_monto.get().strip(),
                "metodo_pago": self.combo_compra_metodo.get(),
                "motivo": "Compra a proveedor",
                "fecha_movimiento": self.date_compra.get() or None}
        exito, msg, _ = inventario_controller.registrar_compra(data)
        self.label_compra_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self.entry_compra_cant.delete(0, "end")
            self.entry_compra_monto.delete(0, "end")
            self._cargar_productos()
            if self.tab_movimiento is not None:
                self._cargar_combo_productos()
            self._cargar_productos_compra()

    def _cargar_productos_compra(self):
        try:
            prods = inventario_controller.listar_productos(activo=1)
            if self._canal is not None:
                prods = [p for p in prods if p.get("canal") == self._canal]
        except Exception:
            prods = []
        nombres = [f"{p.get('codigo','')} - {p.get('nombre','')}" for p in prods]
        self.combo_producto_compra.configure(values=nombres if nombres else ["Sin productos"])
        self._productos_compra_map = {n: p for n, p in zip(nombres, prods)}

    def _crear_tab_movimiento(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_movimiento)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec = crear_seccion(scroll, titulo="Registrar Movimiento", icono="🔄",
                            descripcion="ENTRADA suma, SALIDA resta (valida stock), AJUSTE fija el stock.",
                            nro=1)
        cuerpo = ctk.CTkFrame(sec, fg_color="transparent")
        cuerpo.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo, text="Producto:").pack(anchor="w")
        self.combo_producto = ctk.CTkComboBox(cuerpo, width=400, values=["Cargando..."])
        self.combo_producto.pack(anchor="w", pady=3)

        self.label_stock_actual = ctk.CTkLabel(
            cuerpo, text="",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#7C3AED",
        )
        self.label_stock_actual.pack(anchor="w", pady=(0, 3))

        ctk.CTkLabel(cuerpo, text="Tipo de movimiento:").pack(anchor="w")
        self.combo_tipo_mov = ctk.CTkComboBox(
            cuerpo, width=200,
            values=["ENTRADA", "SALIDA", "AJUSTE"],
        )
        self.combo_tipo_mov.set("ENTRADA")
        self.combo_tipo_mov.pack(anchor="w", pady=3)

        ctk.CTkLabel(cuerpo, text="Cantidad:").pack(anchor="w")
        self.entry_cantidad = ctk.CTkEntry(cuerpo, placeholder_text="0", width=150)
        self.entry_cantidad.pack(anchor="w", pady=3)

        ctk.CTkLabel(cuerpo, text="Motivo:").pack(anchor="w")
        self.entry_motivo = ctk.CTkEntry(cuerpo, placeholder_text="Motivo del movimiento", width=400)
        self.entry_motivo.pack(anchor="w", pady=3)

        from widgets.date_picker import DatePicker as _DP
        self.date_mov = _DP(cuerpo, label_text="Fecha del movimiento:", default="today")
        self.date_mov.pack(anchor="w", pady=3)
        crear_nota(sec, "Todo movimiento queda en el Historial con usuario y fecha.")

        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_mov_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_mov_status.pack(anchor="w", padx=10, pady=(8, 2))

        crear_boton_interactivo(
            footer, text="Registrar Movimiento", width=180,
            command=self._registrar_movimiento, fg_color="#7C3AED",
        ).pack(anchor="w", padx=10, pady=(2, 8))

    def _crear_tab_historial(self):
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_historial, titulo="Historial de Movimientos", icono="📜",
            descripcion="Entradas, salidas y ajustes con usuario y fecha.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_historial,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        self.scroll_historial = ctk.CTkScrollableFrame(self.tab_historial)
        self.scroll_historial.pack(fill="both", expand=True, padx=5, pady=5)

        self.label_status_hist = ctk.CTkLabel(self.tab_historial, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status_hist.pack(pady=3)

    def _recargar_actual(self):
        # Fase 6e: el evento ahora sí llega (publish en controllers);
        # refresca lista + combos + categorías.
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_productos()
        try:
            if self.tab_compra is not None:
                self._cargar_productos_compra()
            if self.tab_movimiento is not None:
                self._cargar_combo_productos()
            if self.tab_categorias is not None:
                self._cargar_categorias()
                self._cargar_combo_categorias()
        except Exception:
            pass

    def _on_page(self, page, per_page):
        self._pagina = page
        self._cargar_paginado()

    def _cargar_productos(self):
        self._q_actual = self.entry_busqueda.get().strip()
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _on_busqueda_cambiar(self, event=None):
        self._q_actual = self.entry_busqueda.get().strip()
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _cargar_paginado(self):
        for widget in self.scroll_productos.winfo_children():
            widget.destroy()

        cat_id = getattr(self, "_filtro_categoria_id", None)
        try:
            from repositories import producto_repository
            offset = (self._pagina - 1) * self._per_page
            rows, total = producto_repository.buscar_paginado(
                q=self._q_actual, limit=self._per_page, offset=offset,
                id_categoria_producto=cat_id, canal=self._canal)
            self._total = total
            if hasattr(self, 'pagination'):
                self.pagination.set_total(total)
        except Exception:
            from utils.busqueda import coincide as _coincide
            todos = inventario_controller.listar_productos()
            if self._canal is not None:
                todos = [p for p in todos if p.get("canal") == self._canal]
            if cat_id is not None:
                todos = [p for p in todos if p.get("id_categoria_producto") == cat_id]
            if self._q_actual:
                rows = [p for p in todos if _coincide(
                    self._q_actual, p.get('nombre', ''), p.get('codigo', ''))]
                total = len(rows)
                rows = rows[(self._pagina - 1) * self._per_page : self._pagina * self._per_page]
            else:
                total = len(todos)
                rows = todos[(self._pagina - 1) * self._per_page : self._pagina * self._per_page]
            self._total = total

        if not rows:
            ctk.CTkLabel(self.scroll_productos, text="No se encontraron productos", text_color="gray").pack(pady=20)
            self.label_status.configure(text=f"Total: {self._total} • Página {self._pagina}")
            return

        if getattr(self, "_vista_modo", "Cards") == "Tabla":
            self._render_tabla_productos(rows)
        else:
            for prod in rows:
                self._crear_card_producto(prod)

        total_paginas = max(1, (self._total + self._per_page - 1) // self._per_page)
        self.label_status.configure(text=f"Total: {self._total} producto(s) • Página {self._pagina}/{total_paginas} • 50 por página")

    # ── Bloque B1: tabla densa modo Excel (misma data que las cards) ──
    @staticmethod
    def _metricas_producto(prod):
        compra = float(prod.get('precio_compra', 0) or prod.get('precio', 0) or 0)
        venta = float(prod.get('precio_venta', 0) or prod.get('precio', 0) or 0)
        gan_u = round(venta - compra, 2)
        pct = round(gan_u / compra * 100, 1) if compra else 0
        total_inv = round(compra * (prod.get('stock_actual', 0) or 0), 2)
        return compra, venta, gan_u, pct, total_inv

    def _render_tabla_productos(self, rows):
        header = ctk.CTkFrame(self.scroll_productos, fg_color="#3D1559", corner_radius=6)
        header.pack(fill="x", padx=6, pady=(4, 2))
        cols = ["Código", "Nombre", "Categoría", "Stock", "Compra", "Venta", "Gan.%", "Total inv.", ""]
        anchos = [90, 200, 130, 60, 80, 80, 70, 90, 40]
        for i, (c, a) in enumerate(zip(cols, anchos)):
            lbl = ctk.CTkLabel(header, text=c, width=a,
                               font=ctk.CTkFont(size=11, weight="bold"), text_color="white")
            lbl.grid(row=0, column=i, padx=2, pady=6, sticky="w")

        for prod in rows:
            compra, venta, _gan_u, pct, total_inv = self._metricas_producto(prod)
            stock_bajo = (prod.get("stock_actual", 0) or 0) <= (prod.get("stock_minimo", 0) or 0) \
                and (prod.get("stock_minimo", 0) or 0) > 0
            fila = ctk.CTkFrame(self.scroll_productos, fg_color="white", corner_radius=6)
            fila.pack(fill="x", padx=6, pady=1)
            vals = [str(prod.get("codigo", "")), str(prod.get("nombre", "")),
                    str(prod.get("categoria_nombre", "")),
                    str(prod.get("stock_actual", 0)), f"S/{compra:.2f}",
                    f"S/{venta:.2f}", f"{pct:.1f}%", f"S/{total_inv:.2f}"]
            for i, (v, a) in enumerate(zip(vals, anchos)):
                color = "red" if (i == 3 and stock_bajo) else "#1F0A33"
                ctk.CTkLabel(fila, text=v, width=a,
                             font=ctk.CTkFont(size=11), text_color=color).grid(
                    row=0, column=i, padx=2, pady=4, sticky="w")
            detalle = ctk.CTkFrame(fila, fg_color="transparent")
            detalle.grid(row=1, column=0, columnspan=len(cols), sticky="ew", padx=10)
            self._poblar_detalle(detalle, prod)
            detalle.grid_remove()
            btn = ctk.CTkButton(fila, text="▾", width=anchos[-1], height=24,
                                fg_color="transparent", text_color="#7C3AED")
            btn.grid(row=0, column=len(cols) - 1, padx=2, pady=4)
            btn.configure(command=lambda d=detalle, b=btn: (
                d.grid_remove(), b.configure(text="▾")) if d.winfo_viewable()
                else (d.grid(), b.configure(text="▴")))

    def _poblar_detalle(self, frame, prod):
        from utils.ui_helpers import linea_detalle
        compra = float(prod.get("precio_compra", 0) or prod.get("precio", 0) or 0)
        venta = float(prod.get("precio_venta", 0) or prod.get("precio", 0) or 0)
        try:
            gan = round(venta - compra, 2)
            pct = round(gan / compra * 100, 1) if compra else 0
            val = round(compra * (prod.get("stock_actual", 0) or 0), 2)
            linea_detalle(frame, "Compra unit. / Venta", f"S/{compra:.2f} / S/{venta:.2f}")
            linea_detalle(frame, "Ganancia", f"S/{gan:.2f} ({pct:.1f}%)")
            linea_detalle(frame, "Total inventario", f"S/{val:.2f}")
            linea_detalle(frame, "Empaque", f"{prod.get('tipo_empaque') or 'Unidad'} x {prod.get('cantidad_por_caja', 1) or 1}")
        except Exception:
            linea_detalle(frame, "Precios", f"{compra} / {venta}")
        linea_detalle(frame, "ID producto", prod.get("id_producto"))
        linea_detalle(frame, "Categoría", prod.get("categoria_nombre"))
        linea_detalle(frame, "Canal", prod.get("canal"))
        linea_detalle(frame, "Uniforme", prod.get("tipo_uniforme_nombre") or prod.get("nombre_tipo_uniforme"))
        linea_detalle(frame, "Stock mín.", prod.get("stock_minimo"))
        _bajo = ((prod.get('stock_actual', 0) or 0) <= (prod.get('stock_minimo', 0) or 0)) and ((prod.get('stock_minimo', 0) or 0) > 0)
        linea_detalle(frame, "Estado", "⚠ BAJO STOCK" if _bajo else "OK")

    def _crear_card_producto(self, prod):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible
        card = crear_card_interactiva(self.scroll_productos)
        card.pack(fill="x", padx=6, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        stock_bajo = prod.get("stock_actual", 0) <= prod.get("stock_minimo", 0)
        stock_color = "red" if stock_bajo and prod.get("stock_minimo", 0) > 0 else "gray"

        ctk.CTkLabel(
            info,
            text=f"{prod.get('codigo', '')} - {prod.get('nombre', '')}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33",
        ).pack(anchor="w")

        compra = float(prod.get('precio_compra', 0) or prod.get('precio', 0) or 0)
        venta = float(prod.get('precio_venta', 0) or prod.get('precio', 0) or 0)
        gan_u = round(venta - compra, 2)
        pct = round(gan_u / compra * 100, 1) if compra else 0
        total_inv = round(compra * (prod.get('stock_actual', 0) or 0), 2)
        tipo_u = prod.get('tipo_uniforme_nombre') or prod.get('nombre_tipo_uniforme') or ''
        empaque = prod.get('tipo_empaque') or 'Unidad'
        ctk.CTkLabel(
            info,
            text=f"{prod.get('categoria_nombre', '')} | {empaque}" + (f" | Uniforme: {tipo_u}" if tipo_u else ""),
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"Compra: S/{compra:.2f}  •  Venta: S/{venta:.2f}  •  Ganancia: S/{gan_u:.2f} ({pct:.1f}%)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#1F0A33",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"Stock: {prod.get('stock_actual', 0)} (mín {prod.get('stock_minimo', 0)})  •  Total inventario: S/{total_inv:.2f}" + (f"  •  Tallas: ver variantes" if prod.get('id_tipo_uniforme') else ""),
            font=ctk.CTkFont(size=12), text_color=stock_color,
        ).pack(anchor="w")

        botones = ctk.CTkFrame(top, fg_color="transparent")
        botones.pack(side="right", padx=5, pady=5)

        ctk.CTkButton(
            botones, text="Editar", width=70, height=28,
            command=lambda p=prod: self._editar_producto(p),
        ).pack(side="left", padx=2)

        # Fase 6b: sin tab Movimiento (Tiendita) no hay botón directo;
        # el stock se mueve en Compras/Ventas.
        if self.tab_movimiento is not None:
            ctk.CTkButton(
                botones, text="Movimiento", width=90, height=28,
                fg_color="#7C3AED", hover_color="#6D28D9",  # Morado
                command=lambda p=prod: self._ir_movimiento(p),
            ).pack(side="left", padx=2)

        # ── Detalle expandible inline (mismo que la vista Tabla) ──
        toggle_btn, _, _ = agregar_detalle_expandible(
            card, lambda frame, _p=prod: self._poblar_detalle(frame, _p))
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    def _nuevo_producto(self):
        self._limpiar_formulario()
        self._cargar_combo_categorias()
        self._cargar_combo_tipos_uniforme()
        self.label_codigo.configure(text="Código: Se generará al guardar")
        self._id_producto_editando = None
        # Fase 6b: vista estanca → canal fijo y bloqueado (no se cruza)
        if self._canal is not None:
            try:
                self.combo_tipo_uso.set(self._canal)
                self.combo_tipo_uso.configure(state="disabled")
            except Exception:
                pass
        try:
            self.entry_stock_inicial.configure(state="normal")
        except Exception:
            pass
        try:
            self.label_stock_readonly.pack_forget()
            self.label_stock_nota.pack_forget()
        except Exception:
            pass
        self.tabview.set("Registrar Producto")

    def _cargar_combo_tipos_uniforme(self):
        try:
            from controllers import tipo_uniforme_controller
            tipos = tipo_uniforme_controller.listar_tipos()
        except Exception:
            from services import tipo_uniforme_service
            tipos = tipo_uniforme_service.listar_tipos()
        nombres = ["Sin tipo"] + [t["nombre"] for t in tipos]
        self.combo_tipo_uniforme.configure(values=nombres)
        self._tipos_uniforme_map = {t["nombre"]: t["id_tipo_uniforme"] for t in tipos}
        if "Sin tipo" not in self._tipos_uniforme_map:
            self._tipos_uniforme_map["Sin tipo"] = None

    def _editar_producto(self, prod):
        self._limpiar_formulario()
        self._cargar_combo_categorias()
        self._cargar_combo_tipos_uniforme()
        self._id_producto_editando = prod["id_producto"]

        producto = inventario_controller.obtener_producto(prod["id_producto"])
        if producto:
            # B3: stock solo-lectura + nota/link a Compras (AJUSTE sigue en Movimiento)
            try:
                self.label_stock_readonly.configure(
                    text=f"Stock actual: {producto.get('stock_actual', 0)} (solo lectura)")
                self.label_stock_readonly.pack(anchor="w", pady=(4, 0))
                self.label_stock_nota.pack(anchor="w")
                self.entry_stock_inicial.configure(state="disabled")
            except Exception:
                pass
            self.label_codigo.configure(text=f"Código: {producto.get('codigo', '')}")
            self.entry_nombre.insert(0, producto.get("nombre", ""))
            self.combo_tipo_uso.set(producto.get("canal", "ALMACEN"))
            self.entry_stock_min.insert(0, str(producto.get("stock_minimo", 0)))
            self.combo_empaque.set(producto.get("tipo_empaque", "Unidad") or "Unidad")
            self._on_empaque_change(self.combo_empaque.get())
            self.entry_unitario.delete(0, "end")
            self.entry_unitario.insert(0, str(producto.get("precio_compra", producto.get("precio", 0)) or ""))
            self.entry_cant_caja.delete(0, "end")
            self.entry_cant_caja.insert(0, str(producto.get("cantidad_por_caja", 1) or 1))
            self.entry_precio_total.delete(0, "end")
            self.entry_precio_total.insert(0, str(producto.get("precio_compra_total", producto.get("precio_compra", 0)) or ""))
            self.entry_precio_venta.insert(0, str(producto.get("precio_venta", producto.get("precio", 0))))
            self._actualizar_calculo()
            if producto.get("id_tipo_uniforme"):
                for k, v in self._tipos_uniforme_map.items():
                    if v == producto.get("id_tipo_uniforme"):
                        self.combo_tipo_uniforme.set(k)
                        break

        self.tabview.set("Registrar Producto")

    def _on_empaque_change(self, valor):
        # Fase 6d: Unidad pide COSTO X UNIDAD; Caja pide COSTO TOTAL + cantidad
        es_unidad = (valor or self.combo_empaque.get()) == "Unidad"
        try:
            if es_unidad:
                self.row_total.pack_forget()
                ref = getattr(self, "_row_empaque", None)
                if ref is not None:
                    self.row_unit.pack(fill="x", anchor="w", pady=3, after=ref)
                else:
                    self.row_unit.pack(fill="x", anchor="w", pady=3)
                self.label_cant_caja.pack_forget()
                self.entry_cant_caja.pack_forget()
                self.label_calculo.configure(text="")
            else:
                self.row_unit.pack_forget()
                self.row_total.pack(fill="x", anchor="w", pady=3)
                self.label_cant_caja.pack(side="left", padx=(10, 0))
                self.entry_cant_caja.pack(side="left", padx=10)
                self._actualizar_calculo()
        except Exception:
            pass

    def _actualizar_calculo(self):
        # cálculo en vivo: unitario y ganancia (misma fórmula del service)
        try:
            from services import inventario_service
            emp = self.combo_empaque.get()
            venta_txt = self.entry_precio_venta.get().strip()
            if emp == "Unidad":
                unit_txt = self.entry_unitario.get().strip()
                if not unit_txt or not venta_txt:
                    self.label_calculo.configure(text="")
                    return
                unit = float(unit_txt)
                gan = round(float(venta_txt) - unit, 2)
                pct = round(gan / unit * 100, 1) if unit else 0
                self.label_calculo.configure(
                    text=f"COSTO X UNIDAD: S/{unit:.2f}  •  Ganancia: S/{gan:.2f} ({pct:.1f}%)")
                return
            total_txt = self.entry_precio_total.get().strip()
            if not total_txt or not venta_txt:
                self.label_calculo.configure(text="")
                return
            cant_txt = self.entry_cant_caja.get().strip()
            cant = int(cant_txt) if cant_txt else 1
            r = inventario_service.calcular_unitario_y_ganancia(float(total_txt), cant, float(venta_txt))
            self.label_calculo.configure(
                text=f"COSTO X UNIDAD: S/{r['unitario']:.2f}  •  Ganancia: S/{r['ganancia_unitaria']:.2f} ({r['ganancia_pct']:.1f}%)")
        except Exception:
            try:
                self.label_calculo.configure(text="")
            except Exception:
                pass

    def _guardar_producto(self):
        # Fase 6d: Unidad manda COSTO X UNIDAD; Caja manda COSTO TOTAL.
        emp = self.combo_empaque.get()
        if emp == "Unidad":
            unit = self.entry_unitario.get().strip() or "0"
            total_txt, cant_txt, precio_txt = unit, "1", unit
        else:
            total_txt = self.entry_precio_total.get().strip()
            cant_txt = self.entry_cant_caja.get().strip() or "1"
            try:
                precio_txt = str(round(float(total_txt) / max(int(cant_txt), 1), 2))
            except (ValueError, ZeroDivisionError):
                precio_txt = total_txt
        data = {
            "nombre": self.entry_nombre.get().strip(),
            "canal": self.combo_tipo_uso.get(),
            "stock_minimo": self.entry_stock_min.get().strip() or "0",
            "precio": precio_txt,
            "tipo_empaque": emp,
            "cantidad_por_caja": cant_txt,
            "precio_compra_total": total_txt,
            "precio_venta": self.entry_precio_venta.get().strip() or "0",
            "modo_compra": self.combo_modo_compra.get(),
            "stock_inicial": self.entry_stock_inicial.get().strip() or "0",
        }
        tipo_sel = self.combo_tipo_uniforme.get()
        if tipo_sel in self._tipos_uniforme_map:
            data["id_tipo_uniforme"] = self._tipos_uniforme_map[tipo_sel]
        # talla escalable (S1)
        talla_sel = self.combo_talla.get().strip() if hasattr(self, 'combo_talla') else "UNICA"
        if talla_sel and talla_sel != "UNICA":
            data["talla"] = talla_sel

        cat_selection = self.combo_categoria.get()
        if cat_selection in self._categorias_map:
            data["id_categoria_producto"] = self._categorias_map[cat_selection]

        # Fase 6b: en vista estanca el canal no se negocia (combo bloqueado)
        if self._canal is not None:
            data["canal"] = self._canal

        if self._id_producto_editando:
            exito, msg = inventario_controller.editar_producto(self._id_producto_editando, data)
        else:
            exito, msg, _ = inventario_controller.crear_producto(data)

        if exito:
            self.label_form_status.configure(text=msg, text_color="green")
            self._limpiar_formulario()
            self._cargar_productos()
            self.tabview.set("Productos")
        else:
            self.label_form_status.configure(text=msg, text_color="red")

    def _cargar_combo_categorias(self):
        categorias = inventario_controller.listar_categorias(activo=1)
        nombres = [c["nombre"] for c in categorias]
        self.combo_categoria.configure(values=nombres if nombres else ["Sin categorías"])
        self._categorias_map = {c["nombre"]: c["id_categoria_producto"] for c in categorias}
        self._reconstruir_filtro_categorias()

    # ── Bloque B1/B2: vista Cards/Tabla + filtro por categoría ──
    def _on_vista_cambiar(self, valor):
        self._vista_modo = valor
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _on_filtro_categoria(self, valor):
        self._filtro_categoria_id = self._categorias_filtro_map.get(valor)
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _reconstruir_filtro_categorias(self):
        if not hasattr(self, "filtro_cat_frame"):
            return
        for w in self.filtro_cat_frame.winfo_children():
            w.destroy()
        try:
            categorias = inventario_controller.listar_categorias(activo=1)
        except Exception:
            categorias = []
        nombres = [c["nombre"] for c in categorias]
        self._categorias_filtro_map = {"Todas": None}
        self._categorias_filtro_map.update(
            {c["nombre"]: c["id_categoria_producto"] for c in categorias}
        )
        # Si el filtro actual ya no existe (categoría desactivada), volver a Todas
        actual = next((k for k, v in self._categorias_filtro_map.items()
                       if v == self._filtro_categoria_id), "Todas")
        self._filtro_categoria_id = self._categorias_filtro_map[actual]
        seg = ctk.CTkSegmentedButton(
            self.filtro_cat_frame, values=["Todas"] + nombres,
            command=self._on_filtro_categoria,
        )
        try:
            seg.set(actual)
        except Exception:
            pass
        seg.pack(side="left", padx=5)
        self.seg_categoria = seg

    def _ir_movimiento(self, prod):
        if self.tab_movimiento is None:
            return
        self._cargar_combo_productos()
        self.tabview.set("Movimiento")
        for key, val in self._productos_map.items():
            if val["id_producto"] == prod["id_producto"]:
                self.combo_producto.set(key)
                self._on_producto_seleccionado(key)
                break

    def _cargar_combo_productos(self):
        productos = inventario_controller.listar_productos(activo=1)
        if self._canal is not None:
            productos = [p for p in productos if p.get("canal") == self._canal]
        nombres = [f"{p.get('codigo', '')} - {p.get('nombre', '')}" for p in productos]
        self.combo_producto.configure(values=nombres if nombres else ["Sin productos"])
        self._productos_map = {n: p for n, p in zip(nombres, productos)}
        self.combo_producto.configure(command=self._on_producto_seleccionado)

    def _on_producto_seleccionado(self, seleccion):
        prod = self._productos_map.get(seleccion)
        if prod:
            self.label_stock_actual.configure(
                text=f"Stock actual: {prod.get('stock_actual', 0)}",
            )
        else:
            self.label_stock_actual.configure(text="")

    def _registrar_movimiento(self):
        prod_selection = self.combo_producto.get()
        prod = self._productos_map.get(prod_selection)
        if not prod:
            self.label_mov_status.configure(text="Seleccione un producto", text_color="red")
            return
        id_prod = prod["id_producto"]

        cantidad_str = self.entry_cantidad.get().strip()
        if not cantidad_str:
            self.label_mov_status.configure(text="Ingrese la cantidad", text_color="red")
            return

        usuario = login_controller.obtener_usuario_actual()
        if not usuario:
            self.label_mov_status.configure(text="Sesión no válida", text_color="red")
            return

        data = {
            "id_producto": id_prod,
            "tipo_movimiento": self.combo_tipo_mov.get(),
            "cantidad": cantidad_str,
            "motivo": self.entry_motivo.get().strip(),
            "id_usuario": usuario["id_usuario"],
            "fecha_movimiento": self.date_mov.get() or None,
        }

        exito, msg, _ = inventario_controller.registrar_movimiento(data)

        if exito:
            self.label_mov_status.configure(text=msg, text_color="green")
            self._cargar_productos()
            self._cargar_historial()
            self.entry_cantidad.delete(0, "end")
            self.entry_motivo.delete(0, "end")
        else:
            self.label_mov_status.configure(text=msg, text_color="red")

    def _cargar_historial(self):
        for widget in self.scroll_historial.winfo_children():
            widget.destroy()

        movimientos = inventario_controller.listar_movimientos()

        if not movimientos:
            ctk.CTkLabel(
                self.scroll_historial, text="No hay movimientos registrados",
                text_color="gray",
            ).pack(pady=20)
            self.label_status_hist.configure(text="Total: 0")
            return

        for mov in movimientos:
            card = ctk.CTkFrame(self.scroll_historial)
            card.pack(fill="x", padx=5, pady=3)

            tipo = mov.get("tipo_movimiento", "")
            color = {"ENTRADA": "green", "SALIDA": "red", "AJUSTE": "orange"}.get(tipo, "gray")

            ctk.CTkLabel(
                card,
                text=f"{mov.get('codigo', '')} - {mov.get('producto_nombre', '')}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(
                card,
                text=f"{tipo}: {mov.get('cantidad', 0)} | "
                     f"Stock: {mov.get('stock_anterior', 0)} → {mov.get('stock_nuevo', 0)}",
                font=ctk.CTkFont(size=12), text_color=color,
            ).pack(side="left", padx=10)

        self.label_status_hist.configure(text=f"Total: {len(movimientos)} movimiento(s)")

    def _limpiar_formulario(self):
        self._id_producto_editando = None
        self.entry_nombre.delete(0, "end")
        self.combo_tipo_uso.set("ALMACEN")
        self.entry_stock_min.delete(0, "end")
        try:
            self.entry_unitario.delete(0, "end")
        except Exception:
            pass
        try:
            self.entry_stock_inicial.configure(state="normal")
        except Exception:
            pass
        try:
            self.label_stock_readonly.pack_forget()
            self.label_stock_nota.pack_forget()
        except Exception:
            pass
        try:
            self.combo_empaque.set("Unidad")
            self._on_empaque_change("Unidad")
            self.entry_cant_caja.delete(0, "end")
            self.entry_precio_total.delete(0, "end")
            self.entry_precio_venta.delete(0, "end")
            self.combo_modo_compra.set("EFECTIVO")
            self.entry_stock_inicial.delete(0, "end")
            self.label_calculo.configure(text="")
            self.combo_tipo_uniforme.set("Sin tipo")
        except Exception:
            pass
        self.label_form_status.configure(text="")
