"""Regresion: cada card de las 6 vistas lista tiene boton Ver detalle
que expande el bloque inline al hacer clic (y lo colapsa al re-clic)."""
import pytest

pytestmark = pytest.mark.ui

from views.estudiantes.estudiante_view import EstudianteView
from views.pagos.pago_view import PagoView
from views.egresos.egreso_view import EgresoView
from views.ventas.venta_view import VentaView
from views.matriculas.matricula_view import MatriculaView
from views.inventario.inventario_view import InventarioView


def _toggles_en(widget):
    out = []

    def _rec(w):
        try:
            if "ver detalle" in str(w.cget("text")).lower() or "ocultar" in str(w.cget("text")).lower():
                out.append(w)
        except Exception:
            pass
        for ch in w.winfo_children():
            _rec(ch)

    _rec(widget)
    return out


def _verificar_toggle(ctk_root, contenedor):
    ctk_root.update_idletasks()
    cards = list(contenedor.winfo_children())
    assert cards, "no se creo ninguna card"
    toggles = _toggles_en(cards[-1])
    assert toggles, "la card no tiene boton Ver detalle"
    btn = toggles[0]
    btn.invoke()
    ctk_root.update_idletasks()
    assert "ocultar" in str(btn.cget("text")).lower(), f"no abrio: {btn.cget('text')}"
    # el detalle debe tener filas pobladas
    assert len(cards[-1].winfo_children()) >= 3, "detalle vacio"
    btn.invoke()
    ctk_root.update_idletasks()
    assert "ver detalle" in str(btn.cget("text")).lower(), "no colapso"


def test_toggle_estudiante(crear_vista, usuario_admin, ctk_root):
    vista = crear_vista(EstudianteView)
    vista._crear_card_estudiante({"id_estudiante": 9999, "nombres": "Test", "apellidos": "Demo",
                                  "dni": "12345678", "estado": "ACTIVO", "es_nuevo": 0})
    _verificar_toggle(ctk_root, vista.scroll_estudiantes)


def test_toggle_pago(crear_vista, usuario_admin, ctk_root):
    vista = crear_vista(PagoView)
    vista._crear_card_pago({"id_pago": 1, "numero_recibo": "R-001", "monto_total": 50.0,
                            "metodo_pago": "EFECTIVO", "fecha_pago": "2026-01-01", "username": "admin"})
    _verificar_toggle(ctk_root, vista.scroll_pagos)


def test_toggle_egreso(crear_vista, usuario_admin, ctk_root, monkeypatch):
    import controllers.egreso_controller as ec
    monkeypatch.setattr(ec, "listar_egresos", lambda *a, **k: [
        {"id_egreso": 1, "concepto": "PROFESOR", "monto": 200.0,
         "fecha": "2026-01-01", "responsable": "Juan", "observacion": "Enero"}])
    vista = crear_vista(EgresoView)
    _verificar_toggle(ctk_root, vista.scroll)


def test_toggle_venta(crear_vista, usuario_admin, ctk_root, monkeypatch):
    import controllers.venta_controller as vc
    monkeypatch.setattr(vc, "listar_ventas", lambda *a, **k: [
        {"id_venta": 1, "tipo_venta": "UNIFORME", "numero_recibo": "V-001",
         "monto_total": 60.0, "metodo_pago": "EFECTIVO", "fecha_venta": "2026-01-01"}])
    vista = crear_vista(VentaView)
    _verificar_toggle(ctk_root, vista.scroll)


def test_toggle_matricula(crear_vista, usuario_admin, ctk_root):
    vista = crear_vista(MatriculaView)
    vista._crear_card({"id_matricula": 1, "nombres": "Test", "apellidos": "Demo",
                       "dni": "12345678", "tarifa_nombre": "Mensual", "tarifa_monto": 100.0,
                       "fecha_inicio": "2026-01-01", "dia_vencimiento": 1})
    _verificar_toggle(ctk_root, vista.scroll_matriculas)


def test_toggle_inventario(crear_vista, usuario_admin, ctk_root):
    vista = crear_vista(InventarioView)
    vista._crear_card_producto({"id_producto": 1, "codigo": "C-001", "nombre": "Camiseta",
                                "categoria_nombre": "Uniforme", "canal": "TIENDITA",
                                "precio_compra": 10.0, "precio_venta": 20.0,
                                "stock_actual": 5, "stock_minimo": 2})
    _verificar_toggle(ctk_root, vista.scroll_productos)
