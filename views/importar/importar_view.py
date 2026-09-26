import customtkinter as ctk
from tkinter import filedialog, messagebox
from controllers import importar_controller


class ImportarView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._archivo_actual = None
        self._datos_cargados = []
        self._columnas_archivo = []
        self._mapeo_actual = {}
        if not importar_controller.puede_acceder():
            ctk.CTkLabel(
                self, text="Acceso denegado. Solo administradores.",
                font=ctk.CTkFont(size=16), text_color="red",
            ).pack(expand=True)
            return
        self._crear_widgets()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_seleccion = self.tabview.add("Seleccionar Archivo")
        self.tab_vista_previa = self.tabview.add("Vista Previa")
        self.tab_mapeo = self.tabview.add("Mapeo de Columnas")
        self.tab_resultados = self.tabview.add("Resultados")

        self._crear_tab_seleccion()
        self._crear_tab_vista_previa()
        self._crear_tab_mapeo()
        self._crear_tab_resultados()

    def _crear_tab_seleccion(self):
        header = ctk.CTkFrame(self.tab_seleccion, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Importar Datos desde Archivo",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        info_frame = ctk.CTkFrame(self.tab_seleccion, fg_color="#f0f0f0", corner_radius=8)
        info_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            info_frame, text="Formatos soportados: CSV, XLSX",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            info_frame,
            text="Estudiantes: DNI, Nombres, Apellidos (+ apoderado opcional).\n"
                 "Tienda: PRODUCTOS, CANTIDAD, COSTO TOTAL, COSTO VENTA, YAPE, "
                 "EFECTIVO, CANTIDAD VENDIDO, QUEDAN.",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        self._tipo_importacion = "Estudiantes"
        self.seg_tipo = ctk.CTkSegmentedButton(
            info_frame, values=["Estudiantes", "Tienda"],
            command=self._on_tipo_cambiar,
        )
        try:
            self.seg_tipo.set("Estudiantes")
        except Exception:
            pass
        self.seg_tipo.pack(anchor="w", padx=10, pady=(0, 10))

        file_frame = ctk.CTkFrame(self.tab_seleccion, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=10)

        self.entry_ruta = ctk.CTkEntry(
            file_frame, placeholder_text="Seleccione un archivo CSV o XLSX...",
            width=500, state="disabled",
        )
        self.entry_ruta.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            file_frame, text="Examinar...", width=120,
            command=self._seleccionar_archivo,
        ).pack(side="left")

        self.btn_cargar = ctk.CTkButton(
            file_frame, text="Cargar Archivo", width=140,
            command=self._cargar_archivo, state="disabled",
        )
        self.btn_cargar.pack(side="left", padx=10)

        self.hoja_frame = ctk.CTkFrame(self.tab_seleccion, fg_color="transparent")
        self.hoja_frame.pack(fill="x", padx=10, pady=5)
        self.hoja_frame.pack_forget()

        ctk.CTkLabel(
            self.hoja_frame, text="Hoja:",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 5))

        self.combo_hoja = ctk.CTkComboBox(
            self.hoja_frame, values=[""], width=200,
            command=self._on_hoja_cambiar,
        )
        self.combo_hoja.pack(side="left")

        self.label_estado = ctk.CTkLabel(
            self.tab_seleccion, text="",
            font=ctk.CTkFont(size=11),
        )
        self.label_estado.pack(pady=10)

    def _crear_tab_vista_previa(self):
        header = ctk.CTkFrame(self.tab_vista_previa, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Vista Previa de Datos",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        self.label_info_previa = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=12),
        )
        self.label_info_previa.pack(side="right")

        self.scroll_preview = ctk.CTkScrollableFrame(self.tab_vista_previa)
        self.scroll_preview.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_preview = ctk.CTkLabel(
            self.scroll_preview, text="Cargue un archivo para ver la vista previa",
            font=ctk.CTkFont(size=12),
        )
        self.label_preview.pack(anchor="w", padx=5, pady=5)

    def _crear_tab_mapeo(self):
        header = ctk.CTkFrame(self.tab_mapeo, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Mapeo de Columnas",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Asocie las columnas del archivo con los campos del sistema",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
        ).pack(side="left", padx=10)

        self.scroll_mapeo = ctk.CTkScrollableFrame(self.tab_mapeo)
        self.scroll_mapeo.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_mapeo = ctk.CTkLabel(
            self.scroll_mapeo,
            text="Cargue un archivo primero para configurar el mapeo",
            font=ctk.CTkFont(size=12),
        )
        self.label_mapeo.pack(anchor="w", padx=5, pady=5)

    def _crear_tab_resultados(self):
        header = ctk.CTkFrame(self.tab_resultados, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Resultados de la Importación",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        self.btn_importar = ctk.CTkButton(
            header, text="Ejecutar Importación", width=180,
            command=self._ejecutar_importacion, state="disabled",
        )
        self.btn_importar.pack(side="right")

        self.scroll_resultados = ctk.CTkScrollableFrame(self.tab_resultados)
        self.scroll_resultados.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_resultados = ctk.CTkLabel(
            self.scroll_resultados, text="",
            font=ctk.CTkFont(size=12),
        )
        self.label_resultados.pack(anchor="w", padx=5, pady=5)

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo para importar",
            filetypes=[
                ("Archivos soportados", "*.csv *.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not ruta:
            return

        self._archivo_actual = ruta
        self.entry_ruta.configure(state="normal")
        self.entry_ruta.delete(0, "end")
        self.entry_ruta.insert(0, ruta)
        self.entry_ruta.configure(state="disabled")

        self.btn_cargar.configure(state="normal")
        self.label_estado.configure(text="Archivo seleccionado. Presione 'Cargar Archivo'.", text_color="#333333")

        extension = ruta.rsplit(".", 1)[-1].lower() if "." in ruta else ""
        if extension in ("xlsx", "xls"):
            self._cargar_hojas(ruta)
        else:
            self.hoja_frame.pack_forget()

    def _cargar_hojas(self, ruta: str):
        exito, msg, hojas = importar_controller.obtener_hojas(ruta)
        if exito and hojas:
            self.hoja_frame.pack(fill="x", padx=10, pady=5)
            self.combo_hoja.configure(values=hojas)
            self.combo_hoja.set(hojas[0])
        else:
            self.hoja_frame.pack_forget()

    def _on_tipo_cambiar(self, seleccion):
        self._tipo_importacion = seleccion
        if self._datos_cargados:
            self._configurar_mapeo()

    def _on_hoja_cambiar(self, seleccion):
        if self._archivo_actual:
            self._cargar_archivo()

    def _cargar_archivo(self):
        if not self._archivo_actual:
            return

        self.label_estado.configure(text="Cargando archivo...", text_color="#333333")
        self.update_idletasks()

        hoja = None
        extension = self._archivo_actual.rsplit(".", 1)[-1].lower() if "." in self._archivo_actual else ""
        if extension in ("xlsx", "xls"):
            hoja = self.combo_hoja.get()

        exito, msg, datos = importar_controller.cargar_archivo(self._archivo_actual, hoja)

        if not exito:
            self.label_estado.configure(text=f"Error: {msg}", text_color="#DC2626")
            messagebox.showerror("Error", msg)
            return

        self._datos_cargados = datos
        self.label_estado.configure(
            text=f"Archivo cargado: {len(datos)} registros",
            text_color="#22C55E",
        )

        self._mostrar_vista_previa()
        self._configurar_mapeo()
        self.btn_importar.configure(state="normal")

    def _mostrar_vista_previa(self):
        for widget in self.scroll_preview.winfo_children():
            widget.destroy()

        if not self._datos_cargados:
            return

        self.label_info_previa.configure(text=f"Mostrando {min(10, len(self._datos_cargados))} de {len(self._datos_cargados)} registros")

        primer_fila = self._datos_cargados[0]
        columnas = list(primer_fila.keys())

        tabla = ctk.CTkFrame(self.scroll_preview, fg_color="transparent")
        tabla.pack(fill="x", padx=5, pady=5)

        for col_idx, col in enumerate(columnas):
            header_label = ctk.CTkLabel(
                tabla, text=col,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#7C3AED",
                text_color="#ffffff",
                corner_radius=4,
                width=120,
            )
            header_label.grid(row=0, column=col_idx, padx=1, pady=1, sticky="ew")

        for row_idx, fila in enumerate(self._datos_cargados[:10]):
            for col_idx, col in enumerate(columnas):
                valor = str(fila.get(col, ""))[:30]
                cell = ctk.CTkLabel(
                    tabla, text=valor,
                    font=ctk.CTkFont(size=10),
                    width=120,
                    anchor="w",
                )
                cell.grid(row=row_idx + 1, column=col_idx, padx=1, pady=1, sticky="ew")

        for col_idx in range(len(columnas)):
            tabla.columnconfigure(col_idx, weight=1)

    def _configurar_mapeo(self):
        for widget in self.scroll_mapeo.winfo_children():
            widget.destroy()

        if not self._datos_cargados:
            return

        self._columnas_archivo = list(self._datos_cargados[0].keys())
        tipo = getattr(self, "_tipo_importacion", "Estudiantes")
        campos_sistema = importar_controller.obtener_campos_sistema(tipo)
        campos_obligatorios = importar_controller.obtener_campos_obligatorios(tipo)

        self._mapeo_actual = {}

        instrucciones = ctk.CTkLabel(
            self.scroll_mapeo,
            text="Seleccione para cada columna del archivo el campo del sistema correspondiente.\n"
                 "Los campos obligatorios están marcados con *",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
        )
        instrucciones.pack(anchor="w", padx=5, pady=5)

        for col_archivo in self._columnas_archivo:
            row_frame = ctk.CTkFrame(self.scroll_mapeo, fg_color="#f8f8f8", corner_radius=6)
            row_frame.pack(fill="x", padx=5, pady=3)

            es_requerida = col_archivo.upper() in [c.upper() for c in campos_obligatorios]

            ctk.CTkLabel(
                row_frame, text=f"{col_archivo}{'*' if es_requerida else ''}",
                font=ctk.CTkFont(size=11, weight="bold" if es_requerida else "normal"),
                width=180, anchor="w",
            ).pack(side="left", padx=5)

            ctk.CTkLabel(
                row_frame, text="→",
                font=ctk.CTkFont(size=14),
            ).pack(side="left", padx=5)

            combo = ctk.CTkComboBox(
                row_frame,
                values=["(No importar)"] + campos_sistema,
                width=220,
            )

            sugerencia = self._sugerir_mapeo(col_archivo, campos_sistema)
            combo.set(sugerencia if sugerencia else "(No importar)")

            combo.pack(side="left", padx=5)
            self._mapeo_actual[col_archivo] = combo

    def _sugerir_mapeo(self, col_archivo: str, campos_sistema: list[str]) -> str:
        col_upper = col_archivo.upper().replace(" ", "_")

        equivalencias = {
            "DNI": "dni",
            "NOMBRES": "nombres",
            "APELLIDOS": "apellidos",
            "FECHA_NACIMIENTO": "fecha_nacimiento",
            "SEXO": "sexo",
            "TELEFONO": "telefono",
            "CORREO": "correo",
            "EMAIL": "correo",
            "TIPO_DOCUMENTO": "tipo_documento",
            "DIRECCION": "direccion",
            "DNI_APODERADO": "dni_apoderado",
            "NOMBRES_APODERADO": "nombres_apoderado",
            "APELLIDOS_APODERADO": "apellidos_apoderado",
            "PARENTESCO": "parentesco",
            "TELEFONO_APODERADO": "telefono_apoderado",
            "DIRECCION_APODERADO": "direccion_apoderado",
            "TIPO_DOCUMENTO_APODERADO": "tipo_documento_apoderado",
        }

        if col_upper in equivalencias:
            return equivalencias[col_upper]

        for campo_sistema in campos_sistema:
            if col_upper == campo_sistema.upper():
                return campo_sistema

        return ""

    def _ejecutar_importacion(self):
        if not self._datos_cargados:
            return

        mapeo = {}
        for col_archivo, combo in self._mapeo_actual.items():
            valor = combo.get()
            if valor and valor != "(No importar)":
                mapeo[col_archivo] = valor

        respuesta = messagebox.askyesno(
            "Confirmar Importación",
            f"Se importarán {len(self._datos_cargados)} registros.\n"
            f"¿Desea continuar?",
        )

        if not respuesta:
            return

        self.label_resultados.configure(text="Procesando importación...", text_color="#333333")
        self.update_idletasks()

        exito, msg, resultados = importar_controller.ejecutar_importacion(
            self._datos_cargados, mapeo,
            getattr(self, "_tipo_importacion", "Estudiantes"),
        )

        self._mostrar_resultados(exito, msg, resultados)

    def _mostrar_resultados(self, exito: bool, msg: str, resultados: dict):
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            ctk.CTkLabel(
                self.scroll_resultados, text=msg,
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=5, pady=5)
            return

        color = "#22C55E" if exito else "#DC2626"
        ctk.CTkLabel(
            self.scroll_resultados, text=msg,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=5, pady=5)

        stats_frame = ctk.CTkFrame(self.scroll_resultados, fg_color="#f0f0f0", corner_radius=8)
        stats_frame.pack(fill="x", padx=5, pady=10)

        stats = [
            ("Estudiantes creados", resultados.get("estudiantes_creados", 0)),
            ("Apoderados creados", resultados.get("apoderados_creados", 0)),
            ("Asociaciones creadas", resultados.get("asociaciones_creadas", 0)),
            ("Productos creados", resultados.get("productos_creados", 0)),
            ("Compras registradas", resultados.get("compras", 0)),
            ("Ventas registradas", resultados.get("ventas", 0)),
        ]
        stats = [(k, v) for k, v in stats if v]

        for label, valor in stats:
            row = ctk.CTkFrame(stats_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)

            ctk.CTkLabel(
                row, text=f"{label}:",
                font=ctk.CTkFont(size=11),
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=str(valor),
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

        errores = resultados.get("errores", [])
        detalles = resultados.get("detalles", [])

        if detalles:
            ctk.CTkLabel(
                self.scroll_resultados, text="Detalles:",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(anchor="w", padx=5, pady=(10, 5))

            scroll_detalles = ctk.CTkScrollableFrame(
                self.scroll_resultados, height=150,
            )
            scroll_detalles.pack(fill="x", padx=5, pady=5)

            for detalle in detalles[:50]:
                ctk.CTkLabel(
                    scroll_detalles, text=f"  {detalle}",
                    font=ctk.CTkFont(size=10),
                    text_color="#22C55E",
                ).pack(anchor="w", padx=5)

        if errores:
            ctk.CTkLabel(
                self.scroll_resultados, text="Errores:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#DC2626",
            ).pack(anchor="w", padx=5, pady=(10, 5))

            scroll_errores = ctk.CTkScrollableFrame(
                self.scroll_resultados, height=150,
            )
            scroll_errores.pack(fill="x", padx=5, pady=5)

            for error in errores[:50]:
                ctk.CTkLabel(
                    scroll_errores, text=f"  {error}",
                    font=ctk.CTkFont(size=10),
                    text_color="#DC2626",
                ).pack(anchor="w", padx=5)
