"""Tipo Compras: entradas a proveedor + detección + plantilla + revisión."""
import pytest


def _fila(**kw):
    base = {"PRODUCTO": "Gaseosa 500ml", "CANTIDAD": "12",
            "COSTO TOTAL": "21.00", "METODO": "EFECTIVO",
            "FECHA": "2026-05-01", "CATEGORIA": "Bebidas"}
    base.update(kw)
    return base


def test_validar_compras_ok_y_errores():
    from services import importar_service
    ok, _, errores = importar_service.validar_filas_compras([_fila()])
    assert ok and not errores
    # unitario x cantidad cuando no hay total
    ok, _, errores = importar_service.validar_filas_compras(
        [_fila(**{"COSTO TOTAL": "", "COSTO X UNIDAD": "1.75"})])
    assert ok, errores
    ok, _, errores = importar_service.validar_filas_compras([_fila(CANTIDAD="0")])
    assert not ok and any("CANTIDAD" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_compras(
        [_fila(**{"COSTO TOTAL": "", "COSTO X UNIDAD": ""})])
    assert not ok and any("COSTO" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_compras([_fila(METODO="CREDITO")])
    assert not ok and any("METODO" in e for e in errores)
    # mismo producto 2 veces: válido (varias compras)
    ok, _, errores = importar_service.validar_filas_compras([_fila(), _fila()])
    assert ok, errores


def test_importar_compras_crea_producto_y_entrada():
    from services import importar_service
    from repositories import producto_repository, movimiento_inventario_repository
    ok, msg, res = importar_service.importar_compras([_fila()], id_usuario=1)
    assert ok, res
    assert res["compras"] == 1
    assert res["productos_creados"] == 1
    prods = [p for p in producto_repository.obtener_todos(activo=1)
             if p["nombre"] == "Gaseosa 500ml"]
    assert prods
    assert (prods[0].get("stock_actual") or 0) == 12, "la compra suma stock"
    movs = [m for m in movimiento_inventario_repository.obtener_todos(limit=10000)
            if m["id_producto"] == prods[0]["id_producto"]]
    assert any(m["tipo_movimiento"] == "ENTRADA" for m in movs)


def test_importar_compras_metodo_vacio_es_efectivo():
    from services import importar_service
    ok, _, res = importar_service.importar_compras([_fila(METODO="")], id_usuario=1)
    assert ok and res["compras"] == 1
    assert "EFECTIVO" in res["detalles"][0]


def test_revision_compras_omitir():
    from services import importar_revision
    filas = [_fila(), _fila(PRODUCTO=""), _fila(CANTIDAD="mal")]
    h = importar_revision.revisar("Compras", filas, None)
    codigos = {x["codigo"] for x in h}
    assert "FALTA_NOMBRE" in codigos
    assert "CANTIDAD_INVALIDA" in codigos
    res = {x["id"]: "omitir" for x in h}
    efectivas, _ = importar_revision.aplicar_resoluciones("Compras", filas, None, res)
    assert len(efectivas) == 1


def test_plantilla_compras_genera_csv(tmp_path):
    from services import importar_plantillas
    assert "Compras" in importar_plantillas.listar_plantillas()
    ruta = str(tmp_path / "c.csv")
    ok, _ = importar_plantillas.generar_csv("Compras", ruta)
    assert ok
    from controllers import importar_controller
    ok_c, _, columnas = importar_controller.obtener_columnas(ruta)
    assert ok_c and "PRODUCTO" in columnas
    # la plantilla oficial debe autodetectarse como Compras
    tipo, _ = importar_controller.detectar_tipo(ruta)
    assert tipo == "Compras", tipo
