import customtkinter as ctk
from tkinter import filedialog, messagebox
from controllers import reporte_controller
from utils.dates import get_today


class ReporteView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()

    def _crear_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header, text="Reportes",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        self.contenido = ctk.CTkScrollableFrame(self)
        self.contenido.pack(fill="both", expand=True, padx=15, pady=5)

        self._mostrar_lista_reportes()

    def _mostrar_lista_reportes(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

        reportes = reporte_controller.listar_reportes()

        for reporte in reportes:
            card = ctk.CTkFrame(self.contenido)
            card.pack(fill="x", padx=5, pady=5)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

            ctk.CTkLabel(
                info_frame, text=reporte["nombre"],
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame, text=reporte["descripcion"],
                font=ctk.CTkFont(size=12), text_color="gray",
            ).pack(anchor="w")

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=10)

            ctk.CTkButton(
                btn_frame, text="Exportar Excel", width=120,
                command=lambda r=reporte["id"], n=reporte["nombre"]: self._exportar(r, n),
            ).pack(side="right")

    def _exportar(self, reporte_id, nombre_reporte):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Exportar: {nombre_reporte}")
        dialog.geometry("400x280")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Seleccionar Período del Reporte",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 10))

        fecha_actual = get_today()
        mes_actual = fecha_actual[:7]

        ctk.CTkLabel(dialog, text="Fecha Inicio (YYYY-MM-DD):").pack(pady=(10, 5))
        entry_inicio = ctk.CTkEntry(dialog, width=280)
        entry_inicio.insert(0, f"{mes_actual}-01")
        entry_inicio.pack()

        ctk.CTkLabel(dialog, text="Fecha Fin (YYYY-MM-DD):").pack(pady=(10, 5))
        entry_fin = ctk.CTkEntry(dialog, width=280)
        entry_fin.insert(0, fecha_actual)
        entry_fin.pack()

        ctk.CTkLabel(dialog, text="Formato:").pack(pady=(10, 2))
        combo_formato = ctk.CTkComboBox(dialog, values=["Excel (.xlsx)", "PDF (.pdf) - demo"], width=200)
        combo_formato.set("Excel (.xlsx)")
        combo_formato.pack()

        resultado = {"valor": None}

        def confirmar():
            fecha_inicio = entry_inicio.get().strip()
            fecha_fin = entry_fin.get().strip()
            if not fecha_inicio or not fecha_fin:
                messagebox.showwarning("Advertencia", "Ingrese ambas fechas")
                return
            fmt = combo_formato.get()
            ext = ".pdf" if "PDF" in fmt else ".xlsx"
            ftype = [("PDF", "*.pdf")] if ext == ".pdf" else [("Archivos Excel", "*.xlsx")]
            ruta = filedialog.asksaveasfilename(
                title="Guardar reporte",
                defaultextension=ext,
                filetypes=ftype,
                initialfile=f"reporte_{reporte_id}_{fecha_inicio}_a_{fecha_fin}{ext}",
            )
            if not ruta:
                return
            if not ruta.lower().endswith(ext):
                ruta += ext
            resultado["valor"] = (fecha_inicio, fecha_fin, ruta)
            dialog.destroy()

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(
            btn_row, text="Seleccionar y Exportar", width=180,
            command=confirmar,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_row, text="Cancelar", width=110, fg_color="gray",
            command=dialog.destroy,
        ).pack(side="left", padx=5)

        dialog.wait_window()

        if resultado["valor"]:
            fecha_inicio, fecha_fin, ruta = resultado["valor"]
            self._ejecutar_exportacion(reporte_id, fecha_inicio, fecha_fin, ruta)

    def _ejecutar_exportacion(self, reporte_id, fecha_inicio, fecha_fin, ruta):
        # Soporte demo PDF: si ruta .pdf, usa pdf_exporter con mismos datos
        es_pdf = ruta.lower().endswith(".pdf")
        try:
            if es_pdf:
                # generar datos primero y luego exportar a PDF demo
                ok, msg = self._exportar_pdf_demo(reporte_id, fecha_inicio, fecha_fin, ruta)
                if ok:
                    messagebox.showinfo("Éxito", msg)
                else:
                    messagebox.showerror("Error", msg)
                return
            if reporte_id == "morosos":
                exito, msg = reporte_controller.reporte_morosos(ruta)
            elif reporte_id == "pagos_fecha":
                exito, msg = reporte_controller.reporte_pagos_por_fecha(
                    fecha_inicio, fecha_fin, ruta
                )
            elif reporte_id == "ingresos_mensuales":
                exito, msg = reporte_controller.reporte_ingresos_mensuales(ruta)
            elif reporte_id == "alumnos_categoria":
                exito, msg = reporte_controller.reporte_alumnos_por_categoria(ruta)
            elif reporte_id == "inventario":
                exito, msg = reporte_controller.reporte_inventario(ruta)
            elif reporte_id == "becas_activas":
                exito, msg = reporte_controller.reporte_becas_activas(ruta)
            elif reporte_id == "ingresos_vs_egresos":
                # v2 flexible
                from controllers import egreso_controller
                rep = egreso_controller.reporte_ingresos_vs_egresos(fecha_inicio, fecha_fin)
                # exportar simple via openpyxl
                try:
                    from openpyxl import Workbook
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Ingresos vs Egresos"
                    ws.append(["Concepto","Monto"])
                    ws.append(["Ingresos pagos", rep.get("ingresos_pagos",0)])
                    ws.append(["Ingresos ventas", rep.get("ingresos_ventas",0)])
                    ws.append(["Total ingresos", rep.get("total_ingresos",0)])
                    ws.append(["Egresos", rep.get("egresos",0)])
                    ws.append(["Neto", rep.get("neto",0)])
                    wb.save(ruta)
                    exito, msg = True, f"Reporte guardado en {ruta}"
                except Exception as e:
                    exito, msg = False, str(e)
            elif reporte_id == "stock_bajo_uniformes":
                try:
                    from controllers import inventario_controller
                    from openpyxl import Workbook
                    bajos = inventario_controller.listar_productos()
                    bajos = [p for p in bajos if p.get("stock_actual",0) <= p.get("stock_minimo",0) and p.get("activo",1)]
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Stock bajo uniformes"
                    ws.append(["Codigo","Nombre","Stock","Minimo"])
                    for p in bajos:
                        ws.append([p.get("codigo",""), p.get("nombre",""), p.get("stock_actual",0), p.get("stock_minimo",0)])
                    wb.save(ruta)
                    exito, msg = True, f"Reporte guardado en {ruta}"
                except Exception as e:
                    exito, msg = False, str(e)
            elif reporte_id == "nuevos_vs_antiguos":
                try:
                    from services import reporte_service
                    from openpyxl import Workbook
                    nuevos = reporte_service.contar_nuevos(fecha_inicio, fecha_fin)
                    total_mats = reporte_service.contar_matriculas_periodo(fecha_inicio, fecha_fin)
                    antiguos = max(0, total_mats - nuevos)
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Nuevos vs Antiguos"
                    ws.append(["Tipo","Cantidad"])
                    ws.append(["Nuevos", nuevos])
                    ws.append(["Antiguos", antiguos])
                    ws.append(["Total matriculas", total_mats])
                    wb.save(ruta)
                    exito, msg = True, f"Reporte guardado en {ruta}"
                except Exception as e:
                    exito, msg = False, str(e)
            elif reporte_id == "regalos_matricula":
                try:
                    from services import reporte_service
                    from openpyxl import Workbook
                    regalos = reporte_service.reporte_regalos_matricula(fecha_inicio, fecha_fin)
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Regalos Matricula"
                    ws.append(["Fecha","Producto","Cantidad","Estudiante"])
                    for r in regalos:
                        ws.append([r.get("fecha",""), r.get("producto",""), r.get("cantidad",0), r.get("estudiante","")])
                    wb.save(ruta)
                    exito, msg = True, f"Reporte guardado en {ruta}"
                except Exception as e:
                    exito, msg = False, str(e)
            else:
                messagebox.showerror("Error", "Reporte no reconocido")
                return

            if exito:
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def _exportar_pdf_demo(self, reporte_id, fecha_inicio, fecha_fin, ruta):
        """Demo PDF sin estilo final — usa mismos datos que Excel pero con pdf_exporter."""
        try:
            from utils.pdf_exporter import exportar_a_pdf
            # reutilizar datos de reporte_service
            if reporte_id == "morosos":
                from services import reporte_service as rs
                # generar datos morosos
                from repositories import cuota_repository
                cuotas = cuota_repository.obtener_vencidas()
                morosos = {}
                for c in cuotas:
                    dni = c.get("dni", "")
                    if dni not in morosos:
                        morosos[dni] = {"dni": dni, "estudiante": f"{c.get('nombres','')} {c.get('apellidos','')}", "cuotas_vencidas": 0, "total_deuda": 0, "periodos": []}
                    morosos[dni]["total_deuda"] += c.get("saldo",0)
                    morosos[dni]["cuotas_vencidas"] += 1
                    morosos[dni]["periodos"].append(c.get("periodo",""))
                datos = [{"dni": m["dni"], "estudiante": m["estudiante"], "cuotas_vencidas": m["cuotas_vencidas"], "total_deuda": round(m["total_deuda"],2), "periodos": ", ".join(m["periodos"])} for m in morosos.values()]
                cols = [("dni","DNI"),("estudiante","Estudiante"),("cuotas_vencidas","Cuotas Vencidas"),("total_deuda","Total Deuda (S/)"),("periodos","Periodos")]
                return exportar_a_pdf(datos, cols, "Reporte de Morosos", ruta)
            elif reporte_id == "inventario":
                from services import reporte_service as rs
                # usar datos de inventario valorizado
                from repositories import producto_repository
                prods = producto_repository.obtener_todos(activo=1)
                datos = []
                for p in prods:
                    stock = p.get("stock_actual",0)
                    datos.append({"codigo": p.get("codigo",""), "nombre": p.get("nombre",""), "stock": stock, "minimo": p.get("stock_minimo",0), "precio": p.get("precio",0)})
                cols = [("codigo","Código"),("nombre","Nombre"),("stock","Stock"),("minimo","Mínimo"),("precio","Precio")]
                return exportar_a_pdf(datos, cols, "Inventario", ruta)
            else:
                # fallback: crear PDF simple con datos genéricos
                datos = [{"info": f"Reporte {reporte_id} del {fecha_inicio} al {fecha_fin}", "valor": "Demo PDF"}]
                cols = [("info","Info"),("valor","Valor")]
                return exportar_a_pdf(datos, cols, f"Reporte {reporte_id}", ruta)
        except Exception as e:
            return False, f"Error PDF demo: {e}"
