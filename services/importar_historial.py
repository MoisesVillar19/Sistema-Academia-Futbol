"""Importación histórica Excel Roncalli (RELACIÓN / INGRESOS / VENTA UNIFORME).

Lee el XLSX directamente (los colores de fila dan la beca: verde=1/2,
celeste=COMPLETA) y ejecuta vía services existentes, atómico por fila.
BALANCE lo cubre `importar_service.importar_tienda`.

Reglas (acordadas):
- DNI provisional 90000001… secuencial; nombres: 1er token=nombres, resto=apellidos.
- C.M → enero (dd/C.M = 2026-01-dd); fecha 1900-01-07 se ignora.
- Mensualidad por escala central (cuota_service.ESCALA_MENSUALIDAD:
  2026-01→100, 2026-09→120); 120/150 pre-SET sin matrícula previa = NUEVO.
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


def _fill_verde_celeste(rgb) -> str:
    """Heurística para rellenos directos (no de tema): verde≈1/2 beca,
    celeste≈completa. El normalizador CSV solo emite themes; el XLSX real
    trae verdes/celestes directos que antes se perdían (Beca —)."""
    try:
        h = str(rgb or "")[-6:]
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, TypeError):
        return ""
    if g >= 0x70 and g > r + 0x28 and g > b + 0x28:
        return "theme6"
    if b >= 0x70 and b > r + 0x28 and b > g:
        return "theme7"
    return ""


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
                if f and f.patternType not in (None, "none"):
                    if f.fgColor.type != "rgb":
                        fill = "theme" + str(getattr(f.fgColor, "theme", "?"))
                    else:
                        fill = _fill_verde_celeste(getattr(f.fgColor, "rgb", ""))
                    if fill in ("theme6", "theme7"):
                        break
                    fill = ""
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

    def _pagar_con_partes(self, id_cuota, partes, base, txt, per,
                            etiqueta) -> float:
        """Imputa las partes a la cuota hasta cubrirla; retorna el resto
        (adelanto de uniforme). Respeta el orden de la celda."""
        from services import pago_service
        pendiente = round(base, 2)
        resto, resto_metodo = 0.0, "EFECTIVO"
        for monto, metodo in partes:
            m = monto if monto else base
            f_pago = fecha_en(txt) or f"{per}-01"
            if pendiente > 0:
                toma = min(m, pendiente)
                ok_p, msg_p, _ = pago_service.registrar_pago({
                    "id_usuario": self.id_usuario, "id_cuota": id_cuota,
                    "monto_pagado": round(toma, 2),
                    "metodo_pago": metodo or "EFECTIVO",
                    "fecha_pago": f_pago, "observacion": "Importación Excel",
                    "permitir_sin_comprobante": True,
                })
                if ok_p:
                    self.res["pagos"] += 1
                else:
                    self.res["errores"].append(f"{etiqueta}: pago {toma} ({msg_p})")
                pendiente = round(pendiente - toma, 2)
                sobra = round(m - toma, 2)
            else:
                sobra = round(m, 2)
            if sobra > 0:
                resto = round(resto + sobra, 2)
                resto_metodo = metodo or resto_metodo
        self._resto_metodo = resto_metodo
        return resto

    def _venta_resto_uniforme(self, id_est, monto, txt, per, nombre):
        """Resto de celda bundled → venta UNIFORME-COM (adelanto)."""
        from services import inventario_service, venta_service
        id_prod = self._asegurar_uniforme("COM")
        metodo = getattr(self, "_resto_metodo", None) or "EFECTIVO"
        fecha = fecha_en(txt) or f"{per}-01"
        inventario_service.registrar_compra({
            "id_producto": id_prod, "cantidad": 1, "monto_total": monto,
            "metodo_pago": "EFECTIVO", "motivo": "Importación Excel",
            "id_usuario": self.id_usuario,
        })
        ok, msg, _ = venta_service.registrar_venta({
            "id_estudiante": id_est, "id_usuario": self.id_usuario,
            "tipo_venta": "TIENDA", "metodo_pago": metodo,
            "items": [{"id_producto": id_prod, "cantidad": 1,
                       "precio_unitario": monto}],
            "monto_total": monto,
            "observacion": f"Importación Excel: parte uniforme de {nombre} {per}",
            "fecha_venta": fecha,
        })
        if ok:
            self.res["ventas"] += 1
            self.res["detalles"].append(f"{nombre} {per}: S/{monto:.2f} a uniforme (adelanto)")
        else:
            self.res["errores"].append(f"{nombre} {per}: venta uniforme ({msg})")

    def _id_estudiante_por_nombre(self, nombre: str) -> int | None:
        """ID por match EXACTO normalizado (idempotencia en re-corridas).
        Incluye inactivos (retirados por auto-retiro previo)."""
        from repositories import estudiante_repository
        objetivo = norm(nombre)
        if not objetivo:
            return None
        for e in estudiante_repository.obtener_todos():
            if norm(f"{e.get('nombres', '')} {e.get('apellidos', '')}") == objetivo:
                return e["id_estudiante"]
        return None

    def _existe_estudiante(self, nombre: str) -> bool:
        return self._id_estudiante_por_nombre(nombre) is not None

    def _backfill_beca(self, id_estudiante: int, beca_nombre: str):
        """Re-importe: asigna la beca a la matrícula activa si no la tiene
        (recalcula pendientes). Sin matrícula activa → nota de revisión."""
        from services import matricula_service
        from repositories import matricula_repository
        bid = self._beca_id(beca_nombre)
        if not bid:
            self.revision.append(f"Beca '{beca_nombre}' no existe (asignar manual)")
            return
        activas = [m for m in matricula_repository.obtener_por_estudiante(id_estudiante)
                   if m.get("estado") == "ACTIVO"]
        if not activas:
            self.revision.append(f"Beca {beca_nombre} pendiente: sin matrícula activa")
            return
        try:
            actuales = [b for b in matricula_service.obtener_becas_por_matricula(
                activas[0]["id_matricula"]) if b.get("activo", 1)]
        except Exception:
            actuales = []
        if any(b.get("id_beca") == bid for b in actuales):
            return
        ok, msg = matricula_service.asignar_beca(
            activas[0]["id_matricula"], bid, "Importación Excel")
        if ok:
            self.res["becas"] += 1
            self.res["detalles"].append(f"Beca {beca_nombre} asignada a matrícula activa")
        else:
            self.revision.append(f"Beca {beca_nombre} no asignada: {msg}")

    def _mapa_cuotas(self, id_mat) -> dict:
        """Cuotas activas por periodo (mapa vivo: la cadena RN-014 puede
        crear meses mientras se importa)."""
        from services import cuota_service
        mapa = {}
        try:
            for c in cuota_service.obtener_cuotas_por_matricula(id_mat):
                if c.get("activo", 1):
                    mapa[str(c.get("periodo", ""))] = c
        except Exception:
            pass
        return mapa

    def _adoptar_o_crear_cuota(self, id_mat, per, total) -> tuple[int, bool]:
        """Reutiliza la cuota del periodo si existe sin pagos (auto-cuota o
        cadena RN-014), ajustando su monto al histórico; si no, la crea.
        Retorna (id_cuota, creada_por_import)."""
        from services import cuota_service
        from models.cuota import Cuota
        c0 = self._mapa_cuotas(id_mat).get(per)
        if c0 and float(c0.get("monto_pagado", 0) or 0) == 0:
            if round(float(c0.get("monto_total", 0) or 0), 2) != round(total, 2):
                cuota_service.cuota_repository.actualizar(Cuota(
                    id_cuota=c0["id_cuota"], id_matricula=c0["id_matricula"],
                    periodo=per, fecha_vencimiento=c0["fecha_vencimiento"],
                    monto_total=round(total, 2), monto_pagado=0,
                    monto_mora=c0.get("monto_mora", 0),
                    saldo=round(total, 2),
                    estado=c0.get("estado", "PENDIENTE"), activo=1,
                ))
            return c0["id_cuota"], False
        id_cuota = cuota_service.crear_cuota(
            id_mat, round(total, 2), f"{per}-01", per)
        return id_cuota, True

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
        ya_id = self._id_estudiante_por_nombre(nombre)
        if ya_id:
            # Adoptar: el alumno existe (CSV previo); se completan meses,
            # beca y retiros sin duplicar persona ni matrícula activa.
            from repositories import (matricula_repository as _mr2,
                                      cuota_repository as _cr2,
                                      estudiante_repository as _er2)
            id_est = ya_id
            self.res["detalles"].append(f"{nombre} → existe, se completa")
            # Beca primero (aunque no haya nada más que hacer).
            if fill in ("theme6", "theme7"):
                self._backfill_beca(
                    ya_id, "1/2 BECA" if fill == "theme6" else "BECA COMPLETA")
            # Cobertura: meses ya pagados → nada que hacer (idempotente).
            cubiertos = set()
            try:
                for m in _mr2.obtener_por_estudiante(id_est):
                    for c in _cr2.obtener_por_matricula(m["id_matricula"]):
                        if c.get("activo", 1) and float(c.get("monto_pagado", 0) or 0) > 0:
                            cubiertos.add(str(c.get("periodo", ""))[:7])
            except Exception:
                pass
            need = {f"2026-{mm:02d}" for mm in marcas}
            if need and need <= cubiertos:
                self.revision.append(f"{nombre}: sin cambios (ya importado)")
                return
            # Retirado con actividad nueva → reingreso para matricular.
            try:
                est_ya = _er2.obtener_por_id(id_est) or {}
                if est_ya.get("estado") == "RETIRADO" and (need - cubiertos):
                    estudiante_service.registrar_reingreso(id_est, self.id_usuario)
                    self.res["detalles"].append(f"{nombre} → reingreso por actividad nueva")
            except Exception:
                pass
        else:
            dni = self._dni_provisional()
            ok, msg, id_est = estudiante_service.crear_estudiante(
                {"dni": dni, "nombres": nombres, "apellidos": ape}, self.id_usuario)
            if not ok:
                raise RuntimeError(msg)
            self.res["estudiantes"] += 1
            self.res["detalles"].append(f"{nombre} → DNI prov. {dni}")
        # ¿NUEVO? primer mes marcado con ≥120 pre-SET sin INICIO previo
        fecha_ini = ini or (f"2026-{min(marcas):02d}-01" if marcas else "2026-01-01")
        if ini and marcas:
            per_min = f"2026-{min(marcas):02d}"
            if ini[:7] > per_min:
                # Caso Kenzo: INICIO posterior a pagos → manda el primer pago
                # (nunca se huérfanan pagos ya registrados).
                fecha_ini = f"{per_min}-01"
                self.res["detalles"].append(
                    f"{nombre}: INICIO {ini} posterior a pagos; manda {per_min}")
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
        # Adoptar matrícula activa (re-importe) en vez de duplicar.
        from repositories import matricula_repository
        id_mat = None
        try:
            for m in matricula_repository.obtener_por_estudiante(id_est):
                if m.get("estado") == "ACTIVO":
                    id_mat = m["id_matricula"]
                    break
        except Exception:
            pass
        if id_mat is None:
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
        else:
            self.res["detalles"].append(f"{nombre} → matrícula activa existente")
        # Tarifa por era del INICIO (cuotas existentes intactas).
        try:
            from services import importar_service as _imp_svc
            nota_tar = _imp_svc._aplicar_tarifa_era(id_mat, fecha_ini)
            if nota_tar:
                self.res["detalles"].append(f"{nombre}{nota_tar}")
        except Exception:
            pass
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
            per = f"2026-{mes:02d}"
            base = cuota_service.monto_mensualidad(per)  # escala central (F0)
            total = sum(m for m, _ in partes if m) or base
            if total > base:
                # Celda bundled (150 = 120 mensualidad + 30 uniforme): la
                # cuota va por tarifa del mes y el resto es adelanto de
                # uniforme (venta UNIFORME-COM). Adopta auto-cuota si existe.
                id_cuota, creada = self._adoptar_o_crear_cuota(id_mat, per, base)
                if creada:
                    self.res["cuotas"] += 1
                resto = self._pagar_con_partes(
                    id_cuota, partes, base, txt, per, f"{nombre} {per}")
                if resto > 0:
                    self._venta_resto_uniforme(
                        id_est, resto, txt, per, nombre)
            else:
                id_cuota, creada = self._adoptar_o_crear_cuota(id_mat, per, total)
                if creada:
                    self.res["cuotas"] += 1
                for monto, metodo in partes:
                    m = monto if monto else base
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
        if beca == "BECA COMPLETA":
            # La cuota se genera y se paga sola: meses INICIO→CULMINO
            # (default primer→último mes marcado, si no ENE→DIC) sin cuota.
            # EFECTIVO + observación (sin cobro real; visible en reportes).
            try:
                mes_ini = int(str(fecha_ini)[5:7])
            except (ValueError, TypeError, IndexError):
                mes_ini = min(marcas) if marcas else 1
            try:
                mes_fin = int(str(retiro or "")[5:7]) if retiro else None
            except (ValueError, TypeError, IndexError):
                mes_fin = None
            if not mes_fin:
                mes_fin = max(marcas) if marcas else 12
            for mes in range(max(1, mes_ini), min(12, mes_fin) + 1):
                per = f"2026-{mes:02d}"
                base = cuota_service.monto_mensualidad(per)  # escala central (F0)
                # Adopta la cuota si la cadena RN-014 ya la creó al pagar
                id_cuota, _creada = self._adoptar_o_crear_cuota(id_mat, per, base)
                self.res["cuotas"] += 1
                ok_p, msg_p, _ = pago_service.registrar_pago({
                    "id_usuario": self.id_usuario, "id_cuota": id_cuota,
                    "monto_pagado": base, "metodo_pago": "EFECTIVO",
                    "fecha_pago": f"{per}-01",
                    "observacion": "Beca completa (sin cobro)",
                    "permitir_sin_comprobante": True,
                })
                if ok_p:
                    self.res["pagos"] += 1
                else:
                    self.res["errores"].append(f"{nombre} {per}: autopago beca ({msg_p})")
            self.res["detalles"].append(f"{nombre}: beca completa autopagada")
        if beca:
            bid = self._beca_id(beca)
            if bid:
                try:
                    actuales = [b for b in matricula_service.obtener_becas_por_matricula(
                        id_mat) if b.get("activo", 1)]
                except Exception:
                    actuales = []
                if not any(b.get("id_beca") == bid for b in actuales):
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
        elif not rein and marcas:
            # 2+ meses vacíos seguidos hasta el mes actual → retiro con
            # fecha = último día del último mes con pago (historial fiel).
            self._auto_retiro_por_vacios(id_est, nombre, max(marcas))

    def _auto_retiro_por_vacios(self, id_est: int, nombre: str, ultimo_mes: int):
        import calendar
        from utils.dates import get_today
        from services import estudiante_service
        try:
            hoy_mes = int(str(get_today())[:7].split("-")[1])
        except (ValueError, TypeError, IndexError):
            return
        vacios = [m for m in range(ultimo_mes + 1, min(hoy_mes, 12) + 1)]
        if len(vacios) < 2:
            return
        ultimo_dia = calendar.monthrange(2026, ultimo_mes)[1]
        fecha = f"2026-{ultimo_mes:02d}-{ultimo_dia:02d}"
        ok, _msg = estudiante_service.registrar_retiro(id_est, self.id_usuario, fecha)
        if ok:
            self.res["detalles"].append(f"{nombre}: retiro automático al {fecha} (sin pagos desde entonces)")

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
            ya_id = self._id_estudiante_por_nombre(nombre)
            if ya_id:
                # Adoptar: con matrícula activa se omite; sin ella se matricula
                # con el DNI existente (no provisional nuevo).
                from repositories import matricula_repository as _mr
                from repositories import estudiante_repository as _er
                from repositories import persona_repository as _pr
                tiene_activa = False
                try:
                    tiene_activa = any(
                        m.get("estado") == "ACTIVO"
                        for m in _mr.obtener_por_estudiante(ya_id))
                except Exception:
                    pass
                if tiene_activa:
                    self.revision.append(f"{nombre}: ya existe (omitido en re-importe)")
                    if re.search(r"S/\.\s*50", textos):
                        self._backfill_beca(ya_id, "1/2 BECA")
                    continue
                est_ya = _er.obtener_por_id(ya_id) or {}
                per_ya = _pr.obtener_por_id(est_ya.get("id_persona", 0)) or {}
                dni_existente = per_ya.get("dni", "")
                self.res["detalles"].append(f"{nombre} → existe, se matricula")
            else:
                dni_existente = ""
            try:
                fecha = fecha_en(textos) or "2026-05-01"
                nombres, ape = _split_nombre(nombre)
                dni = dni_existente or self._dni_provisional()
                ok, msg, ids = matricula_service.matricula_express({
                    "tipo": "NUEVO", "nombres": nombres, "apellidos": ape,
                    "dni": dni, "metodo_pago": "EFECTIVO", "fecha_inicio": fecha,
                }, self.id_usuario)
                if not ok:
                    raise RuntimeError(msg)
                if not dni_existente:
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
