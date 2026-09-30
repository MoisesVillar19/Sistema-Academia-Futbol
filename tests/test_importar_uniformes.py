"""Tipo Uniformes: 1 fila = 1 venta (COM/ENT) + detección + plantilla + revisión."""
import pytest


def _fila(**kw):
    base = {"DNI": "12345678", "TIPO": "COM", "MONTO": "30.00",
            "FECHA": "2026-05-15", "METODO": "EFECTIVO"}
    base.update(kw)
    return base


def _estudiante(dni="12345678"):
    from repositories import persona_repository, estudiante_repository
    from models.persona import Persona
    from models.estudiante import Estudiante
    pid = persona_repository.insertar(Persona(
        dni=dni, nombres="Uni", apellidos="Forme",
        fecha_nacimiento="2015-01-01", sexo="M"))
    return estudiante_repository.insertar(Estudiante(id_persona=pid, estado="ACTIVO"))


def test_validar_uniformes_ok_y_errores():
    from services import importar_service
    ok, _, e = importar_service.validar_filas_uniformes([_fila()])
    assert ok, e
    ok, _, e = importar_service.validar_filas_uniformes([_fila(FECHA="2026-05")])
    assert ok, e  # solo mes → día 01
    ok, _, e = importar_service.validar_filas_uniformes([_fila(TIPO="XXX")])
    assert not ok and any("TIPO" in x for x in e)
    ok, _, e = importar_service.validar_filas_uniformes([_fila(MONTO="0")])
    assert not ok and any("MONTO" in x for x in e)


def test_importar_uniformes_venta_y_stock():
    from services import importar_service
    from repositories import producto_repository, movimiento_inventario_repository
    from services import venta_service
    _estudiante()
    ok, msg, res = importar_service.importar_uniformes(
        [_fila(), _fila(TIPO="ENT", MONTO="40.00", FECHA="2026-06-02")],
        id_usuario=1)
    assert ok, res
    assert res["ventas"] == 2, res
    # UNIFORME-COM se crea; CAMISETA-ENT puede venir del seed (no se duplica)
    assert producto_repository.obtener_por_codigo("UNIFORME-COM")
    assert producto_repository.obtener_por_codigo("CAMISETA-ENT")
    com = producto_repository.obtener_por_codigo("UNIFORME-COM")
    assert com and (com.get("stock_actual") or 0) == 0, "compra 1 - venta 1 = 0"
    movs = [m for m in movimiento_inventario_repository.obtener_todos(limit=10000)
            if m["id_producto"] == com["id_producto"]]
    assert any(m["tipo_movimiento"] == "ENTRADA" for m in movs)
    assert any(m["tipo_movimiento"] == "SALIDA" for m in movs)
    ventas = venta_service.listar_ventas("2026-01-01", "2026-12-31")
    tipos = {v["tipo_venta"] for v in ventas}
    assert {"TIENDA", "UNIFORME"} <= tipos  # COM→TIENDA, ENT→UNIFORME
    assert any(float(v["monto_total"]) == 30.0 for v in ventas)


def test_importar_uniformes_fecha_solo_mes_dia_01():
    from services import importar_service
    from services import venta_service
    _estudiante()
    ok, _, res = importar_service.importar_uniformes([_fila(FECHA="2026-05")],
                                                     id_usuario=1)
    assert ok and res["ventas"] == 1
    ventas = venta_service.listar_ventas("2026-05-01", "2026-05-31")
    assert any(v["fecha_venta"] == "2026-05-01" for v in ventas), ventas


def test_importar_uniformes_dni_inexistente():
    from services import importar_service
    ok, _, res = importar_service.importar_uniformes([_fila(DNI="99999991")],
                                                     id_usuario=1)
    assert ok and res["ventas"] == 0
    assert any("no registrado" in e for e in res["errores"])


def test_revision_uniformes(crear_estudiante):
    from services import importar_revision
    crear_estudiante(dni="12345678")
    h = importar_revision.revisar("Uniformes", [_fila()], None)
    assert not h, h
    h = importar_revision.revisar("Uniformes", [_fila(DNI="99999991")], None)
    assert any(x["codigo"] == "DNI_NO_EXISTE" for x in h)
    h = importar_revision.revisar("Uniformes", [_fila(TIPO="XXX")], None)
    assert any(x["codigo"] == "TIPO_INVALIDO" for x in h)


def test_detectar_uniformes():
    from services import importar_service
    tipo, _ = importar_service.detectar_tipo(["DNI", "TIPO", "MONTO", "FECHA"], [])
    assert tipo == "Uniformes"
    # no colisiona con Pagos (PERIODO) ni Estudiantes (NOMBRES)
    tipo, _ = importar_service.detectar_tipo(["DNI", "PERIODO", "MONTO"], [])
    assert tipo == "Pagos"


def test_plantilla_uniformes_y_controller(tmp_path, crear_vista, usuario_admin):
    from services import importar_plantillas
    from controllers import importar_controller
    from views.importar.importar_view import ImportarView
    assert "Uniformes" in importar_plantillas.listar_plantillas()
    assert "Uniformes" in importar_controller.TIPOS_IMPORTACION
    assert "TIPO" in importar_controller.obtener_campos_sistema("Uniformes")
    ruta = str(tmp_path / "u.csv")
    ok, _ = importar_plantillas.generar_csv("Uniformes", ruta)
    assert ok
    tipo, _ = importar_controller.detectar_tipo(ruta)
    assert tipo == "Uniformes", tipo
    vista = crear_vista(ImportarView)
    vista.update_idletasks()
    assert "Uniformes" in vista.seg_tipo.cget("values")


pytestmark = pytest.mark.ui
