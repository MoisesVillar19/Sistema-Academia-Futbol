"""v1.2.2: al retirar se anula solo la cuota actual (pendiente sin pagos).

Anteriores y parciales se conservan. Sin DDL (activo=0 vía anular_cuota).
"""
import pytest


def _dos_cuotas(crear_matricula):
    from services import cuota_service
    m = crear_matricula()
    ok, msg, id2 = cuota_service.generar_siguiente_cuota(
        id_matricula=m["id_matricula"], monto_base=200.0, dia_vencimiento=15)
    assert ok, msg
    return m, id2


def test_retiro_anula_solo_actual(crear_matricula):
    from services import estudiante_service
    from repositories import cuota_repository
    m, id2 = _dos_cuotas(crear_matricula)
    ok, msg = estudiante_service.registrar_retiro(m["id_estudiante"])
    assert ok, msg
    assert "anulada" in msg
    assert cuota_repository.obtener_por_id(id2)["activo"] == 0
    assert cuota_repository.obtener_por_id(m["id_cuota"])["activo"] == 1


def test_retiro_conserva_parcial(crear_matricula):
    from services import estudiante_service, pago_service
    from repositories import cuota_repository
    m, id2 = _dos_cuotas(crear_matricula)
    ok, msg, _ = pago_service.registrar_pago({
        "id_usuario": 1, "id_cuota": id2, "monto_pagado": 50.0,
        "metodo_pago": "EFECTIVO", "fecha_pago": "2026-10-01",
        "observacion": "abono", "permitir_sin_comprobante": True})
    assert ok, msg
    ok, msg = estudiante_service.registrar_retiro(m["id_estudiante"])
    assert ok, msg
    assert "sin cuotas pendientes" in msg
    assert cuota_repository.obtener_por_id(id2)["activo"] == 1
    assert cuota_repository.obtener_por_id(m["id_cuota"])["activo"] == 1


def test_retiro_sin_pendientes(crear_matricula):
    # Todo pagado, pero la cadena RN-014 genera la siguiente al pagar:
    # el retiro la anula (era la deuda fantasma) y la pagada queda intacta.
    from services import estudiante_service, pago_service
    from repositories import cuota_repository, matricula_repository
    m = crear_matricula()
    ok, msg, _ = pago_service.registrar_pago({
        "id_usuario": 1, "id_cuota": m["id_cuota"], "monto_pagado": 200.0,
        "metodo_pago": "EFECTIVO", "fecha_pago": "2026-10-01",
        "observacion": "total", "permitir_sin_comprobante": True})
    assert ok, msg
    ok, msg = estudiante_service.registrar_retiro(m["id_estudiante"])
    assert ok, msg
    pagada = cuota_repository.obtener_por_id(m["id_cuota"])
    assert pagada["estado"] == "PAGADO" and pagada["activo"] == 1
    cuotas = cuota_repository.obtener_por_matricula(m["id_matricula"])
    siguientes = [c for c in cuotas if c["id_cuota"] != m["id_cuota"]]
    assert siguientes, "la cadena debió generar la siguiente"
    assert all(c["activo"] == 0 for c in siguientes)


def test_retiro_sin_anular_flag(crear_matricula):
    from services import estudiante_service
    from repositories import cuota_repository
    m, id2 = _dos_cuotas(crear_matricula)
    ok, msg = estudiante_service.registrar_retiro(
        m["id_estudiante"], anular_cuota_actual=False)
    assert ok, msg
    assert cuota_repository.obtener_por_id(id2)["activo"] == 1


def test_reingreso_no_reactiva(crear_matricula):
    from services import estudiante_service
    from repositories import cuota_repository
    m, id2 = _dos_cuotas(crear_matricula)
    assert estudiante_service.registrar_retiro(m["id_estudiante"])[0]
    assert estudiante_service.registrar_reingreso(m["id_estudiante"])[0]
    assert cuota_repository.obtener_por_id(id2)["activo"] == 0


@pytest.mark.ui
def test_retirar_ui_propaga_check(crear_vista, usuario_admin, crear_matricula,
                                  monkeypatch):
    import tkinter.messagebox as mb
    import tkinter.simpledialog as sd
    from views.estudiantes.estudiante_view import EstudianteView
    from repositories import cuota_repository
    m, id2 = _dos_cuotas(crear_matricula)
    est = {"id_estudiante": m["id_estudiante"], "nombres": "T", "apellidos": "T"}
    monkeypatch.setattr(mb, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(sd, "askstring", lambda *a, **k: "2026-10-10")
    vista = crear_vista(EstudianteView)
    vista.update_idletasks()
    monkeypatch.setattr(vista, "_dialog_anular_cuota", lambda *a, **k: True)
    monkeypatch.setattr(vista, "_cargar_estudiantes", lambda: None)
    monkeypatch.setattr(vista, "_cargar_combo_estudiantes", lambda: None)
    vista._retirar(est)
    vista.update_idletasks()
    assert cuota_repository.obtener_por_id(id2)["activo"] == 0
