"""Filtro Becados: backend + segmento + badge + grilla."""
import pytest

pytestmark = pytest.mark.ui

from controllers import estudiante_controller
from services import matricula_service
from database.connection import fetch_one


def _mat_con_beca(crear_estudiante, obtener_tarifa, beca="1/2 BECA", monto=120.0):
    bid = fetch_one("SELECT id_beca FROM beca WHERE nombre = ?", (beca,))["id_beca"]
    id_tarifa, _ = obtener_tarifa(monto=monto)
    ok, _, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": monto, "dia_vencimiento": 5,
        "becas": [{"id_beca": bid}],
    })
    assert ok
    return id_mat


def test_listar_becados(crear_estudiante, obtener_tarifa):
    _mat_con_beca(crear_estudiante, obtener_tarifa)
    crear_estudiante()  # sin beca
    becados = estudiante_controller.listar_becados()
    assert len(becados) == 1
    assert becados[0]["beca_nombre"] == "1/2 BECA"


def test_segmento_becados(crear_vista, usuario_admin, crear_estudiante, obtener_tarifa):
    from views.estudiantes.estudiante_view import EstudianteView
    _mat_con_beca(crear_estudiante, obtener_tarifa, beca="BECA COMPLETA")
    crear_estudiante(nombres="Sin", apellidos="Beca7b")
    vista = crear_vista(EstudianteView)
    vista.filtro_estado.set("Becados")
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text")


def _textos(w):
    out = []
    vistos = set()

    def _rec(x):
        try:
            key = str(x)
        except Exception:
            return
        if key in vistos:
            return
        vistos.add(key)
        try:
            t = x.cget("text")
            if t:
                out.append(str(t))
        except Exception:
            pass
        try:
            for h in x.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(w)
    return " ".join(out)


def test_badge_y_columna(crear_vista, usuario_admin, crear_estudiante, obtener_tarifa):
    from views.estudiantes.estudiante_view import EstudianteView
    _mat_con_beca(crear_estudiante, obtener_tarifa)
    vista = crear_vista(EstudianteView)
    vista.filtro_estado.set("Becados")
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "1/2 BECA" in _textos(vista.scroll_estudiantes)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    todo = _textos(vista.scroll_estudiantes)
    assert "Beca" in todo and "1/2 BECA" in todo


def test_grilla_marca_becados(crear_vista, usuario_admin, crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    crear_matricula()
    vista = crear_vista(MatriculaView)
    vista.tabview.set("Año")
    vista.update_idletasks()
    assert vista.tab_grilla.winfo_exists()
