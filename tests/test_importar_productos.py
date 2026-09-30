"""Tipo Productos: catálogo sin movimientos + detección + plantilla + revisión."""
import pytest


def _fila(**kw):
    base = {"PRODUCTO": "Gaseosa 500ml", "CATEGORIA": "Bebidas",
            "COSTO": "1.75", "PRECIO_VENTA": "3.00"}
    base.update(kw)
    return base


def test_validar_productos_ok_y_errores():
    from services import importar_service
    ok, _, errores = importar_service.validar_filas_productos([_fila()])
    assert ok and not errores
    ok, _, errores = importar_service.validar_filas_productos([_fila(PRODUCTO="")])
    assert not ok and any("obligatorio" in e for e in errores)
    ok, _, errores = importar_service.validar_filas_productos([_fila(COSTO="mal")])
    assert not ok
    ok, _, errores = importar_service.validar_filas_productos([_fila(), _fila()])
    assert not ok and any("duplicado" in e for e in errores)


def test_importar_productos_crea_sin_movimientos():
    from services import importar_service
    from repositories import producto_repository, movimiento_inventario_repository
    ok, msg, res = importar_service.importar_productos([_fila()], id_usuario=1)
    assert ok, res
    assert res["productos_creados"] == 1
    prods = [p for p in producto_repository.obtener_todos(activo=1)
             if p["nombre"] == "Gaseosa 500ml"]
    assert prods, "el producto debe existir"
    assert (prods[0].get("stock_actual") or 0) == 0, "catálogo: sin stock inicial"
    movs = [m for m in movimiento_inventario_repository.obtener_todos(limit=10000)
            if m["id_producto"] == prods[0]["id_producto"]]
    assert not movs, "catálogo: sin movimientos de inventario"


def test_importar_productos_reutiliza_existente():
    from services import importar_service
    importar_service.importar_productos([_fila()], id_usuario=1)
    ok, _, res = importar_service.importar_productos([_fila()], id_usuario=1)
    assert ok
    assert res["productos_creados"] == 0
    assert any("ya existía" in d for d in res["detalles"])


def test_detectar_productos_y_no_ambiguo_con_compras():
    from services import importar_service
    tipo, _ = importar_service.detectar_tipo(
        ["PRODUCTO", "CATEGORIA", "COSTO", "PRECIO_VENTA"], [])
    assert tipo == "Productos"
    # Compras no debe colisionar con Productos
    tipo, _ = importar_service.detectar_tipo(
        ["PRODUCTO", "CANTIDAD", "COSTO TOTAL", "METODO", "FECHA"], [])
    assert tipo == "Compras"
    # Tienda clásica sigue detectando Tienda
    tipo, _ = importar_service.detectar_tipo(
        ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "YAPE", "EFECTIVO",
         "CANTIDAD VENDIDO", "QUEDAN"], [])
    assert tipo == "Tienda"


def test_revision_productos_hallazgos_y_omitir():
    from services import importar_revision
    filas = [_fila(), _fila(PRODUCTO=""), _fila(PRODUCTO="Gaseosa 500ml")]
    h = importar_revision.revisar("Productos", filas, None)
    codigos = {x["codigo"] for x in h}
    assert "FALTA_NOMBRE" in codigos
    assert "DUPLICADO" in codigos
    res = {x["id"]: "omitir" for x in h}
    efectivas, notas = importar_revision.aplicar_resoluciones("Productos", filas, None, res)
    assert len(efectivas) == 1


def test_plantilla_productos_genera_csv(tmp_path):
    from services import importar_plantillas
    assert "Productos" in importar_plantillas.listar_plantillas()
    ruta = str(tmp_path / "p.csv")
    ok, _ = importar_plantillas.generar_csv("Productos", ruta)
    assert ok
    from controllers import importar_controller
    ok_c, _, columnas = importar_controller.obtener_columnas(ruta)
    assert ok_c and "PRODUCTO" in columnas
