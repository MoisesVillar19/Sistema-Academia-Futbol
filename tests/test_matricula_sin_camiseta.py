"""Fase 5: matrícula no ofrece camiseta/uniformes (van por Tienda); regalo RN-051 intacto."""
import pytest

pytestmark = pytest.mark.ui

from services import inventario_service


def _uniforme_y_extra():
    cats = inventario_service.listar_categorias()
    id_cat = cats[0]["id_categoria_producto"]
    from controllers import tipo_uniforme_controller
    try:
        tipos = tipo_uniforme_controller.listar_tipos()
    except Exception:
        from services import tipo_uniforme_service
        tipos = tipo_uniforme_service.listar_tipos()
    id_tipo = tipos[0]["id_tipo_uniforme"]
    ok, _, id_uni = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Uniforme Extra QA",
        "canal": "TIENDITA", "precio_venta": 70.0, "id_tipo_uniforme": id_tipo,
    })
    assert ok
    ok, _, id_ext = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "Extra NoUniforme QA",
        "canal": "TIENDITA", "precio_venta": 5.0,
    })
    assert ok
    return id_uni, id_ext


def test_extras_excluyen_uniformes(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    id_uni, id_ext = _uniforme_y_extra()
    vista = crear_vista(MatriculaView)
    ids = {p["id_producto"] for p in vista._productos_disponibles}
    assert id_ext in ids
    assert id_uni not in ids
    assert not any(p.get("codigo") == "CAMISETA-ENT" for p in vista._productos_disponibles)


def test_regalo_nuevo_sigue_intacto():
    # RN-051 cubierto en test_matricula_express; aquí solo humo del service
    from services import matricula_service
    ok, msg, ids = matricula_service.matricula_express({
        "tipo": "NUEVO", "nombres": "Regalo", "apellidos": "Intacto",
        "dni": "71717176", "metodo_pago": "EFECTIVO",
    })
    assert ok, msg
