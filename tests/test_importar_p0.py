"""P0 crash Importar: la vista debe crear hoja_frame/combo_hoja/
label_deteccion/label_estado al inicio (no dentro de _descargar_plantilla)
y _seleccionar_archivo/_cargar_archivo nunca deben lanzar traceback mudo.
"""
import pytest

pytestmark = pytest.mark.ui


def test_importar_widgets_seleccion_existen(crear_vista, usuario_admin):
    from views.importar.importar_view import ImportarView
    vista = crear_vista(ImportarView)
    vista.update_idletasks()
    assert vista.hoja_frame.winfo_exists()
    assert vista.combo_hoja.winfo_exists()
    assert vista.label_deteccion.winfo_exists()
    assert vista.label_estado.winfo_exists()


def test_cargar_sin_archivo_avisa(crear_vista, usuario_admin, monkeypatch):
    import tkinter.messagebox as mb
    from views.importar.importar_view import ImportarView
    avisos = []
    monkeypatch.setattr(mb, "showwarning", lambda *a, **k: avisos.append(a))
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: avisos.append(a))
    vista = crear_vista(ImportarView)
    vista._archivo_actual = None
    vista._cargar_archivo()  # no debe lanzar, avisa con messagebox
    assert avisos, "sin archivo debe mostrar aviso"


def test_cargar_csv_llega_a_revision(crear_vista, usuario_admin, tmp_path, monkeypatch):
    import tkinter.messagebox as mb
    from views.importar.importar_view import ImportarView
    ruta = tmp_path / "est.csv"
    ruta.write_text("DNI,Nombres,Apellidos\n12345678,HUMO,PRUEBA\n", encoding="utf-8-sig")
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: None)
    monkeypatch.setattr(mb, "showwarning", lambda *a, **k: None)
    vista = crear_vista(ImportarView)
    vista._archivo_actual = str(ruta)
    vista._cargar_archivo()  # sin filedialog: no debe lanzar
    vista.update_idletasks()
    assert vista._datos_cargados, "el CSV debe cargarse"
    assert "registros" in vista.label_estado.cget("text")


def test_doble_ejecucion_no_rompe_resultados(crear_vista, usuario_admin, tmp_path,
                                             monkeypatch):
    """Regresión TclError: label_resultados vivía dentro del scroll y la
    2da ejecución crasheaba (invalid command name)."""
    import tkinter.messagebox as mb
    from views.importar.importar_view import ImportarView
    ruta = tmp_path / "est.csv"
    ruta.write_text("DNI,Nombres,Apellidos\n12345678,HUMO,PRUEBA\n", encoding="utf-8-sig")
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: None)
    monkeypatch.setattr(mb, "showwarning", lambda *a, **k: None)
    monkeypatch.setattr(mb, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(mb, "showinfo", lambda *a, **k: None)
    vista = crear_vista(ImportarView)
    vista._archivo_actual = str(ruta)
    vista._cargar_archivo()
    vista.update_idletasks()
    vista._ejecutar_importacion()
    vista.update_idletasks()
    vista._ejecutar_importacion()  # antes: TclError aquí
    vista.update_idletasks()
    assert vista.label_resultados.winfo_exists()
