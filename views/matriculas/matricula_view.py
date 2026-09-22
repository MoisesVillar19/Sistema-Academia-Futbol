import customtkinter as ctk
from controllers import matricula_controller, estudiante_controller
from utils.debounce import Debouncer
from utils import event_bus
from widgets.pagination import PaginationBar


class MatriculaView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._estudiantes_map = {}
        self._tarifas_map = {}
        self._becas_map = {}
        self._matriculas_map = {}
        self._pagina = 1
        self._per_page = 50
        self._total = 0
        self._q_actual = ""
        self._crear_widgets()
        self._cargar_matriculas()
        self._bus_handler = lambda *a, **kw: self.after(200, lambda: self._recargar_actual())
        event_bus.subscribe("matricula_creada", self._bus_handler)
        # Fase 6e: refrescar extras cuando cambian productos en Tiendita
        self._bus_prod_handler = lambda *a, **kw: self.after(200, lambda: self._recargar_productos())
        event_bus.subscribe("producto_actualizado", self._bus_prod_handler)

    def _recargar_productos(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        try:
            self._cargar_productos_matricula()
        except Exception:
            pass

    def destroy(self):
        # Sin esto cada visita acumulaba un suscriptor zombi que retenía la
        # vista destruida y disparaba recargas fantasma en cada evento.
        try:
            if hasattr(self, "_bus_handler"):
                event_bus.unsubscribe("matricula_creada", self._bus_handler)
        except Exception:
            pass
        try:
            if hasattr(self, "_bus_prod_handler"):
                event_bus.unsubscribe("producto_actualizado", self._bus_prod_handler)
        except Exception:
            pass
        try:
            if hasattr(self, "_debouncer"):
                self._debouncer.cancel()
        except Exception:
            pass
        super().destroy()

    def _on_busqueda_cambiar(self, event=None):
        self._q_actual = self.entry_busqueda.get().strip()
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_matriculas()

    def _refrescar_banner(self):
        from utils.ui_helpers import crear_banner_avisos
        for w in self.banner_frame.winfo_children():
            w.destroy()
        try:
            from services import avisos_service
            avisos = avisos_service.avisos_por_modulo("matriculas")
        except Exception:
            avisos = []
        for av in avisos:
            crear_banner_avisos(self.banner_frame, av["texto"], None, av["severidad"])

    def _on_page(self, page, per_page):
        self._pagina = page
        self._cargar_matriculas()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_lista = self.tabview.add("Matrículas")
        self.tab_form = self.tabview.add("Registrar")
        self.tab_rapida = self.tabview.add("Rápida")
        self.tab_cuotas = self.tabview.add("Cuotas")
        self.tab_grilla = self.tabview.add("Año")

        self._crear_tab_lista()
        self._crear_tab_formulario()
        self._crear_tab_rapida()
        self._crear_tab_cuotas()
        self._crear_tab_grilla()

    def _crear_tab_rapida(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_rapida)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec = crear_seccion(scroll, titulo="Matrícula rápida", icono="⚡",
                            descripcion="Nombre + tipo + monto + pago en 1 clic. Apoderado se completa después en Estudiantes.",
                            nro=1)
        cuerpo = ctk.CTkFrame(sec, fg_color="transparent")
        cuerpo.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo, text="Tipo *").pack(anchor="w")
        self.seg_exp_tipo = ctk.CTkSegmentedButton(
            cuerpo, values=["NUEVO", "ANTIGUO"], command=self._on_exp_tipo)
        self.seg_exp_tipo.set("NUEVO")
        self.seg_exp_tipo.pack(anchor="w", pady=3)
        try:
            self._default_nuevo = f"{matricula_controller.monto_express_default():.2f}"
        except Exception:
            self._default_nuevo = "120.00"
        self.label_exp_panel = ctk.CTkLabel(
            cuerpo, text=f"🆕 Incluye uniforme + mensualidad • S/ {self._default_nuevo} (editable)",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#7C3AED",
            wraplength=500, justify="left")
        self.label_exp_panel.pack(anchor="w", pady=(0, 5))

        row = ctk.CTkFrame(cuerpo, fg_color="transparent")
        row.pack(fill="x", anchor="w", pady=3)
        ctk.CTkLabel(row, text="Nombres *").pack(side="left")
        self.entry_exp_nombres = ctk.CTkEntry(row, placeholder_text="Nombres", width=190)
        self.entry_exp_nombres.pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Apellidos *").pack(side="left")
        self.entry_exp_apellidos = ctk.CTkEntry(row, placeholder_text="Apellidos", width=190)
        self.entry_exp_apellidos.pack(side="left", padx=10)

        row2 = ctk.CTkFrame(cuerpo, fg_color="transparent")
        row2.pack(fill="x", anchor="w", pady=3)
        self.label_exp_doc = ctk.CTkLabel(row2, text="DNI (8 dígitos) *")
        self.label_exp_doc.pack(side="left")
        self.combo_exp_tipodoc = ctk.CTkComboBox(
            row2, width=110, values=["DNI", "CARNET"],
            command=self._on_exp_tipodoc,
        )
        self.combo_exp_tipodoc.set("DNI")
        self.combo_exp_tipodoc.pack(side="left", padx=5)
        self.entry_exp_dni = ctk.CTkEntry(row2, placeholder_text="12345678", width=140)
        self.entry_exp_dni.pack(side="left", padx=10)
        ctk.CTkLabel(row2, text="Monto S/ *").pack(side="left", padx=(10, 0))
        self.entry_exp_monto = ctk.CTkEntry(row2, placeholder_text=self._default_nuevo, width=120)
        self.entry_exp_monto.pack(side="left", padx=10)
        self.entry_exp_monto.insert(0, self._default_nuevo)
        ctk.CTkLabel(row2, text="Pago *").pack(side="left", padx=(10, 0))
        self.combo_exp_metodo = ctk.CTkComboBox(row2, width=130, values=["YAPE", "EFECTIVO"])
        self.combo_exp_metodo.set("EFECTIVO")
        self.combo_exp_metodo.pack(side="left", padx=10)

        comp_row = ctk.CTkFrame(cuerpo, fg_color="transparent")
        comp_row.pack(fill="x", anchor="w", pady=3)
        self.btn_exp_comp = ctk.CTkButton(comp_row, text="📎 Comprobante (Yape)", width=180,
                                          command=self._elegir_comprobante_exp)
        self.btn_exp_comp.pack(side="left", padx=5)
        self.label_exp_comp = ctk.CTkLabel(comp_row, text="Sin comprobante", text_color="gray")
        self.label_exp_comp.pack(side="left", padx=5)
        self._exp_comprobante = None

        from widgets.date_picker import DatePicker as _DP2
        self.date_express = _DP2(cuerpo, label_text="Fecha de inicio (INICIO):", default="today")
        self.date_express.pack(anchor="w", pady=3)
        crear_nota(sec, "Yape exige comprobante (RN-042). Efectivo no.")

        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_exp_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_exp_status.pack(anchor="w", padx=10, pady=(8, 2))
        crear_boton_interactivo(footer, text="Guardar y Matricular", width=180,
                                command=self._guardar_express, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=(2, 8))

    def _on_exp_tipo(self, selection):
        sel = selection if isinstance(selection, str) else self.seg_exp_tipo.get()
        try:
            if sel == "NUEVO":
                try:
                    self._default_nuevo = f"{matricula_controller.monto_express_default():.2f}"
                except Exception:
                    pass
                self.label_exp_panel.configure(
                    text=f"🆕 Incluye uniforme + mensualidad • S/ {self._default_nuevo} (editable)")
                if not self.entry_exp_monto.get().strip():
                    self.entry_exp_monto.insert(0, self._default_nuevo)
            else:
                self.label_exp_panel.configure(
                    text="Solo mensualidad, sin uniforme • Monto libre (vacío no permitido)")
        except Exception:
            pass

    def _on_exp_tipodoc(self, selection):
        sel = selection if isinstance(selection, str) else self.combo_exp_tipodoc.get()
        try:
            if sel == "CARNET":
                self.label_exp_doc.configure(text="Carnet (9 dígitos) *")
                self.entry_exp_dni.configure(placeholder_text="123456789")
            else:
                self.label_exp_doc.configure(text="DNI (8 dígitos) *")
                self.entry_exp_dni.configure(placeholder_text="12345678")
        except Exception:
            pass

    def _elegir_comprobante_exp(self):
        from tkinter import filedialog, messagebox
        import os
        from utils.constants import COMPROBANTES_DIR
        from utils.imagenes import validar_imagen
        path = filedialog.askopenfilename(filetypes=[("Imagen", "*.jpg *.jpeg *.png"), ("Todos", "*.*")])
        if path:
            ok, msg = validar_imagen(path, max_mb=5)
            if not ok:
                messagebox.showerror("Comprobante no válido", msg)
                self.label_exp_status.configure(text=f"❌ {msg}", text_color="red")
                return
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            self._exp_comprobante = path
            self.label_exp_comp.configure(text=os.path.basename(path))

    def _guardar_express(self):
        data = {"tipo": self.seg_exp_tipo.get(),
                "nombres": self.entry_exp_nombres.get().strip(),
                "apellidos": self.entry_exp_apellidos.get().strip(),
                "dni": self.entry_exp_dni.get().strip(),
                "tipo_documento": self.combo_exp_tipodoc.get(),
                "monto": self.entry_exp_monto.get().strip() or None,
                "metodo_pago": self.combo_exp_metodo.get(),
                "comprobante_path": self._exp_comprobante,
                "fecha_inicio": self.date_express.get() or None}
        exito, msg, _ids = matricula_controller.matricula_express(data)
        self.label_exp_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            for e in (self.entry_exp_nombres, self.entry_exp_apellidos,
                      self.entry_exp_dni, self.entry_exp_monto):
                e.delete(0, "end")
            self.entry_exp_monto.insert(0, self._default_nuevo)
            self._exp_comprobante = None
            self.label_exp_comp.configure(text="Sin comprobante")
            try:
                event_bus.publish("matricula_creada")
                event_bus.publish("pago_registrado")
            except Exception:
                pass
            self._cargar_matriculas()
            self._cargar_combo_matriculas()

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec_titulo = crear_seccion(
            self.tab_lista, titulo="Matrículas Activas", icono="🎓",
            descripcion="Todas las matrículas con su tarifa y vencimiento. Clic en ▾ Ver detalle o Ver Cuotas para más info.",
            nro=1,
        )
        crear_boton_interactivo(sec_titulo, text="+ Nueva", width=110, command=self._nueva_matricula,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        sec_filtros = crear_seccion(
            self.tab_lista, titulo="Búsqueda", icono="🔍",
            descripcion="Busca por documento, carnet o nombre de estudiante.",
            nro=2,
        )
        filtros = ctk.CTkFrame(sec_filtros, fg_color="transparent")
        filtros.pack(fill="x", padx=10, pady=(0, 8))
        self.entry_busqueda = ctk.CTkEntry(
            filtros, placeholder_text="Buscar por documento, carnet o nombre...",
            width=250,
        )
        self.entry_busqueda.pack(side="left", padx=5)
        self._debouncer = Debouncer(self, 300)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._debouncer.call(self._on_busqueda_cambiar))
        # Fase 7b: toggle Cards/Tabla
        self._vista_modo = "Cards"
        self.seg_vista = ctk.CTkSegmentedButton(
            filtros, values=["Cards", "Tabla"], command=self._on_vista_cambiar)
        try:
            self.seg_vista.set("Cards")
        except Exception:
            pass
        self.seg_vista.pack(side="left", padx=5)
        crear_nota(sec_filtros, "Tip: clic en ▾ Ver detalle de cada tarjeta para tarifa, montos y vencimiento.")

        # Fase 1: aviso de matrículas sin apoderado principal
        self.banner_frame = ctk.CTkFrame(self.tab_lista, fg_color="transparent")
        self.banner_frame.pack(fill="x", padx=5)
        self._refrescar_banner()

        self.scroll_matriculas = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll_matriculas.pack(fill="both", expand=True, padx=5, pady=5)

        self.pagination = PaginationBar(self.tab_lista, on_page_change=self._on_page, per_page=50)
        self.pagination.pack(fill="x", padx=5, pady=4)

        self.label_status = ctk.CTkLabel(self.tab_lista, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status.pack(pady=3)

    def _crear_tab_formulario(self):
        # contenedor con scroll para campos + footer fijo para totales/acciones
        self._form_container = ctk.CTkFrame(self.tab_form, fg_color="transparent")
        self._form_container.pack(fill="both", expand=True, padx=10, pady=10)

        scroll = ctk.CTkScrollableFrame(self._form_container)
        scroll.pack(fill="both", expand=True, pady=(0,5))

        from utils.ui_helpers import crear_seccion, crear_nota
        sec1 = crear_seccion(scroll, titulo="Estudiante y tarifa", icono="🎓",
                             descripcion="Sugiere tarifa por edad. Precio: monto pactado o tarifa.",
                             nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo1, text="Estudiante *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_estudiante = ctk.CTkComboBox(
            cuerpo1, width=400, values=["Cargando..."],
            command=self._on_estudiante_changed,
        )
        self.combo_estudiante.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Tarifa *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_tarifa = ctk.CTkComboBox(cuerpo1, width=400, values=["Cargando..."])
        self.combo_tarifa.pack(anchor="w", pady=(0, 5))

        # Fase 7e: conceptos eliminados del flujo (precio = tarifa/monto)

        sec2 = crear_seccion(scroll, titulo="Montos, beca y productos", icono="💰",
                             descripcion="Monto pactado libre (0 = gratuito), beca opcional y extras con −1/+1.", nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))

        row1 = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        row1.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row1, text="Monto pactado (S/):").pack(side="left")
        self.entry_monto_pactado = ctk.CTkEntry(row1, placeholder_text="Opcional", width=120)
        self.entry_monto_pactado.pack(side="left", padx=10)

        ctk.CTkLabel(row1, text="Día vencimiento:").pack(side="left", padx=(20, 0))
        self.entry_dia_venc = ctk.CTkEntry(row1, placeholder_text="1-31", width=60)
        self.entry_dia_venc.insert(0, "1")
        self.entry_dia_venc.pack(side="left", padx=5)

        from widgets.date_picker import DatePicker
        self.date_matricula = DatePicker(cuerpo2, label_text="Fecha de inicio (INICIO):", default="today")
        self.date_matricula.pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(cuerpo2, text="Beca (opcional):").pack(anchor="w")
        self.combo_beca = ctk.CTkComboBox(cuerpo2, width=400, values=["Ninguna"])
        self.combo_beca.pack(anchor="w", pady=3)
        # Fase 7e: atajo a tarifas del módulo (filtrado, sin salir del flujo)
        from utils.ui_helpers import crear_boton_interactivo as _btn_tar
        _btn_tar(cuerpo2, text="🏷 Tarifas academia y becas", width=220,
                 command=lambda: self._abrir_tarifas_modulo("Tarifas", "ACADEMIA"),
                 fg_color="#E5E7EB", hover_color="#DDD6E5",
                 text_color="#1F0A33").pack(anchor="w", pady=3)

        ctk.CTkLabel(cuerpo2, text="Pago diferido (mensualidad):").pack(anchor="w", pady=(5,0))
        self.combo_diferir = ctk.CTkComboBox(cuerpo2, width=200, values=["Ahora (0)", "2 meses", "3 meses"])
        self.combo_diferir.set("Ahora (0)")
        self.combo_diferir.pack(anchor="w", pady=3)

        # Productos adicionales (no uniformes) — -1/+1
        ctk.CTkLabel(cuerpo2, text="Productos adicionales — usa −1 / +1:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10,5))
        ctk.CTkLabel(cuerpo2, text="Nuevos incluyen camiseta de regalo. Uniformes extra se venden en Tienda.", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self.frame_productos = ctk.CTkScrollableFrame(cuerpo2, height=150)
        self.frame_productos.pack(fill="x", anchor="w", pady=5)
        self._productos_disponibles = []
        self._productos_seleccionados = {}  # id_producto -> {cantidad, precio, nombre}
        self._productos_map = {}
        self._cargar_productos_matricula()
        # actualizar total al cambiar monto/beca/tarifa
        self.entry_monto_pactado.bind("<KeyRelease>", lambda e: self._actualizar_total())
        self.combo_beca.configure(command=lambda v: self._actualizar_total())
        self.combo_tarifa.configure(command=lambda v: self._actualizar_total())

        # footer fijo (no scrollea)
        footer = ctk.CTkFrame(self._form_container, fg_color="#F8F5FA", border_width=1, border_color="#DDD6E5", corner_radius=8)
        footer.pack(fill="x", pady=(5,0))

        self.label_total = ctk.CTkLabel(footer, text="Total matricula: S/0.00 | Productos: S/0.00 | Importe total: S/0.00", font=ctk.CTkFont(size=12, weight="bold"), text_color="#7C3AED")
        self.label_total.pack(anchor="w", padx=10, pady=4)
        self.label_seleccionados = ctk.CTkLabel(footer, text="Seleccionados: ninguno", font=ctk.CTkFont(size=11), text_color="#7C3AED")
        self.label_seleccionados.pack(anchor="w", padx=10)
        self.label_form_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", padx=10, pady=2)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=10, pady=6)

        ctk.CTkButton(
            btn_frame, text="Registrar Matrícula", width=150,
            command=self._registrar_matricula,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, fg_color="gray",
            command=lambda: self.tabview.set("Matrículas"),
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame, text="🧹 Limpiar", width=100, fg_color="#6B7280", hover_color="#4B5563",
            command=self._limpiar_form_matricula,
        ).pack(side="left", padx=5)

    def _crear_tab_cuotas(self):
        header = ctk.CTkFrame(self.tab_cuotas, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            header, text="Cuotas por Matrícula",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        self.combo_matricula_cuotas = ctk.CTkComboBox(
            self.tab_cuotas, width=400,
            values=["Seleccionar matrícula..."],
            command=self._cargar_cuotas,
        )
        self.combo_matricula_cuotas.set("Seleccionar matrícula...")
        self.combo_matricula_cuotas.pack(anchor="w", padx=5, pady=5)

        self.scroll_cuotas = ctk.CTkScrollableFrame(self.tab_cuotas)
        self.scroll_cuotas.pack(fill="both", expand=True, padx=5, pady=5)

        self._cargar_combo_matriculas()

    def _recargar_actual(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_matriculas()

    def _on_page(self, page, per_page):
        self._pagina = page
        self._cargar_paginado()

    def _cargar_matriculas(self, busqueda=""):
        # compat: si se llama con búsqueda, resetear página
        if busqueda:
            self._q_actual = busqueda
            self._pagina = 1
            if hasattr(self, 'pagination'):
                self.pagination.reset()
        self._cargar_paginado()

    def _cargar_paginado(self):
        for widget in self.scroll_matriculas.winfo_children():
            widget.destroy()

        estado_val = "TODOS"
        try:
            from repositories import matricula_repository
            offset = (self._pagina - 1) * self._per_page
            rows, total = matricula_repository.buscar_paginado(q=self._q_actual, limit=self._per_page, offset=offset)
            self._total = total
            if hasattr(self, 'pagination'):
                self.pagination.set_total(total)
        except Exception:
            from utils.busqueda import coincide as _coincide
            rows = matricula_controller.listar_matriculas_activas()
            if self._q_actual:
                rows = [m for m in rows if _coincide(
                    self._q_actual, m.get("dni", ""), m.get("nombres", ""),
                    m.get("apellidos", ""),
                    f"{m.get('nombres', '')} {m.get('apellidos', '')}")]
            total = len(rows)
            rows = rows[(self._pagina - 1) * self._per_page : self._pagina * self._per_page]
            self._total = total

        if not rows:
            ctk.CTkLabel(
                self.scroll_matriculas, text="No hay matrículas activas",
                text_color="gray",
            ).pack(pady=20)
            self.label_status.configure(text=f"Total: {self._total} • Página {self._pagina}")
            return

        if getattr(self, "_vista_modo", "Cards") == "Tabla":
            self._render_tabla_matriculas(rows)
        else:
            for mat in rows:
                self._crear_card(mat)

        total_paginas = max(1, (self._total + self._per_page - 1) // self._per_page)
        self.label_status.configure(text=f"Total: {self._total} matrícula(s) • Página {self._pagina}/{total_paginas} • 50 por página")

    def _crear_card(self, mat):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle
        card = crear_card_interactiva(self.scroll_matriculas)
        card.pack(fill="x", padx=6, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        nombre = f"{mat.get('nombres', '')} {mat.get('apellidos', '')}"
        ctk.CTkLabel(
            info, text=nombre,
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33",
        ).pack(anchor="w")

        try:
            monto_txt = f"S/{mat.get('tarifa_monto', 0):.2f}"
        except Exception:
            monto_txt = f"S/{mat.get('tarifa_monto', 0)}"
        ctk.CTkLabel(
            info,
            text=f"DNI: {mat.get('dni', '')} | Tarifa: {mat.get('tarifa_nombre', '')} | Montos: {monto_txt}",
            font=ctk.CTkFont(size=12), text_color="#6B5B7B",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=f"Inicio: {mat.get('fecha_inicio', '')} | Vencimiento: día {mat.get('dia_vencimiento', 1)}",
            font=ctk.CTkFont(size=11), text_color="#6B5B7B",
        ).pack(anchor="w")

        botones = ctk.CTkFrame(top, fg_color="transparent")
        botones.pack(side="right", padx=5, pady=5)

        ctk.CTkButton(
            botones, text="Ver Cuotas", width=90, height=28,
            command=lambda m=mat: self._ver_cuotas(m),
        ).pack(side="left", padx=2)

        # ── Detalle expandible inline (mismo que la vista Tabla) ──
        toggle_btn, _, _ = agregar_detalle_expandible(
            card, lambda frame, _m=mat: self._poblar_detalle_matricula(frame, _m))
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    @staticmethod
    def _poblar_detalle_matricula(frame, mat):
        from utils.ui_helpers import linea_detalle
        try:
            monto_txt = f"S/{mat.get('tarifa_monto', 0):.2f}"
        except Exception:
            monto_txt = f"S/{mat.get('tarifa_monto', 0)}"
        linea_detalle(frame, "ID matrícula", mat.get("id_matricula"))
        linea_detalle(frame, "Estudiante", f"{mat.get('nombres','')} {mat.get('apellidos','')} • DNI {mat.get('dni','')}")
        linea_detalle(frame, "Tarifa", f"{mat.get('tarifa_nombre','')} • {monto_txt}")
        linea_detalle(frame, "Monto pactado", mat.get("monto_pactado"))
        linea_detalle(frame, "Beca", mat.get("beca_nombre") or mat.get("beca"))
        linea_detalle(frame, "Concepto", mat.get("concepto_nombre") or mat.get("concepto"))
        linea_detalle(frame, "Inicio", mat.get("fecha_inicio"))
        linea_detalle(frame, "Día vencimiento", mat.get("dia_vencimiento"))
        linea_detalle(frame, "Estado", mat.get("estado"))

    def _on_vista_cambiar(self, valor):
        self._vista_modo = valor
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _render_tabla_matriculas(self, rows):
        from utils.ui_helpers import crear_tabla_densa
        cols = [("Estudiante", 200), ("Documento", 110), ("Tarifa", 170),
                ("Monto", 90), ("Inicio", 100)]
        filas, dets = [], []
        for m in rows:
            try:
                monto = f"S/{m.get('tarifa_monto', 0):.2f}"
            except Exception:
                monto = f"S/{m.get('tarifa_monto', 0)}"
            filas.append([
                f"{m.get('nombres', '')} {m.get('apellidos', '')}".strip(),
                str(m.get("dni", "")),
                str(m.get("tarifa_nombre", "")),
                monto,
                str(m.get("fecha_inicio", "")),
            ])
            dets.append(lambda frame, _m=m: self._poblar_detalle_matricula(frame, _m))
        crear_tabla_densa(self.scroll_matriculas, cols, filas, dets, cap=50)

    def _nueva_matricula(self):
        self._cargar_combo_estudiantes()
        self._cargar_combo_tarifas()
        self._cargar_combo_becas()
        self._productos_seleccionados = {}
        try:
            self.label_total.configure(text="Total matricula: S/0.00 | Productos: S/0.00 | Importe total: S/0.00")
            self.label_seleccionados.configure(text="Seleccionados: ninguno")
        except Exception:
            pass
        self._cargar_productos_matricula()
        self.tabview.set("Registrar")

    def _cargar_combo_estudiantes(self):
        estudiantes = estudiante_controller.listar_estudiantes(activo=1, estado=["ACTIVO", "REINGRESANTE"])
        nombres = [f"{e.get('nombres', '')} {e.get('apellidos', '')}" for e in estudiantes]
        self.combo_estudiante.configure(values=nombres if nombres else ["Sin estudiantes"])
        self._estudiantes_map = {n: e for n, e in zip(nombres, estudiantes)}

    def _on_estudiante_changed(self, selection):
        est = self._estudiantes_map.get(selection)
        if not est:
            return
        fecha_nac = est.get("fecha_nacimiento", "")
        if not fecha_nac:
            return
        id_tarifa_sugerida = matricula_controller.obtener_tarifa_sugerida_por_edad(fecha_nac)
        if not id_tarifa_sugerida:
            return
        for nombre, tid in self._tarifas_map.items():
            if tid == id_tarifa_sugerida:
                self.combo_tarifa.set(nombre)
                break

    def _cargar_combo_tarifas(self):
        tarifas = matricula_controller.listar_tarifas_activas(tipo="ACADEMIA")
        nombres = [f"{t.get('categoria_nombre', '')} - {t['nombre']} (S/{t['monto']:.2f})" for t in tarifas]
        self.combo_tarifa.configure(values=nombres if nombres else ["Sin tarifas"])
        self._tarifas_map = {n: t["id_tarifa"] for n, t in zip(nombres, tarifas)}

    def _cargar_combo_becas(self):
        becas = matricula_controller.listar_becas()
        nombres = ["Ninguna"] + [f"{b['nombre']} ({b['tipo']} {b['valor']})" for b in becas]
        self.combo_beca.configure(values=nombres)
        self._becas_map = {n: b["id_beca"] for n, b in zip(nombres[1:], becas)}

    def _cargar_productos_matricula(self):
        try:
            from controllers import inventario_controller
            prods = inventario_controller.listar_productos(activo=1)
            # Fase 5: uniformes (incl. camiseta-regalo) no se ofrecen aquí;
            # se venden en Tienda. Nuevos ya incluyen la camiseta de regalo.
            prods = [p for p in prods
                     if p.get("canal") == "TIENDITA" and not p.get("id_tipo_uniforme")]
            self._productos_disponibles = prods
            for w in self.frame_productos.winfo_children():
                w.destroy()
            if not self._productos_disponibles:
                ctk.CTkLabel(self.frame_productos, text="Sin extras aquí (uniformes en Tienda)", text_color="gray").pack(pady=5)
                return
            for prod in self._productos_disponibles[:15]:
                row = ctk.CTkFrame(self.frame_productos, fg_color="white", border_width=1, border_color="#E5E7EB", corner_radius=8)
                row.pack(fill="x", padx=3, pady=2)
                precio = prod.get("precio_venta") or prod.get("precio", 0)
                stock = prod.get("stock_actual", 0)
                cant_sel = self._productos_seleccionados.get(prod["id_producto"], {}).get("cantidad", 0)
                ctk.CTkLabel(row, text=f"{prod.get('nombre','')} — S/{precio:.2f}", font=ctk.CTkFont(size=12)).pack(side="left", padx=8, pady=6)
                col = "green" if stock > 5 else "orange" if stock > 0 else "red"
                ctk.CTkLabel(row, text=f"stock {stock}", text_color=col, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
                if cant_sel:
                    ctk.CTkLabel(row, text=f"x{cant_sel}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7C3AED").pack(side="left", padx=5)
                # -1
                ctk.CTkButton(row, text="−1", width=40, height=28, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=lambda p=prod: self._cambiar_cantidad(p, -1)).pack(side="right", padx=2, pady=4)
                ctk.CTkButton(row, text="+1", width=40, height=28, fg_color="#7C3AED", command=lambda p=prod: self._cambiar_cantidad(p, 1)).pack(side="right", padx=2, pady=4)
                self._productos_map[prod["id_producto"]] = prod
            self._actualizar_total()
        except Exception as e:
            ctk.CTkLabel(self.frame_productos, text=f"Error cargando productos: {e}", text_color="red").pack()

    def _cambiar_cantidad(self, prod, delta):
        # bloqueo RN-051: si estudiante es nuevo, no permitir extras
        try:
            est_name = self.combo_estudiante.get()
            est = self._estudiantes_map.get(est_name)
            if est and int(est.get("es_nuevo",0) or 0)==1:
                # si ya tiene regalo, bloquea
                from controllers import matricula_controller
                # check si es primera matricula (no tiene matricula activa)
                # simplifica: avisar y no permitir
                self.label_form_status.configure(text="Estudiante nuevo: extras bloqueados (usa Ventas)", text_color="orange")
                return
        except Exception:
            pass
        pid = prod["id_producto"]
        cur = self._productos_seleccionados.get(pid, {"cantidad":0, "precio": prod.get("precio_venta") or prod.get("precio",0), "nombre": prod.get("nombre","")})
        nueva = cur["cantidad"] + delta
        if nueva <= 0:
            self._productos_seleccionados.pop(pid, None)
        else:
            if prod.get("stock_actual",0) < nueva:
                self.label_form_status.configure(text=f"Stock insuficiente: {prod.get('nombre')} (disp {prod.get('stock_actual')})", text_color="orange")
                return
            cur["cantidad"] = nueva
            cur["precio"] = prod.get("precio_venta") or prod.get("precio",0)
            self._productos_seleccionados[pid] = cur
        self._cargar_productos_matricula()

    def _toggle_producto(self, prod):
        self._cambiar_cantidad(prod, 1)

    def _actualizar_total(self):
        base = 0
        # Fase 7e: precio = monto pactado o tarifa (sin conceptos)
        try:
            monto_pactado = self.entry_monto_pactado.get().strip()
            if monto_pactado:
                base = float(monto_pactado)
            else:
                tarifa_sel = self.combo_tarifa.get()
                tid = self._tarifas_map.get(tarifa_sel)
                if tid:
                    for n, tid2 in self._tarifas_map.items():
                        if tid2 == tid:
                            import re
                            m = re.search(r"S/([0-9.]+)", n)
                            if m:
                                base = float(m.group(1))
                            break
        except Exception:
            base = 0
        beca_sel = self.combo_beca.get() if hasattr(self, 'combo_beca') else "Ninguna"
        if beca_sel != "Ninguna" and beca_sel in getattr(self, '_becas_map', {}):
            try:
                import re
                m = re.search(r"\((PORCENTAJE|MONTO_FIJO) ([0-9.]+)\)", beca_sel)
                if m:
                    tipo, val = m.group(1), float(m.group(2))
                    if tipo == "PORCENTAJE":
                        base = base * (1 - val/100)
                    else:
                        base = base - val
                    base = max(0, base)
            except Exception:
                pass
        prod_total = sum(v["precio"] * v["cantidad"] for v in self._productos_seleccionados.values())
        total = base + prod_total
        try:
            self.label_total.configure(text=f"Total matricula: S/{base:.2f} | Productos: S/{prod_total:.2f} | Importe total: S/{total:.2f}")
            sel = ", ".join([f"{v['nombre']} x{v['cantidad']}" for v in self._productos_seleccionados.values()])
            self.label_seleccionados.configure(text=f"Seleccionados: {sel or 'ninguno'}")
        except Exception:
            pass

    def _limpiar_form_matricula(self):
        self.entry_monto_pactado.delete(0, "end")
        self.entry_dia_venc.delete(0, "end")
        self.entry_dia_venc.insert(0, "1")
        self.combo_beca.set("Ninguna")
        self.combo_diferir.set("Ahora (0)")
        self._productos_seleccionados = {}
        self._cargar_productos_matricula()
        self.label_form_status.configure(text="")

    def _registrar_matricula(self):
        from tkinter import messagebox
        est_selection = self.combo_estudiante.get()
        est = self._estudiantes_map.get(est_selection)
        id_est = est["id_estudiante"] if est else None
        if not id_est:
            self.label_form_status.configure(text="Seleccione un estudiante", text_color="red")
            return
        tarifa_selection = self.combo_tarifa.get()
        id_tarifa = self._tarifas_map.get(tarifa_selection)
        if not id_tarifa:
            self.label_form_status.configure(text="Seleccione una tarifa", text_color="red")
            return
        diferir_map = {"Ahora (0)": 0, "2 meses": 2, "3 meses": 3}
        data = {
            "id_estudiante": id_est,
            "id_tarifa": id_tarifa,
            "monto_pactado": self.entry_monto_pactado.get().strip() or None,
            "dia_vencimiento": self.entry_dia_venc.get().strip() or "1",
            "diferir_meses": diferir_map.get(self.combo_diferir.get(), 0),
            "fecha_inicio": self.date_matricula.get() or None,
        }
        beca_selection = self.combo_beca.get()
        if beca_selection != "Ninguna" and beca_selection in self._becas_map:
            data["becas"] = [{"id_beca": self._becas_map[beca_selection]}]
        if self._productos_seleccionados:
            # bloqueo RN-051 se maneja en service (ignora extras de nuevos)
            if est and int(est.get("es_nuevo",0) or 0)==1:
                pass
            data["productos"] = [{"id_producto": pid, "cantidad": v["cantidad"]} for pid, v in self._productos_seleccionados.items()]
        # MessageBox desglose
        base_txt = self.label_total.cget("text") if hasattr(self.label_total, 'cget') else ""
        sel_txt = self.label_seleccionados.cget("text") if hasattr(self.label_seleccionados,'cget') else ""
        detalle = f"Estudiante: {est_selection}\nTarifa: {tarifa_selection}\n{sel_txt}\n{base_txt}\n\n¿Confirmar matrícula?"
        if not messagebox.askyesno("Confirmar matrícula", detalle):
            return
        exito, msg, id_mat = matricula_controller.crear_matricula(data)
        if exito:
            self.label_form_status.configure(text=msg, text_color="green")
            self._cargar_matriculas()
            self._cargar_combo_matriculas()
            self._refrescar_banner()
            self.tabview.set("Matrículas")
        else:
            self.label_form_status.configure(text=msg, text_color="red")

    def _crear_tab_grilla(self):
        # Fase 7d: grilla anual estilo Excel RELACIÓN DE ALUMNOS
        # (X=CANCELADO, S/=ADELANTO, vacío=pendiente/sin cuota).
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo
        from utils.dates import get_today
        sec = crear_seccion(
            self.tab_grilla, titulo="Cuotas del Año", icono="🗓",
            descripcion="X = cancelado • S/ monto = adelanto (saldo) • vacío = pendiente.",
            nro=1)
        barra = ctk.CTkFrame(sec, fg_color="transparent")
        barra.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(barra, text="Año:").pack(side="left")
        try:
            anio_actual = int((get_today() or "2026")[:4])
        except (ValueError, TypeError):
            anio_actual = 2026
        self.combo_grilla_anio = ctk.CTkComboBox(
            barra, width=110,
            values=[str(a) for a in range(anio_actual - 2, anio_actual + 3)],
            command=lambda v: self._cargar_grilla())
        self.combo_grilla_anio.set(str(anio_actual))
        self.combo_grilla_anio.pack(side="left", padx=10)
        crear_boton_interactivo(barra, text="Actualizar", width=110,
                                command=self._cargar_grilla, fg_color="#7C3AED").pack(side="left")
        self.scroll_grilla = ctk.CTkScrollableFrame(self.tab_grilla)
        self.scroll_grilla.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_grilla_status = ctk.CTkLabel(self.tab_grilla, text="", font=ctk.CTkFont(size=12))
        self.label_grilla_status.pack(pady=3)
        self._cargar_grilla()

    def _cargar_grilla(self):
        from services import cuota_service
        for w in self.scroll_grilla.winfo_children():
            w.destroy()
        try:
            anio = int(self.combo_grilla_anio.get())
        except (ValueError, TypeError):
            anio = 2026
        filas = cuota_service.grilla_anual(anio)
        meses = cuota_service.MESES_GRILLA
        header = ctk.CTkFrame(self.scroll_grilla, fg_color="#3D1559", corner_radius=6)
        header.pack(fill="x", padx=6, pady=(4, 2))
        ctk.CTkLabel(header, text="Estudiante", width=220,
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="white").grid(
            row=0, column=0, padx=2, pady=6, sticky="w")
        for j, mes in enumerate(meses):
            ctk.CTkLabel(header, text=mes, width=55,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="white").grid(
                row=0, column=j + 1, padx=2, pady=6)
        if not filas:
            ctk.CTkLabel(self.scroll_grilla, text=f"Sin cuotas en {anio}",
                         text_color="gray").pack(pady=20)
            self.label_grilla_status.configure(text="Total: 0")
            return
        colores = {"PAGADO": ("X", "green", True), "PARCIAL": (None, "#D97706", True),
                   "VENCIDO": ("!", "#DC2626", True), "PENDIENTE": ("", "#9CA3AF", False)}
        for f in filas:
            row = ctk.CTkFrame(self.scroll_grilla, fg_color="white", corner_radius=6)
            row.pack(fill="x", padx=6, pady=1)
            ctk.CTkLabel(row, text=f["nombre"], width=220,
                         font=ctk.CTkFont(size=11), text_color="#1F0A33").grid(
                row=0, column=0, padx=2, pady=4, sticky="w")
            for j in range(1, 13):
                celda = f["meses"].get(j)
                if celda is None:
                    txt, color, negrita = "", "#9CA3AF", False
                elif celda["estado"] == "PARCIAL":
                    txt, color, negrita = f"S/{celda['saldo']:.0f}", "#D97706", True
                else:
                    txt, color, negrita = colores.get(celda["estado"], ("", "#9CA3AF", False))
                ctk.CTkLabel(row, text=txt, width=55,
                             font=ctk.CTkFont(size=11, weight="bold" if negrita else "normal"),
                             text_color=color).grid(row=0, column=j, padx=2, pady=4)
        self.label_grilla_status.configure(
            text=f"Total: {len(filas)} estudiante(s) • X=cancelado • S/=adelanto")

    @staticmethod
    def _abrir_tarifas_modulo(tab=None, tipo=None):
        try:
            from utils import event_bus
            event_bus.publish("abrir_tarifas", tab=tab, tipo=tipo)
        except Exception:
            pass

    def _ver_cuotas(self, mat):
        self.tabview.set("Cuotas")
        self._cargar_combo_matriculas()
        id_str = f"ID:{mat['id_matricula']}"
        for key, val in self._matriculas_map.items():
            if val == mat["id_matricula"]:
                self.combo_matricula_cuotas.set(key)
                self._cargar_cuotas(key)
                break

    def _cargar_combo_matriculas(self):
        matriculas = matricula_controller.listar_matriculas_activas()
        nombres = [f"{m.get('nombres', '')} {m.get('apellidos', '')} - {m.get('tarifa_nombre', '')}" for m in matriculas]
        self.combo_matricula_cuotas.configure(values=nombres if nombres else ["Sin matrículas"])
        self._matriculas_map = {n: m["id_matricula"] for n, m in zip(nombres, matriculas)}

    def _cargar_cuotas(self, selection):
        for widget in self.scroll_cuotas.winfo_children():
            widget.destroy()

        id_mat = self._matriculas_map.get(selection)
        if not id_mat:
            return

        cuotas = matricula_controller.obtener_cuotas_por_matricula(id_mat)

        if not cuotas:
            ctk.CTkLabel(
                self.scroll_cuotas, text="Sin cuotas registradas",
                text_color="gray",
            ).pack(pady=10)
            return

        for cuota in cuotas:
            card = ctk.CTkFrame(self.scroll_cuotas)
            card.pack(fill="x", padx=5, pady=3)

            color = {"PENDIENTE": "gray", "PARCIAL": "orange",
                     "PAGADO": "green", "VENCIDO": "red"}.get(cuota["estado"], "gray")

            ctk.CTkLabel(
                card,
                text=f"{cuota['periodo']} | S/{cuota['monto_total']:.2f} | "
                     f"Pagado: S/{cuota['monto_pagado']:.2f} | Saldo: S/{cuota['saldo']:.2f}",
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(
                card, text=cuota["estado"], text_color=color,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right", padx=10)
