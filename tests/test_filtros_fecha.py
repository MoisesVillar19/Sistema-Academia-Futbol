"""Filtros de fecha/mes (bugs reportados) + mapeo mensualidades."""
import pytest

pytestmark = pytest.mark.ui


def test_pagos_filtro_fecha_funciona(crear_vista, usuario_admin, crear_matricula):
    from views.pagos.pago_view import PagoView
    from services import pago_service
    m = crear_matricula()
    pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m["id_cuota"],
        "monto_pagado": 5.0, "metodo_pago": "EFECTIVO", "fecha_pago": "2026-03-10"})
    m2 = crear_matricula()
    pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": m2["id_cuota"],
        "monto_pagado": 5.0, "metodo_pago": "EFECTIVO", "fecha_pago": "2026-06-10"})
    vista = crear_vista(PagoView)
    vista.date_picker_inicio.set("2026-03-01")
    vista.date_picker_fin.set("2026-03-31")
    vista._buscar_por_fecha()
    vista.update_idletasks()
    assert vista._total == 1, f"filtro marzo debe dar 1, dio {vista._total}"
    vista._limpiar_fechas()
    vista.update_idletasks()
    assert vista._total == 2


def test_historial_filtro_fecha(crear_vista, usuario_admin):
    from views.almacen.almacen_view import AlmacenView
    from services import inventario_service
    cats = inventario_service.listar_categorias()
    ok, _, id_prod = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "Hist QA", "canal": "ALMACEN"})
    assert ok
    inventario_service.registrar_movimiento({
        "id_producto": id_prod, "tipo_movimiento": "ENTRADA", "cantidad": 3,
        "motivo": "QA", "id_usuario": usuario_admin["id_usuario"],
        "fecha_movimiento": "2026-02-05"})
    vista = crear_vista(AlmacenView)
    vista.tabview.set("Historial")
    vista.date_hist_ini.set("2026-02-01")
    vista.date_hist_fin.set("2026-02-28")
    vista._filtrar_historial()
    vista.update_idletasks()
    assert "Total: 1" in vista.label_status_hist.cget("text")
    vista.date_hist_ini.set("2026-03-01")
    vista.date_hist_fin.set("2026-03-31")
    vista._filtrar_historial()
    vista.update_idletasks()
    assert "Total: 0" in vista.label_status_hist.cget("text")


def test_estudiantes_filtro_ingreso(crear_vista, usuario_admin, crear_estudiante):
    from views.estudiantes.estudiante_view import EstudianteView
    crear_estudiante()
    vista = crear_vista(EstudianteView)
    vista.date_ing_ini.set("2026-01-01")
    vista.date_ing_fin.set("2026-12-31")
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "Total: 0" not in vista.label_status.cget("text")
    vista.date_ing_ini.set("2020-01-01")
    vista.date_ing_fin.set("2020-12-31")
    vista._on_busqueda_cambiar()
    vista.update_idletasks()
    assert "Total: 0" in vista.label_status.cget("text")


def test_cuotas_se_generan_y_mapean_mes(crear_estudiante, obtener_tarifa, usuario_admin):
    # matrícula → 1ra cuota; al pagarla completa → siguiente mes automática
    from services import matricula_service, cuota_service, pago_service
    from repositories import cuota_repository
    id_tarifa, _ = obtener_tarifa(monto=100.0)
    ok, _, id_mat = matricula_service.crear_matricula({
        "id_estudiante": crear_estudiante(), "id_tarifa": id_tarifa,
        "monto_pactado": 100.0, "dia_vencimiento": 5,
        "fecha_inicio": "2026-05-10",
    })
    assert ok
    cuotas = cuota_repository.obtener_por_matricula(id_mat)
    assert len(cuotas) == 1
    c1 = cuotas[0]
    ok, _, _ = pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": c1["id_cuota"],
        "monto_pagado": float(c1["saldo"]), "metodo_pago": "EFECTIVO"})
    assert ok
    cuotas = cuota_repository.obtener_por_matricula(id_mat)
    assert len(cuotas) == 2, "al cancelar debe generarse el mes siguiente"
    periodos = sorted(c["periodo"] for c in cuotas)
    assert periodos[0] < periodos[1], f"meses encadenados: {periodos}"
    # parcial NO genera siguiente
    c2 = [c for c in cuotas if c["estado"] != "PAGADO"][0]
    pago_service.registrar_pago({
        "id_usuario": usuario_admin["id_usuario"], "id_cuota": c2["id_cuota"],
        "monto_pagado": 10.0, "metodo_pago": "EFECTIVO"})
    assert len(cuota_repository.obtener_por_matricula(id_mat)) == 2
