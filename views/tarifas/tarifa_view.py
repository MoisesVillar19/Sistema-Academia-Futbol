import customtkinter as ctk
from tkinter import messagebox
from controllers import tarifa_controller, configuracion_controller
from utils.logger import logger


class TarifaView(ctk.CTkFrame):
    # Fase 7e: tab_inicial ("Tarifas"/"Becas") + filtro_tipo
    # ("Todas"/"ACADEMIA"/"SERVICIO"/"CAMPEONATO") para accesos por módulo.
    def __init__(self, parent, tab_inicial=None, filtro_tipo=None):
        super().__init__(parent, fg_color="transparent")
        self._cats_map = {}
        self._filtro_actual = "Activas"
        self._filtro_tipo = filtro_tipo or "Todas"
        self._editing_id = None
        self._crear_widgets()
        self._cargar_tarifas()
        if tab_inicial in ("Tarifas", "Becas"):
            try:
                self.tabview.set(tab_inicial)
            except Exception:
                pass

    def _crear_widgets(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_tarifas = self.tabview.add("Tarifas")
        self.tab_becas = self.tabview.add("Becas")
        sec_titulo = crear_seccion(
            self.tab_tarifas, titulo="Tarifas", icono="🏷",
            descripcion="Precios de cobro por categoría (mensualidades por edad, inscripción, campeonatos). Clic en ▾ Ver detalle para descripción y uso.",
            nro=1,
        )
        crear_boton_interactivo(sec_titulo, text="+ Nueva", width=110, command=self._nueva_tarifa,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        sec_filtros = crear_seccion(
            self.tab_tarifas, titulo="Estado", icono="🔍",
            descripcion="Muestra activas (disponibles) o desactivadas.",
            nro=2,
        )
        filtros = ctk.CTkFrame(sec_filtros, fg_color="transparent")
        filtros.pack(fill="x", padx=10, pady=(0, 8))
        self.filtro_estado = ctk.CTkSegmentedButton(
            filtros, values=["Activas", "Desactivadas"],
            command=self._filtrar,
        )
        self.filtro_estado.set("Activas")
        self.filtro_estado.pack(side="left")
        self.filtro_tipo = ctk.CTkSegmentedButton(
            filtros, values=["Todas", "ACADEMIA", "SERVICIO", "CAMPEONATO"],
            command=self._filtrar_tipo,
        )
        try:
            self.filtro_tipo.set(self._filtro_tipo)
        except Exception:
            pass
        self.filtro_tipo.pack(side="left", padx=5)
        crear_nota(sec_filtros, "Tip: las tarifas con matrículas activas no se pueden eliminar, solo desactivar.")

        self.scroll = ctk.CTkScrollableFrame(self.tab_tarifas)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.label_status = ctk.CTkLabel(self.tab_tarifas, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status.pack(pady=3)

        self._crear_formulario()
        self._crear_tab_becas()

    def _crear_tab_becas(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_becas, titulo="Becas", icono="🎓",
            descripcion="Descuentos PORCENTAJE o MONTO_FIJO que se asignan al matricular. Clic en ▾ Ver detalle.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="+ Nueva Beca", width=130, command=self._nueva_beca,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))
        crear_nota(sec, "En matrícula se elige 1 beca (o varias si Configuración lo permite).")
        self.scroll_becas = ctk.CTkScrollableFrame(self.tab_becas)
        self.scroll_becas.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_becas_status = ctk.CTkLabel(self.tab_becas, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_becas_status.pack(pady=3)
        self._cargar_becas()
        self._crear_formulario_beca()

    def _cargar_becas(self):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle, crear_lista_vacia
        from controllers import beca_controller
        for w in self.scroll_becas.winfo_children():
            w.destroy()
        becas = beca_controller.listar_todas()
        if not becas:
            crear_lista_vacia(self.scroll_becas, "No hay becas", "Crea la primera con + Nueva Beca")
            self.label_becas_status.configure(text="Total: 0")
            return
        for b in becas:
            card = crear_card_interactiva(self.scroll_becas)
            card.pack(fill="x", padx=6, pady=4)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=8)
            info = ctk.CTkFrame(top, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            estado = "Activa" if b.get("activo") else "Desactivada"
            ctk.CTkLabel(info, text=f"{b.get('nombre','')} — {b.get('tipo','')} {b.get('valor',0)}",
                         font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33").pack(anchor="w")
            ctk.CTkLabel(info, text=f"{estado} | {b.get('observacion','') or '—'}",
                         font=ctk.CTkFont(size=12), text_color="#6B5B7B").pack(anchor="w")
            badge = ctk.CTkFrame(top, fg_color="#F3E8FF" if b.get("activo") else "#E5E7EB", corner_radius=8)
            badge.pack(side="right", padx=10)
            suf = "%" if b.get("tipo") == "PORCENTAJE" else ""
            ctk.CTkLabel(badge, text=f"{b.get('valor',0)}{suf}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#7C3AED").pack(padx=10, pady=6)
            botones = ctk.CTkFrame(top, fg_color="transparent")
            botones.pack(side="right", padx=5, pady=5)
            ctk.CTkButton(botones, text="Editar", width=70, height=28,
                          command=lambda x=b: self._editar_beca(x)).pack(side="left", padx=2)
            if b.get("activo"):
                ctk.CTkButton(botones, text="Desactivar", width=90, height=28, fg_color="#d9534f",
                              command=lambda x=b: self._desactivar_beca(x)).pack(side="left", padx=2)
            else:
                ctk.CTkButton(botones, text="Activar", width=80, height=28, fg_color="#28a745",
                              command=lambda x=b: self._activar_beca(x)).pack(side="left", padx=2)

            def _poblar(frame, _b=b):
                linea_detalle(frame, "ID beca", _b.get("id_beca"))
                linea_detalle(frame, "Tipo", _b.get("tipo"))
                linea_detalle(frame, "Valor", f"{_b.get('valor',0)}{'%' if _b.get('tipo')=='PORCENTAJE' else ' S/'}")
                linea_detalle(frame, "Observación", _b.get("observacion"))
                linea_detalle(frame, "Estado", "Activa" if _b.get("activo") else "Desactivada")

            toggle_btn, _, _ = agregar_detalle_expandible(card, _poblar)
            toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))
        self.label_becas_status.configure(text=f"Total: {len(becas)} beca(s)")

    def _crear_formulario(self):
        self.form_window = ctk.CTkToplevel(self)
        self.form_window.title("Nueva Tarifa")
        self.form_window.geometry("420x500")
        self.form_window.withdraw()

        scroll = ctk.CTkScrollableFrame(self.form_window)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.label_form_title = ctk.CTkLabel(
            scroll, text="Nueva Tarifa",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.label_form_title.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(scroll, text="Categoría:").pack(anchor="w")
        self.combo_categoria = ctk.CTkComboBox(scroll, width=380, values=["Cargando..."])
        self.combo_categoria.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Nombre:").pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(scroll, placeholder_text="Nombre de la tarifa", width=380)
        self.entry_nombre.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Monto (S/):").pack(anchor="w")
        self.entry_monto = ctk.CTkEntry(scroll, placeholder_text="0.00", width=380)
        self.entry_monto.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Descripción:").pack(anchor="w")
        self.entry_descripcion = ctk.CTkEntry(scroll, placeholder_text="Opcional", width=380)
        self.entry_descripcion.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Observaciones:").pack(anchor="w")
        self.entry_observaciones = ctk.CTkEntry(scroll, placeholder_text="Opcional", width=380)
        self.entry_observaciones.pack(anchor="w", pady=3)

        self.label_form_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", pady=5)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=10)

        ctk.CTkButton(
            btn_frame, text="Guardar", width=120,
            command=self._guardar_tarifa,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, fg_color="gray",
            command=lambda: self.form_window.withdraw(),
        ).pack(side="left", padx=5)

    def _cargar_categorias(self):
        cats = configuracion_controller.listar_categorias()
        nombres = [f"{c['nombre']} ({c['edad_min']}-{c['edad_max']} años)" for c in cats]
        self.combo_categoria.configure(values=nombres if nombres else ["Sin categorías"])
        self._cats_map = {n: c["id_categoria"] for n, c in zip(nombres, cats)}

    def _filtrar(self, valor):
        self._filtro_actual = valor
        self._cargar_tarifas()

    def _filtrar_tipo(self, valor):
        self._filtro_tipo = valor
        self._cargar_tarifas()

    def _nueva_tarifa(self):
        self._cargar_categorias()
        self.label_form_title.configure(text="Nueva Tarifa")
        self._editing_id = None
        self.entry_nombre.delete(0, "end")
        self.entry_monto.delete(0, "end")
        self.entry_descripcion.delete(0, "end")
        self.entry_observaciones.delete(0, "end")
        self.label_form_status.configure(text="")
        self.form_window.deiconify()

    def _editar_tarifa(self, t):
        self._cargar_categorias()
        self.label_form_title.configure(text="Editar Tarifa")

        cat_id = t["id_categoria"]
        for nombre, cid in self._cats_map.items():
            if cid == cat_id:
                self.combo_categoria.set(nombre)
                break

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, t["nombre"])

        self.entry_monto.delete(0, "end")
        self.entry_monto.insert(0, str(t["monto"]))

        self.entry_descripcion.delete(0, "end")
        self.entry_descripcion.insert(0, t.get("descripcion", "") or "")

        self.entry_observaciones.delete(0, "end")
        self.entry_observaciones.insert(0, t.get("observaciones", "") or "")

        self.label_form_status.configure(text="")
        self._editing_id = t["id_tarifa"]
        self.form_window.deiconify()

    def _guardar_tarifa(self):
        cat_selection = self.combo_categoria.get()
        id_categoria = self._cats_map.get(cat_selection)
        if not id_categoria:
            self.label_form_status.configure(text="Seleccione una categoría", text_color="red")
            return

        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.label_form_status.configure(text="El nombre es obligatorio", text_color="red")
            return

        try:
            monto = float(self.entry_monto.get().strip() or "0")
            if monto <= 0:
                self.label_form_status.configure(text="El monto debe ser mayor a 0", text_color="red")
                return
        except ValueError:
            self.label_form_status.configure(text="Monto no válido", text_color="red")
            return

        data = {
            "id_categoria": id_categoria,
            "nombre": nombre,
            "monto": monto,
            "descripcion": self.entry_descripcion.get().strip(),
            "observaciones": self.entry_observaciones.get().strip(),
        }

        if hasattr(self, "_editing_id") and self._editing_id:
            exito, msg = tarifa_controller.editar_tarifa(self._editing_id, data)
            self._editing_id = None
        else:
            exito, msg, _ = tarifa_controller.crear_tarifa(data)

        if exito:
            self.label_status.configure(text=msg, text_color="green")
            self.form_window.withdraw()
            self._cargar_tarifas()
        else:
            self.label_form_status.configure(text=msg, text_color="red")

    def _cargar_tarifas(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if self._filtro_actual == "Activas":
            tarifas = tarifa_controller.listar_tarifas_activas()
        else:
            tarifas = tarifa_controller.listar_tarifas_inactivas()
        if getattr(self, "_filtro_tipo", "Todas") != "Todas":
            tarifas = [t for t in tarifas
                       if (t.get("categoria_tipo", "ACADEMIA") or "ACADEMIA") == self._filtro_tipo]

        if not tarifas:
            from utils.ui_helpers import crear_lista_vacia
            texto = "No hay tarifas activas" if self._filtro_actual == "Activas" else "No hay tarifas desactivadas"
            crear_lista_vacia(self.scroll, texto, "Crea la primera con + Nueva")
            self.label_status.configure(text=f"Total: 0")
            return

        for t in tarifas:
            self._crear_card(t)

        self.label_status.configure(text=f"Total: {len(tarifas)} tarifa(s)")

    def _crear_card(self, t):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle
        card = crear_card_interactiva(self.scroll)
        card.pack(fill="x", padx=6, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        tipo_cat = t.get("categoria_tipo", "ACADEMIA") or "ACADEMIA"
        titulo = f"{t.get('categoria_nombre', '')} - {t['nombre']}"
        if tipo_cat != "ACADEMIA":
            titulo += f"  [{tipo_cat}]"
        ctk.CTkLabel(
            info,
            text=titulo,
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33",
        ).pack(anchor="w")

        desc = t.get("descripcion", "") or ""
        monto_line = f"Monto: S/{t['monto']:.2f}"
        if desc:
            monto_line += f" | {desc}"
        ctk.CTkLabel(
            info, text=monto_line,
            font=ctk.CTkFont(size=12), text_color="#6B5B7B",
        ).pack(anchor="w")

        if t.get("observaciones"):
            ctk.CTkLabel(
                info, text=f"Obs: {t['observaciones']}",
                font=ctk.CTkFont(size=11), text_color="#6B5B7B",
            ).pack(anchor="w")

        badge = ctk.CTkFrame(top, fg_color="#F3E8FF", corner_radius=8)
        badge.pack(side="right", padx=10)
        try:
            ctk.CTkLabel(badge, text=f"S/{t['monto']:.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#7C3AED").pack(padx=10, pady=6)
        except Exception:
            pass

        botones = ctk.CTkFrame(top, fg_color="transparent")
        botones.pack(side="right", padx=5, pady=5)

        if t["activo"]:
            ctk.CTkButton(
                botones, text="Editar", width=80, height=28,
                command=lambda t=t: self._editar_tarifa(t),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                botones, text="Desactivar", width=90, height=28,
                fg_color="#d9534f", hover_color="#c9302c",
                command=lambda t=t: self._desactivar_tarifa(t),
            ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(
                botones, text="Activar", width=80, height=28,
                fg_color="#28a745", hover_color="#218838",
                command=lambda t=t: self._activar_tarifa(t),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                botones, text="Eliminar", width=80, height=28,
                fg_color="#dc3545", hover_color="#c82333",
                command=lambda t=t: self._eliminar_tarifa(t),
            ).pack(side="left", padx=2)

        # ── Detalle expandible inline ──
        def _poblar(frame, _t=t):
            linea_detalle(frame, "ID tarifa", _t.get("id_tarifa"))
            linea_detalle(frame, "Categoría", f"{_t.get('categoria_nombre','')} [{_t.get('categoria_tipo','ACADEMIA') or 'ACADEMIA'}]")
            linea_detalle(frame, "Descripción", _t.get("descripcion"))
            linea_detalle(frame, "Observaciones", _t.get("observaciones"))
            try:
                from repositories import tarifa_repository
                uso = tarifa_repository.contar_matriculas_por_tarifa(_t.get("id_tarifa"))
                linea_detalle(frame, "Matrículas activas que la usan", uso)
            except Exception:
                pass
            linea_detalle(frame, "Estado", "Activa" if _t.get("activo") else "Desactivada")

        toggle_btn, _, _ = agregar_detalle_expandible(card, _poblar)
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    def _desactivar_tarifa(self, t):
        respuesta = messagebox.askyesno(
            "Confirmar desactivación",
            f"¿Desactivar la tarifa '{t['nombre']}'?\n\n"
            "La tarifa dejará de estar disponible para nuevas matrículas.",
        )
        if not respuesta:
            return

        exito, msg = tarifa_controller.desactivar_tarifa(t["id_tarifa"])
        if exito:
            self.label_status.configure(text=msg, text_color="green")
            self._cargar_tarifas()
        else:
            self.label_status.configure(text=f"Error: {msg}", text_color="red")

    def _activar_tarifa(self, t):
        respuesta = messagebox.askyesno(
            "Confirmar activación",
            f"¿Activar la tarifa '{t['nombre']}'?",
        )
        if not respuesta:
            return

        exito, msg = tarifa_controller.activar_tarifa(t["id_tarifa"])
        if exito:
            self.label_status.configure(text=msg, text_color="green")
            self._cargar_tarifas()
        else:
            self.label_status.configure(text=f"Error: {msg}", text_color="red")

    def _eliminar_tarifa(self, t):
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar permanentemente la tarifa '{t['nombre']}'?\n\n"
            "Esta acción no se puede deshacer.",
            icon="warning",
        )
        if not respuesta:
            return

        exito, msg = tarifa_controller.eliminar_tarifa(t["id_tarifa"])
        if exito:
            self.label_status.configure(text=msg, text_color="green")
            self._cargar_tarifas()

    # ── Becas (CRUD, solo ADMIN por menú Tarifas) ──
    def _crear_formulario_beca(self):
        self.form_beca = ctk.CTkToplevel(self)
        self.form_beca.title("Beca")
        self.form_beca.geometry("420x420")
        self.form_beca.withdraw()

        scroll = ctk.CTkScrollableFrame(self.form_beca)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.label_beca_title = ctk.CTkLabel(scroll, text="Nueva Beca", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_beca_title.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(scroll, text="Nombre *").pack(anchor="w")
        self.entry_beca_nombre = ctk.CTkEntry(scroll, placeholder_text="Ej: Pronto pago", width=380)
        self.entry_beca_nombre.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Tipo *").pack(anchor="w")
        self.combo_beca_tipo = ctk.CTkComboBox(scroll, width=380, values=["PORCENTAJE", "MONTO_FIJO"])
        self.combo_beca_tipo.set("PORCENTAJE")
        self.combo_beca_tipo.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Valor * (% si PORCENTAJE, S/ si MONTO_FIJO)").pack(anchor="w")
        self.entry_beca_valor = ctk.CTkEntry(scroll, placeholder_text="10", width=380)
        self.entry_beca_valor.pack(anchor="w", pady=3)

        ctk.CTkLabel(scroll, text="Observación:").pack(anchor="w")
        self.entry_beca_obs = ctk.CTkEntry(scroll, placeholder_text="Opcional", width=380)
        self.entry_beca_obs.pack(anchor="w", pady=3)

        self.label_beca_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12))
        self.label_beca_status.pack(anchor="w", pady=5)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=10)
        ctk.CTkButton(btn_frame, text="Guardar", width=120, command=self._guardar_beca).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", width=100, fg_color="gray",
                      command=lambda: self.form_beca.withdraw()).pack(side="left", padx=5)
        self._editing_beca_id = None

    def _nueva_beca(self):
        self.label_beca_title.configure(text="Nueva Beca")
        self._editing_beca_id = None
        for e in (self.entry_beca_nombre, self.entry_beca_valor, self.entry_beca_obs):
            e.delete(0, "end")
        self.combo_beca_tipo.set("PORCENTAJE")
        self.label_beca_status.configure(text="")
        self.form_beca.deiconify()

    def _editar_beca(self, b):
        self.label_beca_title.configure(text="Editar Beca")
        self._editing_beca_id = b["id_beca"]
        for e, v in ((self.entry_beca_nombre, b.get("nombre", "")),
                     (self.entry_beca_valor, str(b.get("valor", ""))),
                     (self.entry_beca_obs, b.get("observacion", "") or "")):
            e.delete(0, "end")
            e.insert(0, v)
        self.combo_beca_tipo.set(b.get("tipo", "PORCENTAJE"))
        self.label_beca_status.configure(text="")
        self.form_beca.deiconify()

    def _guardar_beca(self):
        from controllers import beca_controller
        nombre = self.entry_beca_nombre.get().strip()
        if not nombre:
            self.label_beca_status.configure(text="El nombre es obligatorio", text_color="red")
            return
        try:
            valor = float(self.entry_beca_valor.get().strip() or "0")
            if valor <= 0:
                raise ValueError
        except ValueError:
            self.label_beca_status.configure(text="Valor inválido (mayor a 0)", text_color="red")
            return
        data = {"nombre": nombre, "tipo": self.combo_beca_tipo.get(),
                "valor": valor, "observacion": self.entry_beca_obs.get().strip()}
        if self._editing_beca_id:
            exito, msg = beca_controller.editar_beca(self._editing_beca_id, data)
            self._editing_beca_id = None
        else:
            exito, msg, _ = beca_controller.crear_beca(data)
        if exito:
            self.label_becas_status.configure(text=msg, text_color="green")
            self.form_beca.withdraw()
            self._cargar_becas()
        else:
            self.label_beca_status.configure(text=msg, text_color="red")

    def _desactivar_beca(self, b):
        from tkinter import messagebox
        from controllers import beca_controller
        if not messagebox.askyesno("Confirmar", f"¿Desactivar la beca '{b['nombre']}'?"):
            return
        exito, msg = beca_controller.desactivar_beca(b["id_beca"])
        self.label_becas_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self._cargar_becas()

    def _activar_beca(self, b):
        from controllers import beca_controller
        exito, msg = beca_controller.activar_beca(b["id_beca"])
        self.label_becas_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self._cargar_becas()
        else:
            self.label_status.configure(text=f"Error: {msg}", text_color="red")
