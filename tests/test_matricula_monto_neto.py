"""G2: mensualidad neta (pactado o tarifa menos becas) en lista/detalle."""
from services import matricula_service


def test_monto_mensual_sin_beca():
    assert matricula_service.monto_mensual({"tarifa_monto": 100.0}) == 100.0
    assert matricula_service.monto_mensual(
        {"monto_pactado": 150.0, "tarifa_monto": 100.0}) == 150.0


def test_monto_mensual_con_beca():
    assert matricula_service.monto_mensual({
        "tarifa_monto": 100.0,
        "becas_info": "1/2 BECA|MONTO_FIJO|50"}) == 50.0
    assert matricula_service.monto_mensual({
        "tarifa_monto": 120.0,
        "becas_info": "BECA COMPLETA|PORCENTAJE|100"}) == 0.0
    assert matricula_service.monto_mensual({
        "tarifa_monto": 200.0,
        "becas": [("PORCENTAJE", 50.0)]}) == 100.0


def test_lista_muestra_neto(crear_vista, usuario_admin, crear_matricula):
    import pytest
    pytest.importorskip("customtkinter")
    from views.matriculas.matricula_view import MatriculaView
    from services import matricula_service
    from repositories import beca_repository
    from models.beca import Beca
    m = crear_matricula(monto_pactado=100.0)
    bid = beca_repository.insertar(Beca(nombre="Media QA", tipo="MONTO_FIJO",
                                        valor=50.0, activo=1))
    ok, _ = matricula_service.asignar_beca(m["id_matricula"], bid, "QA")
    assert ok
    vista = crear_vista(MatriculaView)
    vista._vista_modo = "Tabla"
    vista._cargar_matriculas()
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

    todo = " ".join(_textos(vista.scroll_matriculas))
    assert "S/50.00" in todo, todo
