"""Sección Uniformes: ventas COM (competencia) y ENT (entrenamiento).

No van a Tiendita: la tienda vende al público general; aquí solo uniformes
asociados a estudiantes (adelantos y cancelados, con stock propio).
Reutiliza la lógica del tipo de importación Uniformes fila por fila.
"""
import customtkinter as ctk
from tkinter import messagebox

from controllers import venta_controller
from utils.logger import logger

CODIGOS_UNIFORME = ("UNIFORME-COM", "CAMISETA-ENT")


class UniformesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        self._cargar_ventas()

    # ── estructura ──
    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_lista = self.tabview.add("Ventas de uniforme")
        self.tab_form = self.tabview.add("Registrar venta")
        self._crear_tab_lista()
        self._crear_tab_form()

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion
        crear_seccion(
            self.tab_lista, titulo="Ventas de uniforme", icono="🎽",
            descripcion="COM = competencia (Uniforme Competencia) • ENT = "
                        "entrenamiento (Camiseta Entrenamiento).",
            nro=1)
        self.scroll = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_status = ctk.CTkLabel(self.tab_lista, text="",
                                         font=ctk.CTkFont(size=12))
        self.label_status.pack(pady=3)

    def _crear_tab_form(self):
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_form, titulo="Registrar venta de uniforme", icono="🧾",
            descripcion="1 pago = 1 venta. Adelanto y resto se registran por "
                        "separado, cada uno en su mes.",
            nro=1)
        cuerpo = ctk.CTkFrame(sec, fg_color="transparent")
        cuerpo.pack(fill="x", padx=10, pady=(0, 8))
        self.entry_dni = ctk.CTkEntry(cuerpo, placeholder_text="DNI del estudiante",
                                      width=180)
        self.entry_dni.pack(side="left", padx=5)
        self.combo_tipo = ctk.CTkComboBox(cuerpo, values=["COM", "ENT"], width=110)
        self.combo_tipo.set("COM")
        self.combo_tipo.pack(side="left", padx=5)
        self.entry_monto = ctk.CTkEntry(cuerpo, placeholder_text="Monto S/", width=110)
        self.entry_monto.pack(side="left", padx=5)
        self.entry_fecha = ctk.CTkEntry(cuerpo, placeholder_text="AAAA-MM-DD o AAAA-MM",
                                        width=170)
        self.entry_fecha.pack(side="left", padx=5)
        self.combo_metodo = ctk.CTkComboBox(
            cuerpo, values=["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA"], width=140)
        self.combo_metodo.set("EFECTIVO")
        self.combo_metodo.pack(side="left", padx=5)
        crear_boton_interactivo(cuerpo, text="Registrar", width=120,
                                command=self._registrar,
                                fg_color="#7C3AED").pack(side="left", padx=5)
        self.label_form_status = ctk.CTkLabel(sec, text="",
                                              font=ctk.CTkFont(size=12))
        self.label_form_status.pack(anchor="w", padx=10, pady=4)

    # ── datos ──
    @staticmethod
    def _es_uniforme(venta: dict) -> bool:
        if venta.get("tipo_venta") == "UNIFORME":
            return True
        if venta.get("tipo_venta") != "TIENDA":
            return False
        try:
            from repositories import detalle_venta_repository
            for d in detalle_venta_repository.obtener_por_venta(venta["id_venta"]):
                prod = (d.get("codigo", "") or "")
                if not prod:
                    try:
                        from repositories import producto_repository
                        p = producto_repository.obtener_por_id(d["id_producto"])
                        prod = (p or {}).get("codigo", "")
                    except Exception:
                        pass
                if prod in CODIGOS_UNIFORME:
                    return True
        except Exception:
            pass
        return False

    def _cargar_ventas(self):
        from utils.ui_helpers import crear_tabla_densa
        for w in self.scroll.winfo_children():
            w.destroy()
        try:
            ventas = venta_controller.listar_ventas()
        except Exception as e:
            logger.error(f"Uniformes listar fallo: {e}")
            ventas = []
        uni = [v for v in (ventas or []) if self._es_uniforme(v)][:100]
        nombres: dict = {}
        try:
            from repositories import estudiante_repository
            for v in uni:
                eid = v.get("id_estudiante")
                if eid and eid not in nombres:
                    e = estudiante_repository.obtener_por_id_con_persona(eid)
                    nombres[eid] = (f"{e.get('nombres', '')} {e.get('apellidos', '')}".strip()
                                    if e else "—")
        except Exception:
            pass
        filas = [[nombres.get(v.get("id_estudiante"), "—"),
                  str(v.get("numero_recibo", "")),
                  str(v.get("tipo_venta", "")),
                  (f"S/{float(v.get('monto_total', 0) or 0):.2f}",
                   {"text_color": "green", "weight": "bold"}),
                  str(v.get("metodo_pago", "")),
                  str(v.get("fecha_venta", ""))] for v in uni]
        if filas:
            crear_tabla_densa(
                self.scroll,
                [("Estudiante", 180), ("Recibo", 130), ("Tipo", 90),
                 ("Monto", 90), ("Método", 90), ("Fecha", 100)],
                filas, cap=100)
        else:
            ctk.CTkLabel(self.scroll, text="Sin ventas de uniforme",
                         text_color="gray").pack(pady=20)
        self.label_status.configure(text=f"Total: {len(uni)}")

    def _registrar(self):
        from services import importar_service
        fila = {"DNI": self.entry_dni.get().strip(),
                "TIPO": self.combo_tipo.get().strip(),
                "MONTO": self.entry_monto.get().strip(),
                "FECHA": self.entry_fecha.get().strip(),
                "METODO": self.combo_metodo.get().strip()}
        errores = importar_service.validar_fila_uniformes(fila, 1)
        if errores:
            self.label_form_status.configure(text="; ".join(errores),
                                             text_color="#DC2626")
            return
        try:
            from services import auth_service
            uid = auth_service.id_usuario_sesion_or_system()
        except Exception:
            uid = 1
        try:
            ok, msg, res = importar_service.importar_uniformes([fila], uid)
        except Exception as e:
            logger.error(f"Uniformes registrar fallo: {e}", exc_info=True)
            ok, msg, res = False, str(e), {}
        if ok and not res.get("errores"):
            self.label_form_status.configure(text=msg, text_color="#22C55E")
            messagebox.showinfo("Uniformes", msg)
            self._cargar_ventas()
            self.tabview.set("Ventas de uniforme")
        else:
            det = "; ".join((res or {}).get("errores", [msg]))
            self.label_form_status.configure(text=det, text_color="#DC2626")
            messagebox.showerror("Uniformes", det)
