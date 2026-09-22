"""Fase 2: fechas editables por operación (default hoy, explícita persiste)."""
import pytest

pytestmark = pytest.mark.ui

from services import pago_service, inventario_service, venta_service, matricula_service
from repositories import pago_repository


def _producto(id_cat=None, canal="ALMACEN"):
    # Fase 6a: movimientos manuales solo en ALMACEN
    from services import inventario_service as inv
    cats = inv.listar_categorias()
    id_cat = id_cat or cats[0]["id_categoria_producto"]
    ok, _, id_prod = inv.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Fecha QA",
        "canal": canal, "precio_venta": 10.0,
    })
    assert ok
    return id_prod


def test_pago_fecha_explicita_y_default(crear_matricula, usuario_admin):
    m = crear_matricula()
    ok, _, id_pago = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": 5.0, "metodo_pago": "EFECTIVO", "fecha_pago": "2026-03-15",
    })
    assert ok
    assert pago_repository.obtener_por_id(id_pago)["fecha_pago"] == "2026-03-15"

    m2 = crear_matricula()
    ok, _, id_pago2 = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m2["id_cuota"],
        "monto_pagado": 5.0, "metodo_pago": "EFECTIVO",
    })
    assert ok
    from utils.dates import get_today
    assert pago_repository.obtener_por_id(id_pago2)["fecha_pago"] == get_today()


def test_compra_y_movimiento_fecha_explicita(usuario_admin):
    id_prod = _producto()
    ok, _, id_mov = inventario_service.registrar_compra({
        "id_producto": id_prod, "cantidad": 3, "monto_total": "30.00",
        "metodo_pago": "EFECTIVO", "fecha_movimiento": "2026-04-02",
    })
    assert ok
    from repositories import movimiento_inventario_repository
    movs = movimiento_inventario_repository.obtener_por_producto(id_prod)
    assert movs[0]["fecha_movimiento"].startswith("2026-04-02")

    ok, _, _ = inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "SALIDA", "cantidad": 1,
        "motivo": "QA", "id_usuario": usuario_admin["id_usuario"],
        "fecha_movimiento": "2026-04-03",
    })
    assert ok
    movs = movimiento_inventario_repository.obtener_por_producto(id_prod)
    assert any(m["fecha_movimiento"].startswith("2026-04-03") for m in movs)


def test_venta_fecha_explicita(usuario_admin):
    id_prod = _producto(canal="TIENDITA")
    inventario_service.registrar_compra({
        "id_producto": id_prod, "cantidad": 5, "monto_total": "10.00",
        "metodo_pago": "EFECTIVO",
    })
    ok, _, id_venta = venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": id_prod, "cantidad": 1}],
        "fecha_venta": "2026-05-20",
        "id_usuario": usuario_admin["id_usuario"],
    })
    assert ok, id_venta
    from repositories import venta_repository
    assert venta_repository.obtener_por_id(id_venta)["fecha_venta"] == "2026-05-20"


def test_matricula_fecha(crear_estudiante, obtener_tarifa):
    from repositories import matricula_repository
    id_tarifa, _ = obtener_tarifa()
    ok, _, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": 100.0, "dia_vencimiento": 5,
        "fecha_inicio": "2026-02-10",
    })
    assert ok
    assert matricula_repository.obtener_por_id(id_mat)["fecha_inicio"] == "2026-02-10"


def test_express_fecha_inicio_y_pago(crear_matricula):
    ok, msg, ids = matricula_service.matricula_express({
        "tipo": "NUEVO", "nombres": "Fecha", "apellidos": "Express",
        "dni": "71717173", "monto": "120.00", "metodo_pago": "EFECTIVO",
        "fecha_inicio": "2026-06-01",
    })
    assert ok, msg
    from repositories import matricula_repository
    assert matricula_repository.obtener_por_id(ids["id_matricula"])["fecha_inicio"] == "2026-06-01"
    assert pago_repository.obtener_por_id(ids["id_pago"])["fecha_pago"] == "2026-06-01"


def test_vistas_tienen_datepickers(crear_vista, usuario_admin):
    from views.pagos.pago_view import PagoView
    from views.ventas.venta_view import VentaView
    from views.inventario.inventario_view import InventarioView
    from views.matriculas.matricula_view import MatriculaView
    assert crear_vista(PagoView).date_pago.winfo_exists()
    v = crear_vista(VentaView)
    assert v.date_venta.winfo_exists() and v.date_camp.winfo_exists()
    inv = crear_vista(InventarioView)
    assert inv.date_compra.winfo_exists() and inv.date_mov.winfo_exists()
    m = crear_vista(MatriculaView)
    assert m.date_matricula.winfo_exists() and m.date_express.winfo_exists()
