import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from controllers import egreso_controller
from utils.dates import get_today
from utils.constants import COMPROBANTES_DIR
try:
    from PIL import Image
except ImportError:
    Image = None


class EgresoView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        self._cargar_egresos()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_lista = self.tabview.add("Egresos")
        self.tab_form = self.tabview.add("Registrar Egreso")
        self.tab_reporte = self.tabview.add("Reporte")
        self._crear_lista()
        self._crear_form()
        self._crear_reporte()

    def _crear_lista(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_lista, titulo="Egresos", icono="💸",
            descripcion="Profesor / Personal / Campeonato. Clic en ▾ Ver detalle para responsable, observación y comprobante.",
            nro=1,
        )
        crear_boton_interactivo(sec, text="Actualizar", width=110, command=self._cargar_egresos,
                                fg_color="#7C3AED").pack(anchor="e", padx=10, pady=(0, 8))
        # Fase 7b: toggle Cards/Tabla
        self._vista_modo = "Cards"
        self.seg_vista = ctk.CTkSegmentedButton(
            sec, values=["Cards", "Tabla"], command=self._on_vista_cambiar)
        try:
            self.seg_vista.set("Cards")
        except Exception:
            pass
        self.seg_vista.pack(anchor="e", padx=10, pady=(0, 8))
        crear_nota(sec, "Tip: cada tarjeta se expande inline con el detalle completo.")
        self.scroll = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_lista_status = ctk.CTkLabel(self.tab_lista, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6B5B7B")
        self.label_lista_status.pack(pady=3)

    def _crear_form(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        from widgets.date_picker import DatePicker
        scroll = ctk.CTkScrollableFrame(self.tab_form)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        sec1 = crear_seccion(scroll, titulo="Concepto y monto", icono="💸",
                             descripcion="PROFESOR/ARBITRAJE sugieren monto editable. División solo para campeonatos.",
                             nro=1)
        cuerpo1 = ctk.CTkFrame(sec1, fg_color="transparent")
        cuerpo1.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(cuerpo1, text="Concepto *").pack(anchor="w")
        self.combo_concepto = ctk.CTkComboBox(cuerpo1, width=250, values=["PROFESOR","PERSONAL","CAMPEONATO_FIJO","ARBITRAJE","VIATICOS"], command=self._on_concepto_changed)
        self.combo_concepto.set("PROFESOR")
        self.combo_concepto.pack(anchor="w", pady=3)
        self.frame_division = ctk.CTkFrame(cuerpo1, fg_color="transparent")
        ctk.CTkLabel(self.frame_division, text="División campeonato (opcional, para ARBITRAJE/CAMPEONATO_FIJO)").pack(anchor="w")
        self.combo_tarifa_egr = ctk.CTkComboBox(self.frame_division, width=400, values=["Ninguna"])
        self.combo_tarifa_egr.set("Ninguna")
        self.combo_tarifa_egr.pack(anchor="w", pady=3)
        self._tarifas_egr_map = {}
        from utils import event_bus as _eb2
        crear_boton_interactivo(cuerpo1, text="🏷 Tarifas campeonato", width=180,
                                command=lambda: _eb2.publish("abrir_tarifas", tab="Tarifas", tipo="CAMPEONATO"),
                                fg_color="#E5E7EB", hover_color="#DDD6E5",
                                text_color="#1F0A33").pack(anchor="w", pady=3)
        ctk.CTkLabel(cuerpo1, text="Monto S/ * (editable: cada profesor/árbitro puede cobrar distinto)").pack(anchor="w")
        self.entry_monto = ctk.CTkEntry(cuerpo1, width=150, placeholder_text="200")
        self.entry_monto.pack(anchor="w", pady=3)
        self.date_fecha = DatePicker(cuerpo1, label_text="Fecha *", default="today")
        self.date_fecha.pack(anchor="w", pady=3)
        ctk.CTkLabel(cuerpo1, text="Responsable").pack(anchor="w")
        self.entry_resp = ctk.CTkEntry(cuerpo1, width=300, placeholder_text="Nombre")
        self.entry_resp.pack(anchor="w", pady=3)
        ctk.CTkLabel(cuerpo1, text="Observación").pack(anchor="w")
        self.entry_obs = ctk.CTkEntry(cuerpo1, width=400)
        self.entry_obs.pack(anchor="w", pady=3)
        sec2 = crear_seccion(scroll, titulo="Comprobante", icono="📎",
                             descripcion="Opcional, jpg/png/pdf ≤5MB.", nro=2)
        cuerpo2 = ctk.CTkFrame(sec2, fg_color="transparent")
        cuerpo2.pack(fill="x", padx=10, pady=(0, 8))
        comp_frame = ctk.CTkFrame(cuerpo2, fg_color="transparent")
        comp_frame.pack(fill="x", anchor="w", pady=2)
        self.btn_comp = ctk.CTkButton(comp_frame, text="📎 Seleccionar comprobante", width=180, command=self._elegir_comprobante)
        self.btn_comp.pack(side="left", padx=5)
        self.label_comp = ctk.CTkLabel(comp_frame, text="Sin comprobante", text_color="gray")
        self.label_comp.pack(side="left", padx=5)
        self.label_comp_preview = ctk.CTkLabel(comp_frame, text="")
        self.label_comp_preview.pack(side="left", padx=5)
        self._comprobante_path = None
        footer = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8)
        footer.pack(fill="x", padx=5, pady=5)
        self.label_status = ctk.CTkLabel(footer, text="")
        self.label_status.pack(anchor="w", padx=10, pady=(8, 2))
        crear_boton_interactivo(footer, text="Guardar", width=120, command=self._guardar,
                                fg_color="#7C3AED").pack(anchor="w", padx=10, pady=(2, 8))

    def _crear_reporte(self):
        frame = ctk.CTkFrame(self.tab_reporte, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame, text="Ingresos vs Egresos (mes actual)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.label_reporte = ctk.CTkLabel(frame, text="", justify="left")
        self.label_reporte.pack(anchor="w", pady=5)
        ctk.CTkButton(frame, text="Calcular", command=self._calcular).pack(anchor="w", pady=5)

    def _cargar_egresos(self):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible, linea_detalle, crear_lista_vacia
        for w in self.scroll.winfo_children():
            w.destroy()
        egresos = egreso_controller.listar_egresos()
        if hasattr(self, "label_lista_status"):
            self.label_lista_status.configure(text=f"Total: {len(egresos)} egreso(s)")
        if not egresos:
            crear_lista_vacia(self.scroll, "No hay egresos", "Registra el primero en la pestaña Registrar Egreso")
            return
        if getattr(self, "_vista_modo", "Cards") == "Tabla":
            self._render_tabla_egresos(egresos)
            return
        for e in egresos:
            self._crear_card_egreso(e)

    def _on_vista_cambiar(self, valor):
        self._vista_modo = valor
        self._cargar_egresos()

    def _render_tabla_egresos(self, egresos):
        from utils.ui_helpers import crear_tabla_densa
        cols = [("Concepto", 150), ("Monto", 90), ("Fecha", 100),
                ("Responsable", 150)]
        filas, dets = [], []
        for e in egresos:
            filas.append([
                str(e.get("concepto", "")),
                (f"S/{e.get('monto', 0):.2f}", {"weight": "bold"}),
                str(e.get("fecha", "")),
                str(e.get("responsable", "") or "—"),
            ])
            dets.append(lambda frame, _e=e: self._poblar_detalle_egreso(frame, _e))
        crear_tabla_densa(self.scroll, cols, filas, dets, cap=100)

    @staticmethod
    def _poblar_detalle_egreso(frame, e):
        from utils.ui_helpers import linea_detalle
        linea_detalle(frame, "ID egreso", e.get("id_egreso"))
        linea_detalle(frame, "Concepto", e.get("concepto"))
        if e.get("id_tarifa"):
            try:
                from controllers import tarifa_controller
                _t = tarifa_controller.obtener_tarifa(e.get("id_tarifa"))
                linea_detalle(frame, "División", f"{_t.get('nombre','')} (S/{_t.get('monto',0)})" if _t else e.get("id_tarifa"))
            except Exception:
                linea_detalle(frame, "División", e.get("id_tarifa"))
        linea_detalle(frame, "Monto", f"S/{e.get('monto',0)}")
        linea_detalle(frame, "Fecha", e.get("fecha"))
        linea_detalle(frame, "Responsable", e.get("responsable"))
        linea_detalle(frame, "Observación", e.get("observacion"))
        linea_detalle(frame, "Comprobante", e.get("comprobante_path"))
        linea_detalle(frame, "Registrado por", e.get("username") or e.get("usuario"))

    def _crear_card_egreso(self, e):
        from utils.ui_helpers import crear_card_interactiva, agregar_detalle_expandible
        card = crear_card_interactiva(self.scroll)
        card.pack(fill="x", padx=6, pady=4)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)
        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        try:
            titulo = f"{e['concepto']} - S/{e['monto']:.2f} - {e['fecha']}"
        except Exception:
            titulo = f"{e.get('concepto','')} - S/{e.get('monto',0)} - {e.get('fecha','')}"
        ctk.CTkLabel(info, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#1F0A33").pack(anchor="w")
        ctk.CTkLabel(info, text=f"Resp: {e.get('responsable','')} | {e.get('observacion','')}", text_color="#6B5B7B", font=ctk.CTkFont(size=12)).pack(anchor="w")
        badge = ctk.CTkFrame(top, fg_color="#F3E8FF", corner_radius=8)
        badge.pack(side="right", padx=10)
        try:
            ctk.CTkLabel(badge, text=f"S/{e['monto']:.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#7C3AED").pack(padx=10, pady=6)
        except Exception:
            pass

        comp = e.get("comprobante_path")
        if comp and os.path.isfile(comp) and Image:
            try:
                img = Image.open(comp)
                img.thumbnail((60, 60))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                if not hasattr(self, "_comp_cache"):
                    self._comp_cache = {}
                self._comp_cache[e.get("id_egreso", id(comp))] = ctk_img
                lbl = ctk.CTkLabel(info, image=ctk_img, text="")
                lbl.pack(anchor="w", pady=2)
                lbl.bind("<Button-1>", lambda ev, p=comp: os.startfile(p) if os.path.exists(p) else None)
                ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp)} (clic para ampliar)", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
            except Exception:
                ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")
        elif comp:
            ctk.CTkLabel(info, text=f"📎 {os.path.basename(comp)}", font=ctk.CTkFont(size=11), text_color="#7C3AED").pack(anchor="w")

        toggle_btn, _, _ = agregar_detalle_expandible(
            card, lambda frame, _e=e: self._poblar_detalle_egreso(frame, _e))
        toggle_btn.pack(anchor="e", padx=10, pady=(0, 8))

    def _on_concepto_changed(self, selection):
        # División visible solo para ARBITRAJE/CAMPEONATO_FIJO
        try:
            if selection in ("ARBITRAJE", "CAMPEONATO_FIJO"):
                self.frame_division.pack(anchor="w", pady=3, before=self.entry_monto)
                self._cargar_tarifas_egreso()
            else:
                self.frame_division.pack_forget()
        except Exception:
            pass
        # Prefill editable con el default de Configuración (cada caso puede variar)
        if self.entry_monto.get().strip():
            return
        try:
            from controllers import configuracion_controller
            config = configuracion_controller.obtener_configuracion() or {}
        except Exception:
            config = {}
        defaults = {"PROFESOR": config.get("pago_profesor", 200),
                    "ARBITRAJE": config.get("arbitraje_por_equipo", 15)}
        if selection in defaults:
            try:
                self.entry_monto.delete(0, "end")
                self.entry_monto.insert(0, str(defaults[selection]))
            except Exception:
                pass

    def _cargar_tarifas_egreso(self):
        try:
            from controllers import tarifa_controller
            tarifas = tarifa_controller.listar_tarifas_activas(tipo="CAMPEONATO")
        except Exception:
            tarifas = []
        nombres = ["Ninguna"] + [f"{t.get('categoria_nombre','')} - {t['nombre']} (S/{t['monto']:.2f})" for t in tarifas]
        self.combo_tarifa_egr.configure(values=nombres)
        self._tarifas_egr_map = {n: t["id_tarifa"] for n, t in zip(nombres[1:], tarifas)}

    def _elegir_comprobante(self):
        from tkinter import messagebox
        from utils.imagenes import validar_imagen
        path = filedialog.askopenfilename(filetypes=[("Imagen/PDF","*.jpg *.jpeg *.png *.pdf"),("Todos","*.*")])
        if not path:
            return
        ok, msg = validar_imagen(path, max_mb=5, permitir_pdf=True)
        if not ok:
            messagebox.showerror("Comprobante no válido", msg)
            self.label_status.configure(text=f"❌ {msg}", text_color="red")
            return
        os.makedirs(COMPROBANTES_DIR, exist_ok=True)
        # copiar a OneDrive con nombre temporal, se renombrará al guardar con recibo
        self._comprobante_path = path
        self.label_comp.configure(text=f"✅ {os.path.basename(path)}")
        if Image and path.lower().endswith(('.jpg','.jpeg','.png')) and os.path.isfile(path):
            try:
                img = Image.open(path)
                img.thumbnail((60, 60))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                self._comp_preview = ctk_img
                self.label_comp_preview.configure(image=ctk_img, text="")
            except Exception:
                self.label_comp_preview.configure(image=None, text="⚠ vista no disponible")

    def _guardar(self):
        comprobante_dest = None
        if self._comprobante_path:
            try:
                os.makedirs(COMPROBANTES_DIR, exist_ok=True)
                # se copiara con nombre EG- id tras insert, por ahora guardar tmp
                comprobante_dest = self._comprobante_path
            except Exception:
                comprobante_dest = self._comprobante_path
        id_tarifa = self._tarifas_egr_map.get(self.combo_tarifa_egr.get())
        data = {
            "concepto": self.combo_concepto.get(),
            "monto": self.entry_monto.get().strip(),
            "fecha": self.date_fecha.get().strip() or get_today(),
            "responsable": self.entry_resp.get().strip(),
            "observacion": self.entry_obs.get().strip(),
            "comprobante_path": comprobante_dest,
            "id_tarifa": id_tarifa,
        }
        exito, msg, id_eg = egreso_controller.registrar_egreso(data)
        self.label_status.configure(text=msg, text_color="green" if exito else "red")
        if exito:
            # si hay comprobante, copiar con nombre EG-{id}.jpg
            if self._comprobante_path and id_eg:
                try:
                    ext = os.path.splitext(self._comprobante_path)[1] or ".jpg"
                    dest = os.path.join(COMPROBANTES_DIR, f"EG-{id_eg}{ext}")
                    import shutil
                    shutil.copy2(self._comprobante_path, dest)
                    # actualizar via service (respeta capas)
                    from services import egreso_service
                    egreso_service.editar_egreso(id_eg, {"comprobante_path": dest})
                except Exception:
                    pass
            self._comprobante_path = None
            self.label_comp.configure(text="Sin comprobante")
            self.label_comp_preview.configure(image=None, text="")
            self._cargar_egresos()
            self.entry_monto.delete(0, "end")
            try:
                self.combo_tarifa_egr.set("Ninguna")
                self.frame_division.pack_forget()
            except Exception:
                pass

    def _calcular(self):
        from datetime import date
        hoy = date.today()
        ini = hoy.replace(day=1).isoformat()
        fin = hoy.isoformat()
        rep = egreso_controller.reporte_ingresos_vs_egresos(ini, fin)
        if rep:
            self.label_reporte.configure(text=f"Ingresos: S/{rep.get('total_ingresos',0):.2f} (ventas {rep.get('ingresos_ventas',0):.2f} + pagos {rep.get('ingresos_pagos',0):.2f})\nEgresos: S/{rep.get('egresos',0):.2f}\nNeto: S/{rep.get('neto',0):.2f}")
