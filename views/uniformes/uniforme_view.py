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
        self._tallas_map = {}
        self._crear_widgets()
        self._refrescar_tallas()
        self._cargar_ventas()

    # ── estructura ──
    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_productos = self.tabview.add("Productos")
        self.tab_lista = self.tabview.add("Ventas de uniforme")
        self.tab_form = self.tabview.add("Registrar venta")
        self._crear_tab_productos()
        self._crear_tab_lista()
        self._crear_tab_form()

    def _crear_tab_productos(self):
        from utils.ui_helpers import crear_seccion, crear_boton_interactivo
        crear_seccion(
            self.tab_productos, titulo="Productos de uniforme", icono="🎽",
            descripcion="COM = competencia • ENT = entrenamiento. "
                        "Tallas con stock; compras en Almacén.",
            nro=1)
        self.scroll_productos = ctk.CTkScrollableFrame(self.tab_productos)
        self.scroll_productos.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_prod_status = ctk.CTkLabel(self.tab_productos, text="",
                                              font=ctk.CTkFont(size=12))
        self.label_prod_status.pack(pady=3)
        self._cargar_productos()

    def _cargar_productos(self):
        from utils.ui_helpers import crear_tabla_densa, linea_detalle
        from utils.ui_helpers import crear_boton_interactivo
        for w in self.scroll_productos.winfo_children():
            w.destroy()
        try:
            from services import uniforme_service
            grupos = uniforme_service.productos_uniforme()
        except Exception:
            grupos = []
        cols = [("Producto", 200), ("Precio", 85), ("Stock", 70), ("Tallas", 220)]
        filas, dets = [], []
        for g in grupos:
            p = g["producto"]
            tallas_txt = ", ".join(
                f"{t['talla']}:{t['stock']}" for t in g["tallas"]) or "sin tallas"
            filas.append([
                str(p.get("nombre", "")), f"S/{float(p.get('precio_venta', 0) or 0):.2f}",
                p.get("stock_actual", 0), tallas_txt,
            ])
            dets.append(lambda frame, _g=dict(g): self._detalle_producto_uni(frame, _g))
        crear_tabla_densa(self.scroll_productos, cols, filas, dets, cap=50)
        self.label_prod_status.configure(text=f"Total: {len(grupos)} producto(s)")

    def _detalle_producto_uni(self, frame, grupo):
        from utils.ui_helpers import linea_detalle, crear_boton_interactivo
        p = grupo["producto"]
        linea_detalle(frame, "Código", p.get("codigo", ""))
        linea_detalle(frame, "Precio venta", f"S/{float(p.get('precio_venta', 0) or 0):.2f}")
        linea_detalle(frame, "Stock global", p.get("stock_actual", 0))
        for t in grupo["tallas"]:
            linea_detalle(frame, f"Talla {t['talla']}",
                          f"stock {t['stock']}")
        crear_boton_interactivo(
            frame, text="Editar precio", width=120,
            command=lambda: self._dialog_precio_uni(dict(p)),
            fg_color="#7C3AED").pack(anchor="w", padx=10, pady=2)
        crear_boton_interactivo(
            frame, text="+ Talla", width=120,
            command=lambda: self._dialog_talla_uni(grupo["tipo"]),
            fg_color="#6B7280").pack(anchor="w", padx=10, pady=2)

    def _dialog_precio_uni(self, prod):
        from tkinter import messagebox
        from services import inventario_service
        top = ctk.CTkToplevel(self)
        top.title(f"Precio {prod.get('nombre', '')}")
        top.geometry("360x200")
        try:
            top.transient(self)
        except Exception:
            pass
        cuerpo = ctk.CTkFrame(top, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(cuerpo, text="Precio de venta S/").pack(anchor="w")
        e = ctk.CTkEntry(cuerpo, width=150)
        e.insert(0, str(prod.get("precio_venta", 0)))
        e.pack(anchor="w", pady=5)
        lbl = ctk.CTkLabel(cuerpo, text="")
        lbl.pack(anchor="w")
        self._refrescar_tallas()

        def guardar():
            try:
                precio = float(e.get().strip())
                assert precio > 0
            except (ValueError, TypeError, AssertionError):
                lbl.configure(text="Precio no válido", text_color="red")
                return
            ok, msg = inventario_service.editar_producto(
                prod["id_producto"], {"precio_venta": precio})
            if ok:
                messagebox.showinfo("Producto", msg)
                top.destroy()
                self._cargar_productos()
                self._refrescar_tallas()
            else:
                lbl.configure(text=msg, text_color="red")

        btnf = ctk.CTkFrame(cuerpo, fg_color="transparent")
        btnf.pack(pady=10)
        ctk.CTkButton(btnf, text="Cancelar", fg_color="gray",
                      command=top.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Guardar", command=guardar).pack(side="left", padx=5)

    def _dialog_talla_uni(self, tipo):
        from tkinter import messagebox
        from services import uniforme_service
        try:
            from repositories import talla_repository
            tallas = [t["codigo"] for t in talla_repository.obtener_todas()]
        except Exception:
            tallas = []
        top = ctk.CTkToplevel(self)
        top.title(f"Nueva talla ({tipo})")
        top.geometry("360x240")
        try:
            top.transient(self)
        except Exception:
            pass
        cuerpo = ctk.CTkFrame(top, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(cuerpo, text="Talla del catálogo").pack(anchor="w")
        cb = ctk.CTkComboBox(cuerpo, width=150, values=tallas or ["UNICA"])
        try:
            cb.set(tallas[0] if tallas else "UNICA")
        except Exception:
            pass
        cb.pack(anchor="w", pady=5)
        ctk.CTkLabel(cuerpo, text="Stock inicial").pack(anchor="w")
        e_stock = ctk.CTkEntry(cuerpo, width=150)
        e_stock.insert(0, "0")
        e_stock.pack(anchor="w", pady=5)
        lbl = ctk.CTkLabel(cuerpo, text="")
        lbl.pack(anchor="w")

        def guardar():
            try:
                stock = int(e_stock.get().strip() or "0")
            except ValueError:
                lbl.configure(text="Stock no válido", text_color="red")
                return
            ok, msg = uniforme_service.agregar_talla(tipo, cb.get(), stock)
            if ok:
                messagebox.showinfo("Talla", msg)
                top.destroy()
                self._cargar_productos()
                self._refrescar_tallas()
            else:
                lbl.configure(text=msg, text_color="red")

        btnf = ctk.CTkFrame(cuerpo, fg_color="transparent")
        btnf.pack(pady=10)
        ctk.CTkButton(btnf, text="Cancelar", fg_color="gray",
                      command=top.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Guardar", command=guardar).pack(side="left", padx=5)

    def _crear_tab_lista(self):
        from utils.ui_helpers import crear_seccion
        crear_seccion(
            self.tab_lista, titulo="Ventas de uniforme", icono="🎽",
            descripcion="COM = competencia (Uniforme Competencia) • ENT = "
                        "entrenamiento (Camiseta Entrenamiento).",
            nro=1)
        from widgets.periodo_filter import PeriodoFilter
        self.periodo_uniformes = PeriodoFilter(
            self.tab_lista, on_change=self._on_periodo_uniformes)
        self.periodo_uniformes.pack(fill="x", padx=5, pady=(0, 4))
        self.scroll = ctk.CTkScrollableFrame(self.tab_lista)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.label_status = ctk.CTkLabel(self.tab_lista, text="",
                                         font=ctk.CTkFont(size=12))
        self.label_status.pack(pady=3)

    def _on_periodo_uniformes(self, filtro):
        self._filtro_uniformes = filtro
        self._cargar_ventas()

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
        self.combo_tipo = ctk.CTkComboBox(
            cuerpo, values=["COM", "ENT"], width=110, command=self._on_tipo_uniforme)
        self.combo_tipo.set("COM")
        self.combo_tipo.pack(side="left", padx=5)
        self.combo_talla = ctk.CTkComboBox(cuerpo, width=150, values=["Sin talla"])
        self.combo_talla.pack(side="left", padx=5)
        self._tallas_map = {}
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
            from utils.constants import TABLA_MAX_FILAS
            fp = getattr(self, "_filtro_uniformes", None) or {}
            uni = venta_controller.listar_uniformes(
                limit=TABLA_MAX_FILAS, anio=fp.get("anio"),
                meses=fp.get("meses"), orden=fp.get("orden"))
        except Exception as e:
            logger.error(f"Uniformes listar fallo: {e}")
            uni = []
        filas = [[f"{v.get('nombres', '')} {v.get('apellidos', '')}".strip() or "—",
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

    def _on_tipo_uniforme(self, _selection=None):
        self._refrescar_tallas()

    def _refrescar_tallas(self):
        try:
            from services import uniforme_service
            tallas = uniforme_service.tallas_disponibles(self.combo_tipo.get().strip())
        except Exception:
            tallas = []
        nombres = [f"{t['talla']} (stock {t['stock']})" for t in tallas]
        self._tallas_map = {n: t["id_variante"] for n, t in zip(nombres, tallas)}
        try:
            self.combo_talla.configure(values=nombres if nombres else ["Sin talla"])
            self.combo_talla.set(nombres[0] if nombres else "Sin talla")
        except Exception:
            pass

    def _registrar(self):
        from services import importar_service
        fila = {"DNI": self.entry_dni.get().strip(),
                "TIPO": self.combo_tipo.get().strip(),
                "MONTO": self.entry_monto.get().strip(),
                "FECHA": self.entry_fecha.get().strip(),
                "METODO": self.combo_metodo.get().strip()}
        if getattr(self, "_tallas_map", None) and self.combo_talla.get() in self._tallas_map:
            fila["id_variante"] = self._tallas_map[self.combo_talla.get()]
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
            from widgets.loading_dialog import con_indicador_ocupado
            ok, msg, res = con_indicador_ocupado(
                self, "Guardando venta...",
                lambda: importar_service.importar_uniformes([fila], uid))
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
