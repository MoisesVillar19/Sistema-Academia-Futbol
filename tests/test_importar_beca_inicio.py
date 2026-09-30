"""Estudiantes: INICIO→fecha_ingreso, BECA→matrícula+beca, nav Siguiente."""
import pytest

pytestmark = pytest.mark.ui


def _fila(**kw):
    base = {"DNI": "87654321", "Nombres": "Beca", "Apellidos": "Test",
            "INICIO": "2026-03-10", "BECA": ""}
    base.update(kw)
    return base


def _beca_y_tarifa():
    from repositories import beca_repository, tarifa_repository
    from models.beca import Beca
    from database.connection import fetch_one
    bid = beca_repository.insertar(Beca(nombre="Beca Import Test", tipo="PORCENTAJE",
                                        valor=50.0, activo=1))
    cat = fetch_one("SELECT id_categoria FROM categoria WHERE activo = 1 LIMIT 1")
    assert cat is not None
    from models.tarifa import Tarifa
    tid = tarifa_repository.insertar(Tarifa(id_categoria=cat["id_categoria"],
                                            nombre="Mensualidad Test", monto=200.0))
    return bid, tid


def test_inicio_guarda_fecha_ingreso_y_matricula():
    from services import importar_service
    from repositories import estudiante_repository, matricula_repository
    _beca_y_tarifa()
    ok, msg, res = importar_service.importar_estudiantes([_fila()], id_usuario=1)
    assert ok, res
    assert res["estudiantes_creados"] == 1
    assert res["matriculas"] == 1, "todo importado sale matriculado"
    assert res["becas"] == 0, "sin BECA no hay beca"
    est = estudiante_repository.obtener_todos()[0]
    assert est["fecha_ingreso"] == "2026-03-10"
    mats = matricula_repository.obtener_activas()
    assert len(mats) == 1 and mats[0]["fecha_inicio"] == "2026-03-10"


def test_inicio_invalido_es_error():
    from services import importar_service
    ok, _, errores = importar_service.validar_filas([_fila(INICIO="ayer")])
    assert not ok and any("INICIO" in e for e in errores)


def test_beca_crea_matricula_y_cuota_retrotraida():
    from services import importar_service
    from repositories import matricula_repository, matricula_beca_repository
    from repositories import cuota_repository
    _beca_y_tarifa()
    ok, msg, res = importar_service.importar_estudiantes(
        [_fila(BECA="Beca Import Test")], id_usuario=1)
    assert ok, res
    assert res["matriculas"] == 1, res
    assert res["becas"] == 1, res
    mats = matricula_repository.obtener_activas()
    assert len(mats) == 1
    assert mats[0]["fecha_inicio"] == "2026-03-10"
    becas = matricula_beca_repository.obtener_por_matricula(mats[0]["id_matricula"])
    assert becas, "la beca debe quedar asignada"
    cuotas = cuota_repository.obtener_por_matricula(mats[0]["id_matricula"])
    assert cuotas and cuotas[0]["periodo"] == "2026-03", cuotas


def test_beca_inexistente_hallazgo_con_sin_beca():
    from services import importar_revision
    h = importar_revision.revisar("Estudiantes", [_fila(BECA="No Existe")], None)
    beca_h = [x for x in h if x["codigo"] == "BECA_NO_EXISTE"]
    assert beca_h, h
    assert {o["id"] for o in beca_h[0]["opciones"]} == {"omitir", "sin_beca"}
    # sin_beca → entra solo el estudiante
    res = {beca_h[0]["id"]: "sin_beca"}
    efectivas, notas = importar_revision.aplicar_resoluciones(
        "Estudiantes", [_fila(BECA="No Existe")], None, res)
    assert len(efectivas) == 1 and not efectivas[0].get("BECA")
    from services import importar_service
    ok, _, r = importar_service.importar_estudiantes(efectivas, id_usuario=1)
    assert ok and r["estudiantes_creados"] == 1 and r["matriculas"] == 0


def test_nav_siguiente_sin_salto_auto(crear_vista, usuario_admin, tmp_path):
    from views.importar.importar_view import ImportarView
    p = tmp_path / "est.csv"
    p.write_text("DNI,Nombres,Apellidos,INICIO,BECA\n12345678,A,B,2026-03-10,\n",
                 encoding="utf-8-sig")
    vista = crear_vista(ImportarView)
    assert vista.btn_siguiente_sel.cget("state") == "disabled"
    vista._archivo_actual = str(p)
    vista._cargar_archivo()
    vista.update_idletasks()
    # no salta solo: sigue en Selección y Siguiente se habilita
    assert vista.tabview.get() == "Seleccionar Archivo"
    assert vista.btn_siguiente_sel.cget("state") == "normal"
    # mapeo sugiere beca/inicio y el resumen no marca falsos faltantes
    textos = " ".join(
        w.cget("text") for w in vista.scroll_mapeo.winfo_children()
        if _tiene_texto(w))
    assert "Faltan obligatorios" not in textos, textos


def test_reimporte_actualiza_sin_duplicar():
    from services import importar_service, importar_revision
    from repositories import estudiante_repository, matricula_repository
    _beca_y_tarifa()
    # 1ra carga: DNI vacío + beca (flujo real: revisión→provisional→ejecutar)
    h1 = importar_revision.revisar(
        "Estudiantes", [_fila(DNI="", BECA="Beca Import Test")], None)
    assert any(x["codigo"] == "FALTA_DNI" for x in h1)
    ef1, _ = importar_revision.aplicar_resoluciones(
        "Estudiantes", [_fila(DNI="", BECA="Beca Import Test")], None,
        {x["id"]: x["default"] for x in h1})
    ok, _, r1 = importar_service.importar_estudiantes(ef1, id_usuario=1)
    assert ok and r1["estudiantes_creados"] == 1 and r1["matriculas"] == 1
    # 2da carga (CSV corregido): mismo nombre, DNI real, otro inicio
    fila2 = _fila(DNI="11222333", INICIO="2026-04-05", BECA="Beca Import Test")
    h = importar_revision.revisar("Estudiantes", [fila2], None)
    ya = [x for x in h if x["codigo"] == "YA_EXISTE"]
    assert ya, h
    assert {o["id"] for o in ya[0]["opciones"]} == {"actualizar", "omitir"}
    res = {x["id"]: (x["default"]) for x in h}
    efectivas, _ = importar_revision.aplicar_resoluciones(
        "Estudiantes", [fila2], None, res)
    ok, _, r2 = importar_service.importar_estudiantes(efectivas, id_usuario=1)
    assert ok, r2
    assert r2["estudiantes_creados"] == 0, "no debe duplicar"
    todos = estudiante_repository.obtener_todos()
    assert len(todos) == 1
    assert todos[0]["dni"] == "11222333", "provisional→real"
    assert todos[0]["fecha_ingreso"] == "2026-04-05"
    assert len(matricula_repository.obtener_activas()) == 1, "sin matrícula duplicada"


def test_reimporte_omitir_no_toca_nada():
    from services import importar_service, importar_revision
    from repositories import estudiante_repository
    _beca_y_tarifa()
    importar_service.importar_estudiantes([_fila()], id_usuario=1)
    h = importar_revision.revisar("Estudiantes", [_fila()], None)
    ya = [x for x in h if x["codigo"] == "YA_EXISTE"]
    assert ya
    efectivas, _ = importar_revision.aplicar_resoluciones(
        "Estudiantes", [_fila()], None, {ya[0]["id"]: "omitir"})
    ok, _, r = importar_service.importar_estudiantes(efectivas, id_usuario=1)
    assert ok and r["estudiantes_creados"] == 0 and r["matriculas"] == 0
    assert len(estudiante_repository.obtener_todos()) == 1


def test_reimporte_asigna_beca_a_matricula_activa():
    from services import importar_service, importar_revision, matricula_service
    from repositories import matricula_repository
    _beca_y_tarifa()
    ok, _, r1 = importar_service.importar_estudiantes([_fila()], id_usuario=1)
    assert ok and r1["matriculas"] == 1 and r1["becas"] == 0
    # re-importe (flujo real con revisión) con BECA: actualiza y asigna
    h = importar_revision.revisar(
        "Estudiantes", [_fila(BECA="Beca Import Test")], None)
    assert any(x["codigo"] == "YA_EXISTE" for x in h)
    ef, _ = importar_revision.aplicar_resoluciones(
        "Estudiantes", [_fila(BECA="Beca Import Test")], None,
        {x["id"]: x["default"] for x in h})
    ok, _, r2 = importar_service.importar_estudiantes(ef, id_usuario=1)
    assert ok, r2
    assert r2["estudiantes_creados"] == 0
    assert r2["becas"] == 1, r2
    assert any("asignada a matrícula activa" in d for d in r2["detalles"]), r2
    mats = matricula_repository.obtener_activas()
    assert len(mats) == 1
    becas = matricula_service.obtener_becas_por_matricula(mats[0]["id_matricula"])
    assert becas, "la beca debe quedar asignada sin nota manual"


def test_dni_duplicado_misma_persona_ofrece_actualizar(crear_estudiante):
    from services import importar_revision
    crear_estudiante(dni="12345678", nombres="Dni", apellidos="Mismo")
    h = importar_revision.revisar(
        "Estudiantes", [_fila(DNI="12345678", Nombres="Dni", Apellidos="Mismo")], None)
    dup = [x for x in h if x["codigo"] == "DNI_DUPLICADO"]
    assert dup, h
    assert {o["id"] for o in dup[0]["opciones"]} == {"actualizar", "omitir"}
    assert dup[0]["default"] == "actualizar"


def test_dni_duplicado_otra_persona_solo_omite(crear_estudiante):
    from services import importar_revision
    crear_estudiante(dni="12345678", nombres="Otro", apellidos="Alguien")
    h = importar_revision.revisar(
        "Estudiantes", [_fila(DNI="12345678", Nombres="Dni", Apellidos="Mismo")], None)
    dup = [x for x in h if x["codigo"] == "DNI_DUPLICADO"]
    assert dup, h
    assert [o["id"] for o in dup[0]["opciones"]] == ["omitir"]


def test_bulk_actualizar_marca_reimportes(crear_vista, usuario_admin, crear_estudiante):
    from views.importar.importar_view import ImportarView
    crear_estudiante(dni="12345678", nombres="Dni", apellidos="Mismo")
    vista = crear_vista(ImportarView)
    vista._datos_cargados = [_fila(DNI="12345678", Nombres="Dni", Apellidos="Mismo")]
    vista._mapeo_actual = {}
    vista._validar()
    vista.update_idletasks()
    vista._aplicar_bulk("actualizar")
    res = vista._resoluciones_dict()
    assert any(v == "actualizar" for v in res.values()), res


def _tiene_texto(w):
    try:
        return bool(w.cget("text"))
    except Exception:
        return False


def test_inicio_cm_a_enero_y_vacio_a_mayo():
    from services import importar_service
    assert importar_service._normalizar_inicio_csv("28CM") == "2026-01-28"
    assert importar_service._normalizar_inicio_csv("01/CM") == "2026-01-01"
    assert importar_service._inicio_de_fila({"INICIO": ""}, {}) == "2026-05-15"
    ok, _, res = importar_service.importar_estudiantes(
        [_fila(INICIO="")], id_usuario=1)
    assert ok and res["estudiantes_creados"] == 1
    from repositories import estudiante_repository, matricula_repository
    est = estudiante_repository.obtener_todos()[0]
    assert est["fecha_ingreso"] == "2026-05-15"
    mats = matricula_repository.obtener_activas()
    assert mats and mats[0]["fecha_inicio"] == "2026-05-15"


def test_actualizar_retarifa_por_era():
    from services import importar_service
    from repositories import matricula_repository, tarifa_repository
    _beca_y_tarifa()
    ok, _, r1 = importar_service.importar_estudiantes([_fila()], id_usuario=1)
    assert ok and r1["matriculas"] == 1
    m0 = matricula_repository.obtener_activas()[0]
    t0 = tarifa_repository.obtener_por_id(m0["id_tarifa"])
    assert float(t0["monto"]) == 100.0
    # re-importe con INICIO de era 120 → re-tariféa sin tocar cuotas
    h = importar_revision_revisar([_fila(INICIO="2026-10-05")])
    ef, _ = importar_revision_aplicar([_fila(INICIO="2026-10-05")], h)
    ok, _, r2 = importar_service.importar_estudiantes(ef, id_usuario=1)
    assert ok, r2
    assert any("tarifa actualizada" in d for d in r2["detalles"]), r2
    m1 = matricula_repository.obtener_por_id(m0["id_matricula"])
    t1 = tarifa_repository.obtener_por_id(m1["id_tarifa"])
    assert float(t1["monto"]) == 120.0, t1
    from repositories import cuota_repository
    cuotas = cuota_repository.obtener_por_matricula(m0["id_matricula"])
    assert cuotas and cuotas[0]["monto_total"] == 100.0, "cuotas intactas"


def importar_revision_revisar(filas):
    from services import importar_revision
    return importar_revision.revisar("Estudiantes", filas, None)


def importar_revision_aplicar(filas, h):
    from services import importar_revision
    return importar_revision.aplicar_resoluciones(
        "Estudiantes", filas, None, {x["id"]: x["default"] for x in h})


def test_crear_beca_inferida_y_aplicada():
    from services import importar_service, importar_revision
    assert importar_service._inferir_beca("Media beca") == ("Media Beca", "MONTO_FIJO", 50.0)
    assert importar_service._inferir_beca("BECA COMPLETA") == ("Beca Completa", "PORCENTAJE", 100.0)
    assert importar_service._inferir_beca("Beca_xyz") is None
    bid, det = importar_service._crear_beca_inferida("Media beca")
    assert bid, det
    # segunda vez reutiliza
    bid2, _ = importar_service._crear_beca_inferida("MEDIA BECA")
    assert bid2 == bid
    # flujo revisión → crear → matricula con beca
    _beca_y_tarifa()
    fila = _fila(BECA="Beca Nueva 25")
    h = importar_revision.revisar("Estudiantes", [fila], None)
    bh = [x for x in h if x["codigo"] == "BECA_NO_EXISTE"]
    assert bh and any(o["id"] == "crear_beca" for o in bh[0]["opciones"]), h
    ef, notas = importar_revision.aplicar_resoluciones(
        "Estudiantes", [fila], None, {bh[0]["id"]: "crear_beca"})
    assert any("creada" in n for n in notas), notas
    ok, _, res = importar_service.importar_estudiantes(ef, id_usuario=1)
    assert ok and res["becas"] == 1, res


def test_tarifa_era_set_elige_120():
    from services import importar_service
    t = importar_service._tarifa_para_beca("2026-09-15")
    assert t and float(t["monto"]) == 120.0, t


def test_tarifa_generica_se_crea_si_falta():
    from services import importar_service
    from repositories import tarifa_repository
    for t in tarifa_repository.obtener_activas():
        tarifa_repository.soft_delete(t["id_tarifa"])
    t = importar_service._tarifa_para_beca("2026-09-15")
    assert t and float(t["monto"]) == 120.0 and "120" in t["nombre"], t
    t2 = importar_service._tarifa_para_beca("2026-10-01")
    assert t2["id_tarifa"] == t["id_tarifa"], "no debe duplicar"


def test_tarifa_era_pre_set_crea_100():
    from services import importar_service
    t = importar_service._tarifa_para_beca("2026-03-10")
    assert t and float(t["monto"]) == 100.0, t


def test_matricula_usa_tarifa_de_era():
    from services import importar_service
    from repositories import matricula_repository
    ok, _, res = importar_service.importar_estudiantes(
        [_fila(INICIO="2026-10-05")], id_usuario=1)
    assert ok and res["matriculas"] == 1, res
    mats = matricula_repository.obtener_activas()
    assert len(mats) == 1
    from repositories import tarifa_repository
    tar = tarifa_repository.obtener_por_id(mats[0]["id_tarifa"])
    assert float(tar["monto"]) == 120.0, tar
