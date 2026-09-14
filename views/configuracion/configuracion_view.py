import customtkinter as ctk
from tkinter import messagebox
from controllers import configuracion_controller, categoria_controller
from utils.dates import calculate_age


class ConfiguracionView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        self._cargar_configuracion()

    def _crear_widgets(self):
        if not configuracion_controller.puede_acceder():
            ctk.CTkLabel(
                self, text="Acceso denegado. Solo administradores.",
                font=ctk.CTkFont(size=16), text_color="red",
            ).pack(expand=True)
            return

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header, text="Configuración del Sistema",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        self.contenido = ctk.CTkScrollableFrame(self)
        self.contenido.pack(fill="both", expand=True, padx=15, pady=5)

    # ── Helpers UI ordenada y explicada (sin hover para evitar glitch) ──
    def _seccion(self, titulo, icono, descripcion, nro):
        sec = ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=8)
        sec.pack(fill="x", padx=5, pady=5)
        head = ctk.CTkFrame(sec, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(head, text=f"{nro}. {icono}  {titulo}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3D1559").pack(side="left")
        ctk.CTkLabel(head, text="ADMIN", font=ctk.CTkFont(size=10), text_color="white", fg_color="#7C3AED", corner_radius=6, width=50).pack(side="right")
        # descripción sin wraplength grande para evitar sobrepuesto
        desc = ctk.CTkLabel(sec, text=descripcion, font=ctk.CTkFont(size=11), text_color="#6B5B7B", justify="left", wraplength=650)
        desc.pack(anchor="w", padx=10, pady=(0, 6))
        return sec

    def _nota(self, parent, texto):
        lbl = ctk.CTkLabel(parent, text=f"ℹ {texto}", font=ctk.CTkFont(size=11), text_color="#6B5B7B", justify="left", wraplength=620)
        lbl.pack(anchor="w", padx=10, pady=2)

    def _cargar_configuracion(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

        config = configuracion_controller.obtener_configuracion()
        if not config:
            ctk.CTkLabel(self.contenido, text="Error: No se pudo cargar la configuración", text_color="red").pack(pady=20)
            return

        self.entries = {}

        # 1 — General
        sec1 = self._seccion("Información General", "🏫", "Datos que aparecen en reportes y encabezados. No afecta cálculos.", 1)
        self._crear_campo(sec1, "nombre_academia", "Nombre de la Academia", config.get("nombre_academia", ""), help="Ej: Roncalli — se imprime en Excel")
        self._crear_campo(sec1, "direccion", "Dirección", config.get("direccion", ""), help="Opcional, para reportes")
        self._crear_campo(sec1, "telefono", "Teléfono", config.get("telefono", ""), help="Contacto en reportes")
        self._crear_campo(sec1, "correo", "Correo", config.get("correo", ""), help="Contacto")
        self._nota(sec1, "Tip: cambia el nombre aquí y se refleja en Dashboard y reportes sin tocar código.")

        # 2 — Precios (v2.2: viven en Tarifas, no aquí)
        sec2 = self._seccion("Precios y Tarifas", "💰", "Los cobros viven en el módulo Tarifas (mensualidades por edad, inscripción, reingreso, campeonatos por división). Lo que elegías aquí se migró a tarifas automáticamente.", 2)
        self._nota(sec2, "Inscripción = solo nuevos (incluye 1 camiseta y descuenta stock). Mensualidad = solo antiguos. Reingreso = con uniforme anterior (más barato).")
        self._nota(sec2, "Egresos PROFESOR/ARBITRAJE sugieren el monto por defecto al registrar, pero cada caso se edita (no todos cobran igual).")
        self._nota(sec2, "Ver y editar precios en el menú lateral SISTEMA → Tarifas.")

        # 3 — Mora
        sec3 = self._seccion("Mora y Vencimientos", "⏰", "Cómo se penaliza la cuota vencida y cuándo avisa 'por vencer'.", 3)
        self.mora_switch = ctk.CTkSwitch(sec3, text="Habilitar mora (aplica al vencer la cuota)")
        self.mora_switch.pack(anchor="w", padx=10, pady=5)
        if config.get("mora_habilitada", 0):
            self.mora_switch.select()
        self._crear_campo(sec3, "porcentaje_mora", "Porcentaje de mora (%)", str(config.get("porcentaje_mora", 0)), help="Ej 5 = +5% sobre saldo al vencer")
        self._nota(sec3, "Si está deshabilitada, la cuota solo cambia a VENCIDO sin recargo.")

        # 4 — Cuotas y becas
        sec4 = self._seccion("Cuotas y Becas", "📅", "Reglas de generación de cuotas y descuentos.", 4)
        self._crear_campo(sec4, "dias_por_vencer", "Días por vencer (alerta)", str(config.get("dias_por_vencer", 3)), help="Dashboard avisa cuotas que vencen en ≤ N días")
        self.becas_switch = ctk.CTkSwitch(sec4, text="Permitir múltiples becas por matrícula")
        self.becas_switch.pack(anchor="w", padx=10, pady=5)
        if config.get("permitir_multiples_becas", 1):
            self.becas_switch.select()
        self._nota(sec4, "Beca = PORCENTAJE o MONTO_FIJO; si deshabilitas, solo 1 beca por matrícula.")

        # 5 — Actualizaciones (nuevo, documenta Setup UAC)
        sec_upd = self._seccion("Actualizaciones", "🔄", "Instalación única vía Setup; luego el sistema se actualiza solo. En Program Files usará instalador silencioso (pedirá UAC), en portable usará ZIP sin permisos.", 5)
        try:
            from utils.constants import __version__
            from updater import update_service as us
            ver = __version__
            en_pf = us.es_instalacion_programfiles()
            tipo_inst = "Program Files (Setup)" if en_pf else "Portable ZIP"
            ctk.CTkLabel(sec_upd, text=f"Versión actual: v{ver}  •  Instalación: {tipo_inst}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=2)
            if en_pf:
                ctk.CTkLabel(sec_upd, text="⚠ Actualizar desde Program Files pedirá permiso de Administrador (UAC) — es normal. La app se cerrará y el instalador hará el resto.", font=ctk.CTkFont(size=11), text_color="#DC2626", wraplength=620, justify="left").pack(anchor="w", padx=10, pady=2)
            else:
                ctk.CTkLabel(sec_upd, text="Actualización sin permisos: usará ZIP y no pedirá UAC.", font=ctk.CTkFont(size=11), text_color="#6B5B7B", wraplength=620).pack(anchor="w", padx=10, pady=2)
            from utils.ui_helpers import crear_boton_interactivo as btn_upd
            btn_upd(sec_upd, text="🔍 Buscar actualizaciones ahora", width=220, command=self._buscar_actualizaciones, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=6)
            self._nota(sec_upd, "Botón fuerza verificación ignorando 24h. Si hay nueva versión, aparece ventana con progreso MB/s y ETA. En Program Files elegirá Setup silencioso; en portable, ZIP.")
            self._nota(sec_upd, "Flujo ideal: instalar una vez con Setup y luego solo Actualizar — sin reemplazo manual.")
        except Exception as e:
            ctk.CTkLabel(sec_upd, text=f"No se pudo cargar updater: {e}", text_color="gray").pack(anchor="w", padx=10)

        # 6 — Backup / OneDrive + Restore (ahora nro 6)
        sec5 = self._seccion("Respaldo y OneDrive", "💾", "Dónde y cada cuánto se guarda la BD central. Restaurar requiere PIN.", 6)
        self.backup_switch = ctk.CTkSwitch(sec5, text="Backup automático (cada 6h verifica)")
        self.backup_switch.pack(anchor="w", padx=10, pady=5)
        if config.get("backup_automatico", 1):
            self.backup_switch.select()
        self._crear_campo(sec5, "frecuencia_backup", "Frecuencia (días)", str(config.get("frecuencia_backup", 7)), help="Si 7, crea backup si pasaron ≥7 días sin uno")
        self._crear_campo(sec5, "ruta_backup", "Ruta de backup", config.get("ruta_backup", "backups/"), help="Recomendado: carpeta compartida (ej. \\\\SERVIDOR\\AcademiaDatos\\BackupsAcademia)")
        from utils.ui_helpers import crear_boton_interactivo as _btn_path
        _btn_path(sec5, text="📁 Examinar…", width=130, command=self._elegir_ruta_backup, fg_color="#E5E7EB", hover_color="#DDD6E5", text_color="#1F0A33").pack(anchor="w", padx=10, pady=(0, 4))
        self._crear_campo(sec5, "correo_onedrive", "Correo contacto (opcional)", config.get("correo_onedrive", ""), help="Solo referencia del responsable")
        # BD en red (separado de entries: vive en config.ini, no en tabla CONFIGURACION)
        try:
            from utils.constants import DB_PATH
            _ruta_bd_actual = DB_PATH
        except Exception:
            _ruta_bd_actual = ""
        _frame_bd = ctk.CTkFrame(sec5, fg_color="transparent")
        _frame_bd.pack(fill="x", padx=10, pady=(6, 3))
        ctk.CTkLabel(_frame_bd, text="Base de datos en uso:", width=200, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.entry_ruta_bd = ctk.CTkEntry(_frame_bd, width=260, border_width=1, border_color="#E5E7EB",
                                           placeholder_text="\\\\SERVIDOR\\AcademiaDatos\\academia.db")
        self.entry_ruta_bd.insert(0, _ruta_bd_actual)
        ctk.CTkLabel(sec5, text="↳ Ej: \\\\192.168.1.50\\AcademiaDatos\\academia.db — la misma en las 4 PCs.", font=ctk.CTkFont(size=10), text_color="#9CA3AF", justify="left", wraplength=600).pack(anchor="w", padx=10, pady=(0,2))
        self.entry_ruta_bd.pack(side="left", padx=5)
        ctk.CTkLabel(sec5, text="↳ En red: \\\\SERVIDOR\\Academia\\academia.db (todas las PCs igual). Cambiar requiere reiniciar.", font=ctk.CTkFont(size=10), text_color="#9CA3AF", justify="left", wraplength=600).pack(anchor="w", padx=10, pady=(0,2))
        _btns_bd = ctk.CTkFrame(sec5, fg_color="transparent")
        _btns_bd.pack(fill="x", padx=10, pady=(0, 4))
        _btn_path(_btns_bd, text="📁 Examinar…", width=130, command=self._elegir_ruta_bd, fg_color="#E5E7EB", hover_color="#DDD6E5", text_color="#1F0A33").pack(side="left", padx=(0, 5))
        _btn_path(_btns_bd, text="🔌 Probar conexión", width=150, command=self._probar_conexion_bd, fg_color="#7C3AED", hover_color="#6D28D9", text_color="white").pack(side="left", padx=5)
        _btn_path(_btns_bd, text="💾 Guardar ruta", width=130, command=self._guardar_ruta_bd, fg_color="#22C55E", hover_color="#16A34A", text_color="white").pack(side="left", padx=5)
        self.label_bd_status = ctk.CTkLabel(sec5, text="", font=ctk.CTkFont(size=11), justify="left", wraplength=600)
        self.label_bd_status.pack(anchor="w", padx=10, pady=2)
        try:
            from database.connection import estado_bd
            _st = estado_bd()
            _tam = f"{_st['bytes']/1048576:.1f}MB" if _st["bytes"] else "—"
            _modo = "RED compartida" if _st["es_red"] else "local"
            self._nota(sec5, f"Estado actual: {_modo} • accesible: {'SÍ' if _st['accesible'] else 'NO'} • journal: {_st['journal']} • tamaño: {_tam}")
        except Exception:
            pass
        self._nota(sec5, "Botón Respaldo en sidebar crea backup manual en la carpeta configurada inmediatamente.")
        self._nota(sec5, "Restaurar sobreescribe academia.db actual — requiere reiniciar la app. Hora muestra (UTC-5).")
        # Lista backups + restaurar/verificar/rotar
        try:
            from controllers import configuracion_controller as cc
            backups = cc.listar_backups()
            if backups:
                ctk.CTkLabel(sec5, text=f"Backups recientes ({len(backups)}):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(8,2))
                for b in backups[:5]:
                    row = ctk.CTkFrame(sec5, fg_color="#F8F5FA", corner_radius=6)
                    row.pack(fill="x", padx=10, pady=1)
                    ctk.CTkLabel(row, text=f"{b['fecha']}  {b['tamano_mb']}MB  {b['hash']}", font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
                    ctk.CTkButton(row, text="Verificar", width=70, height=24, fg_color="#E5E7EB", text_color="#1F0A33", hover_color="#DDD6E5", command=lambda p=b['ruta']: self._verificar_backup(p)).pack(side="right", padx=2)
                    ctk.CTkButton(row, text="Restaurar", width=70, height=24, fg_color="#DC2626", hover_color="#B91C1C", command=lambda p=b['ruta']: self._restaurar_backup(p)).pack(side="right", padx=2)
                if len(backups) > 5:
                    ctk.CTkLabel(sec5, text=f"+ {len(backups)-5} más", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10)
                ctk.CTkButton(sec5, text="Rotar >30 días", width=120, height=28, fg_color="gray", command=self._rotar_backups).pack(anchor="w", padx=10, pady=4)
            else:
                ctk.CTkLabel(sec5, text="No hay backups aún", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        except Exception:
            pass

        # 7 — Categorías edad
        sec6 = self._seccion("Categorías de Edad", "👥", "Rangos que asignan tarifa sugerida por edad.", 7)
        self._cargar_categorias(sec6)
        from utils.ui_helpers import crear_boton_interactivo
        crear_boton_interactivo(sec6, text="+ Nueva Categoría", width=150, command=self._nueva_categoria, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=5)

        # 8 — Tipos uniforme
        sec7 = self._seccion("Tipos de Uniforme", "👕", "Amplía tipos sin código. Cada tipo → producto con stock y precio_venta.", 8)
        self._cargar_tipos_uniforme(sec7)
        crear_boton_interactivo(sec7, text="+ Nuevo Tipo Uniforme", width=180, command=self._nuevo_tipo_uniforme, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=5)

        # 8b — Conceptos flexibles (RN-052 sin redundancia)
        sec7b = self._seccion("Conceptos Flexibles (bundles con ítems)", "🏷", "Crea paquetes con título, precio y productos incluidos. Si eliges concepto en Matrícula, su monto precede a tarifa/monto pactado y descuenta stock de cada ítem. Sin duplicar configuracion.precio_*.", 9)
        self._cargar_conceptos(sec7b)
        crear_boton_interactivo(sec7b, text="+ Nuevo Concepto", width=160, command=self._nuevo_concepto, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=5)

        # 10 — Apariencia Visual (nuevo, ordenado y explicado)
        sec8 = self._seccion("Apariencia Visual", "🎨", "Ajusta tamaño de letra, colores y fuente. Se guarda local y aplica al reiniciar.", 10)
        vis_frame = ctk.CTkFrame(sec8, fg_color="transparent")
        vis_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(vis_frame, text="Tamaño de letra:", width=160, anchor="w").pack(side="left")
        self.combo_font_scale = ctk.CTkComboBox(vis_frame, width=160, values=["Pequeña", "Mediana (default)", "Grande", "Extra grande"])
        self.combo_font_scale.set(self._cargar_visual("font_scale", "Mediana (default)"))
        self.combo_font_scale.pack(side="left", padx=5)
        ctk.CTkLabel(vis_frame, text="↳ Pequeña 0.9x, Grande 1.15x", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(side="left", padx=5)

        vis2 = ctk.CTkFrame(sec8, fg_color="transparent")
        vis2.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(vis2, text="Tema color:", width=160, anchor="w").pack(side="left")
        self.combo_tema = ctk.CTkComboBox(vis2, width=160, values=["Morado Roncalli", "Azul", "Verde"])
        self.combo_tema.set(self._cargar_visual("tema", "Morado Roncalli"))
        self.combo_tema.pack(side="left", padx=5)
        ctk.CTkLabel(vis2, text="↳ Cambia cabeceras y botones", font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(side="left", padx=5)

        vis3 = ctk.CTkFrame(sec8, fg_color="transparent")
        vis3.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(vis3, text="Fuente:", width=160, anchor="w").pack(side="left")
        self.combo_fuente = ctk.CTkComboBox(vis3, width=160, values=["Normal", "Grande (accesible)"])
        self.combo_fuente.set(self._cargar_visual("fuente", "Normal"))
        self.combo_fuente.pack(side="left", padx=5)
        ctk.CTkButton(vis3, text="Aplicar vista previa", width=140, height=28, fg_color="#6B21A8", command=self._aplicar_visual).pack(side="left", padx=10)
        self._nota(sec8, "Tip: Usa Grande si la letra se ve pequeña. Se guarda en config_visual.json y aplica al reiniciar.")

        # Guardar fijo abajo
        btn_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=12)
        st = ctk.CTkLabel(btn_frame, text="💡 Cambios se aplican al guardar, sin reiniciar. Precios afectan solo nuevas operaciones.", text_color="#6B5B7B", font=ctk.CTkFont(size=11))
        st.pack(side="left", padx=5)
        from utils.ui_helpers import crear_boton_interactivo as btn2
        btn2(btn_frame, text="💾 Guardar Cambios", width=160, height=36, command=self._guardar, fg_color="#22C55E").pack(side="right")

    def _crear_campo(self, parent, key, label, valor, help=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label, width=200, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        entry = ctk.CTkEntry(frame, width=260, border_width=1, border_color="#E5E7EB")
        entry.insert(0, str(valor))
        entry.pack(side="left", padx=5)
        self.entries[key] = entry
        if help:
            ctk.CTkLabel(parent, text=f"↳ {help}", font=ctk.CTkFont(size=10), text_color="#9CA3AF", justify="left", wraplength=600).pack(anchor="w", padx=10, pady=(0,2))

    def _cargar_visual(self, clave, defecto):
        try:
            import json, os
            from utils.constants import CONFIG_VISUAL_PATH
            path = CONFIG_VISUAL_PATH
            if os.path.isfile(path):
                import json as js
                with open(path, "r", encoding="utf-8") as f:
                    data = js.load(f)
                    return data.get(clave, defecto)
        except Exception:
            pass
        return defecto

    def _guardar_visual(self):
        try:
            import json, os
            from utils.constants import CONFIG_VISUAL_PATH
            path = CONFIG_VISUAL_PATH
            data = {}
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["font_scale"] = self.combo_font_scale.get()
            data["tema"] = self.combo_tema.get()
            data["fuente"] = self.combo_fuente.get()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            from utils.logger import logger
            logger.warning(f"No se pudo guardar visual: {e}")

    def _aplicar_visual(self):
        escala = {"Pequeña": 0.9, "Mediana (default)": 1.0, "Grande": 1.15, "Extra grande": 1.3}
        sel = self.combo_font_scale.get()
        factor = escala.get(sel, 1.0)
        try:
            import customtkinter as ctk
            ctk.set_widget_scaling(factor)
            ctk.set_window_scaling(factor)
            messagebox.showinfo("Vista previa", f"Escala {sel} ({factor}x) aplicada.\nGuarda para que quede al reiniciar.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _guardar(self):
        # guardar visual primero
        self._guardar_visual()
        data = {}
        for key, entry in self.entries.items():
            valor = entry.get().strip()
            if key in ("dias_por_vencer", "frecuencia_backup"):
                try:
                    data[key] = int(valor)
                except ValueError:
                    messagebox.showerror("Error", f"{key} debe ser un número entero")
                    return
            elif key in ("porcentaje_mora", "precio_inscripcion", "precio_mensualidad", "precio_reingreso", "precio_uniforme", "tasa_campeonato", "arbitraje_por_equipo", "pago_profesor"):
                try:
                    data[key] = float(valor)
                except ValueError:
                    messagebox.showerror("Error", f"{key} debe ser un número")
                    return
            else:
                data[key] = valor

        data["mora_habilitada"] = 1 if self.mora_switch.get() else 0
        data["permitir_multiples_becas"] = 1 if self.becas_switch.get() else 0
        data["backup_automatico"] = 1 if self.backup_switch.get() else 0

        exito, msg = configuracion_controller.actualizar_configuracion(data)
        if exito:
            messagebox.showinfo("Éxito", msg + "\n\nVisual guardado. Reinicia para aplicar fuente/tamaño.")
        else:
            messagebox.showerror("Error", msg)

    def _elegir_ruta_bd(self):
        from tkinter import filedialog
        actual = ""
        try:
            actual = self.entry_ruta_bd.get().strip()
        except Exception:
            pass
        import os
        sel = filedialog.askopenfilename(
            title="Elegir base de datos (academia.db)",
            initialdir=os.path.dirname(actual) or None,
            filetypes=[("Base de datos", "*.db"), ("Todos", "*.*")],
        )
        if sel:
            try:
                self.entry_ruta_bd.delete(0, "end")
                self.entry_ruta_bd.insert(0, sel)
            except Exception:
                pass

    @staticmethod
    def _probar_ruta_bd(ruta: str) -> tuple[bool, str]:
        import os
        import sqlite3
        import time
        if not ruta:
            return False, "Ruta vacía"
        padre = os.path.dirname(os.path.abspath(ruta))
        if not os.path.isdir(padre):
            return False, f"No se accede a la carpeta: {padre} (¿servidor apagado o sin red?)"
        t0 = time.monotonic()
        try:
            conn = sqlite3.connect(ruta, timeout=5)
            try:
                conn.execute("SELECT 1")
                jm = conn.execute("PRAGMA journal_mode").fetchone()
                ms = int((time.monotonic() - t0) * 1000)
                return True, f"OK en {ms}ms (journal: {jm[0] if jm else '?'})"
            finally:
                conn.close()
        except Exception as e:
            return False, f"No se pudo abrir: {e}"

    def _probar_conexion_bd(self):
        try:
            ruta = self.entry_ruta_bd.get().strip()
        except Exception:
            ruta = ""
        ok, msg = self._probar_ruta_bd(ruta)
        try:
            self.label_bd_status.configure(text=("✅ " if ok else "❌ ") + msg,
                                           text_color="green" if ok else "red")
        except Exception:
            pass

    def _guardar_ruta_bd(self):
        import os
        from tkinter import messagebox
        try:
            ruta = self.entry_ruta_bd.get().strip()
        except Exception:
            ruta = ""
        if not ruta:
            messagebox.showwarning("Ruta BD", "Ruta vacía")
            return
        ok, msg = self._probar_ruta_bd(ruta)
        if not ok:
            messagebox.showerror("Ruta BD", f"No se guardó: {msg}")
            try:
                self.label_bd_status.configure(text="❌ " + msg, text_color="red")
            except Exception:
                pass
            return
        try:
            import configparser
            from utils.constants import APP_DIR
            ini = os.path.join(APP_DIR, "config.ini")
            cp = configparser.ConfigParser()
            if os.path.isfile(ini):
                cp.read(ini, encoding="utf-8")
            if not cp.has_section("database"):
                cp.add_section("database")
            cp.set("database", "path", ruta)
            with open(ini, "w", encoding="utf-8") as f:
                cp.write(f)
            messagebox.showinfo("Ruta BD", f"Guardada en config.ini.\n\nReinicia la app para usar:\n{ruta}")
            try:
                self.label_bd_status.configure(text="✅ Guardada. Reinicia la app.", text_color="green")
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Ruta BD", f"No se pudo escribir config.ini: {e}")

    def _elegir_ruta_backup(self):
        from tkinter import filedialog
        actual = ""
        try:
            actual = self.entries["ruta_backup"].get().strip()
        except Exception:
            pass
        sel = filedialog.askdirectory(title="Elegir carpeta de backups", initialdir=actual or None)
        if sel:
            try:
                self.entries["ruta_backup"].delete(0, "end")
                self.entries["ruta_backup"].insert(0, sel)
            except Exception:
                pass

    def _cargar_categorias(self, parent):
        cats = categoria_controller.listar_categorias()
        if not cats:
            ctk.CTkLabel(parent, text="No hay categorías — crea la primera con + Nueva", text_color="gray").pack(anchor="w", padx=10, pady=3)
            return
        for cat in cats:
            row = ctk.CTkFrame(parent, fg_color="#F8F5FA", corner_radius=8)
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=f"{cat['nombre']}", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10, pady=6)
            tipo = cat.get("tipo", "ACADEMIA") or "ACADEMIA"
            if tipo == "ACADEMIA" and cat.get("edad_min") is not None:
                detalle = f"Edad {cat['edad_min']}-{cat['edad_max']} años"
            else:
                detalle = f"[{tipo}] sin rango de edad"
            ctk.CTkLabel(row, text=detalle, font=ctk.CTkFont(size=12), text_color="#6B5B7B").pack(side="left", padx=10)
            ctk.CTkButton(row, text="Editar", width=70, height=28, command=lambda c=cat: self._editar_categoria(c)).pack(side="right", padx=2, pady=4)
            ctk.CTkButton(row, text="Desactivar", width=85, height=28, fg_color="#d9534f", command=lambda c=cat: self._desactivar_categoria(c)).pack(side="right", padx=2, pady=4)

    def _nueva_categoria(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Categoría")
        dialog.geometry("350x330")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nombre:").pack(anchor="w", padx=15, pady=(15, 2))
        entry_nombre = ctk.CTkEntry(dialog, width=300)
        entry_nombre.pack(padx=15)

        ctk.CTkLabel(dialog, text="Tipo:").pack(anchor="w", padx=15, pady=(10, 2))
        combo_tipo = ctk.CTkComboBox(dialog, width=300, values=["ACADEMIA", "CAMPEONATO", "SERVICIO"])
        combo_tipo.set("ACADEMIA")
        combo_tipo.pack(padx=15)
        ctk.CTkLabel(dialog, text="CAMPEONATO/SERVICIO no usan edad.", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=15)

        ctk.CTkLabel(dialog, text="Edad mínima (solo ACADEMIA):").pack(anchor="w", padx=15, pady=(10, 2))
        entry_min = ctk.CTkEntry(dialog, width=300)
        entry_min.pack(padx=15)

        ctk.CTkLabel(dialog, text="Edad máxima (solo ACADEMIA):").pack(anchor="w", padx=15, pady=(10, 2))
        entry_max = ctk.CTkEntry(dialog, width=300)
        entry_max.pack(padx=15)

        label_status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        label_status.pack(padx=15, pady=5)

        def guardar():
            label_status.configure(text="⏳ Guardando...", text_color="#7C3AED")
            dialog.update()
            nombre = entry_nombre.get().strip()
            edad_min = entry_min.get().strip() or None
            edad_max = entry_max.get().strip() or None

            exito, msg, _ = categoria_controller.crear_categoria({
                "nombre": nombre,
                "tipo": combo_tipo.get(),
                "edad_min": edad_min,
                "edad_max": edad_max,
            })
            if exito:
                label_status.configure(text="✅ Se guardó correctamente", text_color="green")
                dialog.after(400, dialog.destroy)
                self.after(500, self._cargar_configuracion)
            else:
                label_status.configure(text=f"❌ {msg}", text_color="red")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Cancelar", width=100, fg_color="gray", command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Guardar", width=120, command=guardar).pack(side="left", padx=5)

    def _editar_categoria(self, cat):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Categoría")
        dialog.geometry("350x330")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nombre:").pack(anchor="w", padx=15, pady=(15, 2))
        entry_nombre = ctk.CTkEntry(dialog, width=300)
        entry_nombre.insert(0, cat["nombre"])
        entry_nombre.pack(padx=15)

        ctk.CTkLabel(dialog, text="Tipo:").pack(anchor="w", padx=15, pady=(10, 2))
        combo_tipo = ctk.CTkComboBox(dialog, width=300, values=["ACADEMIA", "CAMPEONATO", "SERVICIO"])
        combo_tipo.set(cat.get("tipo", "ACADEMIA") or "ACADEMIA")
        combo_tipo.pack(padx=15)

        ctk.CTkLabel(dialog, text="Edad mínima (solo ACADEMIA):").pack(anchor="w", padx=15, pady=(10, 2))
        entry_min = ctk.CTkEntry(dialog, width=300)
        entry_min.insert(0, "" if cat.get("edad_min") is None else str(cat["edad_min"]))
        entry_min.pack(padx=15)

        ctk.CTkLabel(dialog, text="Edad máxima (solo ACADEMIA):").pack(anchor="w", padx=15, pady=(10, 2))
        entry_max = ctk.CTkEntry(dialog, width=300)
        entry_max.insert(0, "" if cat.get("edad_max") is None else str(cat["edad_max"]))
        entry_max.pack(padx=15)

        label_status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        label_status.pack(padx=15, pady=5)

        def guardar():
            label_status.configure(text="⏳ Guardando...", text_color="#7C3AED")
            dialog.update()
            exito, msg = categoria_controller.editar_categoria(cat["id_categoria"], {
                "nombre": entry_nombre.get().strip(),
                "tipo": combo_tipo.get(),
                "edad_min": entry_min.get().strip() or None,
                "edad_max": entry_max.get().strip() or None,
            })
            if exito:
                label_status.configure(text="✅ Se guardó correctamente", text_color="green")
                dialog.after(400, dialog.destroy)
                self.after(500, self._cargar_configuracion)
            else:
                label_status.configure(text=f"❌ {msg}", text_color="red")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Cancelar", width=100, fg_color="gray", command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Guardar", width=120, command=guardar).pack(side="left", padx=5)

    def _desactivar_categoria(self, cat):
        confirm = messagebox.askyesno(
            "Confirmar",
            f"¿Desactivar la categoría '{cat['nombre']}'?"
        )
        if confirm:
            exito, msg = categoria_controller.desactivar_categoria(cat["id_categoria"])
            if exito:
                self._cargar_configuracion()
            else:
                messagebox.showerror("Error", msg)

    def _cargar_tipos_uniforme(self, parent):
        try:
            from controllers import tipo_uniforme_controller
            tipos = tipo_uniforme_controller.listar_tipos()
        except Exception:
            from services import tipo_uniforme_service
            tipos = tipo_uniforme_service.listar_tipos()
        if not tipos:
            ctk.CTkLabel(parent, text="No hay tipos — crea Entrenamiento/Competencia", text_color="gray").pack(anchor="w", padx=10)
            return
        for t in tipos:
            row = ctk.CTkFrame(parent, fg_color="#F8F5FA", corner_radius=8)
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=f"{t['nombre']}", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=t.get('descripcion',''), font=ctk.CTkFont(size=11), text_color="#6B5B7B").pack(side="left")
            ctk.CTkButton(row, text="Desactivar", width=85, height=28, fg_color="#d9534f", command=lambda x=t: self._desactivar_tipo_uniforme(x)).pack(side="right", padx=2, pady=4)

    def _nuevo_tipo_uniforme(self):
        dialog = ctk.CTkInputDialog(text="Nombre del tipo de uniforme:", title="Nuevo Tipo Uniforme")
        nombre = dialog.get_input()
        if not nombre:
            return
        try:
            from controllers import tipo_uniforme_controller
            exito, msg, _ = tipo_uniforme_controller.crear_tipo({"nombre": nombre})
        except Exception:
            from services import tipo_uniforme_service
            exito, msg, _ = tipo_uniforme_service.crear_tipo_uniforme({"nombre": nombre})
        if exito:
            self._cargar_configuracion()
        else:
            messagebox.showerror("Error", msg)

    def _cargar_conceptos(self, parent):
        try:
            from services import concepto_service
            conceptos = concepto_service.listar_conceptos(activo=1)
        except Exception:
            conceptos = []
        if not conceptos:
            ctk.CTkLabel(parent, text="No hay conceptos — crea Matrícula Promocional S/150 incluye Camiseta", text_color="gray").pack(anchor="w", padx=10)
            return
        for c in conceptos:
            row = ctk.CTkFrame(parent, fg_color="#F8F5FA", corner_radius=8)
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=f"{c['nombre']} — S/{c['monto']:.2f} ({c['tipo']})", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10, pady=6)
            try:
                from services import concepto_service as cs
                items = cs.obtener_items(c["id_concepto"])
                txt = ", ".join([f"{it['producto_nombre']} x{it['cantidad']}" for it in items]) if items else "sin ítems"
            except Exception:
                txt = ""
            ctk.CTkLabel(row, text=txt, font=ctk.CTkFont(size=11), text_color="#6B5B7B").pack(side="left")
            ctk.CTkButton(row, text="Desactivar", width=85, height=28, fg_color="#d9534f", command=lambda x=c: self._desactivar_concepto(x)).pack(side="right", padx=2, pady=4)

    def _nuevo_concepto(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nuevo Concepto Flexible")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(scroll, text="Nombre:").pack(anchor="w")
        e_nombre = ctk.CTkEntry(scroll, width=400, placeholder_text="Ej: Matrícula Promocional")
        e_nombre.pack(anchor="w", pady=2)
        ctk.CTkLabel(scroll, text="Tipo:").pack(anchor="w")
        cb_tipo = ctk.CTkComboBox(scroll, values=["PROMOCION","INSCRIPCION","MENSUALIDAD","REINGRESO","CAMPEONATO","OTRO"], width=200)
        cb_tipo.set("PROMOCION")
        cb_tipo.pack(anchor="w", pady=2)
        ctk.CTkLabel(scroll, text="Monto S/:").pack(anchor="w")
        e_monto = ctk.CTkEntry(scroll, width=150, placeholder_text="150")
        e_monto.pack(anchor="w", pady=2)
        ctk.CTkLabel(scroll, text="Descripción:").pack(anchor="w")
        e_desc = ctk.CTkEntry(scroll, width=400)
        e_desc.pack(anchor="w", pady=2)
        ctk.CTkLabel(scroll, text="Productos incluidos (opcional):").pack(anchor="w", pady=(8,2))
        try:
            from controllers import inventario_controller
            prods = inventario_controller.listar_productos(activo=1)
        except Exception:
            prods = []
        checks = {}
        for p in prods[:15]:
            var = ctk.IntVar()
            cb = ctk.CTkCheckBox(scroll, text=f"{p['nombre']} — S/{(p.get('precio_venta') or p.get('precio',0)):.2f} (stock {p.get('stock_actual',0)})", variable=var)
            cb.pack(anchor="w", padx=5, pady=1)
            checks[p["id_producto"]] = var
        lbl = ctk.CTkLabel(scroll, text="", text_color="red")
        lbl.pack(pady=4)
        def guardar():
            nombre = e_nombre.get().strip()
            try:
                monto = float(e_monto.get().strip() or "0")
            except Exception:
                lbl.configure(text="Monto inválido")
                return
            items = [{"id_producto": pid, "cantidad":1} for pid,var in checks.items() if var.get()==1]
            from services import concepto_service
            ok, msg, _ = concepto_service.crear_concepto({"nombre": nombre, "tipo": cb_tipo.get(), "monto": monto, "descripcion": e_desc.get().strip(), "items": items})
            if ok:
                dialog.destroy()
                self._cargar_configuracion()
            else:
                lbl.configure(text=msg)
        btnf = ctk.CTkFrame(scroll, fg_color="transparent")
        btnf.pack(pady=10)
        ctk.CTkButton(btnf, text="Cancelar", fg_color="gray", command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Guardar", command=guardar).pack(side="left", padx=5)

    def _desactivar_concepto(self, c):
        if messagebox.askyesno("Confirmar", f"¿Desactivar '{c['nombre']}'?"):
            from services import concepto_service
            ok, msg = concepto_service.desactivar_concepto(c["id_concepto"])
            if ok:
                self._cargar_configuracion()
            else:
                messagebox.showerror("Error", msg)

    def _verificar_backup(self, ruta):
        from controllers import configuracion_controller as cc
        ok, msg = cc.verificar_backup(ruta)
        messagebox.showinfo("Verificar", msg) if ok else messagebox.showerror("Verificar", msg)

    def _restaurar_backup(self, ruta):
        # pide PIN
        dialog = ctk.CTkInputDialog(text="PIN de emergencia para restaurar:", title="Restaurar Backup")
        pin = dialog.get_input()
        if pin is None:
            return
        pin = pin.strip()
        if not pin:
            messagebox.showwarning("Restaurar", "PIN requerido")
            return
        if not messagebox.askyesno("Confirmar", f"¿Restaurar desde\n{ruta}\n\nSe reiniciará la app."):
            return
        from controllers import configuracion_controller as cc
        ok, msg = cc.restaurar_backup(ruta, pin)
        if ok:
            messagebox.showinfo("Restaurar", msg + "\nReinicie la app.")
        else:
            messagebox.showerror("Restaurar", msg)

    def _rotar_backups(self):
        from controllers import configuracion_controller as cc
        n = cc.rotar_backups(30)
        messagebox.showinfo("Rotar", f"{n} backups antiguos borrados (>30d)")
        self._cargar_configuracion()

    def _buscar_actualizaciones(self):
        try:
            from updater import update_view
            # forzar check ignorando 24h
            update_view.verificar_y_mostrar(self.winfo_toplevel(), forzar=True)
            messagebox.showinfo("Actualizaciones", "Buscando en GitHub...\nSi hay nueva versión aparecerá la ventana de actualización.")
        except Exception as e:
            messagebox.showerror("Actualizaciones", f"Error: {e}")

    def _desactivar_tipo_uniforme(self, t):
        if messagebox.askyesno("Confirmar", f"¿Desactivar '{t['nombre']}'?"):
            try:
                from controllers import tipo_uniforme_controller
                exito, msg = tipo_uniforme_controller.desactivar_tipo(t["id_tipo_uniforme"])
            except Exception:
                from services import tipo_uniforme_service
                exito, msg = tipo_uniforme_service.desactivar_tipo(t["id_tipo_uniforme"])
            if exito:
                self._cargar_configuracion()
            else:
                messagebox.showerror("Error", msg)
