"""B4: matrícula sin productos + es-nuevo editable + uniforme."""
import pytest

pytestmark = pytest.mark.ui


def test_editar_es_nuevo(crear_estudiante):
    from services import estudiante_service
    from repositories import estudiante_repository
    eid = crear_estudiante()
    assert estudiante_repository.obtener_por_id(eid)["es_nuevo"] == 0
    ok, _ = estudiante_service.editar_estudiante(eid, {"es_nuevo": 1})
    assert ok
    assert estudiante_repository.obtener_por_id(eid)["es_nuevo"] == 1
    ok, _ = estudiante_service.editar_estudiante(eid, {"es_nuevo": 0})
    assert ok
    assert estudiante_repository.obtener_por_id(eid)["es_nuevo"] == 0


def test_venta_uniforme_precompra_sin_stock(usuario_admin, crear_estudiante):
    from controllers import venta_controller
    from repositories import producto_repository
    from services import inventario_service
    prod0 = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    if prod0 is None:
        cats = inventario_service.listar_categorias()
        ok_c, _, _ = inventario_service.crear_producto({
            "id_categoria_producto": cats[0]["id_categoria_producto"],
            "nombre": "Camiseta Entrenamiento", "codigo": "CAMISETA-ENT",
            "canal": "TIENDITA", "precio_venta": 70.0, "stock_inicial": 0})
        assert ok_c
        prod0 = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    stock_antes = prod0.get("stock_actual") or 0
    # vaciar para probar pre-compra desde 0
    producto_repository.actualizar_stock(prod0["id_producto"], 0)
    eid = crear_estudiante()
    ok, msg, vid = venta_controller.registrar_venta_uniforme({
        "id_estudiante": eid, "tipo": "ENT",
        "fecha_venta": "2026-09-29", "metodo_pago": "EFECTIVO"})
    assert ok, msg
    assert vid is not None
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    assert (prod.get("stock_actual") or 0) == 0, "compra 1 - venta 1"


def test_venta_uniforme_valida(usuario_admin, crear_estudiante):
    from controllers import venta_controller
    eid = crear_estudiante()
    ok, msg, _ = venta_controller.registrar_venta_uniforme({
        "id_estudiante": eid, "tipo": "XXX"})
    assert not ok and "COM o ENT" in msg
    ok, msg, _ = venta_controller.registrar_venta_uniforme({
        "id_estudiante": None, "tipo": "ENT"})
    assert not ok


def test_form_sin_productos_con_uniforme(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    vista.update_idletasks()
    assert not hasattr(vista, "frame_productos"), "productos fuera del form"
    assert vista.combo_uniforme.get() == "Entrenamiento"
    assert vista.var_es_nuevo.get() is False


def test_registrar_sin_uniforme(crear_vista, usuario_admin, crear_estudiante,
                                monkeypatch):
    import tkinter.messagebox as mb
    monkeypatch.setattr(mb, "askyesno", lambda *a, **k: True)
    from views.matriculas.matricula_view import MatriculaView
    from repositories import matricula_repository
    crear_estudiante(nombres="Form", apellidos="Ninguno")
    vista = crear_vista(MatriculaView)
    vista._nueva_matricula()
    vista.update_idletasks()
    nombres = vista.combo_estudiante.cget("values")
    assert nombres and nombres[0] != "Sin estudiantes"
    vista.combo_estudiante.set(nombres[0])
    vista._on_estudiante_changed(nombres[0])
    tarifas = vista.combo_tarifa.cget("values")
    vista.combo_tarifa.set(tarifas[0])
    vista.combo_uniforme.set("Ninguno")
    vista._registrar_matricula()
    vista.update_idletasks()
    assert "exitosa" in vista.label_form_status.cget("text").lower() or \
        "correct" in vista.label_form_status.cget("text").lower(), \
        vista.label_form_status.cget("text")
    assert len(matricula_repository.obtener_activas()) >= 1
