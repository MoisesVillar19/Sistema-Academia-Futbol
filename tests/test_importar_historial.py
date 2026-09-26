"""Importación histórica Excel: parsers + flujos RELACIÓN/INGRESOS/VENTA."""
import datetime

from services import importar_historial as hist


def _xlsx(path, hojas):
    import openpyxl
    wb = openpyxl.Workbook()
    primero = True
    for nombre, filas in hojas.items():
        ws = wb.active if primero else wb.create_sheet(nombre)
        ws.title = nombre
        for r in filas:
            ws.append(r)
        primero = False
    wb.save(path)
    return path


def test_parsers():
    assert hist.montos_metodo("S/100 EF. S/20 Y.") == [(100.0, "EFECTIVO"), (20.0, "YAPE")]
    assert hist.montos_metodo("s/100 Y.") == [(100.0, "YAPE")]
    assert hist.montos_metodo("X") == []
    assert hist.fecha_en("YAPE(31/03)") == "2026-03-31"
    assert hist.fecha_en("EFECTIVO 23-30/04") == "2026-04-30"
    assert hist.fecha_en("P. 01/09") == "2026-09-01"
    assert hist.parse_inicio(datetime.datetime(2026, 5, 19)) == ("2026-05-19", None, None)
    assert hist.parse_inicio("01/C.M") == ("2026-01-01", None, None)
    assert hist.parse_inicio("28C.M") == ("2026-01-28", None, None)
    assert hist.parse_inicio("REIN. 09/06") == (None, "2026-06-09", None)
    assert hist.parse_inicio("CULMINO 24/06") == (None, None, "2026-06-24")
    assert hist.parse_inicio("INICIO 19/05") == ("2026-05-19", None, None)
    assert hist.parse_inicio(datetime.datetime(1900, 1, 7)) == (None, None, None)
    assert hist.parse_inicio("") == (None, None, None)
    assert hist.norm("D'ÁNGELO  ") == "D'ANGELO"


def test_relacion_e2e(tmp_path):
    ruta = _xlsx(str(tmp_path / "h.xlsx"), {
        "RELACIÓN DE ALUMNOS": [
            ["", "NOMBRES Y APELLIDOS", "2026 / MES"],
            ["", "", "MAYO", "JUNIO"],
            [1, "KENZO TAKIO", "s/100 Y.", "s/100 EF.", None, None, None, None, None, None,
             datetime.datetime(2026, 5, 2)],
            [2, "ALAM JESUS", None, None, None, None, None, None, None, None, "01/C.M"],
        ],
    })
    imp = hist.ImportadorHistorial(id_usuario=1)
    res = imp.importar_relacion(ruta)
    assert not res["errores"], res["errores"]
    assert res["estudiantes"] == 2 and res["matriculas"] == 2
    assert res["pagos"] == 2
    from repositories import persona_repository, cuota_repository, pago_repository
    assert persona_repository.obtener_por_dni("90000001") is not None
    assert persona_repository.obtener_por_dni("90000002") is not None
    pagos = pago_repository.obtener_todos(limit=10)
    assert any(p["fecha_pago"] == "2026-05-01" and p["metodo_pago"] == "YAPE" for p in pagos)
    assert any(p["metodo_pago"] == "EFECTIVO" for p in pagos)


def test_ingresos_e2e(tmp_path):
    ruta = _xlsx(str(tmp_path / "h.xlsx"), {
        "INGRESOS": [
            ["", "NOMBRES Y APELLIDOS", "2026 / MES"],
            ["", "", "MAYO"],
            ["", "YEREMI PRUEBA", "INICIO 19/05 S/. 50.00"],
        ],
    })
    imp = hist.ImportadorHistorial(id_usuario=1)
    res = imp.importar_ingresos(ruta)
    assert not res["errores"], res["errores"]
    assert res["estudiantes"] == 1 and res["becas"] == 1
    from services import matricula_service
    from repositories import estudiante_repository
    est = estudiante_repository.obtener_todos()[0]
    mats = matricula_service.obtener_por_estudiante(est["id_estudiante"])
    becas = matricula_service.obtener_becas_por_matricula(mats[0]["id_matricula"])
    assert any("1/2" in b.get("beca_nombre", "") for b in becas)


def test_venta_e2e(tmp_path):
    ruta = _xlsx(str(tmp_path / "h.xlsx"), {
        "VENTA UNIFORME": [
            ["", "NOMBRES Y APELLIDOS", "2026 / MES"],
            ["", "", "MARZO", "ABRIL"],
            ["", "DAYIRO PRUEBA", "", "1 COM. CANCELADO (YAPE 30/04)"],
            ["", "NENE PRUEBA", "", "YAPE ENTR."],
        ],
    })
    imp = hist.ImportadorHistorial(id_usuario=1)
    res = imp.importar_venta_uniforme(ruta)
    assert not res["errores"], res["errores"]
    assert res["ventas"] == 2
    assert any("Sin match" in r for r in imp.revision)
    from repositories import producto_repository
    assert producto_repository.obtener_por_codigo("UNIFORME-COM") is not None


def test_controller_gate_y_resumen(tmp_path, usuario_secretaria):
    from controllers import importar_controller
    ok, msg, res = importar_controller.importar_historial_excel("nope.xlsx")
    assert ok is False and "denegado" in msg.lower()


def test_anular_cuota_y_retiro_fecha(crear_matricula, usuario_admin):
    from services import cuota_service, estudiante_service
    m = crear_matricula()
    cuotas = cuota_service.obtener_cuotas_por_matricula(m["id_matricula"])
    ok, _ = cuota_service.anular_cuota(cuotas[0]["id_cuota"], "QA")
    assert ok
    from repositories import cuota_repository
    assert cuota_repository.obtener_por_id(cuotas[0]["id_cuota"])["activo"] == 0
    ok, _ = cuota_service.anular_cuota(999999)
    assert not ok
    ok, _ = estudiante_service.registrar_retiro(m["id_estudiante"], 1, "2026-06-24")
    assert ok
    from repositories import estudiante_repository
    est = estudiante_repository.obtener_por_id(m["id_estudiante"])
    assert est["estado"] == "RETIRADO" and est["fecha_retiro"] == "2026-06-24"
