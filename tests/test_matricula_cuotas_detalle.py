"""Matrículas tab Cuotas: detalle expandible con pagos aplicados."""
import pytest

pytestmark = pytest.mark.ui


def test_detalle_cuota_muestra_pagos(crear_vista, usuario_admin, crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    from services import pago_service
    from repositories import cuota_repository
    m = crear_matricula()
    cuotas = cuota_repository.obtener_por_matricula(m["id_matricula"])
    assert cuotas
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": cuotas[0]["id_cuota"],
        "monto_pagado": 50.0, "metodo_pago": "EFECTIVO"})
    assert ok
    vista = crear_vista(MatriculaView)
    vista._ver_cuotas({"id_matricula": m["id_matricula"]})
    vista.update_idletasks()

    def _textos(w):
        out = []
        try:
            t = w.cget("text")
            if t:
                out.append(str(t))
        except Exception:
            pass
        for ch in w.winfo_children():
            out += _textos(ch)
        return out

    # abrir todos los detalles de la pestaña Cuotas
    for card in vista.scroll_cuotas.winfo_children():
        for ch in card.winfo_children():
            try:
                if "Ver detalle" in str(ch.cget("text")):
                    ch.invoke()
            except Exception:
                pass
    vista.update_idletasks()
    todo = " ".join(_textos(vista.scroll_cuotas))
    assert "S/50.00" in todo and "EFECTIVO" in todo, todo


def _textos_de(w):
    out = []

    def _rec(x):
        try:
            t = x.cget("text")
            if t:
                out.append(str(t))
        except Exception:
            pass
        for ch in x.winfo_children():
            _rec(ch)

    _rec(w)
    return " ".join(out)


def test_historial_agrupa_matriculas(crear_vista, usuario_admin, crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    from services import estudiante_service
    m = crear_matricula()
    # retiro + reingreso + 2da matrícula: el reingreso se consume (ACTIVO)
    # y el historial muestra ambos grupos (cerrado + activo).
    estudiante_service.registrar_retiro(m["id_estudiante"], 1, "2026-06-30")
    estudiante_service.registrar_reingreso(m["id_estudiante"], 1)
    m2 = crear_matricula(id_estudiante=m["id_estudiante"])
    assert m2["id_matricula"] != m["id_matricula"]
    vista = crear_vista(MatriculaView)
    vista._ver_cuotas({"id_matricula": m2["id_matricula"]})
    vista.update_idletasks()
    todo = _textos_de(vista.scroll_cuotas)
    assert f"#{m['id_matricula']}" in todo and f"#{m2['id_matricula']}" in todo, todo
    assert "RETIRADO" in todo and "ACTIVO" in todo, todo


def test_badge_reingresante_sin_matricula_nueva(crear_vista, usuario_admin,
                                                crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    from services import estudiante_service
    m = crear_matricula()
    estudiante_service.registrar_retiro(m["id_estudiante"], 1, "2026-06-30")
    estudiante_service.registrar_reingreso(m["id_estudiante"], 1)
    vista = crear_vista(MatriculaView)
    vista._ver_cuotas({"id_matricula": m["id_matricula"]})
    vista.update_idletasks()
    todo = _textos_de(vista.scroll_cuotas)
    assert "Reingresante" in todo, todo
