"""Importación histórica Excel Roncalli (RELACIÓN / INGRESOS / VENTA UNIFORME).

Lee el XLSX directamente (los colores de fila dan la beca: verde=1/2,
celeste=COMPLETA) y ejecuta vía services existentes, atómico por fila.
BALANCE lo cubre `importar_service.importar_tienda`.

Reglas (acordadas):
- DNI provisional 90000001… secuencial; nombres: 1er token=nombres, resto=apellidos.
- C.M → enero (dd/C.M = 2026-01-dd); fecha 1900-01-07 se ignora.
- Mensualidad: MAY–AGO=100, SET–DIC=120; 120/150 pre-SET sin matrícula previa = NUEVO.
- Mes vacío = no viene (sin cuota ni deuda); S/50 = pago parcial por ese monto.
- Cuotas mensuales por monto de celda (beca solo como vínculo para el filtro).
- VENTA: COM/ENT a 70; ADELANTO → total + partes en observación; ENTR. → regalo S/0.
"""

import re
import unicodedata

from utils.logger import logger

MESES = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5,
         "JUNIO": 6, "JULIO": 7, "AGOSTO": 8, "SETIEMBRE": 9, "SETIEMRE": 9,
         "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12}

DNI_BASE = 90000001
PRECIO_UNIFORME = 70.0


def norm(texto) -> str:
    s = str(texto or "").strip().upper()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def _num(txt) -> float | None:
    try:
        return float(str(txt).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def montos_metodo(celda: str) -> list[tuple[float, str | None]]:
    """Extrae [(monto, metodo|None)] de 'S/100 EF. S/20 Y.' etc."""
    out = []
    for m in re.finditer(r"S/\s*([\d.,]+)\s*([A-Za-z.]*)(?=\s*(?:S/|$))",
                         str(celda or ""), re.IGNORECASE):
        monto = _num(m.group(1))
        if monto is None:
            continue
        resto = m.group(2).upper()
        metodo = "YAPE" if "Y" in resto else ("EFECTIVO" if "EF" in resto else None)
        out.append((monto, metodo))
    return out


def fecha_en(texto: str, year: int = 2026) -> str | None:
    # acepta rangos ("23-30/04" → 30/04): usa el último par válido
    import datetime
    t = str(texto or "")
    m = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})", t)
    if m:
        try:
            return datetime.date(year, int(m.group(3)), int(m.group(2))).isoformat()
        except ValueError:
            pass
    cands = re.findall(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", t)
    for c in reversed(cands):
        d, mo = int(c[0]), int(c[1])
        y = int(c[2]) if c[2] else year
        if y < 100:
            y += 2000
        try:
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


def parse_inicio(valor) -> tuple[str | None, str | None, str | None]:
    """Retorna (fecha_inicio, fecha_reingreso, fecha_retiro) en ISO o None."""
    import datetime
    if isinstance(valor, datetime.datetime):
        valor = valor.date()
    if isinstance(valor, datetime.date):
        if valor.year == 1900:
            return None, None, None
        return valor.isoformat(), None, None
    t = norm(valor)
    if not t:
        return None, None, None
    if "REIN" in t:
        f = fecha_en(t)
        return None, f, None
    if any(k in t for k in ("CULMIN", "TERMIN", "CULMINO")):
        f = fecha_en(t)
        return None, None, f
    m = re.search(r"(\d{1,2})\s*/?\s*C\.?M\.?", t)
    if m:
        try:
            return datetime.date(2026, 1, int(m.group(1))).isoformat(), None, None
        except ValueError:
            return None, None, None
    m = re.search(r"INICIO\s+(\d{1,2})/(\d{1,2})", t)
    if m:
        try:
            return datetime.date(2026, int(m.group(2)), int(m.group(1))).isoformat(), None, None
        except ValueError:
            return None, None, None
    return None, None, None


def _leer_hoja(ruta: str, hoja: str) -> list[tuple[list, str | None]]:
    """Filas con valores + fill de la fila (beca por color: theme6=1/2, theme7=completa)."""
    import openpyxl
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    ws = wb[hoja]
    out = []
    for r in ws.iter_rows(values_only=False):
        vals = [(c.value) for c in r]
        if not any(v not in (None, "") for v in vals):
            continue
        fill = ""
        try:
            for c in r[2:10]:
                f = c.fill
                if f and f.patternType not in (None, "none") and f.fgColor.type != "rgb":
                    fill = "theme" + str(getattr(f.fgColor, "theme", "?"))
                    if fill != "theme?":
                        break
        except Exception:
            pass
        out.append((vals, fill if fill in ("theme6", "theme7") else ""))
    return out


def _split_nombre(nombre: str) -> tuple[str, str]:
    partes = str(nombre or "").strip().split()
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], "(APELLIDO)"
    return partes[0], " ".join(partes[1:])


class ImportadorHistorial:
    def __init__(self, id_usuario: int = 1):
        self.id_usuario = id_usuario
        self._dni_seq = DNI_BASE
        self.revision: list[str] = []
        self.res = {"estudiantes": 0, "matriculas": 0, "cuotas": 0, "pagos": 0,
                    "ventas": 0, "becas": 0, "errores": [], "detalles": []}

    # ── utilidades ──
    def _dni_provisional(self) -> str:
        from repositories import persona_repository
        while persona_repository.existe_dni(str(self._dni_seq)):
            self._dni_seq += 1
        dni = str(self._dni_seq)
        self._dni_seq += 1
        return dni

    def _beca_id(self, nombre: str) -> int | None:
        from database.connection import fetch_one
        row = fetch_one("SELECT id_beca FROM beca WHERE nombre = ? AND activo = 1", (nombre,))
        return row["id_beca"] if row else None

    def _match_estudiante(self, nombre: str):
        from repositories import estudiante_repository
        objetivo = norm(nombre)
        if not objetivo:
            return None
        cands = []
        for e in estudiante_repository.obtener_todos(activo=1):
            n = norm(f"{e.get('nombres', '')} {e.get('apellidos', '')}")
            if n == objetivo:
                return e["id_estudiante"]
            if objetivo and (objetivo in n or n.startswith(objetivo)):
                cands.append(e)
        if len(cands) == 1:
            self.res["detalles"].append(f"Match parcial '{nombre}' → {cands[0].get('nombres')} {cands[0].get('apellidos')}")
            return cands[0]["id_estudiante"]
        if len(cands) > 1:
            self.revision.append(f"Ambiguo '{nombre}': {len(cands)} candidatos")
        else:
            self.revision.append(f"Sin match '{nombre}'")
        return None

    def _tarifa_mensualidad(self):
        from repositories import tarifa_repository
        for t in tarifa_repository.obtener_activas():
            if (t.get("categoria_tipo") or "") == "ACADEMIA":
                return t
        todas = tarifa_repository.obtener_activas()
        return todas[0] if todas else None

    # ── RELACIÓN ──
    def importar_relacion(self, ruta: str) -> dict:
        from services import estudiante_service, matricula_service, cuota_service, pago_service
        filas = _leer_hoja(ruta, "RELACIÓN DE ALUMNOS")
        for vals, fill in filas:
            nombre = str(vals[1] or "").strip()
            if not nombre or norm(nombre).startswith("NOMBRES") or norm(nombre).startswith("ALUMNOS"):
                continue
            if vals[0] is None and not any(vals[2:10]):
                continue
            try:
                self._fila_relacion(vals, fill)
            except Exception as e:
                self.res["errores"].append(f"{nombre}: {e}")
                logger.warning(f"Import historial {nombre}: {e}")
        return self.res

    def _fila_relacion(self, vals, fill):
        from services import estudiante_service, matricula_service, cuota_service, pago_service
        nombre = str(vals[1]).strip()
        nombres, ape = _split_nombre(nombre)
        meses = vals[2:10]  # MAYO..DIC
        ini, rein, retiro = parse_inicio(vals[10] if len(vals) > 10 else "")
        beca = "1/2 BECA" if fill == "theme6" else ("BECA COMPLETA" if fill == "theme7" else "")
        # celdas marcadas por mes (5..12)
        marcas = {}
        for i, celda in enumerate(meses):
            txt = str(celda or "").strip()
            if not txt or txt.upper().startswith("2026"):
                continue
            if any(k in norm(txt) for k in ("CULMIN", "TERMIN", "REIN", "INICIO")) and not montos_metodo(txt):
                continue
            partes = montos_metodo(txt)
            if not partes and norm(txt) in ("X", "X CANCELADO"):
                partes = [(None, None)]  # monto por defecto del mes
            if partes:
                marcas[i + 5] = (txt, partes)
        if not marcas and not ini and not rein and not beca:
            self.revision.append(f"{nombre}: sin INICIO ni marcas (¿se importa?)")
            return
        dni = self._dni_provisional()
        ok, msg, id_est = estudiante_service.crear_estudiante(
            {"dni": dni, "nombres": nombres, "apellidos": ape}, self.id_usuario)
        if not ok:
            raise RuntimeError(msg)
        self.res["estudiantes"] += 1
        self.res["detalles"].append(f"{nombre} → DNI prov. {dni}")
        # ¿NUEVO? primer mes marcado con ≥120 pre-SET sin INICIO previo
        fecha_ini = ini or (f"2026-{min(marcas):02d}-01" if marcas else "2026-01-01")
        es_nuevo = False
        if marcas:
            primer_mes = min(marcas)
            total_primero = sum(m for m, _ in marcas[primer_mes][1] if m) or 0
            mes_ini = int(fecha_ini[5:7])
            if primer_mes <= 8 and total_primero >= 120 and mes_ini >= primer_mes:
                es_nuevo = True
        tarifa = self._tarifa_mensualidad()
        if not tarifa:
            raise RuntimeError("Sin tarifa para matricular")
        ok, msg, id_mat = matricula_service.crear_matricula({
            "id_estudiante": id_est,
            "id_tarifa": tarifa["id_tarifa"],
            "monto_pactado": None,
            "dia_vencimiento": 1,
            "fecha_inicio": fecha_ini,
        }, self.id_usuario)
        if not ok:
            raise RuntimeError(msg)
        self.res["matriculas"] += 1
        # anular auto-cuota si no coincide con meses marcados
        for c in cuota_service.obtener_cuotas_por_matricula(id_mat):
            per = str(c.get("periodo", ""))
            try:
                mes_auto = int(per.split("-")[1])
            except (IndexError, ValueError):
                mes_auto = -1
            if mes_auto not in marcas and float(c.get("monto_pagado", 0) or 0) == 0:
                cuota_service.anular_cuota(c["id_cuota"], "importación histórica")
        for mes in sorted(marcas):
            txt, partes = marcas[mes]
            total = sum(m for m, _ in partes if m) or (120.0 if mes >= 9 else 100.0)
            per = f"2026-{mes:02d}"
            id_cuota = cuota_service.crear_cuota(
                id_mat, round(total, 2), f"{per}-01", per)
            self.res["cuotas"] += 1
            for monto, metodo in partes:
                m = monto if monto else (120.0 if mes >= 9 else 100.0)
                f_pago = fecha_en(txt) or f"{per}-01"
                ok_p, msg_p, _ = pago_service.registrar_pago({
                    "id_usuario": self.id_usuario, "id_cuota": id_cuota,
                    "monto_pagado": m, "metodo_pago": metodo or "EFECTIVO",
                    "fecha_pago": f_pago, "observacion": "Importación Excel",
                    "permitir_sin_comprobante": True,
                })
                if ok_p:
                    self.res["pagos"] += 1
                else:
                    self.res["errores"].append(f"{nombre} {per}: pago {m} ({msg_p})")
        if beca:
            bid = self._beca_id(beca)
            if bid:
                matricula_service.asignar_beca(id_mat, bid, "Importación Excel")
                self.res["becas"] += 1
        if rein:
            estudiante_service.registrar_reingreso(id_est, self.id_usuario)
            ok2, _, id_mat2 = matricula_service.crear_matricula({
                "id_estudiante": id_est, "id_tarifa": tarifa["id_tarifa"],
                "monto_pactado": None, "dia_vencimiento": 1,
                "fecha_inicio": rein if len(rein) == 10 else f"{rein}-01",
            }, self.id_usuario)
            if ok2:
                self.res["matriculas"] += 1
        if retiro:
            estudiante_service.registrar_retiro(id_est, self.id_usuario, retiro)

    # ── INGRESOS (nuevos) ──
    def importar_ingresos(self, ruta: str) -> dict:
        from services import matricula_service
        filas = _leer_hoja(ruta, "INGRESOS")
        for vals, _fill in filas:
            nombre = str(vals[1] or "").strip()
            if not nombre or norm(nombre).startswith(("NOMBRES", "ALUMNOS", "VALOR")):
                continue
            textos = " ".join(str(v or "") for v in vals[2:10])
            if "INICIO" not in norm(textos) and not any(vals[2:10]):
                continue
            try:
                fecha = fecha_en(textos) or "2026-05-01"
                nombres, ape = _split_nombre(nombre)
                dni = self._dni_provisional()
                ok, msg, ids = matricula_service.matricula_express({
                    "tipo": "NUEVO", "nombres": nombres, "apellidos": ape,
                    "dni": dni, "metodo_pago": "EFECTIVO", "fecha_inicio": fecha,
                }, self.id_usuario)
                if not ok:
                    raise RuntimeError(msg)
                self.res["estudiantes"] += 1
                self.res["matriculas"] += 1
                self.res["pagos"] += 1
                if re.search(r"S/\.\s*50", textos):
                    bid = self._beca_id("1/2 BECA")
                    if bid:
                        matricula_service.asignar_beca(ids["id_matricula"], bid, "Importación Excel")
                        self.res["becas"] += 1
                self.res["detalles"].append(f"NUEVO {nombre} → DNI prov. {dni}")
            except Exception as e:
                self.res["errores"].append(f"{nombre}: {e}")
        return self.res

    # ── VENTA UNIFORME ──
    def _asegurar_uniforme(self, tipo: str):
        from services import inventario_service
        codigo = "CAMISETA-ENT" if tipo == "ENT" else "UNIFORME-COM"
        from repositories import producto_repository
        prod = producto_repository.obtener_por_codigo(codigo)
        if prod:
            return prod["id_producto"]
        cats = inventario_service.listar_categorias()
        id_cat = cats[0]["id_categoria_producto"]
        id_tipo = None
        try:
            from controllers import tipo_uniforme_controller
            for t in tipo_uniforme_controller.listar_tipos():
                if ("ENTRENAMIENTO" in norm(t["nombre"]) and tipo == "ENT") or \
                   ("COMPETENCIA" in norm(t["nombre"]) and tipo == "COM"):
                    id_tipo = t["id_tipo_uniforme"]
        except Exception:
            pass
        ok, _, id_prod = inventario_service.crear_producto({
            "id_categoria_producto": id_cat,
            "nombre": "Camiseta Entrenamiento" if tipo == "ENT" else "Uniforme Competencia",
            "codigo": codigo, "canal": "TIENDITA", "precio_venta": PRECIO_UNIFORME,
            "id_tipo_uniforme": id_tipo, "stock_inicial": 0,
        })
        if not ok:
            raise RuntimeError(f"No se pudo crear {codigo}")
        return id_prod

    def importar_venta_uniforme(self, ruta: str) -> dict:
        from services import inventario_service, venta_service
        filas = _leer_hoja(ruta, "VENTA UNIFORME")
        for vals, _fill in filas:
            nombre = str(vals[1] or "").strip()
            if not nombre or norm(nombre).startswith(("NOMBRES", "VENTA", "COMPETENCIA")):
                continue
            celdas = [(i + 3, str(v or "").strip()) for i, v in enumerate(vals[2:12])
                      if str(v or "").strip()]
            if not celdas:
                continue
            try:
                self._fila_venta(nombre, celdas)
            except Exception as e:
                self.res["errores"].append(f"{nombre}: {e}")
        return self.res

    def _fila_venta(self, nombre, celdas):
        from services import inventario_service, venta_service
        id_est = self._match_estudiante(nombre)
        for mes, txt in celdas:
            t = norm(txt)
            tipo = "COM" if "COM" in t.split() or re.search(r"\bCOM\b", t) else ("ENT" if "ENT" in t else None)
            if not tipo:
                self.revision.append(f"{nombre} mes {mes}: sin COM/ENT en '{txt[:40]}'")
                continue
            id_prod = self._asegurar_uniforme(tipo)
            partes = montos_metodo(txt)
            if not partes and "CANCELADO" in t:
                # "1 COM. CANCELADO (YAPE 30/04)" sin monto = uniforme a 70
                m = re.search(r"YAPE", t)
                metodo = "YAPE" if m else "EFECTIVO"
                partes = [(PRECIO_UNIFORME, metodo)]
            if not partes and ("ENTR" in t or "ENTRE" in t):
                # regalo/entrega sin monto: compra + venta ítem a 0 (como RN-051)
                fecha = fecha_en(txt) or f"2026-{mes:02d}-01"
                inventario_service.registrar_compra({
                    "id_producto": id_prod, "cantidad": 1,
                    "monto_total": PRECIO_UNIFORME, "metodo_pago": "EFECTIVO",
                    "motivo": "Importación Excel",
                    "id_usuario": self.id_usuario,
                })
                ok, msg, _ = venta_service.registrar_venta({
                    "id_estudiante": id_est, "id_usuario": self.id_usuario,
                    "tipo_venta": "INSCRIPCION", "metodo_pago": "EFECTIVO",
                    "items": [{"id_producto": id_prod, "cantidad": 1}],
                    "monto_total": 0,
                    "observacion": f"Importación Excel: {txt[:60]}",
                    "fecha_venta": fecha,
                })
                if not ok:
                    raise RuntimeError(msg)
                self.res["ventas"] += 1
                continue
            if not partes:
                self.revision.append(f"{nombre} mes {mes}: sin montos en '{txt[:40]}'")
                continue
            total = round(sum(m for m, _ in partes), 2)
            # stock para la venta histórica
            inventario_service.registrar_compra({
                "id_producto": id_prod, "cantidad": 1, "monto_total": total,
                "metodo_pago": "EFECTIVO", "motivo": "Importación Excel",
                "id_usuario": self.id_usuario,
            })
            metodos = [mm or "EFECTIVO" for _, mm in partes]
            metodo = metodos[-1]
            fecha = fecha_en(txt) or f"2026-{mes:02d}-01"
            ok, msg, _ = venta_service.registrar_venta({
                "id_estudiante": id_est, "id_usuario": self.id_usuario,
                "tipo_venta": "UNIFORME" if tipo == "ENT" else "TIENDA",
                "metodo_pago": metodo,
                "items": [{"id_producto": id_prod, "cantidad": 1}],
                "monto_total": total,
                "observacion": f"Importación Excel: {txt[:80]}",
                "fecha_venta": fecha,
            })
            if not ok:
                raise RuntimeError(msg)
            self.res["ventas"] += 1


def importar_historial_excel(ruta: str, id_usuario: int = 1) -> dict:
    imp = ImportadorHistorial(id_usuario)
    imp.importar_relacion(ruta)
    imp.importar_ingresos(ruta)
    imp.importar_venta_uniforme(ruta)
    return {**imp.res, "revision": imp.revision}
