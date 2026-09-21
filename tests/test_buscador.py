"""Bloque A (plan inventario UX): normalizador multi-campo + paginados SQL reales."""
import pytest

from utils.busqueda import normalizar, coincide, filtrar


# ── Matriz de normalización ──────────────────────────────────────

@pytest.mark.parametrize("entrada,esperado", [
    ("PÉREZ", "perez"),
    ("  Juan   Pérez  ", "juan perez"),
    ("NIÑO", "nino"),
    ("García-López", "garcia-lopez"),
    ("CAMISeta  ENT-M", "camiseta ent-m"),
    ("", ""),
    (None, ""),
    (123, "123"),
])
def test_normalizar_matriz(entrada, esperado):
    assert normalizar(entrada) == esperado


# ── Multi-campo ──────────────────────────────────────────────────

def test_coincide_multi_campo_y_tildes():
    assert coincide("juan perez", "Juan", "Pérez López")
    assert coincide("perez juan", "Juan", "Pérez López")
    assert coincide("12345678", "Juan Pérez", "12345678")  # DNI/carnet
    assert coincide("", "cualquier", "cosa")
    assert not coincide("garcia", "Juan", "Pérez")
    assert not coincide("juan garcia", "Juan", "Pérez")


def test_filtrar_listas():
    filas = [
        {"nombres": "Juan", "apellidos": "Pérez", "dni": "12345678"},
        {"nombres": "María", "apellidos": "García", "dni": "87654321"},
    ]
    out = filtrar(filas, "perez", lambda f: f["nombres"], lambda f: f["apellidos"], lambda f: f["dni"])
    assert [f["nombres"] for f in out] == ["Juan"]
    assert len(filtrar(filas, "", lambda f: f["nombres"])) == 2


# ── Paginado producto con datos (A3) ─────────────────────────────

def test_producto_buscar_paginado_real():
    from services import inventario_service
    from repositories import producto_repository

    cats = inventario_service.listar_categorias()
    if not cats:
        _, _, id_cat = inventario_service.crear_categoria({"nombre": "BuscCat"})
    else:
        id_cat = cats[0]["id_categoria_producto"]
    ok, _, _ = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Camiseta Entrenamiento QA",
        "tipo_uso": "VENTA",
    })
    assert ok

    rows, total = producto_repository.buscar_paginado(q="camiseta", limit=50, offset=0)
    assert total >= 1
    assert any("Camiseta Entrenamiento QA" in r["nombre"] for r in rows)

    rows2, total2 = producto_repository.buscar_paginado(q="zzz-sin-coincidencia", limit=50, offset=0)
    assert total2 == 0 and rows2 == []

    rows3, total3 = producto_repository.buscar_paginado(q="", limit=1, offset=0)
    assert len(rows3) <= 1 and total3 >= total


def test_pago_buscar_paginado_real(crear_matricula, usuario_admin):
    from services import pago_service
    from repositories import pago_repository

    m = crear_matricula()
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"],
        "id_cuota": m["id_cuota"],
        "monto_pagado": 10.0,
        "metodo_pago": "EFECTIVO",
    })
    assert ok
    rows, total = pago_repository.buscar_paginado(q="", limit=50, offset=0)
    assert total >= 1 and rows
    rows2, total2 = pago_repository.buscar_paginado(q="zzz-sin-coincidencia", limit=50, offset=0)
    assert total2 == 0 and rows2 == []


def test_matricula_buscar_paginado_real(crear_matricula):
    from repositories import matricula_repository

    crear_matricula()
    rows, total = matricula_repository.buscar_paginado(q="", limit=50, offset=0)
    assert total >= 1 and rows
    assert "dni" in rows[0] and "nombres" in rows[0]


# ── UI: combo compra cargado al instanciar (A1) ───────────────────

pytestmark_ui = pytest.mark.ui


@pytestmark_ui
def test_inventario_combo_compra_cargado_al_instanciar(crear_vista, usuario_admin):
    from views.inventario.inventario_view import InventarioView
    from services import inventario_service

    cats = inventario_service.listar_categorias()
    id_cat = cats[0]["id_categoria_producto"] if cats else inventario_service.crear_categoria({"nombre": "UICat"})[2]
    inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Producto Combo QA", "tipo_uso": "VENTA",
    })

    vista = crear_vista(InventarioView)
    assert vista._productos_compra_map, "combo compra vacío al instanciar (bug A1)"
    assert "Producto Combo QA" in " ".join(vista._productos_compra_map.keys())
    assert vista.combo_producto_compra.cget("values")
