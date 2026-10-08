import customtkinter as ctk

MESES_NOMBRES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                 "JUL", "AGO", "SET", "OCT", "NOV", "DIC"]
TRIMESTRES = {"T1": [1, 2, 3], "T2": [4, 5, 6],
              "T3": [7, 8, 9], "T4": [10, 11, 12]}


class PeriodoFilter(ctk.CTkFrame):
    """Filtro de período compacto: año + preset (Completa/T1-T4/Elegir) +
    desplegable de meses con checks + orden.

    get_filtro() -> {"anio": int, "meses": [1..12], "orden": "DESC"|"ASC"}.
    Compatible con la versión anterior (misma API y callback).
    """

    def __init__(self, parent, on_change=None, show_orden=True, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._show_orden = show_orden
        self._meses_vars = {}
        self._popup = None
        self._crear_widgets()

    def _crear_widgets(self):
        from utils.dates import get_today
        try:
            anio_actual = int((get_today() or "2026")[:4])
        except (ValueError, TypeError):
            anio_actual = 2026

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text="Año:", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 5))
        self.combo_anio = ctk.CTkComboBox(
            row, width=80,
            values=[str(a) for a in range(anio_actual - 2, anio_actual + 3)],
            command=lambda v: self._notificar_cambio(),
        )
        self.combo_anio.set(str(anio_actual))
        self.combo_anio.pack(side="left", padx=(0, 10))

        self.seg_preset = ctk.CTkSegmentedButton(
            row, values=["Completa", "T1", "T2", "T3", "T4", "Elegir"],
            command=self._on_preset,
        )
        try:
            self.seg_preset.set("Completa")
        except Exception:
            pass
        self.seg_preset.pack(side="left", padx=(0, 10))

        for i in range(1, 13):
            self._meses_vars[i] = ctk.BooleanVar(value=True)
        self.btn_meses = ctk.CTkButton(
            row, text="Meses: Todos ▾", width=130, height=28,
            fg_color="#E5E7EB", hover_color="#DDD6E5", text_color="#1F0A33",
            command=self._toggle_popup,
        )
        self.btn_meses.pack(side="left")

        if self._show_orden:
            self.seg_orden = ctk.CTkSegmentedButton(
                row, values=["Más nuevo", "Más antiguo"],
                command=lambda v: self._notificar_cambio(),
            )
            try:
                self.seg_orden.set("Más nuevo")
            except Exception:
                pass
            self.seg_orden.pack(side="right", padx=5)

    # ── presets ──
    def _on_preset(self, valor):
        if valor == "Completa":
            for var in self._meses_vars.values():
                var.set(True)
        elif valor in TRIMESTRES:
            sel = set(TRIMESTRES[valor])
            for m, var in self._meses_vars.items():
                var.set(m in sel)
        # "Elegir": se respeta lo marcado en el desplegable
        self._actualizar_texto_btn()
        self._notificar_cambio()

    def _set_preset_silencioso(self, valor):
        try:
            self.seg_preset.set(valor)
        except Exception:
            pass

    # ── desplegable de meses ──
    def _toggle_popup(self):
        try:
            if self._popup is not None and self._popup.winfo_exists():
                self._popup.destroy()
                self._popup = None
                return
        except Exception:
            self._popup = None
        pop = ctk.CTkToplevel(self)
        pop.title("Meses")
        pop.geometry("280x320")
        pop.resizable(False, False)
        try:
            pop.transient(self.winfo_toplevel())
        except Exception:
            pass
        self._popup = pop
        cuerpo = ctk.CTkScrollableFrame(pop)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)
        for i, nombre in enumerate(MESES_NOMBRES, start=1):
            ctk.CTkCheckBox(
                cuerpo, text=nombre, variable=self._meses_vars[i],
                command=self._on_check_mes,
            ).pack(anchor="w", padx=5, pady=2)
        fila = ctk.CTkFrame(pop, fg_color="transparent")
        fila.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(fila, text="Todos", width=80,
                      command=lambda: self._marcar_todos(True)).pack(side="left", padx=5)
        ctk.CTkButton(fila, text="Ninguno", width=80, fg_color="gray",
                      command=lambda: self._marcar_todos(False)).pack(side="left", padx=5)

    def _marcar_todos(self, valor: bool):
        for var in self._meses_vars.values():
            var.set(valor)
        self._set_preset_silencioso("Completa" if valor else "Elegir")
        self._actualizar_texto_btn()
        self._notificar_cambio()

    def _on_check_mes(self):
        n = sum(1 for var in self._meses_vars.values() if var.get())
        if n == 12:
            self._set_preset_silencioso("Completa")
        elif n == 0:
            for var in self._meses_vars.values():
                var.set(True)
            self._set_preset_silencioso("Completa")
        else:
            self._set_preset_silencioso("Elegir")
        self._actualizar_texto_btn()
        self._notificar_cambio()

    def _actualizar_texto_btn(self):
        try:
            sel = sorted(m for m, var in self._meses_vars.items() if var.get())
            if len(sel) == 12:
                txt = "Meses: Todos ▾"
            elif not sel:
                txt = "Meses: — ▾"
            else:
                txt = f"Meses: {len(sel)} ▾"
            self.btn_meses.configure(text=txt)
        except Exception:
            pass

    def _notificar_cambio(self):
        if self._on_change:
            self._on_change(self.get_filtro())

    def get_filtro(self) -> dict:
        """Retorna dict con anio, meses seleccionados y orden."""
        try:
            anio = int(self.combo_anio.get())
        except (ValueError, TypeError):
            anio = 2026
        meses = sorted(m for m, var in self._meses_vars.items() if var.get()) or list(range(1, 13))
        if self._show_orden:
            try:
                orden = "DESC" if self.seg_orden.get() == "Más nuevo" else "ASC"
            except Exception:
                orden = "DESC"
        else:
            orden = "DESC"
        return {"anio": anio, "meses": meses, "orden": orden}

    def set_anio(self, anio: int):
        self.combo_anio.set(str(anio))
        self._notificar_cambio()
