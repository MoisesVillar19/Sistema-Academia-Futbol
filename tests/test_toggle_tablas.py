"""Fase 7b: toggle Cards/Tabla en Pagos, Estudiantes, Matrículas, Ventas, Egresos."""
import pytest

pytestmark = pytest.mark.ui


def _textos(w):
    out = []

    def _rec(x):
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


def test_pagos_toggle(crear_vista, usuario_admin, crear_matricula):
    from views.pagos.pago_view import PagoView
    from services import pago_service
    m = crear_matricula()
    pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": 10.0, "metodo_pago": "EFECTIVO"})
    vista = crear_vista(PagoView)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    todo = _textos(vista.scroll_pagos)
    assert "Recibo" in todo and "Método" in todo
    vista._on_vista_cambiar("Cards")
    vista.update_idletasks()


def test_estudiantes_toggle(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    crear_estudiante(nombres="Tabla", apellidos="Toggle7b")
    vista = crear_vista(EstudianteView)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    todo = _textos(vista.scroll_estudiantes)
    assert "Estudiante" in todo and "Toggle7b" in todo
    vista._on_vista_cambiar("Cards")


def test_matriculas_toggle(crear_vista, usuario_admin, crear_matricula):
    from views.matriculas.matricula_view import MatriculaView
    crear_matricula()
    vista = crear_vista(MatriculaView)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    assert "Tarifa" in _textos(vista.scroll_matriculas)
    vista._on_vista_cambiar("Cards")


def test_ventas_toggle(crear_vista, usuario_admin):
    from views.ventas.venta_view import VentaView
    from services import inventario_service, venta_service
    cats = inventario_service.listar_categorias()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "VT7b", "canal": "TIENDITA", "precio_venta": 5.0})
    assert ok
    inventario_service.registrar_compra({
        "id_producto": id_prod, "cantidad": 3, "monto_total": "6.00",
        "metodo_pago": "EFECTIVO"})
    venta_service.registrar_venta({
        "tipo_venta": "TIENDA", "metodo_pago": "EFECTIVO",
        "items": [{"id_producto": id_prod, "cantidad": 1}],
        "id_usuario": usuario_admin["id_usuario"]})
    vista = crear_vista(VentaView)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    assert "Recibo" in _textos(vista.scroll)
    vista._on_vista_cambiar("Cards")


def test_egresos_toggle(crear_vista, usuario_admin):
    from views.egresos.egreso_view import EgresoView
    from controllers import egreso_controller
    ok, _, _ = egreso_controller.registrar_egreso({
        "concepto": "VIATICOS", "monto": 12.5, "fecha": "2026-01-05",
        "responsable": "QA", "observacion": "", "id_tarifa": None})
    assert ok
    vista = crear_vista(EgresoView)
    vista._on_vista_cambiar("Tabla")
    vista.update_idletasks()
    todo = _textos(vista.scroll)
    assert "Concepto" in todo and "VIATICOS" in todo
    vista._on_vista_cambiar("Cards")
