import os
import customtkinter as ctk
from controllers import pago_controller, login_controller
from controllers import estudiante_controller, matricula_controller
from widgets.date_picker import DatePicker
from utils.debounce import Debouncer
from utils import event_bus
from widgets.pagination import PaginationBar
try:
    from PIL import Image
except ImportError:
    Image = None


class PagoView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._matriculas_map = {}
        self._cuotas_map = {}
        self._pagina = 1
        self._per_page = 50
        self._total = 0
        self._q_actual = ""
        self._crear_widgets()
        self._cargar_pagos()
        self._bus_handler = lambda *a, **k: self.after(200, lambda: self._recargar_actual())
        event_bus.subscribe("pago_registrado", self._bus_handler)

    def destroy(self):
        # Sin esto cada visita acumulaba un suscriptor zombi que retenía la
        # vista destruida y disparaba recargas fantasma en cada evento.
        try:
            if hasattr(self, "_bus_handler"):
                event_bus.unsubscribe("pago_registrado", self._bus_handler)
        except Exception:
            pass
        try:
            if hasattr(self, "_debouncer"):
                self._debouncer.cancel()
        except Exception:
            pass
        super().destroy()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_lista = self.tabview.add("Pagos")
        self.tab_form = self.tabview.add("Registrar Pago")
        self.tab_morosos = self.tabview.add("Morosos")

        self._crear_tab_lista()
        self._crear_tab_formulario()
        self._crear_tab_morosos()

    def _crear_tab_lista(self):
        header = ctk.CTkFrame(self.tab_lista, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E7EB")
        header.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(header, text="💰 Historial de Pagos", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1F0A33").pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(header, text="Pagos registrados y filtros por fecha", font=ctk.CTkFont(size=12), text_color="#6B5B7B").pack(side="left", padx=10)
        from utils.ui_helpers import crear_boton_interactivo
        crear_boton_interactivo(header, text="+ Nuevo Pago", width=130, height=36, command=self._nuevo_pago, fg_color="#7C3AED").pack(side="right", padx=8, pady=8)

        filtros = ctk.CTkFrame(self.tab_lista, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E7EB")
        filtros.pack(fill="x", padx=8, pady=6)

        self.date_picker_inicio = DatePicker(filtros, label_text="Fecha Inicio:", default="start_of_month")
        self.date_picker_inicio.pack(side="left", padx=(12, 10))

        self.date_picker_fin = DatePicker(filtros, label_text="Fecha Fin:", default="today")
        self.date_picker_fin.pack(side="left", padx=(0, 10))

        from utils.ui_helpers import crear_boton_interactivo
        crear_boton_interactivo(filtros, text="🔍 Buscar", width=90, command=self._buscar_por_fecha, fg_color="#7C3AED").pack(side="left", padx=5)
        crear_boton_interactivo(filtros, text="🧹 Limpiar", width=90, fg_color="#E5E7EB", hover_color="#DDD6E5", text_color="#1F0A33", command=self._limpiar_fechas).pack(side="left", padx=5)
        ctk.CTkLabel(filtros, text="|", text_color="#E5E7EB").pack(side="left", padx=8)
        self.entry_busqueda = ctk.CTkEntry(filtros, placeholder_text="🔍 Buscar por documento, recibo o método...", width=260, border_color="#DDD6E5")
        self.entry_busqueda.pack(side="left", padx=5)
        self._debouncer = Debouncer(self, 300)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._debouncer.call(self._on_busqueda_cambiar))

        self.scroll_pagos = ctk.CTkScrollableFrame(self.tab_lista, fg_color="#F8F5FA")
        self.scroll_pagos.pack(fill="both", expand=True, padx=8, pady=6)

        self.pagination = PaginationBar(self.tab_lista, on_page_change=self._on_page, per_page=50)
        self.pagination.pack(fill="x", padx=8, pady=4)

        self.label_status = ctk.CTkLabel(self.tab_lista, text="⏳ Cargando pagos...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status.pack(pady=4)

    def _crear_tab_formulario(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec1 = crear_seccion(scroll, titulo="Cuota a pagar", icono="🧾",
                             descripcion="Elige estudiante y su cuota pendiente. Acepta pagos parciales.", nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo1, text="Estudiante *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_estudiante = ctk.CTkComboBox(
            cuerpo1, width=400, values=["Cargando..."],
            command=self._on_estudiante_cambiado,
        )
        self.combo_estudiante.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Cuota pendiente *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_cuota = ctk.CTkComboBox(cuerpo1, width=400, values=["Seleccionar estudiante primero"])
        self.combo_cuota.pack(anchor="w", pady=(0, 5))

        sec2 = crear_seccion(scroll, titulo="Monto y comprobante", icono="💵",
                             descripcion="YAPE/PLIN/TRANSFERENCIA exigen foto de comprobante.", nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(cuerpo2, text="Monto a pagar (S/) *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_monto = ctk.CTkEntry(cuerpo2, placeholder_text="0.00", width=200)
        self.entry_monto.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo2, text="Método de pago *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.combo_metodo = ctk.CTkComboBox(
            cuerpo2, width=200,
            values=["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA"],
        )
        self.combo_metodo.set("EFECTIVO")
        self.combo_metodo.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo2, text="Observación (opcional)", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_observacion = ctk.CTkEntry(cuerpo2, placeholder_text="Referencia o nota", width=400)
        self.entry_observacion.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo2, text="Comprobante foto (obligatorio si YAPE/PLIN/TRANSFERENCIA)", font=ctk.CTkFont(size=12)).pack(anchor="w")
        comp_frame = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        comp_frame.pack(fill="x", anchor="w", pady=2)
        self.btn_comprobante = ctk.CTkButton(comp_frame, text="📎 Seleccionar comprobante", width=200, command=self._elegir_comprobante)
        self.btn_comprobante.pack(side="left", padx=5)
        self.label_comprobante = ctk.CTkLabel(comp_frame, text="Sin comprobante", text_color="gray")
        self.label_comprobante.pack(side="left", padx=5)
        self.label_comprobante_preview = ctk.CTkLabel(comp_frame, text="")
        self.label_comprobante_preview.pack(side="left", padx=5)
        self._comprobante_path = None
        crear_nota(sec2, "Si el monto cubre el saldo, la cuota pasa a PAGADO; si no, queda PARCIAL.")

        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_form_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", padx=10, pady=(8, 2))

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=10, pady=(2, 8))

        crear_boton_interactivo(
            btn_frame, text="Registrar Pago", width=130,
            command=self._registrar_pago, fg_color="#7C3AED",
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, fg_color="gray",
            command=lambda: self.tabview.set("Pagos"),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🧹 Limpiar", width=90, fg_color="#6B7280", hover_color="#4B5563",
            command=self._limpiar_form_pago,
        ).pack(side="left", padx=5)

    def _crear_tab_morosos(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_morosos, titulo="Cuotas Vencidas", icono="⚠️",
            descripcion="Cuotas vencidas con saldo pendiente. Registra el pago desde la pestaña Registrar Pago.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_morosos,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        self.scroll_morosos = ctk.CTkScrollableFrame(self.tab_morosos)
        self.scroll_morosos.pack(fill="both", expand=True, padx=5, pady=5)

        self.label_status_morosos = ctk.CTkLabel(self.tab_morosos, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status_morosos.pack(pady=3)

    def _recargar_actual(self):
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_pagos()

    def _on_page(self, page, per_page):
        self._pagina = page
        self._cargar_paginado()

    def _cargar_pagos(self, pagos=None):
        # compatibilidad: si se pasa lista, usa modo legacy (para compatibilidad con llamadas existentes)
        if pagos is not None:
            self._pagos_actuales = pagos
            self._renderizar_pagos(pagos)
            return
        self._cargar_paginado()

    def _cargar_paginado(self):
        for widget in self.scroll_pagos.winfo_children():
            widget.destroy()

        q = self._q_actual
        estado_val = "TODOS"  # filtros por fecha se mantienen en date pickers
        try:
            from repositories import pago_repository
            offset = (self._pagina - 1) * self._per_page
            rows, total = pago_repository.buscar_paginado(q=q, limit=self._per_page, offset=offset)
            self._total = total
            if hasattr(self, 'pagination'):
                self.pagination.set_total(total)
        except Exception:
            from utils.busqueda import coincide as _coincide
            rows = self._pagos_actuales if hasattr(self, '_pagos_actuales') else pago_controller.listar_pagos()
            if q:
                rows = [p for p in rows if _coincide(
                    q, p.get('numero_recibo', ''), p.get('metodo_pago', ''),
                    p.get('dni', ''), p.get('nombres', ''), p.get('apellidos', ''),
                    f"{p.get('nombres', '')} {p.get('apellidos', '')}")]
            total = len(rows)
            rows = rows[(self._pagina - 1) * self._per_page : self._pagina * self._per_page]
            self._total = total

        if not rows:
            ctk.CTkLabel(self.scroll_pagos, text="📭 No se encontraron pagos", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=30)
            ctk.CTkLabel(self.scroll_pagos, text="Registra tu primer pago con + Nuevo Pago", font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack()
            self.label_status.configure(text=f"Total: {self._total} • Página {self._pagina}")
            return

        for pago in rows:
            self._crear_card_pago(pago)

        total_paginas = max(1, (self._total + self._per_page - 1) // self._per_page)
        self.label_status.configure(text=f"✅ Total: {self._total} pago(s) • Página {self._pagina}/{total_paginas} • 50 por página")

    def _on_busqueda_cambiar(self, event=None):
        self._q_actual = self.entry_busqueda.get().strip()
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _renderizar_pagos(self, pagos):
        for widget in self.scroll_pagos.winfo_children():
            widget.destroy()

        if not pagos:
            ctk.CTkLabel(self.scroll_pagos, text="📭 No se encontraron pagos", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=30)
            ctk.CTkLabel(self.scroll_pagos, text="Registra tu primer pago con + Nuevo Pago", font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack()
            self.label_status.configure(text="Total: 0 pagos • Prueba filtros de fecha")
            return
        for pago in pagos:
            self._crear_card_pago(pago)
        self.label_status.configure(text=f"✅ Total: {len(pagos)} pago(s) • {sum(p.get('monto_total',0) for p in pagos):.2f} S/ en total")

    def _crear_card_pago(self, pago):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle
        card = crear_card_interactiva(self.scroll_pagos)
        card.pack(fill="x", padx=6, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=10)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info, text=f"🧾 Recibo: {pago.get('numero_recibo', '')}", font=ctk.CTkFont(size=15, weight="bold"), text_color="#1F0A33").pack(anchor="w")
        ctk.CTkLabel(info, text=f"💵 S/{pago.get('monto_total', 0):.2f}  •  {pago.get('metodo_pago', '')}  •  📅 {pago.get('fecha_pago', '')}", font=ctk.CTkFont(size=13), text_color="#374151").pack(anchor="w", pady=2)
        ctk.CTkLabel(info, text=f"👤 Registrado por: {pago.get('username', '')}", font=ctk.CTkFont(size=12), text_color="#6B5B7B").pack(anchor="w")
        # comprobante thumbnail si existe (OneDrive)
        comp_path = pago.get("comprobante_path") or pago.get("comprobante") or ""
        if comp_path and os.path.isfile(comp_path):
            try:
                from PIL import Image
                img = Image.open(comp_path)
                img.thumbnail((70, 70))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 70))
                if not hasattr(self, "_comp_cache"):
                    self._comp_cache = {}
                self._comp_cache[pago.get("id_pago", pago.get("numero_recibo"))] = ctk_img
                lbl = ctk.CTkLabel(info, image=ctk_img, text="")
                lbl.pack(anchor="w", pady=3)
                lbl.bind("<Button-1>", lambda e, p=comp_path: os.startfile(p) if os.path.exists(p) else None)
                ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp_path)} (clic para ampliar)", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
            except Exception:
                ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp_path)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
        elif comp_path:
            ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp_path)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
        # badge monto
        badge = ctk.CTkFrame(top, fg_color="#F3E8FF", corner_radius=8)
        badge.pack(side="right", padx=10)
        ctk.CTkLabel(badge, text=f"S/{pago.get('monto_total',0):.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#7C3AED").pack(padx=10, pady=6)

        # ── Detalle expandible inline ──
        def _poblar_detalle(frame, _p=pago):
            linea_detalle(frame, "ID pago", _p.get("id_pago"))
            linea_detalle(frame, "Estudiante", f"{_p.get('nombres','')} {_p.get('apellidos','')} • DNI {_p.get('dni','')}")
            linea_detalle(frame, "Cuota / Periodo", f"{_p.get('id_cuota','')} • {_p.get('periodo','')}")
            linea_detalle(frame, "Observación", _p.get("observacion"))
            linea_detalle(frame, "Comprobante", _p.get("comprobante_path") or _p.get("comprobante"))
            linea_detalle(frame, "Registrado por", _p.get("username"))
            linea_detalle(frame, "Fecha pago", _p.get("fecha_pago"))

        toggle_btn, _, _ = agregar_detalle_expandible(card, _poblar_detalle)
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    def _buscar_por_fecha(self):
        fecha_inicio = self.date_picker_inicio.get()
        fecha_fin = self.date_picker_fin.get()

        if not fecha_inicio or not fecha_fin:
            self.label_status.configure(text="Selecciona ambas fechas", text_color="orange")
            return

        if fecha_inicio > fecha_fin:
            self.label_status.configure(text="La fecha de inicio debe ser anterior a la fecha fin", text_color="red")
            return

        # Usar paginación también para búsqueda por fecha
        self._q_actual = f"fecha:{fecha_inicio}..{fecha_fin}"
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _limpiar_fechas(self):
        self.date_picker_inicio.delete()
        self.date_picker_fin.delete()
        self._q_actual = ""
        self._pagina = 1
        if hasattr(self, 'pagination'):
            self.pagination.reset()
        self._cargar_paginado()

    def _limpiar_form_pago(self):
        try:
            self.combo_estudiante.set("Seleccionar estudiante...")
            self.combo_cuota.set("Sin cuotas pendientes")
            self.entry_monto.delete(0, "end")
            self.entry_observacion.delete(0, "end")
            self.combo_metodo.set("EFECTIVO")
            self._comprobante_path = None
            self.label_comprobante.configure(text="Sin comprobante")
            self.label_comprobante_preview.configure(image=None, text="")
            self.label_form_status.configure(text="")
        except Exception:
            pass

    def _nuevo_pago(self):
        self._cargar_combo_estudiantes()
        self.entry_monto.delete(0, "end")
        self.label_form_status.configure(text="")
        self.tabview.set("Registrar Pago")

    def _cargar_combo_estudiantes(self):
        from controllers import pago_controller
        matriculas = pago_controller.listar_matriculas_activas()
        nombres = [f"{m.get('nombres', '')} {m.get('apellidos', '')} - {m.get('tarifa_nombre', '')}" for m in matriculas]
        self.combo_estudiante.configure(values=nombres if nombres else ["Sin matrículas activas"])
        self._matriculas_map = {n: m["id_matricula"] for n, m in zip(nombres, matriculas)}

    def _on_estudiante_cambiado(self, selection):
        self._cargar_combo_cuotas(selection)

    def _cargar_combo_cuotas(self, selection):
        id_mat = self._matriculas_map.get(selection)
        if not id_mat:
            return

        cuotas = pago_controller.obtener_cuotas_pendientes(id_mat)

        nombres = []
        self._cuotas_map = {}
        for c in cuotas:
            nombre = f"{c['periodo']} - S/{c['saldo']:.2f} ({c['estado']})"
            nombres.append(nombre)
            self._cuotas_map[nombre] = c["id_cuota"]

        self.combo_cuota.configure(values=nombres if nombres else ["Sin cuotas pendientes"])

    def _registrar_pago(self):
        est_selection = self.combo_estudiante.get()
        id_mat = self._matriculas_map.get(est_selection)
        if not id_mat:
            self.label_form_status.configure(text="Seleccione un estudiante", text_color="red")
            return

        cuota_selection = self.combo_cuota.get()
        id_cuota = self._cuotas_map.get(cuota_selection)
        if not id_cuota:
            self.label_form_status.configure(text="Seleccione una cuota", text_color="red")
            return

        monto_str = self.entry_monto.get().strip()
        if not monto_str:
            self.label_form_status.configure(text="Ingrese el monto", text_color="red")
            return

        usuario = login_controller.obtener_usuario_actual()
        if not usuario:
            self.label_form_status.configure(text="Sesión no válida", text_color="red")
            return

        comprobante = self._comprobante_path
        if self.combo_metodo.get() != "EFECTIVO" and not comprobante:
            self.label_form_status.configure(text="Suba comprobante para YAPE/PLIN/TRANSFERENCIA (RN-042)", text_color="orange")
            return
        data = {
            "id_usuario": usuario["id_usuario"],
            "id_cuota": id_cuota,
            "monto_pagado": monto_str,
            "metodo_pago": self.combo_metodo.get(),
            "observacion": self.entry_observacion.get().strip(),
            "comprobante_path": comprobante,
        }

        exito, msg, id_pago = pago_controller.registrar_pago(data)

        if exito:
            self.label_form_status.configure(text=msg, text_color="green")
            self._cargar_pagos()
            self.entry_monto.delete(0, "end")
            self.entry_observacion.delete(0, "end")
            self._comprobante_path = None
            self.label_comprobante.configure(text="Sin comprobante")
        else:
            self.label_form_status.configure(text=msg, text_color="red")

    def _elegir_comprobante(self):
        from tkinter import filedialog
        from utils.constants import COMPROBANTES_DIR
        path = filedialog.askopenfilename(filetypes=[("Imagen","*.jpg *.jpeg *.png"),("Todos","*.*")])
        if path:
            if os.path.getsize(path) > 5 * 1024 * 1024:
                self.label_form_status.configure(text="❌ Comprobante debe ser ≤5MB", text_color="red")
                return
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            self._comprobante_path = path
            self.label_comprobante.configure(text=f"✅ {os.path.basename(path)}")
            if Image and os.path.isfile(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((70, 70))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 70))
                    self._comprobante_preview = ctk_img
                    self.label_comprobante_preview.configure(image=ctk_img, text="")
                except Exception:
                    pass

    def _cargar_morosos(self):
        for widget in self.scroll_morosos.winfo_children():
            widget.destroy()

        morosos = pago_controller.obtener_cuotas_vencidas()

        if not morosos:
            ctk.CTkLabel(
                self.scroll_morosos, text="No hay cuotas vencidas",
                text_color="green",
            ).pack(pady=20)
            self.label_status_morosos.configure(text="Total: 0")
            return

        for m in morosos:
            card = ctk.CTkFrame(self.scroll_morosos)
            card.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(
                card,
                text=f"{m.get('nombres', '')} {m.get('apellidos', '')} - DNI: {m.get('dni', '')}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(anchor="w", padx=10, pady=(5, 0))

            ctk.CTkLabel(
                card,
                text=f"Cuota: {m.get('periodo', '')} | Venció: {m.get('fecha_vencimiento', '')} | "
                     f"Saldo: S/{m.get('saldo', 0):.2f}",
                font=ctk.CTkFont(size=12), text_color="red",
            ).pack(anchor="w", padx=10, pady=(0, 5))

        self.label_status_morosos.configure(text=f"Total: {len(morosos)} cuota(s) vencida(s)")
