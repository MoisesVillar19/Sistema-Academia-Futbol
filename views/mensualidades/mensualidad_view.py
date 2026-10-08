import customtkinter as ctk
from controllers import matricula_controller


class MensualidadView(ctk.CTkFrame):
    """Mensualidades: historial por estudiante + grilla general.

    Antes vivía en Matrículas (pestañas Cuotas/Año). Etiqueta visible
    "Mensualidad"; internamente sigue el modelo `cuota`.
    """

    def __init__(self, parent, id_estudiante=None):
        super().__init__(parent, fg_color="transparent")
        self._matriculas_map = {}
        self._cuotas_orden = "reciente"
        self._grilla_cargada = False
        self._crear_widgets()
        if id_estudiante:
            self.after(100, lambda: self.seleccionar_estudiante(id_estudiante))

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_cuotas = self.tabview.add("Por estudiante")
        self.tab_grilla = self.tabview.add("General")

        self._crear_tab_cuotas()
        self._crear_tab_grilla()
        # La grilla anual es pesada: carga perezosa al entrar a la pestaña.
        try:
            self.tabview.configure(command=self._on_tab_cambiada)
        except Exception:
            self._cargar_grilla()
            self._grilla_cargada = True

    def _on_tab_cambiada(self):
        try:
            actual = self.tabview.get()
        except Exception:
            actual = ""
        if actual == "General" and not getattr(self, "_grilla_cargada", False):
            self._grilla_cargada = True
            try:
                self.label_grilla_status.configure(text="Cargando grilla...")
                self.update_idletasks()
            except Exception:
                pass
            self._cargar_grilla()

    def aplicar_navegacion(self, params):
        """Navegación por evento abrir_modulo (avisos, Matrículas)."""
        try:
            id_est = (params or {}).get("id_estudiante")
            if id_est:
                self.seleccionar_estudiante(id_est)
        except Exception:
            pass

    def seleccionar_estudiante(self, id_estudiante):
        """Preselecciona un alumno (navegación desde Matrículas)."""
        try:
            self._cargar_combo_matriculas()
            for key, val in self._matriculas_map.items():
                if val == id_estudiante:
                    self.combo_matricula_cuotas.set(key)
                    self._cargar_cuotas(key)
                    break
            self.tabview.set("Por estudiante")
        except Exception:
            pass

    def _crear_tab_cuotas(self):
        header = ctk.CTkFrame(self.tab_cuotas, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            header, text="Historial de Mensualidades por Alumno",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        self.combo_matricula_cuotas = ctk.CTkComboBox(
            self.tab_cuotas, width=400,
            values=["Seleccionar alumno..."],
            command=self._cargar_cuotas,
        )
        self.combo_matricula_cuotas.set("Seleccionar alumno...")
        self.combo_matricula_cuotas.pack(anchor="w", padx=5, pady=5)

        barra_cuotas = ctk.CTkFrame(self.tab_cuotas, fg_color="transparent")
        barra_cuotas.pack(fill="x", padx=5, pady=2)
        self._cuotas_orden = "reciente"
        self.seg_cuotas_orden = ctk.CTkSegmentedButton(
            barra_cuotas, values=["Más reciente", "Más antiguo"],
            command=self._on_cuotas_orden)
        try:
            self.seg_cuotas_orden.set("Más reciente")
        except Exception:
            pass
        self.seg_cuotas_orden.pack(side="left", padx=5)
        self.label_cuotas_resumen = ctk.CTkLabel(
            barra_cuotas, text="⚙=generada • ⬇=importada",
            font=ctk.CTkFont(size=11), text_color="#6B5B7B")
        self.label_cuotas_resumen.pack(side="left", padx=10)

        self.scroll_cuotas = ctk.CTkScrollableFrame(self.tab_cuotas)
        self.scroll_cuotas.pack(fill="both", expand=True, padx=5, pady=5)

        self._cargar_combo_matriculas()

    def _on_cuotas_orden(self, valor):
        self._cuotas_orden = "antiguo" if valor == "Más antiguo" else "reciente"
        try:
            sel = self.combo_matricula_cuotas.get()
            if sel and sel != "Seleccionar alumno...":
                self._cargar_cuotas(sel)
        except Exception:
            pass

    def _ver_cuotas(self, mat):
        # Compat: historial por alumno desde una matrícula.
        self.tabview.set("Por estudiante")
        self._cargar_combo_matriculas()
        try:
            id_est = mat.get("id_estudiante")
            if not id_est and mat.get("id_matricula"):
                det = matricula_controller.obtener_matricula(mat["id_matricula"]) or {}
                id_est = det.get("id_estudiante")
            for key, val in self._matriculas_map.items():
                if val == id_est:
                    self.combo_matricula_cuotas.set(key)
                    self._cargar_cuotas(key)
                    break
        except Exception:
            pass

    def _cargar_combo_matriculas(self):
        from controllers import estudiante_controller
        from utils.constants import COMBO_MAX_ITEMS
        try:
            estudiantes = (estudiante_controller.listar_estudiantes() or [])[:COMBO_MAX_ITEMS]
        except Exception:
            estudiantes = []
        nombres = [f"{e.get('nombres', '')} {e.get('apellidos', '')}".strip()
                   or f"DNI {e.get('dni', '')}" for e in estudiantes]
        self.combo_matricula_cuotas.configure(
            values=nombres if nombres else ["Sin estudiantes"])
        self._matriculas_map = {n: e["id_estudiante"] for n, e in zip(nombres, estudiantes)}

    def _cargar_cuotas(self, selection):
        from controllers import estudiante_controller
        for widget in self.scroll_cuotas.winfo_children():
            widget.destroy()

        id_est = self._matriculas_map.get(selection)
        if not id_est:
            return

        try:
            est = estudiante_controller.obtener_estudiante(id_est) or {}
        except Exception:
            est = {}
        estado_est = str(est.get("estado", "") or "")
        if estado_est in ("REINGRESANTE", "RETIRADO"):
            ctk.CTkLabel(
                self.scroll_cuotas,
                text=("🔄 Reingresante: historial con varias matrículas"
                      if estado_est == "REINGRESANTE" else
                      "📁 Retirado: historial archivado (se conserva)"),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#7C3AED").pack(anchor="w", padx=6, pady=(4, 0))

        try:
            matriculas = matricula_controller.obtener_por_estudiante(id_est) or []
        except Exception:
            matriculas = []
        if not matriculas:
            ctk.CTkLabel(
                self.scroll_cuotas, text="Sin matrículas registradas",
                text_color="gray",
            ).pack(pady=10)
            return

        try:
            from repositories import matricula_beca_repository
            mapa_becas = matricula_beca_repository.obtener_por_matriculas(
                [m.get("id_matricula") for m in matriculas if m.get("id_matricula")])
        except Exception:
            mapa_becas = {}
        total_cuotas = 0
        for mat in matriculas:
            try:
                becas = mapa_becas.get(mat["id_matricula"], None)
                if becas is None:
                    becas = matricula_controller.obtener_becas_por_matricula(
                        mat["id_matricula"])
                txt_beca = ", ".join(b.get("beca_nombre", "") for b in becas if b.get("beca_nombre"))
            except Exception:
                txt_beca = ""
            head = (f"Matrícula #{mat.get('id_matricula')} • "
                    f"{mat.get('tarifa_nombre', '') or 'Tarifa'} • "
                    f"Inicio {mat.get('fecha_inicio', '')} • {mat.get('estado', '')}"
                    + (f" • 🎓 {txt_beca}" if txt_beca else ""))
            ctk.CTkLabel(self.scroll_cuotas, text=head,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#3D1559").pack(anchor="w", padx=6, pady=(8, 2))
            try:
                cuotas = matricula_controller.obtener_cuotas_por_matricula(
                    mat["id_matricula"])
            except Exception:
                cuotas = []
            # Todas: generadas, importadas y manuales (activas y anuladas).
            # Orden: más reciente primero por defecto.
            try:
                cuotas = sorted(cuotas, key=lambda c: str(c.get("fecha_vencimiento", "")),
                                reverse=(getattr(self, "_cuotas_orden", "reciente") == "reciente"))
            except Exception:
                pass
            total_cuotas += len(cuotas)
            if not cuotas:
                ctk.CTkLabel(self.scroll_cuotas, text="Sin mensualidades registradas",
                             text_color="gray").pack(anchor="w", padx=12)
                continue
            for cuota in cuotas:
                self._card_cuota(self.scroll_cuotas, cuota)
        try:
            self.label_cuotas_resumen.configure(
                text=f"{len(matriculas)} matrícula(s) • {total_cuotas} mensualidad(es) • ⚙=generada • ⬇=importada")
        except Exception:
            pass

    def _card_cuota(self, parent, cuota):
        from utils.ui_helpers import crear_card_interactiva, crear_boton_interactivo
        card = crear_card_interactiva(parent)
        card.pack(fill="x", padx=6, pady=4)

        color = {"PENDIENTE": "#6B7280", "PARCIAL": "#D97706",
                 "PAGADO": "#22C55E", "VENCIDO": "#DC2626"}.get(cuota.get("estado"), "gray")
        origen = str(cuota.get("origen", "") or "")
        badge = {"GENERADA": " ⚙", "IMPORTADA": " ⬇"}.get(origen, "")
        activa = int(cuota.get("activo", 1) or 0) == 1
        anulada_txt = "" if activa else " • ANULADA"

        try:
            mora = float(cuota.get("monto_mora", 0) or 0)
        except (TypeError, ValueError):
            mora = 0.0
        try:
            total = float(cuota.get("monto_total", 0) or 0)
            pagado = float(cuota.get("monto_pagado", 0) or 0)
            saldo = float(cuota.get("saldo", 0) or 0)
        except (TypeError, ValueError):
            total = pagado = saldo = 0.0

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 0))

        ctk.CTkLabel(
            top, text=f"{cuota.get('periodo', '')}{badge}{anulada_txt}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F0A33",
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=cuota.get("estado", ""), text_color=color,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right", padx=10)
        crear_boton_interactivo(
            top, text="Editar", width=80,
            command=lambda _c=dict(cuota): self._dialog_editar_cuota(_c),
            fg_color="#7C3AED").pack(side="right", padx=2)

        sub = ctk.CTkFrame(top, fg_color="transparent")
        sub.pack(side="left", padx=12)
        ctk.CTkLabel(
            sub,
            text=f"Total S/{total:.2f} • Pagado S/{pagado:.2f} • Saldo S/{saldo:.2f}"
                 + (f" • Mora S/{mora:.2f}" if mora > 0 else "")
                 + f" • Vence {cuota.get('fecha_vencimiento', '')}",
            font=ctk.CTkFont(size=12), text_color="#6B5B7B",
        ).pack(anchor="w")

        # Detalle de pagos aplicados (recibo/fecha/método/monto)
        from utils.ui_helpers import agregar_detalle_expandible
        toggle_btn, _, _ = agregar_detalle_expandible(
            card, lambda frame, _c=cuota: self._poblar_detalle_cuota(frame, _c))
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    @staticmethod
    def _poblar_detalle_cuota(frame, cuota):
        from utils.ui_helpers import linea_detalle
        try:
            mora = float(cuota.get("monto_mora", 0) or 0)
        except (TypeError, ValueError):
            mora = 0.0
        linea_detalle(frame, "Periodo", cuota.get("periodo", ""))
        linea_detalle(frame, "Vencimiento", cuota.get("fecha_vencimiento", ""))
        linea_detalle(frame, "Estado", cuota.get("estado", ""))
        linea_detalle(frame, "Origen",
                      {"GENERADA": "Generada automática (RN-014)",
                       "IMPORTADA": "Importada (Excel/CSV)",
                       "MANUAL": "Manual"}.get(str(cuota.get("origen", "") or ""), "—"))
        linea_detalle(frame, "Total", f"S/{float(cuota.get('monto_total', 0) or 0):.2f}")
        linea_detalle(frame, "Pagado", f"S/{float(cuota.get('monto_pagado', 0) or 0):.2f}")
        linea_detalle(frame, "Saldo", f"S/{float(cuota.get('saldo', 0) or 0):.2f}")
        if mora > 0:
            linea_detalle(frame, "Mora", f"S/{mora:.2f}")
        linea_detalle(frame, "Activa", "Sí" if int(cuota.get("activo", 1) or 0) == 1 else "No (anulada)")
        try:
            pagos = matricula_controller.obtener_pagos_por_cuota(cuota["id_cuota"])
        except Exception:
            pagos = []
        if not pagos:
            linea_detalle(frame, "Pagos", "Sin pagos aplicados")
            return
        for p in pagos:
            linea_detalle(
                frame, f"{p.get('numero_recibo', '—')} • {p.get('fecha_pago', '')}",
                f"S/{float(p.get('monto_pagado', 0) or 0):.2f} • {p.get('metodo_pago', '')}")

    def _dialog_editar_cuota(self, cuota):
        from tkinter import messagebox
        top = ctk.CTkToplevel(self)
        top.title(f"Editar mensualidad {cuota.get('periodo', '')}")
        top.geometry("420x420")
        try:
            top.transient(self)
        except Exception:
            pass
        cuerpo = ctk.CTkFrame(top, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(cuerpo, text="Editar mensualidad (corrección de datos)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#3D1559").pack(anchor="w", pady=(0, 8))

        def _fila(etiqueta, valor):
            f = ctk.CTkFrame(cuerpo, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=etiqueta, width=140, anchor="w").pack(side="left")
            e = ctk.CTkEntry(f, width=200)
            e.insert(0, str(valor))
            e.pack(side="left", padx=5)
            return e

        e_total = _fila("Monto total S/", cuota.get("monto_total", 0))
        e_venc = _fila("Vencimiento (AAAA-MM-DD)", cuota.get("fecha_vencimiento", ""))
        e_periodo = _fila("Periodo (AAAA-MM)", cuota.get("periodo", ""))
        f_est = ctk.CTkFrame(cuerpo, fg_color="transparent")
        f_est.pack(fill="x", pady=2)
        ctk.CTkLabel(f_est, text="Estado", width=140, anchor="w").pack(side="left")
        cb_estado = ctk.CTkComboBox(
            f_est, width=200,
            values=["PENDIENTE", "PARCIAL", "PAGADO", "VENCIDO"])
        try:
            cb_estado.set(cuota.get("estado", "PENDIENTE"))
        except Exception:
            pass
        cb_estado.pack(side="left", padx=5)
        var_activa = ctk.BooleanVar(value=int(cuota.get("activo", 1) or 0) == 1)
        ctk.CTkCheckBox(cuerpo, text="Activa (desmarcar = anular)",
                        variable=var_activa).pack(anchor="w", pady=6)
        lbl = ctk.CTkLabel(cuerpo, text="", font=ctk.CTkFont(size=12))
        lbl.pack(anchor="w", pady=4)
        ctk.CTkLabel(
            cuerpo,
            text=f"Pagado hasta ahora: S/{float(cuota.get('monto_pagado', 0) or 0):.2f} "
                 "(el total no puede ser menor)",
            font=ctk.CTkFont(size=11), text_color="#6B5B7B",
            wraplength=380, justify="left").pack(anchor="w")

        def guardar():
            data = {
                "monto_total": e_total.get().strip(),
                "fecha_vencimiento": e_venc.get().strip(),
                "periodo": e_periodo.get().strip(),
                "estado": cb_estado.get(),
                "activo": 1 if var_activa.get() else 0,
            }
            exito, msg = matricula_controller.editar_cuota(cuota["id_cuota"], data)
            if exito:
                messagebox.showinfo("Mensualidad", msg)
                top.destroy()
                try:
                    sel = self.combo_matricula_cuotas.get()
                    if sel and sel != "Seleccionar alumno...":
                        self._cargar_cuotas(sel)
                except Exception:
                    pass
            else:
                lbl.configure(text=f"❌ {msg}", text_color="red")

        btnf = ctk.CTkFrame(cuerpo, fg_color="transparent")
        btnf.pack(pady=10)
        ctk.CTkButton(btnf, text="Cancelar", fg_color="gray",
                      command=top.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Guardar", command=guardar).pack(side="left", padx=5)

    def _crear_tab_grilla(self):
        # Grilla general estilo Excel RELACIÓN DE ALUMNOS
        # (X=CANCELADO, S/=ADELANTO, vacío=pendiente/sin cuota).
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo
        from utils.dates import get_today
        sec = crear_seccion(
            self.tab_grilla, titulo="Mensualidades del Año", icono="🗓",
            descripcion="X = cancelado • S/ monto = adelanto (saldo) • "
                        "! gris = pendiente • ! rojo = vencido • clic en celda = detalle.",
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

    def _cargar_grilla(self):
        from services import cuota_service
        for w in self.scroll_grilla.winfo_children():
            w.destroy()
        try:
            from controllers import estudiante_controller
            becados = {b.get("dni", "") for b in estudiante_controller.listar_becados()}
        except Exception:
            becados = set()
        try:
            anio = int(self.combo_grilla_anio.get())
        except (ValueError, TypeError):
            anio = 2026
        from utils.constants import GRILLA_MAX_ESTUDIANTES
        filas = cuota_service.grilla_anual(anio)
        recorte = ""
        if len(filas) > GRILLA_MAX_ESTUDIANTES:
            filas = filas[:GRILLA_MAX_ESTUDIANTES]
            recorte = f" (mostrando {GRILLA_MAX_ESTUDIANTES}, refine el año)"
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
            ctk.CTkLabel(self.scroll_grilla, text=f"Sin mensualidades en {anio}",
                         text_color="gray").pack(pady=20)
            self.label_grilla_status.configure(text="Total: 0")
            return
        colores = {"PAGADO": ("X", "green", True), "PARCIAL": (None, "#D97706", True),
                   "VENCIDO": ("!", "#DC2626", True), "PENDIENTE": ("!", "#9CA3AF", False)}
        for f in filas:
            row = ctk.CTkFrame(self.scroll_grilla, fg_color="white", corner_radius=6)
            row.pack(fill="x", padx=6, pady=1)
            nombre_grilla = (f"🎓 {f['nombre']}" if f.get("dni", "") in becados
                             else f["nombre"])
            ctk.CTkLabel(row, text=nombre_grilla, width=220,
                         font=ctk.CTkFont(size=11), text_color="#1F0A33").grid(
                row=0, column=0, padx=2, pady=4, sticky="w")
            for j in range(1, 13):
                celda = f["meses"].get(j)
                if celda is None:
                    txt, color, negrita = "", "#9CA3AF", False
                elif celda["estado"] == "PARCIAL":
                    txt, color, negrita = f"S/{celda['saldo']:.0f}", "#D97706", True
                    origen = celda.get("origen", "")
                    if origen == "GENERADA":
                        txt = f"⚙{txt}" if txt else "⚙"
                    elif origen == "IMPORTADA":
                        txt = f"⬇{txt}" if txt else "⬇"
                else:
                    txt, color, negrita = colores.get(celda["estado"], ("", "#9CA3AF", False))
                    origen = celda.get("origen", "")
                    if origen == "GENERADA":
                        txt = f"⚙{txt}" if txt else "⚙"
                    elif origen == "IMPORTADA":
                        txt = f"⬇{txt}" if txt else "⬇"
                lbl = ctk.CTkLabel(row, text=txt, width=55,
                                   font=ctk.CTkFont(size=11, weight="bold" if negrita else "normal"),
                                   text_color=color)
                lbl.grid(row=0, column=j, padx=2, pady=4)
                if celda is not None and celda.get("id_cuota"):
                    try:
                        lbl.configure(cursor="hand2")
                    except Exception:
                        pass
                    lbl.bind("<Button-1>",
                             lambda _e, _c=dict(celda), _n=f["nombre"]:
                             self._dialog_detalle_grilla(_c, _n),
                             add="+")
        self.label_grilla_status.configure(
            text=f"Total: {len(filas)} estudiante(s){recorte} • X=cancelado • S/=adelanto • !=pendiente/vencido • ⚙=generada ⬇=importada")

    def _dialog_detalle_grilla(self, celda, nombre):
        top = ctk.CTkToplevel(self)
        top.title(f"Mensualidad {celda.get('periodo', '')} - {nombre}")
        top.geometry("420x360")
        try:
            top.transient(self)
        except Exception:
            pass
        cuerpo = ctk.CTkFrame(top, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(cuerpo, text=f"{nombre} • {celda.get('periodo', '')}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#3D1559").pack(anchor="w", pady=(0, 8))
        for et, val in (
                ("Estado", celda.get("estado", "")),
                ("Total", f"S/{float(celda.get('monto_total', 0) or 0):.2f}"),
                ("Pagado", f"S/{float(celda.get('monto_pagado', 0) or 0):.2f}"),
                ("Saldo", f"S/{float(celda.get('saldo', 0) or 0):.2f}"),
                ("Vence", celda.get("fecha_vencimiento", "") or "—")):
            fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
            fila.pack(fill="x", pady=1)
            ctk.CTkLabel(fila, text=f"{et}:", width=90, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#3D1559").pack(side="left")
            ctk.CTkLabel(fila, text=str(val), anchor="w",
                         font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(cuerpo, text="Pagos aplicados:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#3D1559").pack(anchor="w", pady=(10, 4))
        try:
            pagos = matricula_controller.obtener_pagos_por_cuota(celda["id_cuota"])
        except Exception:
            pagos = []
        if not pagos:
            ctk.CTkLabel(cuerpo, text="Sin pagos aplicados",
                         text_color="gray").pack(anchor="w")
        for p in pagos:
            ctk.CTkLabel(
                cuerpo,
                text=(f"• {p.get('numero_recibo', '—')} • {p.get('fecha_pago', '')} • "
                      f"S/{float(p.get('monto_pagado', 0) or 0):.2f} • {p.get('metodo_pago', '')}"),
                font=ctk.CTkFont(size=11), anchor="w",
                justify="left").pack(anchor="w")
