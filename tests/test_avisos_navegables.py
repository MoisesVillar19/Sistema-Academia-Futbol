"""E3: avisos con origen navegable + omitir/reactivar."""
import pytest

pytestmark = pytest.mark.ui

from services import avisos_service


def _legacy_yape():
    from utils.dates import get_today
    from database.connection import get_connection
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO pago (id_usuario, numero_recibo, fecha_pago, monto_total,
                             metodo_pago, observacion, comprobante_path, activo)
           VALUES (1, 'Y-NAV-001', ?, 50.0, 'YAPE', '', '', 1)""",
        (get_today(),))
    conn.commit()
    return cur.lastrowid


def test_aviso_trae_ir(usuario_admin):
    _legacy_yape()
    av = next(a for a in avisos_service.obtener_avisos() if a["codigo"] == "comprobantes")
    assert av["ir"] == {"modulo": "pagos", "params": {"filtro": "pendientes"}}


def test_omitir_y_reactivar(usuario_admin):
    id_pago = _legacy_yape()
    assert any(a["codigo"] == "comprobantes" for a in avisos_service.obtener_avisos())
    avisos_service.omitir_aviso("comprobantes", "legado revisado", "pago", id_pago)
    assert avisos_service.listar_pagos_sin_comprobante() == []
    om = avisos_service.listar_omitidos()
    assert any(o["codigo"] == "comprobantes" for o in om)
    avisos_service.reactivar_aviso("comprobantes", "pago", id_pago)
    assert len(avisos_service.listar_pagos_sin_comprobante()) == 1


def test_omitir_grupo(usuario_admin):
    _legacy_yape()
    avisos_service.omitir_aviso("comprobantes", "todo revisado")
    assert not any(a["codigo"] == "comprobantes" for a in avisos_service.obtener_avisos())
    avisos_service.reactivar_aviso("comprobantes")
    assert any(a["codigo"] == "comprobantes" for a in avisos_service.obtener_avisos())


def test_pagos_aplicar_navegacion(crear_vista, usuario_admin):
    from views.pagos.pago_view import PagoView
    _legacy_yape()
    vista = crear_vista(PagoView)
    vista.aplicar_navegacion({"filtro": "pendientes"})
    vista.update_idletasks()
    assert "pendiente" in vista.label_status.cget("text").lower()
    vista.aplicar_navegacion({"busqueda": "Y-NAV-001"})
    vista.update_idletasks()
    assert vista._total >= 1


def test_estudiantes_aplicar_navegacion(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    crear_estudiante(nombres="Navega", apellidos="Origen")
    vista = crear_vista(EstudianteView)
    vista.aplicar_navegacion({"busqueda": "Navega"})
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text")


def test_inventario_aplicar_navegacion(crear_vista, usuario_admin):
    from views.tiendita.tiendita_view import TienditaView
    from services import inventario_service
    cats = inventario_service.listar_categorias()
    inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "NavegaProd", "canal": "TIENDITA"})
    vista = crear_vista(TienditaView)
    vista.aplicar_navegacion({"busqueda": "NavegaProd"})
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status.cget("text")


def test_detalle_con_ir(crear_vista, usuario_admin):
    from views.dashboard.dashboard_view import DashboardView
    _legacy_yape()
    vista = crear_vista(DashboardView)
    vista._mostrar_detalle("comprobantes")
    vista.update_idletasks()

    textos = []
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
                textos.append(str(t))
        except Exception:
            pass
        try:
            for h in x.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(vista.detalle_frame)
    todo = " ".join(textos)
    assert "Ir →" in todo and "Omitir" in todo and "Y-NAV-001" in todo
