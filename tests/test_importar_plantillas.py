"""Plantillas + normalizador + resumen de mapeo + aviso final."""
import csv


def test_plantillas_generan_csv(tmp_path):
    from services import importar_plantillas
    for tipo in importar_plantillas.listar_plantillas():
        ruta = str(tmp_path / f"p_{tipo}.csv")
        ok, _ = importar_plantillas.generar_csv(tipo, ruta)
        assert ok
        with open(ruta, encoding="utf-8-sig") as f:
            r = list(csv.reader(f))
        assert len(r) == 2 and r[0] and r[1]
    ok, _ = importar_plantillas.generar_csv("Inexistente", str(tmp_path / "x.csv"))
    assert not ok


def test_normalizador_csvs_validos():
    import glob
    from services import importar_service
    tienda = sorted(glob.glob("importacion/normalizados/tienda_*.csv"))
    assert len(tienda) == 3, tienda
    total = 0
    for f in tienda:
        rows = list(csv.DictReader(open(f, encoding="utf-8-sig")))
        ok, _, errs = importar_service.validar_filas_tienda(rows)
        assert ok, (f, errs[:3])
        total += len(rows)
    assert total > 50
    rows = list(csv.DictReader(
        open("importacion/normalizados/estudiantes_relacion.csv", encoding="utf-8-sig")))
    assert len(rows) == 55
    assert rows[0]["DNI"] == "90000001" and rows[0]["Nombres"] == "KENZO"
    assert set(rows[0].keys()) >= {"DNI", "Nombres", "Apellidos", "BECA", "INICIO"}


def test_producto_reutilizado_entre_meses(usuario_admin):
    from services import importar_service
    from repositories import producto_repository
    base = {"PRODUCTOS": "Reuso QA", "CANTIDAD": "5", "COSTO TOTAL": "10.00",
            "COSTO VENTA": "3.00", "YAPE": "0", "EFECTIVO": "15.00",
            "CANTIDAD VENDIDO": "5", "QUEDAN": "0"}
    ok, _, r1 = importar_service.importar_tienda([dict(base)], id_usuario=1)
    assert ok, r1
    ok, _, r2 = importar_service.importar_tienda([dict(base)], id_usuario=1)
    assert ok, r2
    assert r2["productos_creados"] == 0
    prods = [p for p in producto_repository.obtener_todos() if p["nombre"] == "Reuso QA"]
    assert len(prods) == 1 and prods[0]["stock_actual"] == 0


def test_mapeo_resumen_y_aviso(crear_vista, usuario_admin, monkeypatch):
    import pytest
    pytest.importorskip("customtkinter")
    import tkinter.messagebox as mb
    from views.importar.importar_view import ImportarView
    vista = crear_vista(ImportarView)
    vista._datos_cargados = [{"DNI": "1", "Nombres": "A", "ZZZ": "x"}]
    vista._configurar_mapeo()
    vista.update_idletasks()
    txt = vista.label_mapeo_resumen.cget("text")
    assert "DNI→dni" in txt and "Nombres→nombres" in txt
    avisos = []
    monkeypatch.setattr(mb, "showinfo", lambda *a, **k: avisos.append("info"))
    monkeypatch.setattr(mb, "showwarning", lambda *a, **k: avisos.append("warn"))
    monkeypatch.setattr(mb, "showerror", lambda *a, **k: avisos.append("err"))
    vista._avisar_resultado(True, "ok", {"errores": []})
    vista._avisar_resultado(True, "ok", {"errores": ["x"]})
    vista._avisar_resultado(False, "mal", {"errores": ["x"]})
    assert avisos == ["info", "warn", "err"]
