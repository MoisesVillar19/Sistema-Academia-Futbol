import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil, os
from controllers import venta_controller, login_controller
from controllers import inventario_controller
from utils.constants import COMPROBANTES_DIR


class VentaView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._productos_map = {}
        self._comprobante_tmp = None
        self._comprobante_camp = None
        self._est_camp_map = {}
        self._est_camp_map_inv = {}
        self._tarifas_camp2_map = {}
        self._crear_widgets()
        self._cargar_productos()
        self._cargar_ventas()
        try:
            self._cargar_campeonatos()
        except Exception:
            pass

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_lista = self.tabview.add("Ventas")
        self.tab_form = self.tabview.add("Registrar Venta")
        self.tab_camp = self.tabview.add("Campeonatos")
        self._crear_tab_lista()
        self._crear_tab_form()
        self._crear_tab_campeonatos()

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_lista, titulo="Ventas", icono="🛒",
            descripcion="Uniformes / Tienda / Campeonato / Inscripción. Clic en ▾ Ver detalle para producto, cantidades y comprobante.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_ventas,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))
        crear_nota(sec, "Tip: cada tarjeta se expande inline con el detalle completo.")
        self.scroll = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_lista_status = ctk.CTkLabel(self.tab_lista, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_lista_status.pack(pady=3)

    def _crear_tab_form(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        sec1 = crear_seccion(scroll, titulo="Producto y tipo", icono="🛒",
                             descripcion="Uniforme/Tienda por producto con stock. Campeonato se cobra por tarifa.",
                             nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(cuerpo1, text="Producto *").pack(anchor="w")
        self.combo_producto = ctk.CTkComboBox(cuerpo1, width=400, values=["Cargando..."])
        self.combo_producto.pack(anchor="w", pady=3)
        ctk.CTkLabel(cuerpo1, text="Cantidad *").pack(anchor="w")
        self.entry_cant = ctk.CTkEntry(cuerpo1, width=150, placeholder_text="1")
        self.entry_cant.pack(anchor="w", pady=3)
        self.entry_cant.insert(0, "1")
        ctk.CTkLabel(cuerpo1, text="Tipo venta").pack(anchor="w")
        self.combo_tipo = ctk.CTkComboBox(cuerpo1, width=200, values=["UNIFORME","TIENDA","CAMPEONATO","INSCRIPCION"], command=self._on_tipo_changed)
        self.combo_tipo.set("UNIFORME")
        self.combo_tipo.pack(anchor="w", pady=3)
        # CAMPEONATO por tarifa (división): sin producto obligatorio
        self.frame_campeonato = ctk.CTkFrame(scroll, fg_color="transparent")
        ctk.CTkLabel(self.frame_campeonato, text="Tarifa campeonato (división) *").pack(anchor="w")
        self.combo_tarifa_camp = ctk.CTkComboBox(self.frame_campeonato, width=400, values=["Cargando..."], command=self._on_tarifa_camp_changed)
        self.combo_tarifa_camp.pack(anchor="w", pady=3)
        ctk.CTkLabel(self.frame_campeonato, text="Monto a cobrar (S/) * — editable").pack(anchor="w")
        self.entry_monto_camp = ctk.CTkEntry(self.frame_campeonato, width=150, placeholder_text="0.00")
        self.entry_monto_camp.pack(anchor="w", pady=3)
        ctk.CTkLabel(self.frame_campeonato, text="↳ En CAMPEONATO el producto es opcional; el monto manda.", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self._tarifas_camp_map = {}
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
        crear_nota(sec2, "Para campeonatos usa la pestaña Campeonatos (inscribe por división).")
        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_status = ctk.CTkLabel(footer, text="")
        self.label_status.pack(anchor="w", padx=10, pady=(8, 2))
        crear_boton_interactivo(footer, text="Registrar Venta", width=150, command=self._registrar,
                                fg_color="#7C3AED").pack(anchor="w", padx=10, pady=(2, 8))

    def _cargar_productos(self):
        prods = inventario_controller.listar_productos(activo=1)
        nombres = [f"{p['codigo']} - {p['nombre']} (S/{p.get('precio_venta', p.get('precio',0)):.2f} stock:{p['stock_actual']})" for p in prods]
        self.combo_producto.configure(values=nombres if nombres else ["Sin productos"])
        self._productos_map = {n: p for n,p in zip(nombres, prods)}

    def _cargar_ventas(self):
        from utils.ui_helpers import crear_lista_vacia
        for w in self.scroll.winfo_children():
            w.destroy()
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

        def _poblar(frame, _v=v):
            linea_detalle(frame, "ID venta", _v.get("id_venta"))
            linea_detalle(frame, "Recibo", _v.get("numero_recibo"))
            linea_detalle(frame, "Tipo", _v.get("tipo_venta"))
            linea_detalle(frame, "División", _v.get("tarifa_nombre") or _v.get("id_tarifa"))
            linea_detalle(frame, "Producto", _v.get("producto_nombre") or _v.get("nombre_producto"))
            linea_detalle(frame, "Cantidad", _v.get("cantidad"))
            linea_detalle(frame, "Precio unit.", _v.get("precio_unitario") or _v.get("precio"))
            linea_detalle(frame, "Método pago", _v.get("metodo_pago"))
            linea_detalle(frame, "Estudiante", _v.get("estudiante_nombre") or _v.get("id_estudiante") or _v.get("estudiante"))
            linea_detalle(frame, "Comprobante", _v.get("comprobante_path"))
            linea_detalle(frame, "Fecha", _v.get("fecha_venta"))

        toggle_btn, _, _ = agregar_detalle_expandible(card, _poblar)
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    # ── Pestaña Campeonatos: inscribir+ cobrar por división, resumen y arbitraje ──
    def _crear_tab_campeonatos(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_camp, titulo="Campeonatos", icono="🏆",
            descripcion="Inscribe estudiantes por división (tarifa), cobra y sigue arbitraje. Las divisiones se crean en Tarifas.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_campeonatos,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))
        crear_nota(sec, "Tip: el resumen muestra inscritos, recaudado, arbitraje y neto por división.")

        form = ctk.CTkFrame(self.tab_camp, fg_color="white", corner_radius=8)
        form.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(form, text="Inscribir y cobrar", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3D1559").pack(anchor="w", padx=10, pady=(8, 2))
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(grid, text="Estudiante *").grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkLabel(grid, text="División (tarifa) *").grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(grid, text="Monto S/ *").grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkLabel(grid, text="Método").grid(row=0, column=3, sticky="w", padx=4)
        self.combo_est_camp = ctk.CTkComboBox(grid, width=220, values=["Cargando..."])
        self.combo_est_camp.grid(row=1, column=0, padx=4, pady=2)
        self.combo_tarifa_camp2 = ctk.CTkComboBox(grid, width=220, values=["Cargando..."], command=self._on_tarifa_camp2_changed)
        self.combo_tarifa_camp2.grid(row=1, column=1, padx=4, pady=2)
        self.entry_monto_camp2 = ctk.CTkEntry(grid, width=110, placeholder_text="0.00")
        self.entry_monto_camp2.grid(row=1, column=2, padx=4, pady=2)
        self.combo_metodo_camp = ctk.CTkComboBox(grid, width=140, values=["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA"])
        self.combo_metodo_camp.set("EFECTIVO")
        self.combo_metodo_camp.grid(row=1, column=3, padx=4, pady=2)
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(row2, text="N° equipos (referencia):").pack(side="left")
        self.entry_equipos_camp = ctk.CTkEntry(row2, width=70, placeholder_text="0")
        self.entry_equipos_camp.pack(side="left", padx=5)
        self.label_equipos_hint = ctk.CTkLabel(row2, text="", font=ctk.CTkFont(size=11), text_color="#6B5B7B")
        self.label_equipos_hint.pack(side="left", padx=5)
        self.entry_equipos_camp.bind("<KeyRelease>", lambda e: self._actualizar_hint_equipos())
        from widgets.date_picker import DatePicker as _DP
        self.date_camp = _DP(row2, label_text="Fecha:", default="today")
        self.date_camp.pack(side="left", padx=5)
        self.btn_comp_camp = ctk.CTkButton(row2, text="📎 Comprobante", width=130, command=self._elegir_comprobante_camp)
        self.btn_comp_camp.pack(side="left", padx=5)
        self.label_comp_camp = ctk.CTkLabel(row2, text="Sin comprobante", text_color="gray")
        self.label_comp_camp.pack(side="left", padx=5)
        self._comprobante_camp = None
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(btn_row, text="Registrar Inscripción + Cobro", width=220, fg_color="#7C3AED",
                      command=self._registrar_campeonato).pack(side="left")
        self.label_camp_status = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.label_camp_status.pack(side="left", padx=10)

        self.label_resumen_camp = ctk.CTkLabel(self.tab_camp, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_resumen_camp.pack(pady=3)
        self.scroll_resumen = ctk.CTkScrollableFrame(self.tab_camp, height=150)
        self.scroll_resumen.pack(fill="x", padx=5, pady=5)
        self.scroll_camp = ctk.CTkScrollableFrame(self.tab_camp)
        self.scroll_camp.pack(fill="both", expand=True, padx=5, pady=5)
        self._est_camp_map = {}
        self._tarifas_camp2_map = {}

    def _cargar_campeonatos(self):
        from utils.ui_helpers import crear_lista_vacia
        self._cargar_estudiantes_camp()
        self._cargar_tarifas_camp2()
        for w in self.scroll_resumen.winfo_children():
            w.destroy()
        for w in self.scroll_camp.winfo_children():
            w.destroy()
        try:
            resumen = venta_controller.resumen_campeonatos()
        except Exception as e:
            self.label_resumen_camp.configure(text=f"Error: {e}")
            return
        tot_r = round(sum(r["recaudado"] for r in resumen), 2)
        tot_a = round(sum(r["arbitraje"] for r in resumen), 2)
        self.label_resumen_camp.configure(
            text=f"Recaudado: S/{tot_r:.2f} • Arbitraje: S/{tot_a:.2f} • Neto: S/{tot_r - tot_a:.2f}")
        if not resumen:
            crear_lista_vacia(self.scroll_resumen, "Sin divisiones", "Crea tarifas tipo CAMPEONATO en Tarifas")
        for r in resumen:
            t = r["tarifa"]
            card = ctk.CTkFrame(self.scroll_resumen, fg_color="white", border_width=1, border_color="#E5E7EB", corner_radius=8)
            card.pack(fill="x", padx=5, pady=3)
            ctk.CTkLabel(card, text=f"{t.get('categoria_nombre','')} - {t['nombre']}",
                         font=ctk.CTkFont(size=13, weight="bold"), text_color="#1F0A33").pack(anchor="w", padx=10, pady=(6, 0))
            neto_c = "#22C55E" if r["neto"] >= 0 else "#DC2626"
            ctk.CTkLabel(card, text=f"👥 {r['inscritos']} inscritos • {r['ventas']} cobros • Recaudado S/{r['recaudado']:.2f} • Arbitraje S/{r['arbitraje']:.2f}",
                         font=ctk.CTkFont(size=12), text_color="#6B5B7B").pack(anchor="w", padx=10)
            ctk.CTkLabel(card, text=f"Neto: S/{r['neto']:.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=neto_c).pack(anchor="w", padx=10, pady=(0, 6))
        try:
            ventas = venta_controller.listar_ventas(tipo_venta="CAMPEONATO")
        except Exception:
            ventas = []
        if not ventas:
            crear_lista_vacia(self.scroll_camp, "Sin cobros de campeonato", "Registra la primera inscripción arriba")
            return
        try:
            from controllers import tarifa_controller
            _tar_map = {t["id_tarifa"]: t["nombre"] for t in tarifa_controller.listar_tarifas_activas(tipo="CAMPEONATO")}
        except Exception:
            _tar_map = {}
        for v in ventas:
            vv = dict(v)
            if vv.get("id_tarifa") in _tar_map:
                vv["tarifa_nombre"] = _tar_map[vv["id_tarifa"]]
            est = self._est_camp_map_inv.get(vv.get("id_estudiante")) if hasattr(self, "_est_camp_map_inv") else None
            if est:
                vv["estudiante_nombre"] = est
            self._crear_card_venta(self.scroll_camp, vv)

    def _cargar_estudiantes_camp(self):
        try:
            from controllers import estudiante_controller
            ests = estudiante_controller.listar_estudiantes(activo=1, estado=["ACTIVO", "REINGRESANTE"])
        except Exception:
            ests = []
        nombres = [f"{e.get('nombres','')} {e.get('apellidos','')} (DNI {e.get('dni','')})" for e in ests]
        self.combo_est_camp.configure(values=nombres if nombres else ["Sin estudiantes"])
        self._est_camp_map = {n: e["id_estudiante"] for n, e in zip(nombres, ests)}
        self._est_camp_map_inv = {e["id_estudiante"]: f"{e.get('nombres','')} {e.get('apellidos','')}" for e in ests}

    def _cargar_tarifas_camp2(self):
        try:
            from controllers import tarifa_controller
            tarifas = tarifa_controller.listar_tarifas_activas(tipo="CAMPEONATO")
        except Exception:
            tarifas = []
        nombres = [f"{t.get('categoria_nombre','')} - {t['nombre']} (S/{t['monto']:.2f})" for t in tarifas]
        self.combo_tarifa_camp2.configure(values=nombres if nombres else ["Sin tarifas de campeonato"])
        self._tarifas_camp2_map = {n: t for n, t in zip(nombres, tarifas)}

    def _on_tarifa_camp2_changed(self, selection):
        t = self._tarifas_camp2_map.get(selection)
        if t:
            self.entry_monto_camp2.delete(0, "end")
            self.entry_monto_camp2.insert(0, f"{t['monto']:.2f}")
            self._actualizar_hint_equipos()

    def _actualizar_hint_equipos(self):
        try:
            n = int((self.entry_equipos_camp.get().strip() or "0"))
            m = float((self.entry_monto_camp2.get().strip() or "0"))
            if n > 0 and m > 0:
                self.label_equipos_hint.configure(text=f"= S/{m/n:.2f} por equipo")
            else:
                self.label_equipos_hint.configure(text="")
        except Exception:
            self.label_equipos_hint.configure(text="")

    def _elegir_comprobante_camp(self):
        path = filedialog.askopenfilename(filetypes=[("Imagen", "*.jpg *.jpeg *.png"), ("Todos", "*.*")])
        if path:
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            self._comprobante_camp = path
            self.label_comp_camp.configure(text=os.path.basename(path))

    def _registrar_campeonato(self):
        id_est = self._est_camp_map.get(self.combo_est_camp.get())
        if not id_est:
            self.label_camp_status.configure(text="Seleccione estudiante", text_color="red")
            return
        t = self._tarifas_camp2_map.get(self.combo_tarifa_camp2.get())
        if not t:
            self.label_camp_status.configure(text="Seleccione división", text_color="red")
            return
        try:
            monto = float(self.entry_monto_camp2.get().strip() or "0")
            if monto <= 0:
                raise ValueError
        except ValueError:
            self.label_camp_status.configure(text="Monto inválido", text_color="red")
            return
        data = {"id_estudiante": id_est, "tipo_venta": "CAMPEONATO",
                "metodo_pago": self.combo_metodo_camp.get(), "items": [],
                "id_tarifa": t["id_tarifa"], "monto_total": monto,
                "comprobante_path": self._comprobante_camp,
                "fecha_venta": self.date_camp.get() or None}
        exito, msg, vid = venta_controller.registrar_venta(data)
        if exito and self._comprobante_camp and vid:
            try:
                import shutil
                v = venta_controller.obtener_venta(vid)
                if v:
                    shutil.copy2(self._comprobante_camp, os.path.join(COMPROBANTES_DIR, f"{v['numero_recibo']}.jpg"))
            except Exception:
                pass
            self._comprobante_camp = None
            self.label_comp_camp.configure(text="Sin comprobante")
        self.label_camp_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self.entry_monto_camp2.delete(0, "end")
            self._cargar_campeonatos()
            self._cargar_ventas()

    def _elegir_comprobante(self):
        path = filedialog.askopenfilename(filetypes=[("Imagen","*.jpg *.jpeg *.png"),("Todos","*.*")])
        if path:
            os.makedirs(COMPROBANTES_DIR, exist_ok=True)
            self._comprobante_tmp = path
            self.label_comp.configure(text=os.path.basename(path))

    def _on_tipo_changed(self, selection):
        if selection == "CAMPEONATO":
            self.frame_campeonato.pack(anchor="w", pady=5, before=self.btn_comprobante)
            self._cargar_tarifas_campeonato()
        else:
            try:
                self.frame_campeonato.pack_forget()
            except Exception:
                pass

    def _cargar_tarifas_campeonato(self):
        try:
            from controllers import tarifa_controller
            tarifas = tarifa_controller.listar_tarifas_activas(tipo="CAMPEONATO")
        except Exception:
            tarifas = []
        nombres = [f"{t.get('categoria_nombre','')} - {t['nombre']} (S/{t['monto']:.2f})" for t in tarifas]
        self.combo_tarifa_camp.configure(values=nombres if nombres else ["Sin tarifas de campeonato"])
        self._tarifas_camp_map = {n: t for n, t in zip(nombres, tarifas)}

    def _on_tarifa_camp_changed(self, selection):
        t = self._tarifas_camp_map.get(selection)
        if t:
            self.entry_monto_camp.delete(0, "end")
            self.entry_monto_camp.insert(0, f"{t['monto']:.2f}")

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
        if tipo == "CAMPEONATO":
            t = self._tarifas_camp_map.get(self.combo_tarifa_camp.get())
            if not t:
                self.label_status.configure(text="Seleccione tarifa de campeonato", text_color="red")
                return
            try:
                monto = float(self.entry_monto_camp.get().strip() or "0")
                if monto <= 0:
                    raise ValueError
            except ValueError:
                self.label_status.configure(text="Monto de campeonato inválido", text_color="red")
                return
            data = {
                "id_estudiante": id_est,
                "tipo_venta": tipo,
                "metodo_pago": self.combo_metodo.get(),
                "items": [],
                "id_tarifa": t["id_tarifa"],
                "monto_total": monto,
                "comprobante_path": comprobante_path,
                "fecha_venta": self.date_venta.get() or None,
            }
        else:
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
        exito, msg, vid = venta_controller.registrar_venta(data)
        if exito and comprobante_path and vid:
            # copiar a central con recibo
            try:
                import glob
                # el service ya generó recibo, obtener venta para nombre
                v = venta_controller.obtener_venta(vid)
                if v:
                    dest = os.path.join(COMPROBANTES_DIR, f"{v['numero_recibo']}.jpg")
                    shutil.copy2(comprobante_path, dest)
            except Exception:
                pass
            self._comprobante_tmp = None
            self.label_comp.configure(text="Sin comprobante")
        self.label_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            self._cargar_productos()
            self._cargar_ventas()
