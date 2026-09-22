"""Fase 0 (refactorización v2): canal TIENDITA/ALMACEN, comprobante en pago, seeds Excel."""
from services import inventario_service, pago_service
from repositories import pago_repository
from database.connection import fetch_one, fetch_all, get_connection


def _cat():
    cats = inventario_service.listar_categorias()
    if cats:
        return cats[0]["id_categoria_producto"]
    ok, _, id_cat = inventario_service.crear_categoria({"nombre": "Fase0Cat"})
    assert ok
    return id_cat


def test_canal_valido_y_default_almacen():
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Sin canal QA",
    })
    assert ok
    prod = inventario_service.obtener_producto(id_prod)
    assert prod["canal"] == "ALMACEN"

    ok, _, id_prod2 = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Tienda QA", "canal": "TIENDITA",
    })
    assert ok
    assert inventario_service.obtener_producto(id_prod2)["canal"] == "TIENDITA"

    ok, msg, _ = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Mal QA", "canal": "VENTA",
    })
    assert ok is False


def test_canal_legacy_tipo_uso_mapea():
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": _cat(), "nombre": "Legacy QA", "tipo_uso": "VENTA",
    })
    assert ok
    assert inventario_service.obtener_producto(id_prod)["canal"] == "TIENDITA"


def test_migracion_canal_backfill_legacy():
    from database import create_db
    conn = get_connection()
    conn.execute("ALTER TABLE producto ADD COLUMN tipo_uso TEXT DEFAULT 'CONSUMO_INTERNO'")
    conn.execute("ALTER TABLE producto DROP COLUMN canal")
    conn.execute("INSERT INTO categoria_producto (nombre) VALUES ('MigCat')")
    cat = fetch_one("SELECT id_categoria_producto FROM categoria_producto WHERE nombre='MigCat'")
    conn.execute(
        "INSERT INTO producto (id_categoria_producto, tipo_uso, codigo, nombre) VALUES (?, 'VENTA', 'MIG-001', 'Mig')",
        (cat["id_categoria_producto"],))
    conn.execute(
        "INSERT INTO producto (id_categoria_producto, tipo_uso, codigo, nombre) VALUES (?, 'CONSUMO_INTERNO', 'MIG-002', 'Mig2')",
        (cat["id_categoria_producto"],))
    conn.commit()
    create_db._migrar_columnas_faltantes(conn.cursor())
    conn.commit()
    assert fetch_one("SELECT canal FROM producto WHERE codigo='MIG-001'")["canal"] == "TIENDITA"
    assert fetch_one("SELECT canal FROM producto WHERE codigo='MIG-002'")["canal"] == "ALMACEN"


def test_pago_guarda_comprobante(crear_matricula, usuario_admin):
    m = crear_matricula()
    ok, _, id_pago = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"],
        "id_cuota": m["id_cuota"],
        "monto_pagado": 10.0,
        "metodo_pago": "EFECTIVO",
        "comprobante_path": "/tmp/comp.jpg",
    })
    assert ok
    pago = pago_repository.obtener_por_id(id_pago)
    assert pago["comprobante_path"] == "/tmp/comp.jpg"


def test_seeds_precios_excel():
    from repositories import tarifa_repository
    tarifas = {t["nombre"]: t for t in tarifa_repository.obtener_activas()}
    assert float(tarifas["Inscripción"]["monto"]) == 150.0
    assert float(tarifas["Uniforme base"]["monto"]) == 70.0
    assert float(tarifas["Mensualidad"]["monto"]) == 120.0


def test_seeds_becas_excel():
    becas = {b["nombre"]: b for b in fetch_all("SELECT * FROM beca WHERE activo = 1")}
    assert becas["1/2 BECA"]["tipo"] == "MONTO_FIJO"
    assert float(becas["1/2 BECA"]["valor"]) == 50.0
    assert becas["BECA COMPLETA"]["tipo"] == "PORCENTAJE"
    assert float(becas["BECA COMPLETA"]["valor"]) == 100.0


def test_config_defaults_excel():
    from services import configuracion_service
    cfg = configuracion_service.obtener_configuracion()
    assert float(cfg["precio_inscripcion"]) == 150.0
    assert float(cfg["precio_mensualidad"]) == 120.0
    assert float(cfg["precio_uniforme"]) == 70.0


def test_modulos_tiendita_almacen():
    from utils.constants import MODULOS_SISTEMA, PERMISOS_ROL
    assert "tiendita" in MODULOS_SISTEMA and "almacen" in MODULOS_SISTEMA
    assert "tiendita" in PERMISOS_ROL["SECRETARIA"]
    assert "almacen" not in PERMISOS_ROL["SECRETARIA"]
    assert set(MODULOS_SISTEMA) <= PERMISOS_ROL["ADMIN"]
