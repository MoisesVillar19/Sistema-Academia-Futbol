"""Matrícula express: 1 clic crea estudiante + matrícula + pago."""
from services import matricula_service
from repositories import (
    estudiante_repository, matricula_repository, pago_repository,
    producto_repository,
)


def _base(tipo="NUEVO", **kw):
    d = {"tipo": tipo, "nombres": "Exprés", "apellidos": "Test",
         "dni": "71717171", "monto": "150.00", "metodo_pago": "EFECTIVO"}
    d.update(kw)
    return d


def test_express_nuevo_completo_con_uniforme():
    ok, msg, ids = matricula_service.matricula_express(_base())
    assert ok, msg
    est = estudiante_repository.obtener_por_id(ids["id_estudiante"])
    assert int(est.get("es_nuevo", 0)) == 1
    mat = matricula_repository.obtener_por_id(ids["id_matricula"])
    assert mat["tipo"] == "NUEVO"
    assert float(mat["monto_pactado"]) == 150.0
    pago = pago_repository.obtener_por_id(ids["id_pago"])
    assert pago and pago["metodo_pago"] == "EFECTIVO"
    # uniforme descontado (RN-051 vía es_nuevo)
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    if prod:
        assert prod["stock_actual"] == 49


def test_express_nuevo_monto_default_tarifa():
    # Fase 4: el default NUEVO lo manda la tarifa Inscripción (seed 150)
    ok, msg, ids = matricula_service.matricula_express(_base(dni="72727272", monto=None))
    assert ok, msg
    mat = matricula_repository.obtener_por_id(ids["id_matricula"])
    assert float(mat["monto_pactado"]) == 150.0


def test_express_antiguo_sin_uniforme_y_monto_obligatorio():
    ok, msg, _ = matricula_service.matricula_express(
        _base(tipo="ANTIGUO", dni="73737373", monto=""))
    assert ok is False
    ok, msg, ids = matricula_service.matricula_express(
        _base(tipo="ANTIGUO", dni="73737373", monto="80"))
    assert ok, msg
    mat = matricula_repository.obtener_por_id(ids["id_matricula"])
    assert mat["tipo"] == "ANTIGUO"
    est = estudiante_repository.obtener_por_id(ids["id_estudiante"])
    assert int(est.get("es_nuevo", 0)) == 0
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    if prod:
        assert prod["stock_actual"] == 50  # sin descuento


def test_express_reusa_dni_existente():
    ok, _, ids1 = matricula_service.matricula_express(_base(dni="74747474"))
    assert ok
    # segundo intento: ya tiene matrícula activa -> error, sin duplicar estudiante
    ok, msg, _ = matricula_service.matricula_express(_base(dni="74747474"))
    assert ok is False
    from repositories import persona_repository
    assert persona_repository.obtener_por_dni("74747474") is not None


def test_express_validaciones():
    ok, _, _ = matricula_service.matricula_express(_base(tipo="XX"))
    assert ok is False
    ok, _, _ = matricula_service.matricula_express(_base(dni="123"))
    assert ok is False
    ok, _, _ = matricula_service.matricula_express(_base(nombres=""))
    assert ok is False
    ok, _, _ = matricula_service.matricula_express(_base(metodo_pago="PLIN"))
    assert ok is False
    ok, msg, _ = matricula_service.matricula_express(_base(metodo_pago="YAPE"))
    assert ok is False and "Yape" in msg
    ok, msg, ids = matricula_service.matricula_express(
        _base(dni="75757575", metodo_pago="YAPE", comprobante_path="/tmp/x.jpg"))
    assert ok, msg


def test_tab_rapida_render_y_toggle(crear_vista, usuario_admin, ctk_root):
    import pytest
    pytest.importorskip("customtkinter")
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    assert vista.tab_rapida.winfo_exists()
    assert vista.seg_exp_tipo.get() == "NUEVO"
    vista.seg_exp_tipo.set("ANTIGUO")
    vista._on_exp_tipo("ANTIGUO")
    ctk_root.update_idletasks()
    assert "mensualidad" in vista.label_exp_panel.cget("text").lower()
    vista.seg_exp_tipo.set("NUEVO")
    vista._on_exp_tipo("NUEVO")


def test_express_con_carnet_extranjeria():
    ok, msg, ids = matricula_service.matricula_express(
        _base(dni="123456789", tipo_documento="CARNET"))
    assert ok, msg
    from repositories import persona_repository
    persona = persona_repository.obtener_por_dni("123456789")
    assert persona is not None
    assert persona["tipo_documento"] == "CARNET"
    est = estudiante_repository.obtener_por_id(ids["id_estudiante"])
    assert est is not None


def test_express_carnet_longitud_por_tipo():
    ok, msg, _ = matricula_service.matricula_express(
        _base(dni="12345678", tipo_documento="CARNET"))
    assert ok is False and "Carnet" in msg
    ok, msg, _ = matricula_service.matricula_express(
        _base(dni="123456789", tipo_documento="DNI"))
    assert ok is False and "DNI" in msg
    ok, _, _ = matricula_service.matricula_express(
        _base(dni="12345678", tipo_documento="PASAPORTE"))
    assert ok is False
    # default sin tipo sigue siendo DNI de 8
    ok, msg, _ = matricula_service.matricula_express(_base(dni="71717172"))
    assert ok, msg


def test_express_tipodoc_en_vista(crear_vista, usuario_admin, ctk_root):
    import pytest
    pytest.importorskip("customtkinter")
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    assert vista.combo_exp_tipodoc.get() == "DNI"
    vista.combo_exp_tipodoc.set("CARNET")
    vista._on_exp_tipodoc("CARNET")
    ctk_root.update_idletasks()
    assert "Carnet" in vista.label_exp_doc.cget("text")
    vista.combo_exp_tipodoc.set("DNI")
    vista._on_exp_tipodoc("DNI")
    assert "DNI" in vista.label_exp_doc.cget("text")


def test_express_atomico_sin_cuota_huerfana():
    # monto 0 inválido: no debe crear ni estudiante ni matrícula
    ok, _, _ = matricula_service.matricula_express(_base(dni="76767676", monto="0"))
    assert ok is False
    from repositories import persona_repository
    assert persona_repository.obtener_por_dni("76767676") is None
