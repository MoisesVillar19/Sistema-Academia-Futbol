import customtkinter as ctk
from controllers import dashboard_controller
from utils.ui_helpers import crear_tabla_cards, crear_bloque_grafico_tabla

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


def _num(v, default=0.0):
    """Número seguro para formateo: None/texto inválido → default (BD real trae NULLs)."""
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        self._cargar_indicadores()

    def _crear_widgets(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 5))

        self.titulo_label = ctk.CTkLabel(
            self.header, text="📊  Dashboard  •  Resumen operativo",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#3D1559",
        )
        self.titulo_label.pack(side="left")
        ctk.CTkLabel(self.header, text="  Clic en una tarjeta para detalle  •  Datos en tiempo real", font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack(side="left", padx=12)

        self.btn_volver = ctk.CTkButton(
            self.header, text="Volver", width=100,
            command=self._mostrar_cards, fg_color="gray",
        )

        self.btn_actualizar = ctk.CTkButton(
            self.header, text="Actualizar", width=100,
            command=self._cargar_indicadores,
        )
        self.btn_actualizar.pack(side="right")

        # NOTA geometría: antes cards_frame (fijo, ~800px por 6 filas) y
        # detalle_frame (scrollable con expand) competían por la altura de la
        # ventana. Como lo pedido (>1000px) excedía la ventana (~750px), el
        # packer dejaba al detalle con 1x1 px: existía pero invisible.
        # Ahora TODO va en un único scroll; el detalle es un frame plano
        # (sin canvas anidado que pueda colapsar) y siempre se ve completo.
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=5)

        self.cards_frame = None
        self.detalle_frame = None
        self._reset_contenedores()

    def _reset_contenedores(self):
        # Quirk CTk 6.0: vaciar hijos NO encoge el frame (conserva altura
        # vieja y empuja el resto fuera de pantalla). Se recrean los
        # contenedores para geometría siempre correcta.
        for attr in ("cards_frame", "detalle_frame"):
            try:
                viejo = getattr(self, attr, None)
                if viejo is not None and viejo.winfo_exists():
                    viejo.destroy()
            except Exception:
                pass
        # height=1: CTk 6 deja los frames vacíos en 200px; con 1 el
        # contenedor vacío es invisible y crece normal con contenido.
        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=1)
        self.cards_frame.pack(fill="x", pady=5)
        self.detalle_frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=1)
        self.detalle_frame.pack(fill="x", pady=5)

    def _cargar_indicadores(self):
        from utils.ui_helpers import mostrar_cargando as _mc
        _detener = _mc(self, "Cargando dashboard")
        try:
            self._cargar_indicadores_impl()
        finally:
            try:
                _detener()
            except Exception:
                pass

    def _cargar_indicadores_impl(self):
        self._reset_contenedores()

        data = dashboard_controller.obtener_indicadores()

        self.btn_volver.pack_forget()
        self.btn_actualizar.pack(side="right")
        self.titulo_label.configure(text="Dashboard")

        # Fase 1: Pendientes primero (avisos por módulo, sin toast)
        try:
            from services import avisos_service
            from utils.ui_helpers import crear_banner_avisos
            avisos = avisos_service.obtener_avisos()
        except Exception:
            avisos = []
        if avisos:
            sec = ctk.CTkFrame(self.cards_frame, fg_color="white", corner_radius=8)
            sec.pack(fill="x", pady=5)
            ctk.CTkLabel(sec, text="🔔  Pendientes", font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#3D1559").pack(anchor="w", padx=10, pady=(8, 2))
            _mapa_detalle = {"comprobantes": "comprobantes", "vencidas": "vencidas",
                             "por_vencer": "por_vencer", "stock_bajo": "stock",
                             "sin_apoderado": "sin_apoderado"}
            for av in avisos:
                crear_banner_avisos(
                    sec, av["texto"], None, av["severidad"],
                    command=lambda t=_mapa_detalle.get(av["codigo"], "vencidas"): self._mostrar_detalle(t))

        try:
            din = dashboard_controller.resumen_dinero()
        except Exception:
            din = None
        if din:
            row0 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
            row0.pack(fill="x", pady=5)
            self._crear_card_dinero(row0, "Compras (mes)", din["compras_yape"], din["compras_efectivo"],
                                    "#F59E0B", lambda: self._mostrar_detalle("dinero_compras"))
            self._crear_card_dinero(row0, "Ventas (mes)", din["ventas_yape"], din["ventas_efectivo"],
                                    "#22C55E", lambda: self._mostrar_detalle("dinero_ventas"))
            self._crear_card_dinero(row0, "Ganancias (mes)", din["ganancia_yape"], din["ganancia_efectivo"],
                                    "#7C3AED", lambda: self._mostrar_detalle("dinero_ganancias"))
            self._crear_card_dinero(row0, "Ganancia Total (mes)", din["ganancia_total"], None,
                                    "#1F0A33", lambda: self._mostrar_detalle("dinero_ganancias"))

        row1 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        self._crear_card(row1, "Alumnos Activos", str(data["alumnos_activos"]), "#7C3AED",
                         lambda: self._mostrar_detalle("alumnos"))
        self._crear_card(row1, "Cuotas Vencidas", str(data["cuotas_vencidas"]), "#DC2626",
                         lambda: self._mostrar_detalle("vencidas"))
        self._crear_card(row1, "Por Vencer", str(data["cuotas_por_vencer"]), "#F59E0B",
                         lambda: self._mostrar_detalle("por_vencer"))

        row2 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        self._crear_card(row2, "Pagos Hoy", str(data.get("pagos_hoy", 0) or 0), "#22C55E",
                         lambda: self._mostrar_detalle("pagos_hoy"))
        self._crear_card(row2, "Ingresos Hoy", f"S/{_num(data.get('ingresos_hoy')):.2f}", "#22C55E",
                         lambda: self._mostrar_detalle("ingresos_hoy"))
        self._crear_card(row2, "Ingresos Mes", f"S/{_num(data.get('ingresos_mes')):.2f}", "#6B21A8",
                         lambda: self._mostrar_detalle("ingresos_mes"))

        row3 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        self._crear_card(row3, "Monto Vencido", f"S/{_num(data.get('monto_vencido')):.2f}", "#DC2626",
                         lambda: self._mostrar_detalle("monto_vencido"))
        self._crear_card(row3, "Monto por Vencer", f"S/{_num(data.get('monto_por_vencer')):.2f}", "#F59E0B",
                         lambda: self._mostrar_detalle("monto_por_vencer"))
        self._crear_card(row3, "Stock Bajo", str(data["stock_bajo"]), "#F59E0B",
                         lambda: self._mostrar_detalle("stock"))

        # Helper para mostrar — si es None (error) muestra —
        def _fmt(v, suf=""):
            if v is None:
                return "—"
            try:
                return f"S/{v:.2f}{suf}" if isinstance(v, (int, float)) else str(v)
            except Exception:
                return str(v)

        # 3 cards por fila: con 4 la última se corta (overflow horizontal)
        row4 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)

        self._crear_card(row4, "Ventas Mes", _fmt(data.get('ingresos_ventas_mes')), "#7C3AED",
                         lambda: self._mostrar_detalle("ventas_mes"))
        self._crear_card(row4, "Egresos Mes", _fmt(data.get('egresos_mes')), "#DC2626",
                         lambda: self._mostrar_detalle("egresos_mes"))
        neto = data.get('neto_mes')
        self._crear_card(row4, "Neto Mes", _fmt(neto), "#22C55E" if (neto or 0) >=0 else "#DC2626",
                         lambda: self._mostrar_detalle("neto_mes"))

        row5 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row5.pack(fill="x", pady=5)

        # MoM si existe (en fila propia para no cortar)
        mom = data.get('mom_ingresos')
        if mom is not None:
            mom_txt = f"{mom:+.1f}% vs mes anterior"
            mom_color = "#22C55E" if mom >=0 else "#DC2626"
            self._crear_card(row5, "MoM Ingresos", mom_txt, mom_color, lambda: self._mostrar_detalle("mom"))
        self._crear_card(row5, "Nuevos Mes", str(data.get("nuevos_mes",0)), "#22C55E",
                         lambda: self._mostrar_detalle("nuevos_mes"))
        self._crear_card(row5, "Antiguos Mes", str(data.get("antiguos_mes",0)), "#6B21A8",
                         lambda: self._mostrar_detalle("antiguos_mes"))

        row6 = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
        row6.pack(fill="x", pady=5)

        self._crear_card(row6, "Total Matrículas Mes", str(data.get("matriculas_mes",0)), "#3D1559",
                         lambda: self._mostrar_detalle("matriculas_mes"))

        for widget in self.detalle_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.detalle_frame,
            text="Haga clic en cualquier card para ver el detalle",
            font=ctk.CTkFont(size=14), text_color="gray",
        ).pack(expand=True)

    def _crear_card(self, parent, titulo, valor, color, comando):
        # Card clickeable estilo Configuración (frame blanco, sin hover que
        # repinte). NOTA: antes era CTkButton, pero en CustomTkinter 6 el
        # botón es un compuesto (frame+canvas+label internos) que se traga
        # los clics: solo el borde respondía. Con frame + clic propagado a
        # TODO el interior, cualquier punto abre el detalle (sin doble
        # disparo: los frames/labels no tienen comando nativo).
        card = ctk.CTkFrame(
            parent, fg_color="white",
            border_width=1, border_color="#E5E7EB",
            corner_radius=12,
        )
        card.pack(side="left", padx=6, pady=6, fill="x", expand=True)

        frame_interno = ctk.CTkFrame(card, fg_color="transparent")
        frame_interno.pack(expand=True, fill="both", padx=8, pady=8)

        ctk.CTkLabel(frame_interno, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B").pack(pady=(6, 2))
        ctk.CTkLabel(frame_interno, text=valor, font=ctk.CTkFont(size=26, weight="bold"), text_color=color).pack(pady=(2, 6))
        # sutil línea color
        ctk.CTkFrame(frame_interno, fg_color=color, height=3, corner_radius=2).pack(fill="x", padx=20, pady=(0,4))

        try:
            def _hacer_clickeable(w):
                try:
                    w.bind("<Button-1>", lambda e: comando(), add="+")
                except Exception:
                    pass
                try:
                    w.configure(cursor="hand2")
                except Exception:
                    pass
                try:
                    hijos = w.winfo_children()
                except Exception:
                    return
                for ch in hijos:
                    _hacer_clickeable(ch)
            _hacer_clickeable(card)
        except Exception:
            pass

    def _crear_card_dinero(self, parent, titulo, valor_yape, valor_efectivo, color, comando):
        # Card doble línea Yape/Efectivo con clic en todo el interior
        card = ctk.CTkFrame(
            parent, fg_color="white",
            border_width=1, border_color="#E5E7EB",
            corner_radius=12,
        )
        card.pack(side="left", padx=6, pady=6, fill="x", expand=True)

        frame_interno = ctk.CTkFrame(card, fg_color="transparent")
        frame_interno.pack(expand=True, fill="both", padx=8, pady=8)

        ctk.CTkLabel(frame_interno, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B").pack(pady=(6, 2))
        if valor_efectivo is None:
            ctk.CTkLabel(frame_interno, text=f"S/{valor_yape:.2f}", font=ctk.CTkFont(size=24, weight="bold"), text_color=color).pack(pady=(2, 2))
        else:
            ctk.CTkLabel(frame_interno, text=f"Yape S/{valor_yape:.2f}", font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(pady=(0, 0))
            ctk.CTkLabel(frame_interno, text=f"Efectivo S/{valor_efectivo:.2f}", font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(pady=(0, 2))
        ctk.CTkFrame(frame_interno, fg_color=color, height=3, corner_radius=2).pack(fill="x", padx=20, pady=(0, 4))

        try:
            def _hacer_clickeable(w):
                try:
                    w.bind("<Button-1>", lambda e: comando(), add="+")
                except Exception:
                    pass
                try:
                    w.configure(cursor="hand2")
                except Exception:
                    pass
                try:
                    hijos = w.winfo_children()
                except Exception:
                    return
                for ch in hijos:
                    _hacer_clickeable(ch)
            _hacer_clickeable(card)
        except Exception:
            pass

    def _mostrar_detalle(self, tipo):
        from utils.ui_helpers import mostrar_cargando as _mc
        _detener = _mc(self, "Cargando detalle")
        try:
            self._mostrar_detalle_impl(tipo)
        finally:
            try:
                _detener()
            except Exception:
                pass

    def _mostrar_detalle_impl(self, tipo):
        self._reset_contenedores()

        self.btn_actualizar.pack_forget()
        self.btn_volver.pack(side="right")

        titulos = {
            "alumnos": "Alumnos Activos",
            "vencidas": "Cuotas Vencidas",
            "por_vencer": "Cuotas por Vencer",
            "pagos_hoy": "Pagos de Hoy",
            "ingresos_hoy": "Ingresos de Hoy",
            "ingresos_mes": "Ingresos del Mes",
            "monto_vencido": "Monto Vencido",
            "monto_por_vencer": "Monto por Vencer",
            "stock": "Productos con Stock Bajo",
            "ventas_mes": "Ventas del Mes (Uniformes/Tienda)",
            "egresos_mes": "Egresos del Mes",
            "neto_mes": "Neto del Mes (Ingresos - Egresos)",
            "nuevos_mes": "Alumnos Nuevos del Mes",
            "antiguos_mes": "Alumnos Antiguos (Matrículas)",
            "matriculas_mes": "Matrículas del Mes",
            "mom": "Comparativa Mensual (vs mes anterior)",
            "dinero_compras": "Compras del Mes (Yape/Efectivo)",
            "dinero_ventas": "Ventas del Mes (Yape/Efectivo)",
            "dinero_ganancias": "Ganancias del Mes (Yape/Efectivo)",
            "comprobantes": "Pagos con Comprobante Pendiente",
            "sin_apoderado": "Matrículas sin Apoderado Principal",
        }
        self.titulo_label.configure(text=titulos.get(tipo, "Detalle"))

        try:
            from utils.logger import logger as _diag_log
            _diag_log.info(f"Dashboard detalle solicitado: {tipo}")
        except Exception:
            pass
        try:
            if tipo == "alumnos":
                self._detalle_alumnos()
            elif tipo == "vencidas":
                self._detalle_cuotas(dashboard_controller.listar_cuotas_vencidas(), "vencida")
            elif tipo == "por_vencer":
                self._detalle_cuotas(dashboard_controller.listar_cuotas_por_vencer(), "por vencer")
            elif tipo == "pagos_hoy":
                self._detalle_pagos(dashboard_controller.listar_pagos_hoy())
            elif tipo == "ingresos_hoy":
                self._detalle_ingresos_hoy()
            elif tipo == "ingresos_mes":
                self._detalle_ingresos_mes()
            elif tipo == "monto_vencido":
                self._detalle_monto(dashboard_controller.listar_monto_vencido(), "vencido")
            elif tipo == "monto_por_vencer":
                self._detalle_monto(dashboard_controller.listar_monto_por_vencer(), "por vencer")
            elif tipo == "stock":
                self._detalle_stock()
            elif tipo == "ventas_mes":
                self._detalle_ventas_mes()
            elif tipo == "egresos_mes":
                self._detalle_egresos_mes()
            elif tipo == "neto_mes":
                self._detalle_neto_mes()
            elif tipo == "nuevos_mes":
                self._detalle_nuevos_mes()
            elif tipo == "antiguos_mes":
                self._detalle_antiguos_mes()
            elif tipo == "matriculas_mes":
                self._detalle_matriculas_mes()
            elif tipo == "mom":
                self._detalle_mom()
            elif tipo == "dinero_compras":
                self._detalle_dinero_compras()
            elif tipo == "dinero_ventas":
                self._detalle_dinero_ventas()
            elif tipo == "dinero_ganancias":
                self._detalle_dinero_ganancias()
            elif tipo == "comprobantes":
                self._detalle_comprobantes()
            elif tipo == "sin_apoderado":
                self._detalle_sin_apoderado()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Dashboard detalle '{tipo}' fallo: {e}", exc_info=True)
            ctk.CTkLabel(
                self.detalle_frame,
                text=f"⚠ No se pudo cargar el detalle: {e}",
                font=ctk.CTkFont(size=13), text_color="red",
                wraplength=600, justify="left",
            ).pack(pady=20)
        try:
            self.detalle_frame.update_idletasks()
        except Exception:
            pass
        try:
            from utils.logger import logger as _diag_log2
            n = len(self.detalle_frame.winfo_children())
            _diag_log2.info(f"Dashboard detalle '{tipo}' renderizado: {n} widgets "
                            f"(mpl={'SI' if MATPLOTLIB_DISPONIBLE else 'NO'})")
        except Exception:
            pass

    def _mostrar_cards(self):
        self._cargar_indicadores()

    def _detalle_alumnos(self):
        alumnos = dashboard_controller.listar_alumnos_activos()

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(alumnos)} alumnos activos",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not alumnos:
            ctk.CTkLabel(self.detalle_frame, text="No hay alumnos activos").pack(pady=10)
            return

        crear_tabla_cards(
            self.detalle_frame,
            [("DNI", 80), ("Nombre", 200), ("Edad", 60), ("Teléfono", 100)],
            [[str(a.get("dni", "")),
              f"{a.get('nombres', '')} {a.get('apellidos', '')}",
              str(a.get("edad", "") or "—"),
              str(a.get("telefono", "") or "—")] for a in alumnos],
            cap=50,
            nota_mas=f"Mostrando 50 de {len(alumnos)} alumnos",
        )

    def _detalle_cuotas(self, cuotas, tipo):
        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(cuotas)} cuotas {tipo}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not cuotas:
            ctk.CTkLabel(self.detalle_frame, text=f"No hay cuotas {tipo}").pack(pady=10)
            return

        crear_tabla_cards(
            self.detalle_frame,
            [("Estudiante", 200), ("DNI", 80), ("Período", 80), ("Saldo", 80), ("Vencimiento", 100)],
            [[f"{c.get('nombres', '')} {c.get('apellidos', '')}",
              str(c.get("dni", "")),
              str(c.get("periodo", "")),
              (f"S/{_num(c.get('saldo')):.2f}", {"text_color": "red", "weight": "bold"}),
              str(c.get("fecha_vencimiento", ""))] for c in cuotas],
            cap=30,
            nota_mas=f"Mostrando 30 de {len(cuotas)} cuotas",
        )

    def _detalle_pagos(self, pagos):
        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(pagos)} pagos realizados hoy",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not pagos:
            ctk.CTkLabel(self.detalle_frame, text="No hay pagos registrados hoy").pack(pady=10)
            return

        crear_tabla_cards(
            self.detalle_frame,
            [("N° Recibo", 120), ("Monto", 80), ("Método", 100), ("Fecha", 100)],
            [[str(p.get("numero_recibo", "")),
              (f"S/{_num(p.get('monto_total')):.2f}", {"text_color": "green", "weight": "bold"}),
              str(p.get("metodo_pago", "")),
              str(p.get("fecha_pago", ""))] for p in pagos],
            cap=30,
            nota_mas=f"Mostrando 30 de {len(pagos)} pagos",
        )

    def _detalle_comprobantes(self):
        from services import avisos_service
        pagos = avisos_service.listar_pagos_sin_comprobante()
        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(pagos)} pago(s) no-efectivo sin comprobante archivado",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))
        if not pagos:
            ctk.CTkLabel(self.detalle_frame, text="Sin pendientes 🎉").pack(pady=10)
            return
        crear_tabla_cards(
            self.detalle_frame,
            [("N° Recibo", 120), ("Estudiante", 200), ("Monto", 80), ("Método", 100), ("Fecha", 100)],
            [[str(p.get("numero_recibo", "")),
              f"{p.get('nombres', '')} {p.get('apellidos', '')}".strip() or "—",
              (f"S/{_num(p.get('monto_total')):.2f}", {"text_color": "green", "weight": "bold"}),
              str(p.get("metodo_pago", "")),
              str(p.get("fecha_pago", ""))] for p in pagos],
            cap=30,
            nota_mas=f"Mostrando 30 de {len(pagos)} pagos",
        )

    def _detalle_sin_apoderado(self):
        from services import avisos_service
        mats = avisos_service.listar_matriculas_sin_apoderado()
        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(mats)} matrícula(s) activa(s) sin apoderado principal",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))
        if not mats:
            ctk.CTkLabel(self.detalle_frame, text="Sin pendientes 🎉").pack(pady=10)
            return
        crear_tabla_cards(
            self.detalle_frame,
            [("Estudiante", 220), ("DNI", 100), ("Tarifa", 160), ("Inicio", 100)],
            [[f"{m.get('nombres', '')} {m.get('apellidos', '')}".strip(),
              str(m.get("dni", "")),
              str(m.get("tarifa_nombre", "")),
              str(m.get("fecha_inicio", ""))] for m in mats],
            cap=30,
            nota_mas=f"Mostrando 30 de {len(mats)} matrículas",
        )

    def _detalle_ingresos_hoy(self):
        pagos = dashboard_controller.listar_pagos_hoy()
        total = sum(_num(p.get("monto_total")) for p in pagos)

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: S/{total:.2f} en {len(pagos)} transacciones",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not pagos:
            ctk.CTkLabel(self.detalle_frame, text="No hay ingresos hoy").pack(pady=10)
            return

        hay_grafico = bool(MATPLOTLIB_DISPONIBLE and pagos)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            self._crear_grafico_barras_simple(
                [f"Pago {i+1}" for i in range(len(pagos))],
                [_num(p.get("monto_total")) for p in pagos],
                "Ingresos por Transacción",
                contenedor=frame_g,
            )
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        crear_tabla_cards(
            padre_tabla,
            [("N° Recibo", 120), ("Monto", 100), ("Método", 120)],
            [[str(p.get("numero_recibo", "")),
              (f"S/{_num(p.get('monto_total')):.2f}", {"text_color": "green", "weight": "bold"}),
              str(p.get("metodo_pago", ""))] for p in pagos],
            cap=30,
            nota_mas=f"Mostrando 30 de {len(pagos)} pagos",
        )

    def _detalle_ingresos_mes(self):
        datos = dashboard_controller.obtener_ingresos_por_dia_mes()
        total = sum(_num(d.get("monto")) for d in datos)

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: S/{total:.2f} en {len(datos)} días con actividad",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not datos:
            ctk.CTkLabel(self.detalle_frame, text="No hay ingresos este mes").pack(pady=10)
            return

        hay_grafico = bool(MATPLOTLIB_DISPONIBLE and datos)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            self._crear_grafico_barras_simple(
                [d.get("dia", "")[-5:] for d in datos],
                [_num(d.get("monto")) for d in datos],
                "Ingresos por Día del Mes",
                contenedor=frame_g,
            )
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        crear_tabla_cards(
            padre_tabla,
            [("Fecha", 120), ("Monto", 100)],
            [[str(d.get("dia", "")),
              (f"S/{_num(d.get('monto')):.2f}", {"text_color": "green", "weight": "bold"})] for d in datos],
            cap=31,
        )

    def _detalle_monto(self, cuotas, tipo):
        total = sum(_num(c.get("saldo")) for c in cuotas)

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: S/{total:.2f} en {len(cuotas)} cuotas {tipo}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not cuotas:
            ctk.CTkLabel(self.detalle_frame, text=f"No hay cuotas {tipo}").pack(pady=10)
            return

        hay_grafico = bool(MATPLOTLIB_DISPONIBLE and cuotas)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            nombres = [f"{c.get('nombres', '')[:10]} {c.get('apellidos', '')[:10]}" for c in cuotas[:10]]
            saldos = [_num(c.get("saldo")) for c in cuotas[:10]]
            self._crear_grafico_barras_simple(nombres, saldos, f"Saldo {tipo} por Estudiante", contenedor=frame_g)
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        crear_tabla_cards(
            padre_tabla,
            [("Estudiante", 200), ("DNI", 80), ("Saldo", 100)],
            [[f"{c.get('nombres', '')} {c.get('apellidos', '')}",
              str(c.get("dni", "")),
              (f"S/{_num(c.get('saldo')):.2f}", {"text_color": "red", "weight": "bold"})] for c in cuotas],
            cap=20,
            nota_mas=f"Mostrando 20 de {len(cuotas)} cuotas",
        )

    @staticmethod
    def _agrupar_por_dia(filas, campo_fecha, campo_monto):
        agg: dict = {}
        for f in filas:
            dia = str(f.get(campo_fecha, "") or "")[:10]
            if dia:
                agg[dia] = agg.get(dia, 0) + _num(f.get(campo_monto))
        dias = sorted(agg)
        return [d[-5:] for d in dias], [round(agg[d], 2) for d in dias]

    @staticmethod
    def _agrupar_por_campo(filas, campo, campo_monto):
        agg: dict = {}
        for f in filas:
            clave = str(f.get(campo, "") or "—")
            agg[clave] = agg.get(clave, 0) + _num(f.get(campo_monto))
        claves = sorted(agg)
        return claves, [round(agg[c], 2) for c in claves]

    def _detalle_ventas_mes(self):
        from datetime import date
        hoy = date.today()
        ini = hoy.replace(day=1).isoformat()
        try:
            from controllers import venta_controller
            ventas = venta_controller.listar_ventas(ini, hoy.isoformat())
            total = sum(_num(v.get("monto_total")) for v in ventas)
            ctk.CTkLabel(self.detalle_frame, text=f"Ventas mes: S/{total:.2f} en {len(ventas)} ventas", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10,5))
            if not ventas:
                ctk.CTkLabel(self.detalle_frame, text="No hay ventas este mes").pack(pady=10)
                return
            hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
            if hay_grafico:
                frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
                dias, montos = self._agrupar_por_dia(ventas, "fecha_venta", "monto_total")
                self._crear_grafico_barras_simple(dias, montos, "Ventas por Día del Mes", contenedor=frame_g)
                tipos, montos_t = self._agrupar_por_campo(ventas, "tipo_venta", "monto_total")
                self._crear_grafico_barras_simple(tipos, montos_t, "Ventas por Tipo", contenedor=frame_g)
                padre_tabla = frame_t
            else:
                padre_tabla = self.detalle_frame
            crear_tabla_cards(
                padre_tabla,
                [("Recibo", 150), ("Tipo", 100), ("Monto", 90), ("Fecha", 100)],
                [[str(v.get("numero_recibo", "")),
                  str(v.get("tipo_venta", "")),
                  (f"S/{_num(v.get('monto_total')):.2f}", {"text_color": "green", "weight": "bold"}),
                  str(v.get("fecha_venta", ""))] for v in ventas],
                cap=20,
                nota_mas=f"Mostrando 20 de {len(ventas)} ventas",
            )
        except Exception as e:
            ctk.CTkLabel(self.detalle_frame, text=f"Error: {e}").pack()

    def _detalle_egresos_mes(self):
        from datetime import date
        hoy = date.today()
        ini = hoy.replace(day=1).isoformat()
        try:
            from controllers import egreso_controller
            egresos = egreso_controller.listar_egresos(ini, hoy.isoformat())
            total = sum(_num(e.get("monto")) for e in egresos)
            ctk.CTkLabel(self.detalle_frame, text=f"Egresos mes: S/{total:.2f} en {len(egresos)}", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10,5))
            if not egresos:
                ctk.CTkLabel(self.detalle_frame, text="No hay egresos este mes").pack(pady=10)
                return
            hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
            if hay_grafico:
                frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
                dias, montos = self._agrupar_por_dia(egresos, "fecha", "monto")
                self._crear_grafico_barras_simple(dias, montos, "Egresos por Día del Mes", contenedor=frame_g)
                conceptos, montos_c = self._agrupar_por_campo(egresos, "concepto", "monto")
                self._crear_grafico_barras_simple(conceptos, montos_c, "Egresos por Concepto", contenedor=frame_g)
                padre_tabla = frame_t
            else:
                padre_tabla = self.detalle_frame
            crear_tabla_cards(
                padre_tabla,
                [("Concepto", 130), ("Monto", 90), ("Fecha", 100), ("Responsable", 150)],
                [[str(e.get("concepto", "")),
                  (f"S/{_num(e.get('monto')):.2f}", {"text_color": "red", "weight": "bold"}),
                  str(e.get("fecha", "")),
                  str(e.get("responsable", "") or "—")] for e in egresos],
                cap=20,
                nota_mas=f"Mostrando 20 de {len(egresos)} egresos",
            )
        except Exception as e:
            ctk.CTkLabel(self.detalle_frame, text=f"Error: {e}").pack()

    def _detalle_neto_mes(self):
        from datetime import date
        hoy = date.today()
        ini = hoy.replace(day=1).isoformat()
        fin = hoy.isoformat()
        try:
            from controllers import egreso_controller
            rep = egreso_controller.reporte_ingresos_vs_egresos(ini, fin)
            txt = f"Ingresos: S/{_num(rep.get('total_ingresos')):.2f} (pagos {_num(rep.get('ingresos_pagos')):.2f} + ventas {_num(rep.get('ingresos_ventas')):.2f})\nEgresos: S/{_num(rep.get('egresos')):.2f}\nNeto: S/{_num(rep.get('neto')):.2f}"
            ctk.CTkLabel(self.detalle_frame, text=txt, font=ctk.CTkFont(size=14), justify="left").pack(anchor="w", pady=10)
        except Exception as e:
            ctk.CTkLabel(self.detalle_frame, text=f"Error: {e}").pack()

    def _detalle_mom(self):
        comp = dashboard_controller.comparativa_mensual()

        delta = comp.get("delta_pct", 0)
        color = "#22C55E" if delta >= 0 else "#DC2626"
        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Ingresos {comp.get('mes_actual','')} S/{comp.get('total_actual',0):.2f}  vs  "
                 f"{comp.get('mes_anterior','')} S/{comp.get('total_anterior',0):.2f}  →  "
                 f"{delta:+.1f}%",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=color,
            justify="left", wraplength=700,
        ).pack(anchor="w", pady=(10, 5))

        etiquetas = comp.get("etiquetas", [])
        if not etiquetas:
            ctk.CTkLabel(self.detalle_frame, text="Sin datos para comparar").pack(pady=10)
            return

        hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            self._crear_grafico_comparativo(
                etiquetas, comp.get("actual", []), comp.get("anterior", []),
                comp.get("mes_actual", "Actual"), comp.get("mes_anterior", "Anterior"),
                "Ingresos por Día: Actual vs Anterior", contenedor=frame_g)
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        filas = []
        for i, et in enumerate(etiquetas):
            a = comp["actual"][i] if i < len(comp.get("actual", [])) else 0
            p = comp["anterior"][i] if i < len(comp.get("anterior", [])) else 0
            d = round(a - p, 2)
            filas.append([et,
                          f"S/{a:.2f}",
                          f"S/{p:.2f}",
                          (f"S/{d:+.2f}", {"text_color": "#22C55E" if d >= 0 else "#DC2626"})])
        crear_tabla_cards(
            padre_tabla,
            [("Día", 60), (comp.get("mes_actual", "Actual"), 110), (comp.get("mes_anterior", "Anterior"), 110), ("Diferencia", 110)],
            filas,
            cap=31,
        )

    def _detalle_dinero_compras(self):
        movs = dashboard_controller.listar_compras_mes()
        total = round(sum(_num(m.get("monto_total")) for m in movs), 2)
        ctk.CTkLabel(self.detalle_frame, text=f"Total compras: S/{total:.2f} en {len(movs)} compras",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        if not movs:
            ctk.CTkLabel(self.detalle_frame, text="Sin compras con método este mes").pack(pady=10)
            return
        hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            dias, montos = self._agrupar_por_dia(movs, "fecha_movimiento", "monto_total")
            self._crear_grafico_barras_simple(dias, montos, "Compras por Día", contenedor=frame_g, color_fijo="#F59E0B")
            padre = frame_t
        else:
            padre = self.detalle_frame
        crear_tabla_cards(
            padre,
            [("Producto", 180), ("Cant.", 60), ("Monto", 90), ("Método", 80), ("Fecha", 100)],
            [[str(m.get("producto_nombre", "")),
              str(m.get("cantidad", "")),
              (f"S/{_num(m.get('monto_total')):.2f}", {"text_color": "#F59E0B", "weight": "bold"}),
              str(m.get("metodo_pago", "")),
              str((m.get("fecha_movimiento", "") or "")[:10])] for m in movs],
            cap=30, nota_mas=f"Mostrando 30 de {len(movs)} compras")

    def _detalle_dinero_ventas(self):
        ventas = dashboard_controller.listar_ventas_dinero_mes()
        total = round(sum(_num(v.get("monto_total")) for v in ventas), 2)
        ctk.CTkLabel(self.detalle_frame, text=f"Total ventas: S/{total:.2f} en {len(ventas)} ventas",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        if not ventas:
            ctk.CTkLabel(self.detalle_frame, text="Sin ventas Yape/Efectivo este mes").pack(pady=10)
            return
        hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            dias, montos = self._agrupar_por_dia(ventas, "fecha_venta", "monto_total")
            self._crear_grafico_barras_simple(dias, montos, "Ventas por Día", contenedor=frame_g, color_fijo="#22C55E")
            padre = frame_t
        else:
            padre = self.detalle_frame
        crear_tabla_cards(
            padre,
            [("Recibo", 140), ("Monto", 90), ("Método", 80), ("Fecha", 100)],
            [[str(v.get("numero_recibo", "")),
              (f"S/{_num(v.get('monto_total')):.2f}", {"text_color": "green", "weight": "bold"}),
              str(v.get("metodo_pago", "")),
              str(v.get("fecha_venta", ""))] for v in ventas],
            cap=30, nota_mas=f"Mostrando 30 de {len(ventas)} ventas")

    def _detalle_dinero_ganancias(self):
        filas = dashboard_controller.listar_ganancias_mes()
        total = round(sum(_num(f.get("ganancia")) for f in filas), 2)
        ctk.CTkLabel(self.detalle_frame, text=f"Ganancia total: S/{total:.2f} en {len(filas)} ventas",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        if not filas:
            ctk.CTkLabel(self.detalle_frame, text="Sin ganancias Yape/Efectivo este mes").pack(pady=10)
            return
        crear_tabla_cards(
            self.detalle_frame,
            [("Recibo", 140), ("Método", 80), ("Ingresos", 90), ("Ganancia", 90)],
            [[str(f.get("recibo", "")),
              str(f.get("metodo", "")),
              f"S/{_num(f.get('ingresos')):.2f}",
              (f"S/{_num(f.get('ganancia')):.2f}", {"text_color": "green", "weight": "bold"})] for f in filas],
            cap=30, nota_mas=f"Mostrando 30 de {len(filas)} ventas")

    def _detalle_nuevos_mes(self):
        alumnos = dashboard_controller.listar_nuevos_mes()

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(alumnos)} alumnos nuevos este mes",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not alumnos:
            ctk.CTkLabel(self.detalle_frame, text="No hay alumnos nuevos este mes").pack(pady=10)
            return

        hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            dias, conteos = self._agrupar_conteos_por_dia(alumnos, "fecha_ingreso")
            self._crear_grafico_barras_simple(dias, conteos, "Nuevos por Día del Mes", contenedor=frame_g, ylabel="Alumnos", color_fijo="#22C55E")
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        crear_tabla_cards(
            padre_tabla,
            [("DNI", 80), ("Nombre", 220), ("Ingreso", 100), ("Teléfono", 110)],
            [[str(a.get("dni", "")),
              f"{a.get('nombres', '')} {a.get('apellidos', '')}",
              str(a.get("fecha_ingreso", "")),
              str(a.get("telefono", "") or "—")] for a in alumnos],
            cap=50,
            nota_mas=f"Mostrando 50 de {len(alumnos)} alumnos",
        )

    @staticmethod
    def _agrupar_conteos_por_dia(filas, campo_fecha):
        agg: dict = {}
        for f in filas:
            dia = str(f.get(campo_fecha, "") or "")[:10]
            if dia:
                agg[dia] = agg.get(dia, 0) + 1
        dias = sorted(agg)
        return [d[-5:] for d in dias], [agg[d] for d in dias]

    @staticmethod
    def _agrupar_conteos_por_campo(filas, campo):
        agg: dict = {}
        for f in filas:
            clave = str(f.get(campo, "") or "—")
            agg[clave] = agg.get(clave, 0) + 1
        claves = sorted(agg)
        return claves, [agg[c] for c in claves]

    def _detalle_antiguos_mes(self):
        matriculas = dashboard_controller.listar_antiguos_mes()

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(matriculas)} matrículas de antiguos este mes",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not matriculas:
            ctk.CTkLabel(self.detalle_frame, text="No hay matrículas de antiguos este mes").pack(pady=10)
            return

        self._tabla_matriculas_mes(matriculas)

    def _detalle_matriculas_mes(self):
        matriculas = dashboard_controller.listar_matriculas_mes()

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(matriculas)} matrículas este mes",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not matriculas:
            ctk.CTkLabel(self.detalle_frame, text="No hay matrículas este mes").pack(pady=10)
            return

        self._tabla_matriculas_mes(matriculas)

    @staticmethod
    def _condicion_matricula(mat):
        return ("🆕 Nuevo", {"text_color": "#22C55E", "weight": "bold"}) if int(mat.get("es_nuevo", 0) or 0) == 1 else ("Antiguo", {"text_color": "#6B21A8"})

    def _tabla_matriculas_mes(self, matriculas):
        hay_grafico = bool(MATPLOTLIB_DISPONIBLE)
        if hay_grafico:
            frame_g, frame_t = crear_bloque_grafico_tabla(self.detalle_frame)
            dias, conteos = self._agrupar_conteos_por_dia(matriculas, "fecha_inicio")
            self._crear_grafico_barras_simple(dias, conteos, "Matrículas por Día del Mes", contenedor=frame_g, ylabel="Matrículas", color_fijo="#7C3AED")
            tarifas, conteos_t = self._agrupar_conteos_por_campo(matriculas, "tarifa_nombre")
            if tarifas:
                self._crear_grafico_barras_simple(tarifas, conteos_t, "Matrículas por Tarifa", contenedor=frame_g, ylabel="Matrículas", color_fijo="#6B21A8")
            padre_tabla = frame_t
        else:
            padre_tabla = self.detalle_frame

        crear_tabla_cards(
            padre_tabla,
            [("Estudiante", 180), ("DNI", 80), ("Tarifa", 140), ("Condición", 90), ("Inicio", 90)],
            [[f"{m.get('nombres', '')} {m.get('apellidos', '')}",
              str(m.get("dni", "")),
              str(m.get("tarifa_nombre", "")),
              self._condicion_matricula(m),
              str(m.get("fecha_inicio", ""))] for m in matriculas],
            cap=50,
            nota_mas=f"Mostrando 50 de {len(matriculas)} matrículas",
        )

    def _detalle_stock(self):
        productos = dashboard_controller.listar_stock_bajo()

        ctk.CTkLabel(
            self.detalle_frame,
            text=f"Total: {len(productos)} productos con stock bajo",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        if not productos:
            ctk.CTkLabel(self.detalle_frame, text="No hay productos con stock bajo").pack(pady=10)
            return

        crear_tabla_cards(
            self.detalle_frame,
            [("Código", 80), ("Nombre", 150), ("Categoría", 120), ("Stock Actual", 90), ("Stock Mínimo", 90)],
            [[str(p.get("codigo", "")),
              str(p.get("nombre", "")),
              str(p.get("categoria_nombre", "")),
              (str(p.get("stock_actual", 0)), {"text_color": "red", "weight": "bold"}),
              str(p.get("stock_minimo", 0))] for p in productos],
            cap=50,
            nota_mas=f"Mostrando 50 de {len(productos)} productos",
        )

    def _crear_grafico_barras_simple(self, etiquetas, valores, titulo, contenedor=None, ylabel="Monto (S/)", color_fijo=None):
        if not MATPLOTLIB_DISPONIBLE or not valores:
            return False

        padre = contenedor if contenedor is not None else self.detalle_frame
        frame_grafico = ctk.CTkFrame(padre)
        frame_grafico.pack(fill="x", padx=5, pady=10)

        # Rendimiento: figura compacta, fondo opaco y barras sin alpha.
        # Las transparencias y figuras grandes obligan a recomponer todo el
        # scroll en cada movimiento → tintineo en GPUs integradas.
        fig = Figure(figsize=(7.5, 3.4), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)
        ax.set_facecolor("white")

        if color_fijo:
            colores = [color_fijo] * len(valores)
        else:
            colores = ["#4CAF50" if v >= 0 else "#F44336" for v in valores]
        ax.bar(range(len(valores)), valores, color=colores, alpha=1.0, edgecolor="none")
        ax.set_xticks(range(len(etiquetas)))
        ax.set_xticklabels(etiquetas, rotation=45, ha="right", fontsize=8)
        ax.set_title(titulo, fontsize=12, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.3)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return True

    def _crear_grafico_comparativo(self, etiquetas, serie_a, serie_b, nombre_a, nombre_b, titulo, contenedor=None):
        """Barras agrupadas A vs B (ej. mes actual vs anterior)."""
        if not MATPLOTLIB_DISPONIBLE or not etiquetas:
            return False

        padre = contenedor if contenedor is not None else self.detalle_frame
        frame_grafico = ctk.CTkFrame(padre)
        frame_grafico.pack(fill="x", padx=5, pady=10)

        try:
            import numpy as np
            x = list(np.arange(len(etiquetas)))
        except ImportError:
            x = list(range(len(etiquetas)))
        fig = Figure(figsize=(8, 3.4), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)
        ax.set_facecolor("white")

        ancho = 0.38
        ax.bar([i - ancho / 2 for i in x], serie_a, ancho, label=nombre_a, color="#7C3AED", alpha=1.0, edgecolor="none")
        ax.bar([i + ancho / 2 for i in x], serie_b, ancho, label=nombre_b, color="#9CA3AF", alpha=1.0, edgecolor="none")
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas, rotation=45, ha="right", fontsize=8)
        ax.set_title(titulo, fontsize=12, fontweight="bold")
        ax.set_ylabel("Monto (S/)")
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return True
