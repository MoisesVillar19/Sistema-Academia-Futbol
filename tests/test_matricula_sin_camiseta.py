"""B4: matrícula sin extras (van por Ventas/Uniformes); regalo RN-051 intacto."""
import pytest

pytestmark = pytest.mark.ui

from services import inventario_service


def test_form_sin_extras_con_uniforme(crear_vista, usuario_admin):
    from views.matriculas.matricula_view import MatriculaView
    vista = crear_vista(MatriculaView)
    assert not hasattr(vista, "frame_productos")
    assert vista.var_incluye_uniforme.get() is False
    assert vista.seg_tipo_uniforme is not None
    assert vista.combo_talla_uniforme is not None


def test_regalo_nuevo_sigue_intacto():
    # RN-051 cubierto en test_matricula_express; aquí solo humo del service
    from services import matricula_service
    ok, msg, ids = matricula_service.matricula_express({
        "tipo": "NUEVO", "nombres": "Regalo", "apellidos": "Intacto",
        "dni": "71717176", "metodo_pago": "EFECTIVO",
    })
    assert ok, msg
