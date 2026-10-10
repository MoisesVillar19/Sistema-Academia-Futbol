"""v1.2.1: uniformes N tipos dinámicos + CRUD + independencia + importador.

Service: tipos_vendibles, slug UNI-XXX único, asegurar/crear/desactivar.
Vistas: Uniformes CRUD + combo dinámico, Matrícula segmentado dinámico,
Tiendita/Almacén/Ventas excluyen N tipos. Importador: nombres nuevos +
choques de código.
"""
import pytest


def _crear_tipo(nombre):
    from services import tipo_uniforme_service
    ok, msg, tid = tipo_uniforme_service.crear_tipo_uniforme({"nombre": nombre})
    assert ok, msg
    return tid


# ── service: registro dinámico ──────────────────────────────────────

def test_tipos_vendibles_incluye_legacy():
    from services import uniforme_service
    # COM se crea a demanda (el seed solo trae CAMISETA-ENT).
    ok, msg, _ = uniforme_service.asegurar_producto("COM")
    assert ok, msg
    vend = uniforme_service.tipos_vendibles()
    claves = {v["clave"] for v in vend}
    assert {"ENT", "COM"} <= claves
    ent = next(v for v in vend if v["clave"] == "ENT")
    assert ent["codigo"] == "CAMISETA-ENT" and ent["tipo_venta"] == "UNIFORME"
    com = next(v for v in vend if v["clave"] == "COM")
    assert com["codigo"] == "UNIFORME-COM" and com["tipo_venta"] == "TIENDA"


def test_crear_producto_uniforme_nuevo_tipo(usuario_admin):
    from services import uniforme_service
    from repositories import producto_repository
    ok, msg, pid = uniforme_service.crear_producto_uniforme(
        "Uniforme Arquero", 80.0, 5)
    assert ok, msg
    prod = producto_repository.obtener_por_id(pid)
    assert prod["codigo"] == "UNI-ARQUERO"
    assert prod["canal"] == "TIENDITA"
    assert prod["id_tipo_uniforme"] is not None
    assert float(prod["precio_venta"]) == 80.0
    vend = uniforme_service.tipos_vendibles()
    arq = next(v for v in vend if v["nombre"] == "Uniforme Arquero")
    assert arq["codigo"] == "UNI-ARQUERO" and arq["tipo_venta"] == "TIENDA"


def test_crear_producto_uniforme_duplicado_rechaza(usuario_admin):
    from services import uniforme_service
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    ok2, msg2, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert not ok2 and "ya tiene producto" in msg2


def test_slug_unico_ante_choque_codigo(usuario_admin):
    from services import uniforme_service, inventario_service
    cats = inventario_service.listar_categorias()
    ok, _, _ = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "Tienda Arquero", "codigo": "UNI-ARQUERO",
        "canal": "TIENDITA", "precio_venta": 50.0, "stock_inicial": 0})
    assert ok
    ok, msg, pid = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok, msg
    from repositories import producto_repository
    assert producto_repository.obtener_por_id(pid)["codigo"] == "UNI-ARQUERO-2"


def test_nombre_reservado_com_ent_rechaza(usuario_admin):
    from services import uniforme_service
    ok, msg, _ = uniforme_service.crear_producto_uniforme("Ent", 70.0, 0)
    assert not ok and "reservado" in msg


def test_asegurar_tipo_inexistente_rechaza():
    from services import uniforme_service
    ok, msg, _ = uniforme_service.asegurar_producto("XXX")
    assert not ok and "Válidos" in msg


def test_tipo_nuevo_competencia_en_nombre_no_colapsa_a_com(usuario_admin):
    from services import uniforme_service
    ok, msg, _ = uniforme_service.asegurar_producto("COM")
    assert ok, msg
    ok, msg, _ = uniforme_service.crear_producto_uniforme(
        "Uniforme Competencia Reserva", 70.0, 0)
    assert ok, msg
    vend = uniforme_service.tipos_vendibles()
    res = next(v for v in vend if v["nombre"] == "Uniforme Competencia Reserva")
    assert res["clave"] == "Uniforme Competencia Reserva"
    assert [v["clave"] for v in vend].count("COM") == 1


def test_venta_tipo_nuevo_con_talla(usuario_admin, crear_estudiante):
    from controllers import venta_controller
    from repositories import producto_repository
    from services import uniforme_service
    ok, msg, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok, msg
    ok, msg = uniforme_service.agregar_talla("Uniforme Arquero", "M", 3)
    assert ok, msg
    tallas = uniforme_service.tallas_disponibles("Uniforme Arquero")
    assert len(tallas) == 1 and tallas[0]["stock"] == 3
    eid = crear_estudiante()
    ok, msg, vid = venta_controller.registrar_venta_uniforme({
        "id_estudiante": eid, "tipo": "Uniforme Arquero",
        "id_variante": tallas[0]["id_variante"],
        "fecha_venta": "2026-10-09", "metodo_pago": "EFECTIVO"})
    assert ok, msg
    assert vid is not None
    prod = producto_repository.obtener_por_codigo("UNI-ARQUERO")
    assert (prod.get("stock_actual") or 0) == 0, "compra 1 - venta 1"


def test_tipo_desactivado_se_oculta_historial_intacto(usuario_admin, crear_estudiante):
    from controllers import venta_controller
    from services import uniforme_service, tipo_uniforme_service, venta_service
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    eid = crear_estudiante()
    ok, msg, vid = venta_controller.registrar_venta_uniforme({
        "id_estudiante": eid, "tipo": "Uniforme Arquero",
        "fecha_venta": "2026-10-09", "metodo_pago": "EFECTIVO"})
    assert ok, msg
    tipos = tipo_uniforme_service.listar_tipos()
    tid = next(t["id_tipo_uniforme"] for t in tipos if t["nombre"] == "Uniforme Arquero")
    ok, msg = tipo_uniforme_service.desactivar_tipo(tid)
    assert ok, msg
    assert all(v["nombre"] != "Uniforme Arquero"
               for v in uniforme_service.tipos_vendibles())
    assert venta_service.obtener_venta(vid) is not None


def test_desactivar_producto_uniforme(usuario_admin):
    from services import uniforme_service
    from repositories import producto_repository
    ok, _, pid = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    ok, msg = uniforme_service.desactivar_producto_uniforme(pid)
    assert ok, msg
    assert producto_repository.obtener_por_id(pid)["activo"] == 0
    assert all(v["nombre"] != "Uniforme Arquero"
               for v in uniforme_service.tipos_vendibles())


# ── independencia: Tiendita / Almacén / Ventas ──────────────────────

def test_buscar_paginado_excluir_uniformes_dinamico(usuario_admin):
    from services import uniforme_service
    from repositories import producto_repository
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    rows, _ = producto_repository.buscar_paginado(q="", excluir_uniformes=True)
    codigos = {r["codigo"] for r in rows}
    assert "UNI-ARQUERO" not in codigos
    assert "CAMISETA-ENT" not in codigos
    rows2, _ = producto_repository.buscar_paginado(q="")
    assert "UNI-ARQUERO" in {r["codigo"] for r in rows2}


def test_tiendita_oculta_tipo_nuevo(crear_vista, usuario_admin):
    from services import uniforme_service
    from views.tiendita.tiendita_view import TienditaView
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    vista = crear_vista(TienditaView)
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

    todo = " ".join(_textos(vista.scroll_productos))
    assert "UNI-ARQUERO" not in todo
    assert "Uniforme Arquero" not in todo


def test_venta_view_oculta_uniformes(crear_vista, usuario_admin):
    from services import uniforme_service
    from views.ventas.venta_view import VentaView
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    vista = crear_vista(VentaView)
    vista.update_idletasks()
    prods = list(getattr(vista, "_productos_map", {}).values())
    assert all(p.get("id_tipo_uniforme") is None for p in prods)


# ── vistas Uniformes / Matrícula dinámicas ──────────────────────────

@pytest.mark.ui
def test_uniformes_combo_muestra_nuevo_tipo(crear_vista, usuario_admin):
    from services import uniforme_service
    from views.uniformes.uniforme_view import UniformesView
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    vista = crear_vista(UniformesView)
    vista.update_idletasks()
    valores = vista.combo_tipo.cget("values")
    assert "Uniforme Arquero" in valores
    assert vista._tipos_uni_map["Uniforme Arquero"] == "Uniforme Arquero"


@pytest.mark.ui
def test_matricula_segmento_muestra_nuevo_tipo(crear_vista, usuario_admin):
    from services import uniforme_service
    from views.matriculas.matricula_view import MatriculaView
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    vista = crear_vista(MatriculaView)
    vista.update_idletasks()
    valores = vista.seg_tipo_uniforme.cget("values")
    assert "Uniforme Arquero" in valores
    assert vista._tipo_uniforme_sel() in ("ENT", "COM", "Uniforme Arquero")


# ── importador: nombres nuevos + choques ────────────────────────────

def _fila_uniforme(**kw):
    base = {"DNI": "12345678", "TIPO": "COM", "MONTO": "30.00",
            "FECHA": "2026-05-15", "METODO": "EFECTIVO"}
    base.update(kw)
    return base


def _estudiante_dni(dni="12345678"):
    from repositories import persona_repository, estudiante_repository
    from models.persona import Persona
    from models.estudiante import Estudiante
    pid = persona_repository.insertar(Persona(
        dni=dni, nombres="Uni", apellidos="Forme",
        fecha_nacimiento="2015-01-01", sexo="M"))
    return estudiante_repository.insertar(Estudiante(id_persona=pid, estado="ACTIVO"))


def test_importar_tipo_nuevo_por_nombre(usuario_admin):
    from services import importar_service, uniforme_service, venta_service
    from repositories import producto_repository
    _estudiante_dni()
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    ok, msg, res = importar_service.importar_uniformes(
        [_fila_uniforme(TIPO="Uniforme Arquero", MONTO="80.00")], id_usuario=1)
    assert ok, res
    assert res["ventas"] == 1, res
    ventas = venta_service.listar_ventas("2026-01-01", "2026-12-31")
    assert any(v["tipo_venta"] == "TIENDA" and float(v["monto_total"]) == 80.0
               for v in ventas), ventas
    assert sum(1 for p in producto_repository.obtener_todos()
               if (p.get("codigo") or "").startswith("UNI-ARQUERO")) == 1


def test_importar_no_choca_codigo_tienda(usuario_admin):
    from services import importar_service, inventario_service, uniforme_service
    _estudiante_dni()
    cats = inventario_service.listar_categorias()
    ok, _, _ = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": "Tienda Arquero", "codigo": "UNI-ARQUERO",
        "canal": "TIENDITA", "precio_venta": 50.0, "stock_inicial": 0})
    assert ok
    # El código de tienda NO debe resolverse como uniforme.
    ok, _, e = importar_service.validar_filas_uniformes([_fila_uniforme(TIPO="UNI-ARQUERO")])
    assert not ok and any("TIPO" in x for x in e)
    # El tipo uniforme convive con slug -2 y se vende bien.
    ok, msg, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok, msg
    ok, msg, res = importar_service.importar_uniformes(
        [_fila_uniforme(TIPO="Uniforme Arquero", MONTO="80.00")], id_usuario=1)
    assert ok, res
    assert res["ventas"] == 1, res


def test_importar_legacy_com_intacto_con_tipos_nuevos(usuario_admin):
    from services import importar_service, uniforme_service
    from repositories import producto_repository
    _estudiante_dni()
    ok, _, _ = uniforme_service.crear_producto_uniforme("Uniforme Arquero", 80.0, 0)
    assert ok
    ok, msg, res = importar_service.importar_uniformes(
        [_fila_uniforme(TIPO="COM", MONTO="30.00")], id_usuario=1)
    assert ok, res
    assert res["ventas"] == 1, res
    assert producto_repository.obtener_por_codigo("UNIFORME-COM") is not None
