"""Tipo Pagos: DNI+PERIODO localizan cuota + detección + plantilla + revisión."""
import pytest

pytestmark = pytest.mark.ui


def _periodo_cuota(crear_matricula):
    from repositories import cuota_repository
    ids = crear_matricula()
    cuota = cuota_repository.obtener_por_id(ids["id_cuota"])
    assert cuota, "el factory debe crear cuota"
    return ids, cuota["periodo"], cuota["saldo"]


def _dni_estudiante(ids):
    from repositories import estudiante_repository, persona_repository
    from database.connection import fetch_one
    est = estudiante_repository.obtener_por_id(ids["id_estudiante"])
    per = fetch_one("SELECT dni FROM persona WHERE id_persona = ?",
                    (est["id_persona"],))
    return per["dni"]


def test_validar_pagos_ok_y_errores():
    from services import importar_service
    base = {"DNI": "12345678", "PERIODO": "2026-05", "MONTO": "50.00",
            "METODO": "EFECTIVO", "FECHA": "2026-05-04"}
    ok, _, e = importar_service.validar_filas_pagos([dict(base)])
    assert ok, e
    ok, _, e = importar_service.validar_filas_pagos([dict(base, PERIODO="05/2026")])
    assert ok, e  # MM/AAAA se normaliza
    ok, _, e = importar_service.validar_filas_pagos([dict(base, PERIODO="mayo")])
    assert not ok and any("PERIODO" in x for x in e)
    ok, _, e = importar_service.validar_filas_pagos([dict(base, MONTO="0")])
    assert not ok and any("MONTO" in x for x in e)
    ok, _, e = importar_service.validar_filas_pagos([dict(base, METODO="CREDITO")])
    assert not ok and any("METODO" in x for x in e)


def test_importar_pagos_imputa_cuota(crear_matricula):
    from services import importar_service
    ids, periodo, saldo = _periodo_cuota(crear_matricula)
    dni = _dni_estudiante(ids)
    monto = round(saldo / 2, 2)
    fila = {"DNI": dni, "PERIODO": periodo, "MONTO": str(monto),
            "METODO": "EFECTIVO", "FECHA": ""}
    ok, msg, res = importar_service.importar_pagos([fila], id_usuario=1)
    assert ok, res
    assert res["pagos"] == 1, res
    from repositories import cuota_repository
    cuota = cuota_repository.obtener_por_id(ids["id_cuota"])
    assert abs(cuota["saldo"] - (saldo - monto)) < 0.01


def test_importar_pagos_cuota_inexistente_y_dni_fuera():
    from services import importar_service
    from repositories import persona_repository
    dni = "19191919"
    assert persona_repository.obtener_por_dni(dni) is None
    ok, _, res = importar_service.importar_pagos(
        [{"DNI": dni, "PERIODO": "2026-05", "MONTO": "10"}], id_usuario=1)
    assert ok and res["pagos"] == 0
    assert any("no registrado" in e for e in res["errores"]), res["errores"]


def test_revision_pagos_detecta_saldo_y_pagada(crear_matricula):
    from services import importar_revision, importar_service
    ids, periodo, saldo = _periodo_cuota(crear_matricula)
    dni = _dni_estudiante(ids)
    # monto mayor al saldo → MONTO_EXCEDE
    h = importar_revision.revisar(
        "Pagos", [{"DNI": dni, "PERIODO": periodo, "MONTO": str(saldo + 100)}], None)
    assert any(x["codigo"] == "MONTO_EXCEDE" for x in h), h
    # periodo sin cuota → CUOTA_NO_ENCONTRADA
    h = importar_revision.revisar(
        "Pagos", [{"DNI": dni, "PERIODO": "1999-01", "MONTO": "10"}], None)
    assert any(x["codigo"] == "CUOTA_NO_ENCONTRADA" for x in h), h
    # pagar total y revisar de nuevo → CUOTA_YA_PAGADA
    importar_service.importar_pagos(
        [{"DNI": dni, "PERIODO": periodo, "MONTO": str(saldo)}], id_usuario=1)
    h = importar_revision.revisar(
        "Pagos", [{"DNI": dni, "PERIODO": periodo, "MONTO": "10"}], None)
    assert any(x["codigo"] == "CUOTA_YA_PAGADA" for x in h), h


def test_detectar_pagos():
    from services import importar_service
    tipo, _ = importar_service.detectar_tipo(["DNI", "PERIODO", "MONTO"], [])
    assert tipo == "Pagos"
    # con NOMBRES también matchea Estudiantes → ambiguo → manual
    tipo, motivo = importar_service.detectar_tipo(
        ["DNI", "NOMBRES", "PERIODO", "MONTO"], [])
    assert tipo is None and "ambiguo" in motivo


def test_plantilla_pagos_genera_csv(tmp_path):
    from services import importar_plantillas
    assert "Pagos" in importar_plantillas.listar_plantillas()
    ruta = str(tmp_path / "pag.csv")
    ok, _ = importar_plantillas.generar_csv("Pagos", ruta)
    assert ok
    from controllers import importar_controller
    tipo, _ = importar_controller.detectar_tipo(ruta)
    assert tipo == "Pagos", tipo


def test_pagos_en_controller_y_vista(crear_vista, usuario_admin):
    from controllers import importar_controller
    from views.importar.importar_view import ImportarView
    assert "Pagos" in importar_controller.TIPOS_IMPORTACION
    assert "PERIODO" in importar_controller.obtener_campos_sistema("Pagos")
    assert "MONTO" in importar_controller.obtener_campos_obligatorios("Pagos")
    vista = crear_vista(ImportarView)
    vista.update_idletasks()
    assert "Pagos" in vista.seg_tipo.cget("values")
