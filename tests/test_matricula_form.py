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


def test_venta_uniforme_con_talla_descuenta_variante(usuario_admin, crear_estudiante):
    from controllers import venta_controller
    from repositories import producto_repository, producto_variante_repository
    from repositories import stock_almacen_repository, almacen_repository
    from models.producto_variante import ProductoVariante
    from services import inventario_service
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    if prod is None:
        cats = inventario_service.listar_categorias()
        ok_c, _, _ = inventario_service.crear_producto({
            "id_categoria_producto": cats[0]["id_categoria_producto"],
            "nombre": "Camiseta Entrenamiento", "codigo": "CAMISETA-ENT",
            "canal": "TIENDITA", "precio_venta": 70.0, "stock_inicial": 0})
        assert ok_c
        prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    var = producto_variante_repository.obtener_por_sku("CAMISETA-ENT-M")
    if var is None:
        from repositories import talla_repository
        talla = talla_repository.obtener_por_codigo("M")
        var_id = producto_variante_repository.insertar(ProductoVariante(
            id_producto=prod["id_producto"], id_talla=talla["id_talla"],
            sku="CAMISETA-ENT-M", stock_minimo=0, activo=1))
    else:
        var_id = var["id_variante"]
    alm = almacen_repository.obtener_por_nombre("Principal")
    stock_almacen_repository.upsert_stock(
        prod["id_producto"], var_id, alm["id_almacen"], None, 5)
    sa0 = stock_almacen_repository.obtener(
        prod["id_producto"], var_id, alm["id_almacen"], None)["stock"]
    eid = crear_estudiante()
    ok, msg, _ = venta_controller.registrar_venta_uniforme({
        "id_estudiante": eid, "tipo": "ENT", "id_variante": var_id,
        "fecha_venta": "2026-09-29", "metodo_pago": "EFECTIVO"})
    assert ok, msg
    sa1 = stock_almacen_repository.obtener(
        prod["id_producto"], var_id, alm["id_almacen"], None)["stock"]
    assert sa1 == sa0, f"precompra +1 y venta -1, neto 0 (era {sa0}, quedó {sa1})"


def test_asegurar_producto_unico_autocrea(usuario_admin):
    """Centralizado: si falta el producto lo crea (los 3 flujos delegan)."""
    from services import uniforme_service
    from repositories import producto_repository
    prod = producto_repository.obtener_por_codigo("UNIFORME-COM")
    if prod:
        ok, _, id_prod = uniforme_service.asegurar_producto("COM")
        assert ok and id_prod == prod["id_producto"]
        return
    ok, msg, id_prod = uniforme_service.asegurar_producto("COM")
    assert ok, msg
    assert producto_repository.obtener_por_codigo("UNIFORME-COM") is not None
    ok, msg, id_prod2 = uniforme_service.asegurar_producto("COM")
    assert ok and id_prod2 == id_prod
    ok, msg, _ = uniforme_service.asegurar_producto("XXX")
    assert not ok


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
    assert vista.var_incluye_uniforme.get() is False
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
    vista.var_incluye_uniforme.set(False)
    vista._registrar_matricula()
    vista.update_idletasks()
    assert "exitosa" in vista.label_form_status.cget("text").lower() or \
        "correct" in vista.label_form_status.cget("text").lower(), \
        vista.label_form_status.cget("text")
    assert len(matricula_repository.obtener_activas()) >= 1
