import customtkinter as ctk
from controllers import auditoria_controller
from widgets.date_picker import DatePicker


class AuditoriaView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        if hasattr(self, "tabla_frame"):
            self._cargar_logs()

    def _crear_widgets(self):
        if not auditoria_controller.puede_acceder_auditoria():
            ctk.CTkLabel(
                self, text="Acceso denegado. Solo administradores.",
                font=ctk.CTkFont(size=16), text_color="red",
            ).pack(expand=True)
            return

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header, text="Registro de Auditoría",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(header, text="Solo lectura • ADMIN", font=ctk.CTkFont(size=11), text_color="#6B5B7B").pack(side="left", padx=8)

        from utils.ui_helpers import crear_boton_interactivo
        crear_boton_interactivo(header, text="📥 Exportar Excel", width=130, command=self._exportar_excel, fg_color="#7C3AED").pack(side="right", padx=5)
        crear_boton_interactivo(header, text="🔄 Actualizar", width=100, command=self._cargar_logs, fg_color="white", hover_color="#F3E8FF", text_color="#7C3AED").pack(side="right", padx=5)

        filtros = ctk.CTkFrame(self, fg_color="transparent")
        filtros.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filtros, text="Tabla:").pack(side="left", padx=(0, 5))
        self.combo_tabla = ctk.CTkComboBox(
            filtros, values=["", "usuario", "persona", "estudiante",
                             "matricula", "cuota", "pago", "producto",
                             "venta", "egreso", "tipo_uniforme", "movimiento_inventario"],
            width=180, command=self._filtrar_por_tabla,
        )
        self.combo_tabla.set("")
        self.combo_tabla.pack(side="left", padx=5)

        self.date_picker_inicio = DatePicker(filtros, label_text="Desde:")
        self.date_picker_inicio.pack(side="left", padx=(10, 5))

        self.date_picker_fin = DatePicker(filtros, label_text="Hasta:")
        self.date_picker_fin.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            filtros, text="Buscar", width=80,
            command=self._buscar_por_fecha,
        ).pack(side="left")

        self.tabla_frame = ctk.CTkScrollableFrame(self)
        self.tabla_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11))
        self.label_status.pack(pady=5)

    def _cargar_logs(self):
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()
        self._logs_actuales = auditoria_controller.consultar_logs(limit=100)
        logs = self._logs_actuales
        if not logs:
            ctk.CTkLabel(self.tabla_frame, text="No hay registros de auditoría", text_color="gray").pack(pady=20)
            ctk.CTkLabel(self.tabla_frame, text="Realiza una acción (crear estudiante, pago) y vuelve a Actualizar", text_color="#9CA3AF", font=ctk.CTkFont(size=11)).pack()
            self.label_status.configure(text="Total: 0 • Tip: usa filtros Tabla/Fecha")
            return
        self._renderizar_tabla(logs)

    def _renderizar_tabla(self, logs):
        from utils.ui_helpers import crear_card_interactiva
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()
        # Header más completo con valores
        header_row = ctk.CTkFrame(self.tabla_frame, fg_color="#3D1559")
        header_row.pack(fill="x", padx=2, pady=2)
        for text, width in [("Fecha", 125), ("Usuario", 110), ("Tabla", 95), ("Acción", 90), ("Registro", 60), ("Valor Anterior", 140), ("Valor Nuevo", 140), ("", 70)]:
            ctk.CTkLabel(header_row, text=text, width=width, font=ctk.CTkFont(size=11, weight="bold"), text_color="white").pack(side="left", padx=2)
        for log in logs:
            # Fase 7e: card estándar sin bordes (fin del rayado)
            row = crear_card_interactiva(self.tabla_frame)
            row.pack(fill="x", padx=2, pady=2)
            ctk.CTkLabel(row, text=log.get("fecha", "")[:19], width=125, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=self._nombre_usuario(log), width=110, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=log.get("tabla_afectada", ""), width=95, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            # color acción
            accion = log.get("accion", "")
            col_acc = {"INSERT": "#22C55E", "UPDATE": "#F59E0B", "DESACTIVACION": "#DC2626", "LOGIN": "#3B82F6"}.get(accion, "gray")
            ctk.CTkLabel(row, text=accion, width=90, font=ctk.CTkFont(size=11, weight="bold"), text_color=col_acc).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=str(log.get("id_registro", "")), width=60, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            # valores truncados, click para ver detalle
            ant = str(log.get("valor_anterior") or "")[:28]
            nuevo = str(log.get("valor_nuevo") or "")[:28]
            ctk.CTkLabel(row, text=ant or "—", width=160, font=ctk.CTkFont(size=10), text_color="#6B5B7B").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=nuevo or "—", width=160, font=ctk.CTkFont(size=10), text_color="#1F0A33").pack(side="left", padx=2)
            ctk.CTkButton(row, text="Ver", width=60, height=26, fg_color="#F3E8FF", text_color="#7C3AED", hover_color="#DDD6E5", command=lambda l=log: self._ver_detalle(l)).pack(side="left", padx=2)
        self.label_status.configure(text=f"Mostrando {len(logs)} registro(s) • Click Ver para detalle completo • Exportar para Excel")
        # cache para export
        self._logs_actuales = logs

    def _filtrar_por_tabla(self, tabla):
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        if not tabla:
            self._cargar_logs()
            return

        logs = auditoria_controller.filtrar_por_tabla(tabla)
        self._mostrar_logs(logs)

    def _buscar_por_fecha(self):
        fecha_inicio = self.date_picker_inicio.get()
        fecha_fin = self.date_picker_fin.get()

        if not fecha_inicio or not fecha_fin:
            return

        for widget in self.tabla_frame.winfo_children():
            widget.destroy()

        logs = auditoria_controller.filtrar_por_fecha(fecha_inicio, fecha_fin)
        self._mostrar_logs(logs)

    def _mostrar_logs(self, logs):
        self._logs_actuales = logs
        self._renderizar_tabla(logs)

    @staticmethod
    def _nombre_usuario(log) -> str:
        uname = (log.get("username") or "").strip()
        if uname:
            nom = (log.get("usuario_nombre") or "").strip()
            return f"{uname} ({nom})" if nom else uname
        return f"sistema (id={log.get('id_usuario', '?')})"

    def _ver_detalle(self, log):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Auditoría #{log.get('id_log', log.get('id_registro',''))}")
        dialog.geometry("520x380")
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=f"{log.get('tabla_afectada','')} • {log.get('accion','')} • {log.get('fecha','')}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3D1559").pack(pady=(15,5))
        info = ctk.CTkFrame(dialog, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=5)
        row_u = ctk.CTkFrame(info, fg_color="transparent")
        row_u.pack(fill="x", pady=2)
        ctk.CTkLabel(row_u, text="Usuario:", width=120, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(row_u, text=f"{self._nombre_usuario(log)}  [id={log.get('id_usuario','')}]", font=ctk.CTkFont(size=11), wraplength=350, justify="left").pack(side="left", fill="x", expand=True)
        for k in ["tabla_afectada","id_registro","accion","fecha"]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{k}:", width=120, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=str(log.get(k,"")), font=ctk.CTkFont(size=11), wraplength=350, justify="left").pack(side="left", fill="x", expand=True)
        for label, key in [("Valor Anterior", "valor_anterior"), ("Valor Nuevo", "valor_nuevo")]:
            ctk.CTkLabel(dialog, text=label+":", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(anchor="w", padx=15, pady=(8,0))
            txt = ctk.CTkTextbox(dialog, height=70)
            txt.pack(fill="x", padx=15, pady=2)
            txt.insert("1.0", str(log.get(key) or "—"))
            txt.configure(state="disabled")
        ctk.CTkButton(dialog, text="Cerrar", width=100, fg_color="gray", command=dialog.destroy).pack(pady=10)

    def _exportar_excel(self):
        if not hasattr(self, "_logs_actuales") or not self._logs_actuales:
            from tkinter import messagebox
            messagebox.showwarning("Exportar", "No hay registros para exportar. Actualiza o filtra primero.")
            return
        from tkinter import filedialog, messagebox
        from utils.excel_exporter import exportar_a_excel
        ruta = filedialog.asksaveasfilename(title="Guardar auditoría", defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")], initialfile="auditoria.xlsx")
        if not ruta:
            return
        datos = []
        for l in self._logs_actuales:
            datos.append({"fecha": l.get("fecha",""), "usuario": self._nombre_usuario(l), "tabla": l.get("tabla_afectada",""), "accion": l.get("accion",""), "registro": l.get("id_registro",""), "anterior": l.get("valor_anterior",""), "nuevo": l.get("valor_nuevo","")})
        cols = [("fecha","Fecha"),("usuario","Usuario"),("tabla","Tabla"),("accion","Acción"),("registro","Registro"),("anterior","Valor Anterior"),("nuevo","Valor Nuevo")]
        ok, msg = exportar_a_excel(datos, cols, "Auditoría", ruta)
        if ok:
            messagebox.showinfo("Exportar", msg)
        else:
            messagebox.showerror("Exportar", msg)
