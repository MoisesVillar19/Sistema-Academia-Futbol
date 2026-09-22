import customtkinter as ctk
import threading
import time
from updater import update_service


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f} KB"
    return f"{n/1024/1024:.1f} MB"


def _fmt_velocidad(bps: float) -> str:
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1024 * 1024:
        return f"{bps/1024:.1f} KB/s"
    return f"{bps/1024/1024:.1f} MB/s"


class ActualizarDialog(ctk.CTkToplevel):
    def __init__(self, parent, info_actualizacion: dict):
        super().__init__(parent)
        self.info = info_actualizacion
        self.title("Actualizar AcademiaFutbol")
        self.geometry("460x420")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)
        self.grab_set()
        self._centrar()
        self._cancelado = False
        self._descargando = False
        self._inicio_descarga = None
        self._construir_ui()

    def _centrar(self):
        self.update_idletasks()
        ancho = 460
        alto = 420
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _construir_ui(self):
        frame = ctk.CTkFrame(self, fg_color="#FFFFFF")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            frame,
            text="Nueva versión disponible",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#7C3AED",
        ).pack(pady=(6, 4))

        ctk.CTkLabel(
            frame,
            text=f"Versión actual: {self._version_actual()}  →  Nueva: v{self.info['version']}",
            font=ctk.CTkFont(size=12),
            text_color="#6B5B7B",
        ).pack(pady=(0, 2))

        tam = self.info.get("tamano", 0)
        tam_txt = _fmt_bytes(tam) if tam else "tamaño variable"
        tipo = self.info.get("tipo", "zip")
        en_pf = self.info.get("en_programfiles", False)
        if tipo == "setup":
            tipo_txt = "Instalador (recomendado para Program Files) — pedirá permiso UAC"
            color_tipo = "#DC6B00"
        else:
            tipo_txt = "Portable ZIP — sin permisos especiales"
            color_tipo = "#6B5B7B"
        ctk.CTkLabel(
            frame,
            text=f"Tamaño: {tam_txt}  •  {tipo_txt}",
            font=ctk.CTkFont(size=11),
            text_color=color_tipo,
            wraplength=410,
        ).pack(pady=(0, 2))
        if en_pf and tipo == "setup":
            ctk.CTkLabel(
                frame,
                text="⚠ Esta actualización pedirá permiso de Administrador (UAC) y reiniciará la app.",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#DC2626",
                wraplength=410,
                justify="center",
            ).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(
                frame,
                text=f"Publicado: {self.info.get('fecha','')[:10]}",
                font=ctk.CTkFont(size=10),
                text_color="#9CA3AF",
            ).pack(pady=(0, 6))

        desc = self.info.get("descripcion", "Sin descripción")
        if len(desc) > 320:
            desc = desc[:320] + "..."
        ctk.CTkLabel(
            frame,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color="#6B5B7B",
            wraplength=410,
            justify="left",
        ).pack(pady=(0, 10))

        # URL corta para debug
        url = self.info.get("url_descarga", "")
        url_corta = url.replace("https://github.com/", "")[:62]
        ctk.CTkLabel(
            frame,
            text=url_corta,
            font=ctk.CTkFont(size=9),
            text_color="#9CA3AF",
        ).pack(pady=(0, 10))

        self._barra_progreso = ctk.CTkProgressBar(frame, width=410, height=14)
        self._barra_progreso.pack(pady=(0, 6))
        self._barra_progreso.set(0)

        self._label_porcentaje = ctk.CTkLabel(
            frame,
            text="Listo para descargar",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#7C3AED",
        )
        self._label_porcentaje.pack(pady=(0, 2))

        self._label_estado = ctk.CTkLabel(
            frame,
            text="Presione Actualizar para comenzar",
            font=ctk.CTkFont(size=11),
            text_color="#6B5B7B",
            wraplength=410,
            justify="center",
        )
        self._label_estado.pack(pady=(0, 8))

        self._label_detalle = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#9CA3AF",
            wraplength=410,
        )
        self._label_detalle.pack(pady=(0, 12))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        self._btn_no = ctk.CTkButton(
            btn_frame,
            text="Ahora no",
            width=130,
            height=36,
            fg_color="#DDD6E5",
            hover_color="#c0c8d4",
            text_color="#1F0A33",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._on_rechazar,
        )
        self._btn_no.pack(side="left", padx=(0, 10))

        self._btn_actualizar = ctk.CTkButton(
            btn_frame,
            text="Actualizar",
            width=150,
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._on_actualizar,
        )
        self._btn_actualizar.pack(side="right")

        self._btn_cancelar = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=110,
            height=36,
            fg_color="#F3F4F6",
            hover_color="#E5E7EB",
            text_color="#6B7280",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._on_cancelar,
        )
        # no mostrar hasta descargar

    def _version_actual(self):
        from utils.constants import __version__
        return __version__

    def _on_actualizar(self):
        if self._descargando:
            return
        self._descargando = True
        self._cancelado = False
        self._inicio_descarga = time.time()
        tipo = self.info.get("tipo", "zip")
        texto_btn = "Descargando Setup..." if tipo == "setup" else "Descargando..."
        self._btn_actualizar.configure(state="disabled", text=texto_btn)
        self._btn_no.configure(state="disabled")
        self._btn_cancelar.pack(side="right", padx=(0, 10))
        if tipo == "setup":
            self._label_estado.configure(text="Descargando instalador (pedirá UAC al finalizar)...")
        else:
            self._label_estado.configure(text="Conectando a GitHub...")
        self._label_detalle.configure(text=self.info.get("url_descarga", "")[:70])
        self._barra_progreso.set(0)
        self._barra_progreso.configure(progress_color="#7C3AED")

        def _descargar():
            error_msg = ""

            def callback_progreso(bytes_read, total, velocidad=0):
                if self._cancelado:
                    return
                # calcular progreso
                if total and total > 0:
                    progreso = min(bytes_read / total, 1.0)
                    pct = int(progreso * 100)
                    # ETA
                    if velocidad and velocidad > 0 and total:
                        restante = total - bytes_read
                        eta = restante / velocidad
                        eta_txt = f"ETA {int(eta//60)}m {int(eta%60)}s" if eta > 60 else f"ETA {int(eta)}s"
                    else:
                        eta_txt = ""
                    detalle = f"{_fmt_bytes(bytes_read)} / {_fmt_bytes(total)} • {_fmt_velocidad(velocidad)}  {eta_txt}" if velocidad else f"{_fmt_bytes(bytes_read)} / {_fmt_bytes(total)}"
                    self.after(0, lambda: self._update_progreso(progreso, f"{pct}%", detalle))
                else:
                    # tamaño desconocido: barra indeterminada pulsante + bytes
                    detalle = f"{_fmt_bytes(bytes_read)} descargados" + (f" • {_fmt_velocidad(velocidad)}" if velocidad else "")
                    # pulsar barra si no hay total
                    self.after(0, lambda: self._update_progreso_indeterminado(bytes_read, detalle))

            try:
                exito = update_service.descargar_y_actualizar(
                    self.info["url_descarga"],
                    callback_progreso=callback_progreso,
                    debe_cancelar=lambda: self._cancelado,
                )
                if self._cancelado:
                    self.after(0, lambda: self._on_cancelado_ui())
                    return
                if exito:
                    self.after(0, self._on_descarga_completada)
                else:
                    error_msg = getattr(update_service, "ultimo_error", "") or "Error desconocido al descargar"
                    self.after(0, lambda: self._on_descarga_fallo(error_msg))
            except Exception as e:
                error_msg = str(e) or getattr(update_service, "ultimo_error", "Error inesperado")
                self.after(0, lambda: self._on_descarga_fallo(error_msg))

        threading.Thread(target=_descargar, daemon=True).start()

    def _update_progreso(self, progreso: float, pct_txt: str, detalle: str):
        self._barra_progreso.set(progreso)
        self._label_porcentaje.configure(text=pct_txt)
        self._label_estado.configure(text="Descargando actualización...")
        self._label_detalle.configure(text=detalle)

    def _update_progreso_indeterminado(self, bytes_read: int, detalle: str):
        # animar barra 0-1 cíclico cuando no hay total
        cur = self._barra_progreso.get()
        nxt = (cur + 0.06) % 1.0
        self._barra_progreso.set(nxt)
        self._label_porcentaje.configure(text=_fmt_bytes(bytes_read))
        self._label_estado.configure(text="Descargando...")
        self._label_detalle.configure(text=detalle)

    def _on_descarga_completada(self):
        tipo = self.info.get("tipo", "zip")
        self._label_porcentaje.configure(text="100%")
        if tipo == "setup":
            self._label_estado.configure(text="Instalador listo. Lanzando actualización...")
            self._label_detalle.configure(text="Se pedirá permiso de Administrador (UAC). La app se cerrará sola.")
        else:
            self._label_estado.configure(text="Descarga completada. Aplicando actualización...")
            self._label_detalle.configure(text="Extrayendo archivos (no se tocará academia.db)...")
        self._barra_progreso.set(1)
        self._barra_progreso.configure(progress_color="#22C55E")
        self._btn_cancelar.pack_forget()
        # Limpieza: reinicio cancelable si se cierra el diálogo en esos 900ms
        try:
            if getattr(self, "_reinicio_after_id", None) is not None:
                self.after_cancel(self._reinicio_after_id)
        except Exception:
            pass
        try:
            self._reinicio_after_id = self.after(900, update_service.reiniciar_app)
        except Exception:
            self._reinicio_after_id = None

    def _on_descarga_fallo(self, msg: str):
        self._descargando = False
        # acortar msg si es largo
        if len(msg) > 220:
            msg = msg[:220] + "..."
        self._btn_actualizar.configure(state="normal", text="Reintentar")
        self._btn_no.configure(state="normal")
        self._btn_cancelar.pack_forget()
        self._label_porcentaje.configure(text="Error")
        self._label_estado.configure(text="No se pudo completar")
        self._label_detalle.configure(text=msg)
        self._barra_progreso.set(0)
        self._barra_progreso.configure(progress_color="#DC2626")

    def _on_cancelar(self):
        self._cancelado = True
        self._descargando = False
        try:
            if getattr(self, "_reinicio_after_id", None) is not None:
                self.after_cancel(self._reinicio_after_id)
                self._reinicio_after_id = None
        except Exception:
            pass
        self._label_estado.configure(text="Cancelado")
        self._label_detalle.configure(text="Descarga cancelada. Puede reintentar.")
        self._btn_actualizar.configure(state="normal", text="Reintentar")
        self._btn_no.configure(state="normal")
        self._btn_cancelar.pack_forget()
        self._barra_progreso.set(0)

    def _on_cancelado_ui(self):
        self._on_cancelar()

    def _on_rechazar(self):
        if self._descargando:
            self._on_cancelar()
            return
        update_service.registrar_rechazo(self.info["version"])
        self.destroy()

    def _on_cerrar(self):
        if self._descargando:
            self._on_cancelar()
            return
        try:
            if getattr(self, "_reinicio_after_id", None) is not None:
                self.after_cancel(self._reinicio_after_id)
                self._reinicio_after_id = None
        except Exception:
            pass
        update_service.registrar_rechazo(self.info["version"])
        self.destroy()


def verificar_y_mostrar(parent, forzar: bool = False) -> None:
    """forzar=True ignora FRECUENCIA (botón Configuración)."""
    def _verificar():
        if forzar:
            info = update_service.verificar_actualizacion()
            # si no hay update y fue manual, avisar
            if not info:
                err = getattr(update_service, "ultimo_error", "")
                if err:
                    parent.after(0, lambda: _mostrar_sin_update(parent, err))
                else:
                    parent.after(0, lambda: _mostrar_sin_update(parent, "Ya estás en la última versión."))
                return
            parent.after(0, lambda: ActualizarDialog(parent, info))
            return
        info = update_service.verificar_actualizacion()
        if info:
            parent.after(0, lambda: ActualizarDialog(parent, info))
        else:
            update_service.registrar_verificacion()

    if forzar or update_service.debe_verificar():
        threading.Thread(target=_verificar, daemon=True).start()


def _mostrar_sin_update(parent, msg: str):
    import tkinter.messagebox as mb
    mb.showinfo("Actualizaciones", msg)
