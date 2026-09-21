import customtkinter as ctk
from controllers import estudiante_controller
from utils.debounce import Debouncer
from utils.busqueda import coincide
from widgets.date_picker import DatePicker
from utils.logger import logger
import os
from tkinter import filedialog
try:
    from PIL import Image
except ImportError:
    Image = None
from utils.constants import FOTOS_DIR
import shutil


class EstudianteView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._estudiantes_map = {}
        self._id_apoderado_editando = None
        self._crear_widgets()
        self._cargar_estudiantes(activo=1, estado="ACTIVO")

    def destroy(self):
        try:
            if hasattr(self, "_debouncer"):
                self._debouncer.cancel()
        except Exception:
            pass
        try:
            if hasattr(self, "_debouncer_apod"):
                self._debouncer_apod.cancel()
        except Exception:
            pass
        super().destroy()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_lista = self.tabview.add("Estudiantes")
        self.tab_form = self.tabview.add("Registrar / Editar")
        self.tab_apoderados = self.tabview.add("Apoderados")

        self._crear_tab_lista()
        self._crear_tab_formulario()
        self._crear_tab_apoderados()

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        # ── Sección 1: título estilo Configuración ──
        sec_titulo = crear_seccion(
            self.tab_lista, titulo="Lista de Estudiantes", icono="👥",
            descripcion="Todos los alumnos con su estado. Clic en ▾ Ver detalle para contacto, edad y apoderados.",
            nro=1,
        )
        crear_boton_interactivo(sec_titulo, text="+ Nuevo", width=110, command=self._nuevo_estudiante,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))

        # ── Sección 2: filtros ──
        sec_filtros = crear_seccion(
            self.tab_lista, titulo="Filtros y búsqueda", icono="🔍",
             descripcion="Filtra por estado o busca por nombre, documento o carnet.",
            nro=2,
        )
        filtros = ctk.CTkFrame(sec_filtros, fg_color="transparent")
        filtros.pack(fill="x", padx=10, pady=(0, 8))

        self.filtro_estado = ctk.CTkSegmentedButton(
            filtros, values=["Todos", "Activos", "Retirados", "Reingresantes"],
            command=self._filtrar,
        )
        self.filtro_estado.set("Activos")
        self.filtro_estado.pack(side="left", padx=(0, 10))

        self.entry_busqueda = ctk.CTkEntry(
            filtros, placeholder_text="Buscar por nombre, documento o carnet...",
            width=250,
        )
        self.entry_busqueda.pack(side="left", padx=5)
        self._debouncer = Debouncer(self, 300)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._debouncer.call(self._on_busqueda_cambiar))
        crear_nota(sec_filtros, "Tip: clic en ▾ Ver detalle de cada tarjeta para ver contacto y apoderados sin abrir el formulario.")

        self.scroll_estudiantes = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll_estudiantes.pack(fill="both", expand=True, padx=5, pady=5)

        self.label_status = ctk.CTkLabel(self.tab_lista, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_status.pack(pady=3)

    def _crear_tab_formulario(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        sec1 = crear_seccion(scroll, titulo="Documento e identidad", icono="🪪",
                             descripcion="Datos del estudiante. Los marcados con * son obligatorios.", nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))

        row_doc = ctk.CTkFrame(cuerpo1, fg_color="transparent")
        row_doc.pack(fill="x", anchor="w", pady=(0, 5))

        ctk.CTkLabel(row_doc, text="Tipo Doc. *").pack(side="left", padx=(0, 5))
        self.combo_tipo_doc = ctk.CTkComboBox(
            row_doc, values=["DNI", "CARNET"], width=120,
        )
        self.combo_tipo_doc.set("DNI")
        self.combo_tipo_doc.pack(side="left", padx=(0, 10))

        self.label_dni_est = ctk.CTkLabel(row_doc, text="Documento *", font=ctk.CTkFont(size=12))
        self.label_dni_est.pack(side="left", padx=(0, 5))
        self.entry_dni = ctk.CTkEntry(row_doc, placeholder_text="DNI (8) o carnet (9)", width=200)
        self.entry_dni.pack(side="left")

        ctk.CTkLabel(cuerpo1, text="Nombres *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_nombres = ctk.CTkEntry(cuerpo1, placeholder_text="Nombres completos", width=400)
        self.entry_nombres.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo1, text="Apellidos *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_apellidos = ctk.CTkEntry(cuerpo1, placeholder_text="Apellidos completos", width=400)
        self.entry_apellidos.pack(anchor="w", pady=(0, 5))

        sec2 = crear_seccion(scroll, titulo="Foto y condición de ingreso", icono="📷",
                             descripcion="Foto opcional (≤2MB). El check 🆕 define Nuevos del Mes.", nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))
        # Foto del niño (RN-041) - flexible, opcional, ≤2MB jpg/png
        foto_frame = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        foto_frame.pack(fill="x", anchor="w", pady=5)
        ctk.CTkLabel(foto_frame, text="Foto del niño (opcional):").pack(side="left", padx=(0,5))
        self.btn_foto = ctk.CTkButton(foto_frame, text="📷 Seleccionar foto", width=150, command=self._seleccionar_foto)
        self.btn_foto.pack(side="left", padx=5)
        self.label_foto = ctk.CTkLabel(foto_frame, text="Sin foto", text_color="gray")
        self.label_foto.pack(side="left", padx=5)
        self._foto_tmp_path = None
        self._foto_preview = None
        self.label_foto_preview = ctk.CTkLabel(foto_frame, text="")
        self.label_foto_preview.pack(side="left", padx=5)

        # RN-051: es_nuevo única vez — bloque destacado (define Nuevos del Mes en Dashboard)
        marco_nuevo = ctk.CTkFrame(cuerpo2, fg_color="#F3E8FF", border_width=1, border_color="#7C3AED", corner_radius=8)
        marco_nuevo.pack(fill="x", anchor="w", pady=6)
        self.var_es_nuevo = ctk.IntVar(value=0)
        self.check_es_nuevo = ctk.CTkCheckBox(marco_nuevo, text="🆕 ¿Es estudiante REALMENTE nuevo?", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3D1559", variable=self.var_es_nuevo)
        self.check_es_nuevo.pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(marco_nuevo, text="Marca SOLO si es alta nueva real → regala Camiseta S/0 en su 1ª matrícula y cuenta en Dashboard > Nuevos del Mes.", font=ctk.CTkFont(size=11), text_color="#6B5B7B", wraplength=550, justify="left").pack(anchor="w", padx=10)
        ctk.CTkLabel(marco_nuevo, text="⚠ Si es carga masiva de alumnos existentes, DEJAR DESMARCADO (no saldrán como nuevos). Luego se bloquea solo.", font=ctk.CTkFont(size=11, weight="bold"), text_color="#DC2626", wraplength=550, justify="left").pack(anchor="w", padx=10, pady=(2, 8))

        sec3 = crear_seccion(scroll, titulo="Nacimiento y contacto", icono="🎂",
                             descripcion="Fecha, sexo y datos de contacto.", nro=3)
        cuerpo3 = ctk.CTkFrame(sec3, fg_color="transparent")
        cuerpo3.pack(fill="x", padx=10, pady=(0, 8))

        row1 = ctk.CTkFrame(cuerpo3, fg_color="transparent")
        row1.pack(fill="x", anchor="w", pady=3)

        self.date_picker_nac = DatePicker(row1, label_text="Fecha nacimiento:")
        self.date_picker_nac.pack(side="left")

        ctk.CTkLabel(row1, text="Sexo:").pack(side="left", padx=(20, 5))
        self.combo_sexo = ctk.CTkComboBox(row1, values=["", "M", "F"], width=80)
        self.combo_sexo.set("")
        self.combo_sexo.pack(side="left")

        self.entry_direccion = ctk.CTkEntry(cuerpo3, placeholder_text="Dirección", width=400)
        self.entry_direccion.pack(anchor="w", pady=3)

        row2 = ctk.CTkFrame(cuerpo3, fg_color="transparent")
        row2.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row2, text="Teléfono:").pack(side="left", padx=(0, 5))
        self.entry_telefono = ctk.CTkEntry(row2, placeholder_text="Teléfono", width=150)
        self.entry_telefono.pack(side="left")

        ctk.CTkLabel(row2, text="Correo:").pack(side="left", padx=(20, 5))
        self.entry_correo = ctk.CTkEntry(row2, placeholder_text="Correo", width=200)
        self.entry_correo.pack(side="left")

        sec4 = crear_seccion(scroll, titulo="Apoderado Principal (obligatorio)", icono="👨‍👩‍👧",
                             descripcion="Un principal obligatorio; más apoderados en la pestaña Apoderados.", nro=4)
        cuerpo4 = ctk.CTkFrame(sec4, fg_color="transparent")
        cuerpo4.pack(fill="x", padx=10, pady=(0, 8))

        row_doc_ap = ctk.CTkFrame(cuerpo4, fg_color="transparent")
        row_doc_ap.pack(fill="x", anchor="w", pady=(0, 5))

        ctk.CTkLabel(row_doc_ap, text="Tipo Doc. *").pack(side="left", padx=(0, 5))
        self.combo_tipo_doc_ap = ctk.CTkComboBox(
            row_doc_ap, values=["DNI", "CARNET"], width=120,
        )
        self.combo_tipo_doc_ap.set("DNI")
        self.combo_tipo_doc_ap.pack(side="left", padx=(0, 10))

        self.label_dni_ap = ctk.CTkLabel(row_doc_ap, text="Documento *", font=ctk.CTkFont(size=12))
        self.label_dni_ap.pack(side="left", padx=(0, 5))
        self.entry_dni_ap = ctk.CTkEntry(row_doc_ap, placeholder_text="DNI (8) o carnet (9)", width=200)
        self.entry_dni_ap.pack(side="left")

        ctk.CTkLabel(cuerpo4, text="Nombres *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_nombres_ap = ctk.CTkEntry(cuerpo4, placeholder_text="Nombres completos", width=400)
        self.entry_nombres_ap.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(cuerpo4, text="Apellidos *", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_apellidos_ap = ctk.CTkEntry(cuerpo4, placeholder_text="Apellidos completos", width=400)
        self.entry_apellidos_ap.pack(anchor="w", pady=(0, 5))

        row3 = ctk.CTkFrame(cuerpo4, fg_color="transparent")
        row3.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row3, text="Parentesco *").pack(side="left", padx=(0, 5))
        self.combo_parentesco = ctk.CTkComboBox(
            row3, values=["Padre", "Madre", "Tío", "Abuelo", "Hermano", "Otro"],
            width=150,
        )
        self.combo_parentesco.set("Padre")
        self.combo_parentesco.pack(side="left")

        ctk.CTkLabel(row3, text="Teléfono:").pack(side="left", padx=(20, 5))
        self.entry_telefono_ap = ctk.CTkEntry(row3, placeholder_text="Teléfono", width=150)
        self.entry_telefono_ap.pack(side="left")

        self.entry_direccion_ap = ctk.CTkEntry(cuerpo4, placeholder_text="Dirección del apoderado", width=400)
        self.entry_direccion_ap.pack(anchor="w", pady=3)

        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_form_status = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", padx=10, pady=(8, 2))

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=10, pady=(2, 8))

        self.btn_guardar = crear_boton_interactivo(
            btn_frame, text="Guardar", width=120,
            command=self._guardar_estudiante, fg_color="#7C3AED",
        )
        self.btn_guardar.pack(side="left", padx=5)

        self.btn_cancelar = ctk.CTkButton(
            btn_frame, text="Cancelar", width=120, fg_color="gray",
            command=self._cancelar_formulario,
        )
        self.btn_cancelar.pack(side="left", padx=5)

        self._id_estudiante_editando = None

    def _crear_tab_apoderados(self):
        header = ctk.CTkFrame(self.tab_apoderados, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            header, text="Apoderados por Estudiante",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Asociar", width=110,
            command=self._asociar_apoderado,
        ).pack(side="right")

        self.combo_estudiante = ctk.CTkComboBox(
            self.tab_apoderados, values=["Seleccionar estudiante..."],
            width=350, command=self._cargar_apoderados_estudiante,
        )
        self.combo_estudiante.set("Seleccionar estudiante...")
        self.combo_estudiante.pack(anchor="w", padx=5, pady=5)

        self.entry_busqueda_apod = ctk.CTkEntry(
            self.tab_apoderados, placeholder_text="Buscar apoderado por nombre o documento...",
            width=350,
        )
        self.entry_busqueda_apod.pack(anchor="w", padx=5, pady=(0, 5))
        self._debouncer_apod = Debouncer(self, 300)
        self.entry_busqueda_apod.bind("<KeyRelease>", lambda e: self._debouncer_apod.call(self._on_busqueda_apod_cambiar))

        self.scroll_apoderados = ctk.CTkScrollableFrame(self.tab_apoderados)
        self.scroll_apoderados.pack(fill="both", expand=True, padx=5, pady=5)

        self._apoderados_actuales = []
        self._cargar_combo_estudiantes()

    def _cargar_estudiantes(self, activo=None, estado=None):
        for widget in self.scroll_estudiantes.winfo_children():
            widget.destroy()

        estudiantes = estudiante_controller.listar_estudiantes(activo=activo, estado=estado)

        if not estudiantes:
            ctk.CTkLabel(
                self.scroll_estudiantes, text="No hay estudiantes registrados",
                text_color="gray",
            ).pack(pady=20)
            self.label_status.configure(text="Total: 0")
            return

        for est in estudiantes:
            self._crear_card_estudiante(est)

        self.label_status.configure(text=f"Total: {len(estudiantes)} estudiante(s)")

    def _crear_card_estudiante(self, est):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle
        card = crear_card_interactiva(self.scroll_estudiantes)
        card.pack(fill="x", padx=6, pady=4)

        estado = est.get("estado", "ACTIVO")
        color_estado = "green" if estado == "ACTIVO" else ("orange" if estado == "REINGRESANTE" else "red")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        nombre = f"{est.get('nombres', '')} {est.get('apellidos', '')}"
        ctk.CTkLabel(
            info, text=nombre,
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=f"DNI: {est.get('dni', '')}  |  Estado: {estado}",
            font=ctk.CTkFont(size=12), text_color="#6B5B7B",
        ).pack(anchor="w")
        if int(est.get("es_nuevo", 0) or 0) == 1:
            ctk.CTkLabel(info, text="🆕 NUEVO • Regala Camiseta S/0 en 1ª matrícula", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7C3AED").pack(anchor="w")
        # Mostrar foto thumbnail grande si existe (RN-041) — Pillow 12.3 ya en requirements
        foto_path = est.get("foto_path")
        if foto_path and os.path.isfile(foto_path) and Image:
            try:
                img = Image.open(foto_path)
                # thumbnail más grande y visible (90x90) + borde
                img.thumbnail((90, 90))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(90, 90))
                if not hasattr(self, "_fotos_cache"):
                    self._fotos_cache = {}
                self._fotos_cache[est["id_estudiante"]] = ctk_img
                # frame con borde para destacar
                foto_frame = ctk.CTkFrame(info, fg_color="white", border_width=1, border_color="#E5E7EB", corner_radius=8)
                foto_frame.pack(anchor="w", pady=4)
                lbl = ctk.CTkLabel(foto_frame, image=ctk_img, text="")
                lbl.pack(padx=4, pady=4)
                ctk.CTkLabel(info, text=f"📷 {os.path.basename(foto_path)} (clic para ampliar)", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
                def _abrir(path=foto_path):
                    try:
                        os.startfile(path)
                    except Exception:
                        pass
                lbl.bind("<Button-1>", lambda e, p=foto_path: _abrir(p))
                foto_frame.bind("<Button-1>", lambda e, p=foto_path: _abrir(p))
            except Exception:
                ctk.CTkLabel(info, text=f"📷 Foto: {os.path.basename(foto_path)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
        elif foto_path:
            ctk.CTkLabel(info, text=f"📷 Foto: {os.path.basename(foto_path)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")

        botones = ctk.CTkFrame(top, fg_color="transparent")
        botones.pack(side="right", padx=5, pady=5)

        ctk.CTkButton(
            botones, text="Editar", width=70, height=28,
            command=lambda e=est: self._editar_estudiante(e),
        ).pack(side="left", padx=2)

        if estado in ("ACTIVO", "REINGRESANTE"):
            ctk.CTkButton(
                botones, text="Retirar", width=70, height=28,
                fg_color="red", hover_color="darkred",
                command=lambda e=est: self._retirar(e),
            ).pack(side="left", padx=2)
        elif estado == "RETIRADO":
            ctk.CTkButton(
                botones, text="Reingreso", width=80, height=28,
                fg_color="orange", hover_color="darkorange",
                command=lambda e=est: self._reingreso(e),
            ).pack(side="left", padx=2)

        from controllers import login_controller
        if login_controller.es_admin():
            ctk.CTkButton(
                botones, text="Desactivar", width=80, height=28,
                fg_color="#6c757d", hover_color="#5a6268",
                command=lambda e=est: self._desactivar(e),
            ).pack(side="left", padx=2)

        # ── Detalle expandible inline (contacto + apoderados, lazy) ──
        def _poblar_detalle(frame, _est=est):
            linea_detalle(frame, "Dirección", _est.get("direccion"))
            linea_detalle(frame, "Teléfono", _est.get("telefono"))
            linea_detalle(frame, "Correo", _est.get("correo"))
            linea_detalle(frame, "F. nacimiento", _est.get("fecha_nacimiento"))
            linea_detalle(frame, "Edad", _est.get("edad"))
            linea_detalle(frame, "Sexo", _est.get("sexo"))
            linea_detalle(frame, "Carnet", _est.get("carnet"))
            try:
                apods = estudiante_controller.obtener_apoderados_por_estudiante(_est.get("id_estudiante"))
            except Exception:
                apods = []
            if apods:
                for a in apods[:3]:
                    tag = "principal" if a.get("es_principal") else "secundario"
                    linea_detalle(frame, f"Apoderado ({tag})",
                                  f"{a.get('nombres','')} {a.get('apellidos','')} • {a.get('parentesco','')} • {a.get('telefono','')}")
                if len(apods) > 3:
                    linea_detalle(frame, "Apoderados", f"+ {len(apods)-3} más (ver pestaña Apoderados)")
            else:
                linea_detalle(frame, "Apoderados", "Sin apoderados registrados")

        toggle_btn, _, _ = agregar_detalle_expandible(card, _poblar_detalle)
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    def _nuevo_estudiante(self):
        self._limpiar_formulario()
        self.var_es_nuevo.set(0)
        try:
            self.check_es_nuevo.configure(state="normal")
        except Exception:
            pass
        self.tabview.set("Registrar / Editar")

    def _editar_estudiante(self, est):
        self._limpiar_formulario()
        self._id_estudiante_editando = est["id_estudiante"]

        estudiante = estudiante_controller.obtener_estudiante(est["id_estudiante"])
        # RN-051: es_nuevo bloqueado tras crear
        try:
            es_nuevo_val = int(est.get("es_nuevo", 0) or estudiante.get("es_nuevo", 0) if estudiante else 0)
            self.var_es_nuevo.set(es_nuevo_val)
            self.check_es_nuevo.configure(state="disabled")
        except Exception:
            pass
        if estudiante:
            self.combo_tipo_doc.set(estudiante.get("tipo_documento", "DNI") or "DNI")
            self.entry_dni.insert(0, estudiante.get("dni", ""))
            self.entry_nombres.insert(0, estudiante.get("nombres", ""))
            self.entry_apellidos.insert(0, estudiante.get("apellidos", ""))
            self.date_picker_nac.set(estudiante.get("fecha_nacimiento", "") or "")
            self.combo_sexo.set(estudiante.get("sexo", "") or "")
            self.entry_direccion.insert(0, estudiante.get("direccion", "") or "")
            self.entry_telefono.insert(0, estudiante.get("telefono", "") or "")
            self.entry_correo.insert(0, estudiante.get("correo", "") or "")
            self._foto_actual = estudiante.get("foto_path")
            if self._foto_actual:
                self.label_foto.configure(text=os.path.basename(self._foto_actual))

            apoderados = estudiante_controller.obtener_apoderados_por_estudiante(est["id_estudiante"])
            ap_principales = [a for a in apoderados if a.get("es_principal")]
            if ap_principales:
                ap = ap_principales[0]
                self.entry_dni_ap.insert(0, ap.get("dni", "") or "")
                self.entry_nombres_ap.insert(0, ap.get("nombres", "") or "")
                self.entry_apellidos_ap.insert(0, ap.get("apellidos", "") or "")
                self.combo_parentesco.set(ap.get("parentesco", "Padre") or "Padre")
                self.entry_telefono_ap.insert(0, ap.get("telefono", "") or "")
                self.entry_direccion_ap.insert(0, ap.get("direccion", "") or "")
                self._id_apoderado_editando = ap.get("id_apoderado")
            else:
                self._id_apoderado_editando = None
        else:
            self._id_apoderado_editando = None

        self.tabview.set("Registrar / Editar")

    def _guardar_estudiante(self):
        logger.info("[GUARDAR] Boton Guardar presionado")
        try:
            self._guardar_estudiante_impl()
        except Exception as e:
            logger.error(f"Error inesperado al guardar estudiante: {e}", exc_info=True)
            self.label_form_status.configure(
                text=f"Error inesperado: {e}", text_color="red",
            )

    def _guardar_estudiante_impl(self):
        tipo_doc = self.combo_tipo_doc.get()
        documento = self.entry_dni.get().strip()
        logger.info(f"[GUARDAR] tipo_doc={tipo_doc} documento={documento}")

        if tipo_doc == "DNI" and len(documento) != 8:
            logger.info(f"[GUARDAR] FAIL: DNI length={len(documento)}")
            self.label_form_status.configure(text="El DNI debe tener 8 dígitos", text_color="red")
            return
        if tipo_doc == "CARNET" and len(documento) != 9:
            logger.info(f"[GUARDAR] FAIL: Carnet length={len(documento)}")
            self.label_form_status.configure(text="El Carnet debe tener 9 dígitos", text_color="red")
            return

        data = {
            "dni": documento,
            "nombres": self.entry_nombres.get().strip(),
            "apellidos": self.entry_apellidos.get().strip(),
            "fecha_nacimiento": self.date_picker_nac.get(),
            "sexo": self.combo_sexo.get(),
            "direccion": self.entry_direccion.get().strip(),
            "telefono": self.entry_telefono.get().strip(),
            "correo": self.entry_correo.get().strip(),
            "tipo_documento": tipo_doc,
            "es_nuevo": int(self.var_es_nuevo.get()),
        }

        # Copiar foto a OneDrive/fotos si se seleccionó
        foto_path = None
        if self._foto_tmp_path:
            try:
                os.makedirs(FOTOS_DIR, exist_ok=True)
                ext = os.path.splitext(self._foto_tmp_path)[1] or ".jpg"
                foto_path = os.path.join(FOTOS_DIR, f"{documento}{ext}")
                shutil.copy2(self._foto_tmp_path, foto_path)
            except Exception as e:
                logger.warning(f"No se pudo copiar foto: {e}")
                foto_path = self._foto_tmp_path
            data["foto_path"] = foto_path

        if self._id_estudiante_editando:
            # Si edita y no seleccionó nueva foto, mantener existente
            if not foto_path and hasattr(self, '_foto_actual'):
                data["foto_path"] = self._foto_actual
            logger.info(f"[GUARDAR] Modo edicion id={self._id_estudiante_editando}")
            exito, msg = estudiante_controller.editar_estudiante(
                self._id_estudiante_editando, data,
            )
            logger.info(f"[GUARDAR] editar_estudiante: exito={exito} msg={msg}")

            if exito:
                dni_ap = self.entry_dni_ap.get().strip()
                if dni_ap:
                    data_ap = {
                        "dni": dni_ap,
                        "nombres": self.entry_nombres_ap.get().strip(),
                        "apellidos": self.entry_apellidos_ap.get().strip(),
                        "parentesco": self.combo_parentesco.get(),
                        "telefono": self.entry_telefono_ap.get().strip(),
                        "direccion": self.entry_direccion_ap.get().strip(),
                        "tipo_documento": self.combo_tipo_doc_ap.get(),
                    }
                    if hasattr(self, "_id_apoderado_editando") and self._id_apoderado_editando:
                        estudiante_controller.editar_apoderado(self._id_apoderado_editando, data_ap)
                    else:
                        exito_ap, msg_ap, id_ap = estudiante_controller.crear_apoderado(data_ap)
                        if exito_ap:
                            estudiante_controller.asociar_apoderado(
                                self._id_estudiante_editando, id_ap, es_principal=True,
                            )

                self.label_form_status.configure(text=msg, text_color="green")
                self._limpiar_formulario()
                self._cargar_estudiantes()
                self._cargar_combo_estudiantes()
                self.tabview.set("Estudiantes")
            else:
                self.label_form_status.configure(text=msg, text_color="red")
        else:
            logger.info("[GUARDAR] Modo creacion nuevo estudiante")
            tipo_doc_ap = self.combo_tipo_doc_ap.get()
            dni_ap = self.entry_dni_ap.get().strip()
            nombres_ap = self.entry_nombres_ap.get().strip()
            apellidos_ap = self.entry_apellidos_ap.get().strip()
            parentesco = self.combo_parentesco.get()
            logger.info(f"[GUARDAR] Apoderado: dni={dni_ap} nombres={nombres_ap} apellidos={apellidos_ap}")

            if not dni_ap:
                self.label_form_status.configure(text="El documento del apoderado es obligatorio", text_color="red")
                return
            if tipo_doc_ap == "DNI" and len(dni_ap) != 8:
                self.label_form_status.configure(text="El DNI del apoderado debe tener 8 dígitos", text_color="red")
                return
            if tipo_doc_ap == "CARNET" and len(dni_ap) != 9:
                self.label_form_status.configure(text="El Carnet del apoderado debe tener 9 dígitos", text_color="red")
                return
            if not nombres_ap:
                self.label_form_status.configure(text="Los nombres del apoderado son obligatorios", text_color="red")
                return
            if not apellidos_ap:
                self.label_form_status.configure(text="Los apellidos del apoderado son obligatorios", text_color="red")
                return

            logger.info(f"[GUARDAR] Llamando crear_estudiante con data={data}")
            exito, msg, id_estudiante = estudiante_controller.crear_estudiante(data)
            logger.info(f"[GUARDAR] crear_estudiante: exito={exito} msg={msg} id={id_estudiante}")

            if not exito:
                self.label_form_status.configure(text=msg, text_color="red")
                return

            data_ap = {
                "dni": dni_ap,
                "nombres": nombres_ap,
                "apellidos": apellidos_ap,
                "parentesco": parentesco,
                "telefono": self.entry_telefono_ap.get().strip(),
                "direccion": self.entry_direccion_ap.get().strip(),
                "tipo_documento": tipo_doc_ap,
            }
            exito_ap, msg_ap, id_apoderado = estudiante_controller.crear_apoderado(data_ap)

            if not exito_ap:
                self.label_form_status.configure(
                    text=f"Estudiante creado, pero error con apoderado: {msg_ap}",
                    text_color="orange",
                )
                self._limpiar_formulario()
                self._cargar_estudiantes()
                self._cargar_combo_estudiantes()
                self.tabview.set("Estudiantes")
                return

            from controllers import estudiante_controller as ec
            logger.info(f"[GUARDAR] Asociando estudiante={id_estudiante} apoderado={id_apoderado}")
            ec.asociar_apoderado(id_estudiante, id_apoderado, es_principal=True)

            logger.info("[GUARDAR] EXITO: Estudiante y apoderado registrados")
            self.label_form_status.configure(text="Estudiante y apoderado registrados correctamente", text_color="green")
            self._limpiar_formulario()
            self._cargar_estudiantes()
            self._cargar_combo_estudiantes()
            self.tabview.set("Estudiantes")

    def _cancelar_formulario(self):
        self._limpiar_formulario()
        self.tabview.set("Estudiantes")

    def _seleccionar_foto(self):
        path = filedialog.askopenfilename(filetypes=[("Imagen","*.jpg *.jpeg *.png"),("Todos","*.*")])
        if not path:
            return
        if os.path.getsize(path) > 2 * 1024 * 1024:
            self.label_form_status.configure(text="❌ Foto debe ser ≤2MB", text_color="red")
            return
        self._foto_tmp_path = path
        self.label_foto.configure(text=f"✅ {os.path.basename(path)}")
        # preview thumbnail grande en form
        if Image and os.path.isfile(path):
            try:
                img = Image.open(path)
                img.thumbnail((80, 80))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                self._foto_preview = ctk_img
                self.label_foto_preview.configure(image=ctk_img, text="")
            except Exception:
                pass

    def _limpiar_formulario(self):
        self._id_estudiante_editando = None
        self._id_apoderado_editando = None
        self._foto_tmp_path = None
        self._foto_actual = None
        self.label_foto.configure(text="Sin foto")
        try:
            self.var_es_nuevo.set(0)
            self.check_es_nuevo.configure(state="normal")
        except Exception:
            pass
        self.combo_tipo_doc.set("DNI")
        self.entry_dni.delete(0, "end")
        self.entry_nombres.delete(0, "end")
        self.entry_apellidos.delete(0, "end")
        self.date_picker_nac.delete()
        self.combo_sexo.set("")
        self.entry_direccion.delete(0, "end")
        self.entry_telefono.delete(0, "end")
        self.entry_correo.delete(0, "end")
        self.combo_tipo_doc_ap.set("DNI")
        self.entry_dni_ap.delete(0, "end")
        self.entry_nombres_ap.delete(0, "end")
        self.entry_apellidos_ap.delete(0, "end")
        self.combo_parentesco.set("Padre")
        self.entry_telefono_ap.delete(0, "end")
        self.entry_direccion_ap.delete(0, "end")
        self.label_form_status.configure(text="")

    def _retirar(self, est):
        exito, msg = estudiante_controller.registrar_retiro(est["id_estudiante"])
        if exito:
            self._cargar_estudiantes()
            self._cargar_combo_estudiantes()

    def _reingreso(self, est):
        from tkinter import messagebox
        exito, msg = estudiante_controller.registrar_reingreso(est["id_estudiante"])
        if exito:
            self._cargar_estudiantes()
            self._cargar_combo_estudiantes()
            # RN-044: reingreso sin uniforme, ofrecer venta aparte flexible
            if messagebox.askyesno("Reingreso", f"{msg}\n\n¿Vender uniforme ahora? (tipo y precio configurables)"):
                self._dialog_venta_reingreso(est)

    def _dialog_venta_reingreso(self, est):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Venta uniforme - Reingreso")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=f"Estudiante: {est.get('nombres','')} {est.get('apellidos','')}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(dialog, text="Tipo uniforme:").pack(anchor="w", padx=15)
        combo_tipo = ctk.CTkComboBox(dialog, width=250, values=["Cargando..."])
        combo_tipo.pack(padx=15, pady=5)
        ctk.CTkLabel(dialog, text="Cantidad:").pack(anchor="w", padx=15)
        entry_cant = ctk.CTkEntry(dialog, width=100)
        entry_cant.insert(0, "1")
        entry_cant.pack(padx=15)
        # Cargar tipos
        try:
            from controllers import tipo_uniforme_controller
            tipos = tipo_uniforme_controller.listar_tipos()
        except Exception:
            from services import tipo_uniforme_service
            tipos = tipo_uniforme_service.listar_tipos()
        nombres = [t["nombre"] for t in tipos]
        combo_tipo.configure(values=nombres if nombres else ["Uniforme Entrenamiento"])
        if nombres:
            combo_tipo.set(nombres[0])
        label_status = ctk.CTkLabel(dialog, text="")
        label_status.pack(pady=5)
        def vender():
            nombre_tipo = combo_tipo.get()
            id_tipo = next((t["id_tipo_uniforme"] for t in tipos if t["nombre"]==nombre_tipo), None)
            # buscar producto por tipo_uniforme
            from controllers import inventario_controller
            prods = inventario_controller.listar_productos()
            prod = next((p for p in prods if p.get("id_tipo_uniforme")==id_tipo), None)
            if not prod:
                label_status.configure(text="No hay producto para ese tipo", text_color="red")
                return
            try:
                cant = int(entry_cant.get().strip() or "1")
            except ValueError:
                label_status.configure(text="Cantidad inválida", text_color="red")
                return
            from controllers import venta_controller
            exito, msg2, _ = venta_controller.registrar_venta({
                "id_estudiante": est["id_estudiante"],
                "tipo_venta": "UNIFORME",
                "metodo_pago": "EFECTIVO",
                "items": [{"id_producto": prod["id_producto"], "cantidad": cant}]
            })
            label_status.configure(text=msg2, text_color="green" if exito else "red")
            if exito:
                dialog.after(800, dialog.destroy)
        ctk.CTkButton(dialog, text="Vender", command=vender).pack(pady=10)
        ctk.CTkButton(dialog, text="Omitir", fg_color="gray", command=dialog.destroy).pack()

    def _desactivar(self, est):
        from tkinter import messagebox
        nombre = f"{est.get('nombres', '')} {est.get('apellidos', '')}"
        respuesta = messagebox.askyesno(
            "Confirmar desactivación",
            f"¿Desactivar a {nombre}?\n\n"
            "El estudiante no aparecerá en las búsquedas ni listas.\n"
            "Esta acción es reversible contactando al administrador.",
        )
        if respuesta:
            exito, msg = estudiante_controller.desactivar_estudiante(est["id_estudiante"])
            if not exito:
                messagebox.showwarning("Desactivar estudiante", msg)
            self._cargar_estudiantes()
            self._cargar_combo_estudiantes()

    def _filtrar(self, valor):
        self._on_busqueda_cambiar()

    def _on_busqueda_cambiar(self, event=None):
        # Bloque A2: normaliza (tildes/espacios) y multi-campo; el documento
        # cubre DNI (8) y carnet (9, vive en persona.dni con tipo CARNET).
        texto = self.entry_busqueda.get().strip()
        filtro_estado = self.filtro_estado.get()

        activo = None
        estado = None
        if filtro_estado == "Activos":
            activo = 1
            estado = ["ACTIVO", "REINGRESANTE"]
        elif filtro_estado == "Retirados":
            activo = 1
            estado = "RETIRADO"
        elif filtro_estado == "Reingresantes":
            activo = 1
            estado = "REINGRESANTE"

        todos = estudiante_controller.listar_estudiantes(activo=activo, estado=estado)

        if texto:
            filtrados = [
                e for e in todos
                if coincide(texto, e.get("nombres", ""), e.get("apellidos", ""),
                            f"{e.get('nombres', '')} {e.get('apellidos', '')}",
                            e.get("dni", ""))
            ]
            self._renderizar_estudiantes(filtrados)
        else:
            self._renderizar_estudiantes(todos)

    def _renderizar_estudiantes(self, estudiantes):
        for widget in self.scroll_estudiantes.winfo_children():
            widget.destroy()

        if not estudiantes:
            ctk.CTkLabel(
                self.scroll_estudiantes, text="No se encontraron estudiantes",
                text_color="gray",
            ).pack(pady=20)
            self.label_status.configure(text="Total: 0")
            return

        for est in estudiantes:
            self._crear_card_estudiante(est)

        self.label_status.configure(text=f"Total: {len(estudiantes)} estudiante(s)")

    def _cargar_combo_estudiantes(self):
        estudiantes = estudiante_controller.listar_estudiantes(activo=1)
        nombres = [f"{e.get('nombres', '')} {e.get('apellidos', '')}" for e in estudiantes]
        self.combo_estudiante.configure(values=nombres if nombres else ["Sin estudiantes"])
        self._estudiantes_map = {n: e["id_estudiante"] for n, e in zip(nombres, estudiantes)}

    def _cargar_apoderados_estudiante(self, selection):
        id_est = self._estudiantes_map.get(selection)
        if not id_est:
            return

        self._apoderados_actuales = estudiante_controller.obtener_apoderados_por_estudiante(id_est)
        self._id_est_apod_actual = id_est
        self._renderizar_apoderados()

    def _on_busqueda_apod_cambiar(self, event=None):
        self._renderizar_apoderados()

    def _renderizar_apoderados(self):
        for widget in self.scroll_apoderados.winfo_children():
            widget.destroy()

        apoderados = list(getattr(self, "_apoderados_actuales", []) or [])
        try:
            texto = self.entry_busqueda_apod.get().strip()
        except Exception:
            texto = ""
        if texto:
            apoderados = [
                ap for ap in apoderados
                if coincide(texto, ap.get("nombres", ""), ap.get("apellidos", ""),
                            f"{ap.get('nombres', '')} {ap.get('apellidos', '')}",
                            ap.get("dni", ""), ap.get("parentesco", ""))
            ]

        id_est = getattr(self, "_id_est_apod_actual", None)
        if not apoderados:
            ctk.CTkLabel(
                self.scroll_apoderados,
                text="Sin apoderados asociados" if not texto else "Sin coincidencias",
                text_color="gray",
            ).pack(pady=10)
            return

        for ap in apoderados:
            card = ctk.CTkFrame(self.scroll_apoderados)
            card.pack(fill="x", padx=5, pady=3)

            principal_text = " (PRINCIPAL)" if ap.get("es_principal") else ""
            ctk.CTkLabel(
                card,
                text=f"{ap.get('nombres', '')} {ap.get('apellidos', '')} - {ap.get('parentesco', '')}{principal_text}",
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=10, pady=8)

            ctk.CTkButton(
                card, text="Quitar", width=70, height=26,
                fg_color="red", hover_color="darkred",
                command=lambda a=ap, e=id_est: self._desasociar(e, a["id_apoderado"]),
            ).pack(side="right", padx=5, pady=5)

    def _asociar_apoderado(self):
        selection = self.combo_estudiante.get()
        id_est = self._estudiantes_map.get(selection)
        if not id_est:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Asociar Apoderado")
        dialog.geometry("440x520")
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            scroll, text="Datos del Apoderado",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        row_doc = ctk.CTkFrame(scroll, fg_color="transparent")
        row_doc.pack(fill="x", anchor="w", pady=(0, 5))

        ctk.CTkLabel(row_doc, text="Tipo Doc. *").pack(side="left", padx=(0, 5))
        combo_tipo_doc = ctk.CTkComboBox(row_doc, values=["DNI", "CARNET"], width=120)
        combo_tipo_doc.set("DNI")
        combo_tipo_doc.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(row_doc, text="Documento *").pack(side="left", padx=(0, 5))
        entry_dni = ctk.CTkEntry(row_doc, placeholder_text="DNI (8) o carnet (9)", width=200)
        entry_dni.pack(side="left")

        ctk.CTkLabel(scroll, text="Nombres *").pack(anchor="w")
        entry_nombres = ctk.CTkEntry(scroll, placeholder_text="Nombres completos", width=400)
        entry_nombres.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(scroll, text="Apellidos *").pack(anchor="w")
        entry_apellidos = ctk.CTkEntry(scroll, placeholder_text="Apellidos completos", width=400)
        entry_apellidos.pack(anchor="w", pady=(0, 5))

        row_par = ctk.CTkFrame(scroll, fg_color="transparent")
        row_par.pack(fill="x", anchor="w", pady=3)

        ctk.CTkLabel(row_par, text="Parentesco *").pack(side="left", padx=(0, 5))
        combo_parentesco = ctk.CTkComboBox(
            row_par, values=["Padre", "Madre", "Tío", "Abuelo", "Hermano", "Otro"],
            width=150,
        )
        combo_parentesco.set("Padre")
        combo_parentesco.pack(side="left")

        ctk.CTkLabel(row_par, text="Teléfono:").pack(side="left", padx=(20, 5))
        entry_telefono = ctk.CTkEntry(row_par, placeholder_text="Teléfono", width=150)
        entry_telefono.pack(side="left")

        entry_direccion = ctk.CTkEntry(scroll, placeholder_text="Dirección del apoderado", width=400)
        entry_direccion.pack(anchor="w", pady=3)

        label_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12))
        label_status.pack(anchor="w", pady=5)

        def confirmar():
            dni = entry_dni.get().strip()
            nombres = entry_nombres.get().strip()
            apellidos = entry_apellidos.get().strip()
            parentesco = combo_parentesco.get()
            tipo_doc = combo_tipo_doc.get()

            if not dni:
                label_status.configure(text="El DNI es obligatorio", text_color="red")
                return
            if tipo_doc == "DNI" and len(dni) != 8:
                label_status.configure(text="El DNI debe tener 8 dígitos", text_color="red")
                return
            if tipo_doc == "CARNET" and len(dni) != 9:
                label_status.configure(text="El Carnet debe tener 9 dígitos", text_color="red")
                return
            if not nombres:
                label_status.configure(text="Los nombres son obligatorios", text_color="red")
                return
            if not apellidos:
                label_status.configure(text="Los apellidos son obligatorios", text_color="red")
                return

            data_ap = {
                "dni": dni,
                "nombres": nombres,
                "apellidos": apellidos,
                "parentesco": parentesco,
                "telefono": entry_telefono.get().strip(),
                "direccion": entry_direccion.get().strip(),
                "tipo_documento": tipo_doc,
            }

            from controllers import persona_controller
            persona = persona_controller.buscar_por_dni(dni)

            exito_ap, msg_ap, id_apoderado = estudiante_controller.crear_apoderado(data_ap)

            if not exito_ap:
                label_status.configure(text=msg_ap, text_color="red")
                return

            if not id_apoderado:
                apo = estudiante_controller.obtener_apoderado_por_persona(persona["id_persona"] if persona else None)
                if apo:
                    id_apoderado = apo["id_apoderado"]
                else:
                    label_status.configure(text="Error al obtener apoderado", text_color="red")
                    return

            tiene_principal = estudiante_controller.obtener_apoderados_por_estudiante(id_est)
            es_principal = len(tiene_principal) == 0

            exito, msg = estudiante_controller.asociar_apoderado(id_est, id_apoderado, es_principal)
            if exito:
                label_status.configure(text="Apoderado asociado correctamente", text_color="green")
                dialog.after(500, dialog.destroy)
                self._cargar_apoderados_estudiante(selection)
            else:
                label_status.configure(text=msg, text_color="red")

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=10)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, fg_color="gray",
            command=dialog.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Asociar", width=100,
            command=confirmar,
        ).pack(side="left", padx=5)

    def _desasociar(self, id_est, id_apoderado):
        exito, msg = estudiante_controller.desasociar_apoderado(id_est, id_apoderado)
        if exito:
            selection = self.combo_estudiante.get()
            self._cargar_apoderados_estudiante(selection)
