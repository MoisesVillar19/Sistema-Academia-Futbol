import customtkinter as ctk
import threading


class LoadingDialog(ctk.CTkToplevel):
    """Diálogo de carga no bloqueante con spinner y mensaje."""

    def __init__(self, parent, mensaje: str = "Guardando..."):
        super().__init__(parent)
        self.title("Procesando")
        self.geometry("300x120")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.label = ctk.CTkLabel(self, text=mensaje, font=ctk.CTkFont(size=14))
        self.label.pack(pady=(20, 10))

        self.spinner = ctk.CTkLabel(self, text="⏳", font=ctk.CTkFont(size=30))
        self.spinner.pack()

        self._animar()

    def _animar(self):
        import itertools
        frames = itertools.cycle(["⏳", "⌛", "⏳", "⌛"])
        def _tick():
            try:
                if self.winfo_exists():
                    self.spinner.configure(text=next(frames))
                    self.after(500, _tick)
            except Exception:
                pass
        _tick()

    def cerrar(self):
        try:
            if self.winfo_exists():
                self.grab_release()
                self.destroy()
        except Exception:
            pass


def con_indicador_ocupado(parent, mensaje: str, funcion):
    """Muestra el diálogo de carga, repinta la UI, ejecuta `funcion`
    de forma síncrona y cierra el diálogo.

    Síncrono a propósito: los tests llaman a los `_registrar_*` y
    afirman sobre los labels justo después. El diálogo evita que la
    ventana parezca colgada durante la operación de BD.
    """
    loading = None
    try:
        loading = LoadingDialog(parent, mensaje)
        try:
            parent.update_idletasks()
            loading.update()
        except Exception:
            pass
    except Exception:
        loading = None
    try:
        return funcion()
    finally:
        if loading is not None:
            try:
                loading.cerrar()
            except Exception:
                pass


def ejecutar_con_loading(parent, mensaje: str, funcion, on_success=None, on_error=None):
    """Ejecuta una función en un hilo secundario con diálogo de carga.

    Args:
        parent: widget padre
        mensaje: mensaje a mostrar en el diálogo
        funcion: función a ejecutar (debe retornar tuple[bool, str, Any])
        on_success: callback(opcional) recibe (msg, resultado)
        on_error: callback(opcional) recibe (msg_error)
    """
    import tkinter.messagebox as messagebox

    loading = LoadingDialog(parent, mensaje)

    def _worker():
        try:
            exito, msg, resultado = funcion()
            parent.after(0, lambda: _finalizar(exito, msg, resultado))
        except Exception as e:
            parent.after(0, lambda: _finalizar(False, str(e), None))

    def _finalizar(exito, msg, resultado):
        loading.cerrar()
        if exito:
            if on_success:
                on_success(msg, resultado)
        else:
            if on_error:
                on_error(msg)
            else:
                messagebox.showerror("Error", msg)

    threading.Thread(target=_worker, daemon=True).start()
    return loading
