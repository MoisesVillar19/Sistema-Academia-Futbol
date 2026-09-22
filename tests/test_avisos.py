"""Fase 1: avisos por módulo (comprobantes, vencidas, stock, sin apoderado)."""
import pytest

from services import avisos_service, inventario_service
from repositories import pago_repository
from database.connection import get_connection


def _pago_legacy_sin_comprobante():
    """Simula pago histórico pre-Fase-0 (YAPE exigido pero archivo descartado)."""
    from utils.dates import get_today
    from models.pago import Pago
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO pago (id_usuario, numero_recibo, fecha_pago, monto_total,
                             metodo_pago, observacion, comprobante_path, activo)
           VALUES (1, 'Y-LEGACY-001', ?, 50.0, 'YAPE', '', '', 1)""",
        (get_today(),))
    conn.commit()
    return cur.lastrowid


def test_pagos_sin_comprobante_detectados(usuario_admin):
    _pago_legacy_sin_comprobante()
    rows = avisos_service.listar_pagos_sin_comprobante()
    assert any(r["numero_recibo"] == "Y-LEGACY-001" for r in rows)
    avisos = avisos_service.obtener_avisos()
    comp = next(a for a in avisos if a["codigo"] == "comprobantes")
    assert comp["modulo"] == "pagos" and comp["severidad"] == "alta"


def test_pago_con_comprobante_no_avisa(crear_matricula, usuario_admin):
    from services import pago_service
    m = crear_matricula()
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"],
        "id_cuota": m["id_cuota"],
        "monto_pagado": 10.0,
        "metodo_pago": "EFECTIVO",
    })
    assert ok
    assert avisos_service.listar_pagos_sin_comprobante() == []


def test_stock_bajo_avisa():
    cats = inventario_service.listar_categorias()
    id_cat = cats[0]["id_categoria_producto"]
    ok, _, _ = inventario_service.crear_producto({
        "id_categoria_producto": id_cat, "nombre": "BajoQA",
        "canal": "ALMACEN", "stock_minimo": 5,
    })
    assert ok
    avisos = avisos_service.obtener_avisos()
    stock = next(a for a in avisos if a["codigo"] == "stock_bajo")
    assert stock["modulo"] == "inventario"


def test_vencidas_y_por_vencer_avisan(monkeypatch):
    from services import cuota_service
    monkeypatch.setattr(cuota_service, "obtener_vencidas", lambda: [{"id_cuota": 1}])
    monkeypatch.setattr(cuota_service, "obtener_por_vencer", lambda: [{"id_cuota": 2}])
    avisos = {a["codigo"]: a for a in avisos_service.obtener_avisos()}
    assert avisos["vencidas"]["severidad"] == "alta"
    assert avisos["por_vencer"]["severidad"] == "media"


def test_matricula_sin_apoderado_avisa(crear_matricula):
    crear_matricula()
    mats = avisos_service.listar_matriculas_sin_apoderado()
    assert len(mats) >= 1
    avisos = avisos_service.obtener_avisos()
    assert any(a["codigo"] == "sin_apoderado" for a in avisos)


def test_avisos_por_modulo_filtra(crear_matricula):
    crear_matricula()
    assert all(a["modulo"] == "matriculas"
               for a in avisos_service.avisos_por_modulo("matriculas"))


pytestmark = pytest.mark.ui


def test_dashboard_muestra_pendientes(crear_vista, usuario_admin, crear_matricula):
    from views.dashboard.dashboard_view import DashboardView
    crear_matricula()  # sin apoderado → aviso
    vista = crear_vista(DashboardView)
    textos = []

    def _rec(w):
        try:
            t = w.cget("text")
            if t:
                textos.append(str(t))
        except Exception:
            pass
        try:
            for h in w.winfo_children():
                _rec(h)
        except Exception:
            pass

    _rec(vista)
    todo = " ".join(textos)
    assert "Pendientes" in todo
    assert "sin apoderado principal" in todo


def test_pagos_banner_y_filtro_pendientes(crear_vista, usuario_admin):
    from views.pagos.pago_view import PagoView
    _pago_legacy_sin_comprobante()
    vista = crear_vista(PagoView)
    vista.update_idletasks()
    assert "Y-LEGACY-001" not in str(vista.label_status.cget("text"))
    vista._ver_pendientes()
    vista.update_idletasks()
    assert "pendiente" in vista.label_status.cget("text").lower()
    vista._ver_todos()
    vista.update_idletasks()
