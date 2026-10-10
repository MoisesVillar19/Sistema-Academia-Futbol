"""v1.2.3: edición exclusiva — una sola PC en edición masiva a la vez.

Importaciones y restauraciones se rechazan con otra PC activa; cobros y
consultas nunca se bloquean. Stale (2h) se auto-libera.
"""
import pytest


def _activar_como(admin_fixture, motivo="importación test"):
    from services import edicion_service
    admin_fixture  # login ya hecho por el fixture
    ok, msg = edicion_service.activar(motivo)
    assert ok, msg
    return msg


def test_activar_requiere_admin(usuario_secretaria):
    from services import edicion_service
    ok, msg = edicion_service.activar("x")
    assert not ok and "ADMIN" in msg


def test_activar_y_estado(usuario_admin):
    from services import edicion_service
    _activar_como(usuario_admin)
    st = edicion_service.estado()
    assert st["activo"] == 1 and st["motivo"] == "importación test"
    assert "exclusiva" in edicion_service.descripcion_estado()
    # idempotente propia
    ok, _ = edicion_service.activar("otra")
    assert ok


def test_otra_pc_bloqueada_yo_libre(usuario_admin, monkeypatch):
    from services import edicion_service
    _activar_como(usuario_admin)
    holder_pc = edicion_service.estado()["pc"]
    # simulo ser otra PC/usuario: la bandera ajena me bloquea
    monkeypatch.setattr(edicion_service, "_pc_actual", lambda: "OTRA-PC")
    monkeypatch.setattr(edicion_service, "_usuario_actual", lambda: "otro")
    assert edicion_service.es_mia() is False
    ok, msg = edicion_service.exigir_libre("la importación")
    assert not ok and holder_pc in msg
    # vuelvo a ser el dueño: libre
    monkeypatch.undo()
    assert edicion_service.es_mia() is True
    ok, _ = edicion_service.exigir_libre("la importación")
    assert ok


def test_importar_bloqueada_con_bandera_ajena(usuario_admin, monkeypatch):
    from services import edicion_service
    from controllers import importar_controller
    _activar_como(usuario_admin)
    monkeypatch.setattr(edicion_service, "_pc_actual", lambda: "PC1")
    monkeypatch.setattr(edicion_service, "_usuario_actual", lambda: "admin2")
    ok, msg, res = importar_controller.ejecutar_importacion(
        [{"DNI": "12345678"}], tipo="Estudiantes")
    assert not ok and "exclusiva" in msg
    assert res.get("errores")


def test_historial_bloqueado_con_bandera_ajena(usuario_admin, monkeypatch, tmp_path):
    from services import edicion_service
    from controllers import importar_controller
    _activar_como(usuario_admin)
    monkeypatch.setattr(edicion_service, "_pc_actual", lambda: "PC1")
    monkeypatch.setattr(edicion_service, "_usuario_actual", lambda: "admin2")
    f = tmp_path / "h.xlsx"
    f.write_bytes(b"x")
    ok, msg, _ = importar_controller.importar_historial_excel(str(f))
    assert not ok and "exclusiva" in msg


def test_restore_bloqueado_con_bandera_ajena(usuario_admin, monkeypatch):
    from services import edicion_service
    from controllers import configuracion_controller
    _activar_como(usuario_admin)
    monkeypatch.setattr(edicion_service, "_pc_actual", lambda: "PC1")
    monkeypatch.setattr(edicion_service, "_usuario_actual", lambda: "admin2")
    ok, msg = configuracion_controller.restaurar_backup("x.db", "1234")
    assert not ok and "exclusiva" in msg


def test_liberar_dueno_y_admin(usuario_admin):
    from services import edicion_service
    _activar_como(usuario_admin)
    ok, _ = edicion_service.liberar()
    assert ok
    assert edicion_service.estado()["activo"] == 0


def test_liberar_ajeno_no_admin_rechaza(usuario_admin, monkeypatch):
    from services import edicion_service
    from services import auth_service
    _activar_como(usuario_admin)
    # simulo otra PC con usuario no-admin
    monkeypatch.setattr(edicion_service, "_pc_actual", lambda: "PC9")
    monkeypatch.setattr(edicion_service, "_usuario_actual", lambda: "secretaria")
    monkeypatch.setattr(auth_service, "es_admin", lambda: False)
    ok, msg = edicion_service.liberar()
    assert not ok


def test_stale_se_autolibera(usuario_admin):
    from database.connection import get_connection
    from services import edicion_service
    from datetime import datetime, timedelta
    vieja = (datetime.now() - timedelta(hours=3)).isoformat(timespec="seconds")
    conn = get_connection()
    conn.execute(
        """INSERT INTO edicion_exclusiva (id_edicion, activo, pc, username, motivo, desde)
           VALUES (1, 1, 'PC-VIEJA', 'admin', 'cuelgue', ?)
           ON CONFLICT(id_edicion) DO UPDATE SET
             activo=1, pc='PC-VIEJA', username='admin', motivo='cuelgue', desde=excluded.desde""",
        (vieja,))
    conn.commit()
    assert edicion_service.estado()["activo"] == 0
    ok, _ = edicion_service.activar("nueva")
    assert ok


def test_cobro_no_pregunta_bandera(usuario_admin, crear_estudiante):
    # Cobros/ventas no pasan por exigir_libre: la bandera no los afecta.
    from services import edicion_service
    from controllers import venta_controller
    from repositories import producto_repository
    from services import inventario_service
    _activar_como(usuario_admin)
    prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    if prod is None:
        cats = inventario_service.listar_categorias()
        ok_c, _, _ = inventario_service.crear_producto({
            "id_categoria_producto": cats[0]["id_categoria_producto"],
            "nombre": "Camiseta Entrenamiento", "codigo": "CAMISETA-ENT",
            "canal": "TIENDITA", "precio_venta": 70.0, "stock_inicial": 5})
        assert ok_c
        prod = producto_repository.obtener_por_codigo("CAMISETA-ENT")
    eid = crear_estudiante()
    ok, msg, vid = venta_controller.registrar_venta({
        "id_estudiante": eid, "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": prod["id_producto"], "cantidad": 1,
                   "precio_unitario": 70.0}],
        "monto_total": 70.0})
    assert ok, msg
    assert vid is not None
