from repositories import matricula_repository, matricula_beca_repository, estudiante_repository
from models.matricula import Matricula
from services import auditoria_service, cuota_service, beca_service
from database.connection import transaccion
from utils.constants import STATUS_ACTIVO, STATUS_REINGRESANTE
from utils.dates import get_today
from utils.logger import logger


def crear_matricula(data: dict, id_usuario: int = 1) -> tuple[bool, str, int | None]:
    id_estudiante = data.get("id_estudiante")
    id_tarifa = data.get("id_tarifa")

    if not id_estudiante:
        return False, "El estudiante es obligatorio", None
    if not id_tarifa:
        return False, "La tarifa es obligatoria", None

    estudiante = estudiante_repository.obtener_por_id(id_estudiante)
    if not estudiante:
        return False, "Estudiante no encontrado", None

    matriculas_existentes = matricula_repository.obtener_por_estudiante(id_estudiante)
    for m in matriculas_existentes:
        if m["estado"] == "ACTIVO":
            return False, "El estudiante ya tiene una matrícula activa", None

    monto_pactado = data.get("monto_pactado")
    dia_vencimiento = data.get("dia_vencimiento", 1)

    becas_asignadas = data.get("becas", [])
    if len(becas_asignadas) > 1:
        from services import configuracion_service
        if not configuracion_service.permite_multiples_becas():
            return False, "La configuración actual no permite múltiples becas por matrícula", None

    matricula = Matricula(
        id_estudiante=id_estudiante,
        id_tarifa=id_tarifa,
        monto_pactado=monto_pactado,
        fecha_inicio=(str(data.get("fecha_inicio") or "").strip() or get_today()),
        dia_vencimiento=dia_vencimiento,
        tipo=data.get("tipo"),
        estado=STATUS_ACTIVO,
    )

    # Fase 7e: sin conceptos (eliminados del flujo) → monto_pactado > tarifa
    from repositories import tarifa_repository
    tarifa_data = tarifa_repository.obtener_por_id(id_tarifa)
    monto_base = monto_pactado if monto_pactado is not None else tarifa_data["monto"]

    es_primera_matricula = len(matriculas_existentes) == 0
    es_reingreso = estudiante["estado"] == STATUS_REINGRESANTE
    es_nuevo_flag = int(estudiante.get("es_nuevo", 0) or 0) == 1

    try:
        with transaccion():
            id_matricula = matricula_repository.insertar(matricula)

            # RN-051: camiseta 0 solo si es_nuevo=1 y primera matrícula y no reingreso
            debe_regalar_camiseta = es_nuevo_flag and es_primera_matricula and not es_reingreso
            if debe_regalar_camiseta:
                from repositories import producto_repository, tipo_uniforme_repository
                from repositories import detalle_venta_repository, venta_repository
                from models.venta import Venta
                from models.detalle_venta import DetalleVenta
                from utils.helpers import generate_receipt_number
                from utils.dates import get_today as _get_today
                tipo_ent = tipo_uniforme_repository.obtener_por_nombre("Uniforme Entrenamiento")
                prod_camiseta = None
                if tipo_ent:
                    from database.connection import fetch_all as _fetch_all
                    prods = _fetch_all("SELECT * FROM producto WHERE id_tipo_uniforme = ? AND activo=1", (tipo_ent["id_tipo_uniforme"],))
                    if prods:
                        prod_camiseta = prods[0]
                    else:
                        prod_camiseta = producto_repository.obtener_por_codigo("CAMISETA-ENT")
                if prod_camiseta:
                    if prod_camiseta["stock_actual"] < 1:
                        raise ValueError("Stock insuficiente de Camiseta Entrenamiento para inscripción")
                    numero_recibo = generate_receipt_number()
                    venta = Venta(id_estudiante=id_estudiante, id_usuario=id_usuario, fecha_venta=_get_today(), monto_total=0, metodo_pago="EFECTIVO", tipo_venta="INSCRIPCION", numero_recibo=numero_recibo)
                    import sqlite3
                    id_venta = None
                    for _ in range(3):
                        try:
                            id_venta = venta_repository.insertar(venta)
                            break
                        except sqlite3.IntegrityError:
                            venta.numero_recibo = generate_receipt_number()
                    if id_venta is None:
                        raise RuntimeError("No se pudo generar recibo para inscripción")
                    detalle_venta_repository.insertar(DetalleVenta(id_venta=id_venta, id_producto=prod_camiseta["id_producto"], cantidad=1, precio_unitario=0, subtotal=0))
                    stock_ant = prod_camiseta["stock_actual"]
                    stock_nuevo = stock_ant - 1
                    producto_repository.actualizar_stock(prod_camiseta["id_producto"], stock_nuevo)
                    from repositories import movimiento_inventario_repository
                    from models.movimiento_inventario import MovimientoInventario
                    from utils.dates import get_now
                    movimiento_inventario_repository.insertar(MovimientoInventario(id_producto=prod_camiseta["id_producto"], id_usuario=id_usuario, tipo_movimiento="SALIDA", cantidad=1, stock_anterior=stock_ant, stock_nuevo=stock_nuevo, fecha_movimiento=get_now(), motivo=f"Regalo inscripción nuevo es_nuevo=1 estudiante {id_estudiante} - Camiseta Entrenamiento"))
                    auditoria_service.registrar_insert(id_usuario, "venta", id_venta, f"INSCRIPCION camiseta -1 stock {stock_ant}->{stock_nuevo}")

            # RN-051: bloquear productos extra si es_nuevo con regalo
            if es_nuevo_flag and debe_regalar_camiseta and data.get("productos"):
                # backend ignora extras para no cobrar doble; extra va por Ventas
                pass
            else:
                productos_sel = data.get("productos", [])
                if productos_sel:
                    from repositories import producto_repository as prod_repo2
                    from services import venta_service as venta_svc2
                    for p in productos_sel:
                        pid = p.get("id_producto")
                        cant = int(p.get("cantidad", 1))
                        prod = prod_repo2.obtener_por_id(pid)
                        if not prod:
                            raise ValueError(f"Producto {pid} no encontrado")
                        if prod["stock_actual"] < cant:
                            raise ValueError(f"Stock insuficiente de {prod['nombre']} (disp: {prod['stock_actual']})")
                        ok_v, msg_v, _ = venta_svc2.registrar_venta({"id_estudiante": id_estudiante, "id_usuario": id_usuario, "tipo_venta": "UNIFORME", "metodo_pago": "EFECTIVO", "items": [{"id_producto": pid, "cantidad": cant}]})
                        if not ok_v:
                            raise ValueError(msg_v)

            for beca_info in becas_asignadas:
                id_beca = beca_info.get("id_beca")
                beca_data = beca_service.obtener_beca(id_beca)
                if beca_data:
                    if beca_data["tipo"] == "PORCENTAJE":
                        descuento = monto_base * (beca_data["valor"] / 100)
                        monto_base -= descuento
                    else:
                        monto_base -= beca_data["valor"]
                    matricula_beca_repository.insertar(id_matricula=id_matricula, id_beca=id_beca, observacion=beca_info.get("observacion", ""))

            monto_base = round(max(monto_base, 0), 2)
            diferir = int(data.get("diferir_meses", 0) or 0)
            cuota_service.generar_siguiente_cuota(id_matricula=id_matricula, monto_base=monto_base, dia_vencimiento=dia_vencimiento)
            for _ in range(max(0, diferir - 1)):
                cuota_service.generar_siguiente_cuota(id_matricula=id_matricula, monto_base=monto_base, dia_vencimiento=dia_vencimiento)

            if estudiante["estado"] == STATUS_REINGRESANTE:
                estudiante_repository.cambiar_estado(id_estudiante, STATUS_ACTIVO)

            auditoria_service.registrar_insert(id_usuario=id_usuario, tabla="matricula", id_registro=id_matricula, valores_nuevos=f"id_estudiante={id_estudiante}, id_tarifa={id_tarifa}, monto={monto_base}")

        logger.info(f"Matrícula creada: ID={id_matricula}, estudiante={id_estudiante}")
        return True, "Matrícula registrada correctamente", id_matricula
    except ValueError as e:
        # Stock insuficiente o producto no encontrado → mensaje amigable, rollback ya hecho
        logger.warning(f"Matrícula fallida: {e}")
        return False, str(e), None
    except RuntimeError:
        # Para test de atomicidad (fallo simulado en cuota) debe propagar
        raise
    except Exception as e:
        logger.error(f"Error al crear matrícula: {e}", exc_info=True)
        return False, "Error al registrar matrícula", None


def obtener_matricula(id_matricula: int) -> dict | None:
    return matricula_repository.obtener_por_id(id_matricula)


def obtener_por_estudiante(id_estudiante: int) -> list[dict]:
    return matricula_repository.obtener_por_estudiante(id_estudiante)


def listar_matriculas_activas() -> list[dict]:
    return matricula_repository.obtener_activas()


def _recalcular_cuotas_pendientes(id_matricula: int):
    from repositories import tarifa_repository, cuota_repository
    from models.cuota import Cuota
    matricula = matricula_repository.obtener_por_id(id_matricula)
    if not matricula:
        return
    tarifa = tarifa_repository.obtener_por_id(matricula["id_tarifa"])
    if not tarifa:
        return
    monto_base = matricula["monto_pactado"] if matricula["monto_pactado"] is not None else tarifa["monto"]
    becas = [b for b in matricula_beca_repository.obtener_por_matricula(id_matricula) if b.get("activo", 1)]
    for mb in becas:
        bd = beca_service.obtener_beca(mb["id_beca"])
        if not bd:
            continue
        if bd["tipo"] == "PORCENTAJE":
            monto_base -= monto_base * (bd["valor"] / 100)
        else:
            monto_base -= bd["valor"]
    monto_base = round(max(monto_base, 0), 2)
    for c in cuota_repository.obtener_por_matricula(id_matricula):
        if c["estado"] != "PENDIENTE":
            continue
        if abs(c["monto_total"] - monto_base) < 0.01:
            continue
        nuevo_saldo = round(monto_base - c["monto_pagado"], 2)
        cuota_obj = Cuota(id_cuota=c["id_cuota"], id_matricula=c["id_matricula"], periodo=c["periodo"], fecha_vencimiento=c["fecha_vencimiento"], monto_total=monto_base, monto_pagado=c["monto_pagado"], saldo=nuevo_saldo, estado="PENDIENTE", monto_mora=c.get("monto_mora", 0), activo=c["activo"])
        cuota_repository.actualizar(cuota_obj)
        auditoria_service.registrar_update(id_usuario=auditoria_service.id_usuario_sesion(), tabla="cuota", id_registro=c["id_cuota"], valores_anteriores=f"monto_total={c['monto_total']}, saldo={c['saldo']}", valores_nuevos=f"monto_total={monto_base}, saldo={nuevo_saldo}")


def asignar_beca(id_matricula: int, id_beca: int, observacion: str = "") -> tuple[bool, str]:
    beca = beca_service.obtener_beca(id_beca)
    if not beca:
        return False, "Beca no encontrada"
    actuales = [b for b in matricula_beca_repository.obtener_por_matricula(id_matricula) if b.get("activo", 1)]
    if actuales:
        from services import configuracion_service
        if not configuracion_service.permite_multiples_becas():
            return False, "La configuración actual no permite múltiples becas por matrícula"
    from database.connection import transaccion
    with transaccion():
        matricula_beca_repository.insertar(id_matricula, id_beca, observacion)
        _recalcular_cuotas_pendientes(id_matricula)
    auditoria_service.registrar_insert(id_usuario=auditoria_service.id_usuario_sesion(), tabla="matricula_beca", id_registro=id_matricula, valores_nuevos=f"id_beca={id_beca}, observacion={observacion}")
    return True, "Beca asignada correctamente (cuotas pendientes recalculadas)"


def desasignar_beca(id_matricula: int, id_beca: int) -> tuple[bool, str]:
    from database.connection import transaccion
    with transaccion():
        matricula_beca_repository.eliminar(id_matricula, id_beca)
        _recalcular_cuotas_pendientes(id_matricula)
    auditoria_service.registrar_desactivacion(id_usuario=auditoria_service.id_usuario_sesion(), tabla="matricula_beca", id_registro=id_matricula, valores_anteriores=f"id_beca={id_beca}, activo=1", valores_nuevos="activo=0")
    return True, "Beca desasignada correctamente (cuotas pendientes recalculadas)"


def obtener_becas_por_matricula(id_matricula: int) -> list[dict]:
    return matricula_beca_repository.obtener_por_matricula(id_matricula)


MONTO_EXPRESS_NUEVO_DEFAULT = 120.0


def monto_express_nuevo_default() -> float:
    """Fase 4: el default NUEVO lo manda la tarifa Inscripción (editable en
    Tarifas); el constante solo es fallback si no hay tarifa."""
    try:
        tarifa = _tarifa_inscripcion_default()
        if tarifa and float(tarifa.get("monto") or 0) > 0:
            return float(tarifa["monto"])
    except Exception:
        pass
    return MONTO_EXPRESS_NUEVO_DEFAULT


def _tarifa_inscripcion_default() -> dict | None:
    from repositories import tarifa_repository
    try:
        todas = tarifa_repository.obtener_activas(tipo="SERVICIO")
    except TypeError:
        todas = tarifa_repository.obtener_activas()
    for t in todas:
        if (t.get("nombre", "") or "").strip().lower() == "inscripción":
            return t
    return todas[0] if todas else None


def matricula_express(data: dict, id_usuario: int = 1) -> tuple[bool, str, dict | None]:
    """Matrícula en 1 paso: crea/usa estudiante + matrícula + pago primera cuota.

    data: tipo (NUEVO/ANTIGUO), nombres, apellidos, dni, tipo_documento (DNI/CARNET),
          monto (str|float|None), metodo_pago (YAPE/EFECTIVO),
          comprobante_path (obligatorio si YAPE).
    NUEVO: monto default 120 editable, es_nuevo=1 (regala uniforme vía RN-051).
    ANTIGUO: monto obligatorio editable, sin descuento, es_nuevo=0.
    Todo atómico (transacción única). Apoderado queda pendiente.
    """
    from services import estudiante_service, pago_service

    tipo = (data.get("tipo") or "").strip().upper()
    if tipo not in ("NUEVO", "ANTIGUO"):
        return False, "Tipo no válido. Use NUEVO o ANTIGUO", None
    nombres = (data.get("nombres") or "").strip()
    apellidos = (data.get("apellidos") or "").strip()
    dni = (data.get("dni") or "").strip()
    if not nombres or not apellidos:
        return False, "Nombres y apellidos son obligatorios", None
    from utils.validators import validate_documento
    tipo_doc = (data.get("tipo_documento") or "DNI").strip().upper()
    if tipo_doc not in ("DNI", "CARNET"):
        return False, "Tipo de documento no válido. Use DNI o CARNET", None
    if not validate_documento(dni, tipo_doc):
        if tipo_doc == "CARNET":
            return False, "El Carnet debe tener 9 dígitos", None
        return False, "El DNI debe tener 8 dígitos", None
    metodo = (data.get("metodo_pago") or "").strip().upper()
    if metodo not in ("YAPE", "EFECTIVO"):
        return False, "Método no válido. Use Yape o Efectivo", None
    monto_raw = data.get("monto")
    if tipo == "NUEVO" and (monto_raw in (None, "")):
        monto_raw = monto_express_nuevo_default()
    try:
        monto = float(monto_raw)
    except (ValueError, TypeError):
        return False, "Monto inválido", None
    if monto <= 0:
        return False, "El monto debe ser mayor a 0", None
    comprobante = (data.get("comprobante_path") or "").strip() or None
    if metodo == "YAPE" and not comprobante:
        return False, "Suba comprobante para Yape (RN-042)", None

    tarifa = _tarifa_inscripcion_default()
    if not tarifa:
        return False, "Sin tarifa de inscripción (Servicios). Pídala al ADMIN", None

    try:
        with transaccion():
            from repositories import persona_repository
            persona = persona_repository.obtener_por_dni(dni)
            id_estudiante = None
            if persona:
                existente = estudiante_repository.obtener_por_persona(persona["id_persona"])
                if existente:
                    id_estudiante = existente["id_estudiante"]
            if id_estudiante is None:
                ok_e, msg_e, id_estudiante = estudiante_service.crear_estudiante({
                    "dni": dni, "nombres": nombres, "apellidos": apellidos,
                    "tipo_documento": tipo_doc,
                    "es_nuevo": 1 if tipo == "NUEVO" else 0,
                }, id_usuario=id_usuario)
                if not ok_e:
                    raise ValueError(msg_e)
            ok_m, msg_m, id_matricula = crear_matricula({
                "id_estudiante": id_estudiante,
                "id_tarifa": tarifa["id_tarifa"],
                "monto_pactado": monto,
                "dia_vencimiento": 1,
                "diferir_meses": 0,
                "tipo": tipo,
                "fecha_inicio": (str(data.get("fecha_inicio") or "").strip() or get_today()),
            }, id_usuario=id_usuario)
            if not ok_m:
                raise ValueError(msg_m)
            cuotas = cuota_service.obtener_cuotas_por_matricula(id_matricula)
            pendientes = [c for c in cuotas if c.get("estado") != "PAGADO"]
            if not pendientes:
                raise ValueError("Sin cuota pendiente generada")
            cuota = pendientes[0]
            a_pagar = min(monto, float(cuota.get("saldo", 0) or 0))
            if a_pagar <= 0:
                raise ValueError("La cuota no tiene saldo pendiente")
            ok_p, msg_p, id_pago = pago_service.registrar_pago({
                "id_usuario": id_usuario,
                "id_cuota": cuota["id_cuota"],
                "monto_pagado": a_pagar,
                "metodo_pago": metodo,
                "comprobante_path": comprobante,
                "fecha_pago": (str(data.get("fecha_inicio") or "").strip() or get_today()),
                "observacion": "Matrícula express " + tipo,
            })
            if not ok_p:
                raise ValueError(msg_p)
        logger.info("Matrícula express %s: est=%s mat=%s pago=%s", tipo, id_estudiante, id_matricula, id_pago)
        return True, "Matriculado (%s) y cobrado S/%.2f. Apoderado pendiente en Estudiantes." % (tipo, a_pagar), {
            "id_estudiante": id_estudiante,
            "id_matricula": id_matricula,
            "id_pago": id_pago,
            "monto_cobrado": a_pagar,
        }
    except ValueError as e:
        logger.warning("Matrícula express fallida: %s", e)
        return False, str(e), None
    except Exception as e:
        logger.error("Error en matrícula express: %s", e, exc_info=True)
        return False, "Error al registrar matrícula express", None
