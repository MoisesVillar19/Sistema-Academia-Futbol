import sqlite3

from repositories import venta_repository, detalle_venta_repository, producto_repository, movimiento_inventario_repository
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from services import auditoria_service
from database.connection import transaccion
from utils.constants import METODO_EFECTIVO, METODO_YAPE, METODO_PLIN, METODO_TRANSFERENCIA
from utils.helpers import generate_receipt_number
from utils.dates import get_today
from utils.logger import logger

METODOS_VALIDOS = (METODO_EFECTIVO, METODO_YAPE, METODO_PLIN, METODO_TRANSFERENCIA)
TIPOS_VENTA_VALIDOS = ("UNIFORME", "TIENDA", "CAMPEONATO", "INSCRIPCION")


def _obtener_almacen_default() -> int | None:
    try:
        from repositories import almacen_repository
        alm = almacen_repository.obtener_por_nombre("Principal")
        return alm["id_almacen"] if alm else None
    except Exception:
        return None

def registrar_venta(data: dict) -> tuple[bool, str, int | None]:
    """Venta flexible escalable: uniformes (variante/talla), tienda, campeonato. Descuenta stock atómicamente (global + stock_almacen)."""
    id_usuario = data.get("id_usuario") or auditoria_service.id_usuario_sesion()
    id_estudiante = data.get("id_estudiante")
    metodo = data.get("metodo_pago", METODO_EFECTIVO)
    tipo_venta = data.get("tipo_venta", "UNIFORME")
    items: list[dict] = data.get("items", [])  # [{id_producto, cantidad, id_variante}]
    comprobante = data.get("comprobante_path")
    id_almacen = data.get("id_almacen") or _obtener_almacen_default()
    id_caja = data.get("id_caja")

    # CAMPEONATO se cobra por tarifa (división), sin items obligatorios
    try:
        monto_campeonato = float(data.get("monto_total") or 0)
    except (TypeError, ValueError):
        monto_campeonato = 0
    es_campeonato_por_tarifa = (
        tipo_venta == "CAMPEONATO" and not items and monto_campeonato > 0
    )
    if not items and not es_campeonato_por_tarifa:
        return False, "Debe incluir al menos un producto", None
    if metodo not in METODOS_VALIDOS:
        return False, "Método de pago no válido", None
    if tipo_venta not in TIPOS_VENTA_VALIDOS:
        return False, "Tipo de venta no válido", None
    id_tarifa = data.get("id_tarifa")
    if id_tarifa is not None and tipo_venta != "CAMPEONATO":
        return False, "La tarifa solo aplica a ventas CAMPEONATO", None
    if metodo != METODO_EFECTIVO and not comprobante and data.get("requiere_comprobante"):
        logger.warning(f"Venta {tipo_venta} sin comprobante para {metodo} (RN-042)")

    # total flexible (se recalculará dentro de transacción con precios actuales)
    # Permitir monto pactado flexible (descuento)
    total_precalculado = None
    if data.get("monto_total") is not None:
        total_precalculado = float(data["monto_total"])

    numero_recibo = data.get("numero_recibo") or generate_receipt_number()
    # venta se crea dentro de transacción con total correcto

    try:
        with transaccion():
            # Validar stock y calcular total DENTRO de transacción (evita TOCTOU) — maneja variante/talla
            total = 0
            if es_campeonato_por_tarifa:
                total = round(float(data["monto_total"]), 2)
            for it in items:
                prod = producto_repository.obtener_por_id(it["id_producto"])
                if not prod:
                    raise ValueError(f"Producto {it['id_producto']} no encontrado")
                if prod["activo"] == 0:
                    raise ValueError(f"Producto {prod['nombre']} desactivado")
                # Fase 6a: solo Tiendita se vende (Almacén no cruza a ventas)
                if (prod.get("canal") or "") != "TIENDITA":
                    raise ValueError(
                        f"Producto {prod['nombre']} es de Almacén y no se puede vender")
                id_variante = it.get("id_variante")
                # si hay variante, validar stock_almacen de variante, no solo producto
                disp = prod["stock_actual"]
                if id_variante:
                    try:
                        from repositories import stock_almacen_repository, almacen_repository
                        alm = almacen_repository.obtener_por_nombre("Principal")
                        alm_id = alm["id_almacen"] if alm else 1
                        # id_almacen puede venir en item
                        alm_id = it.get("id_almacen") or alm_id
                        sa = stock_almacen_repository.obtener(it["id_producto"], id_variante, alm_id, it.get("id_caja"))
                        if sa:
                            disp = sa["stock"]
                        else:
                            disp = 0
                    except Exception:
                        disp = prod["stock_actual"]
                if disp < it["cantidad"]:
                    raise ValueError(f"Stock insuficiente de {prod['nombre']} (disp: {disp})")
                precio_u = it.get("precio_unitario") or prod.get("precio_venta") or prod.get("precio") or 0
                if precio_u <= 0:
                    logger.warning(f"Venta con precio 0 para {prod['nombre']}")
                total += round(precio_u * it["cantidad"], 2)
            if total_precalculado is not None:
                total = total_precalculado

            venta = Venta(
                id_estudiante=id_estudiante,
                id_usuario=id_usuario,
                fecha_venta=(str(data.get("fecha_venta") or "").strip() or get_today()),
                monto_total=round(total, 2),
                metodo_pago=metodo,
                tipo_venta=tipo_venta,
                numero_recibo=numero_recibo,
                comprobante_path=comprobante,
                id_tarifa=id_tarifa,
            )
            id_venta = None
            for _ in range(3):
                try:
                    id_venta = venta_repository.insertar(venta)
                    break
                except sqlite3.IntegrityError:
                    venta.numero_recibo = generate_receipt_number()
            if id_venta is None:
                raise RuntimeError("No se pudo generar recibo único")

            for it in items:
                prod = producto_repository.obtener_por_id(it["id_producto"])
                stock_ant = prod["stock_actual"]
                stock_nuevo = stock_ant - it["cantidad"]
                precio_u = it.get("precio_unitario") or prod.get("precio_venta") or prod.get("precio") or 0
                # variante/talla opcional (escalable)
                id_variante = it.get("id_variante")
                detalle = DetalleVenta(
                    id_venta=id_venta,
                    id_producto=it["id_producto"],
                    cantidad=it["cantidad"],
                    precio_unitario=round(precio_u, 2),
                    subtotal=round(precio_u * it["cantidad"], 2),
                )
                # si hay variante, añadir al detalle
                if id_variante:
                    detalle.id_variante = id_variante  # type: ignore
                detalle_venta_repository.insertar(detalle)
                producto_repository.actualizar_stock(it["id_producto"], stock_nuevo)
                # stock_almacen escalable (si solo 1 almacén, no visible)
                try:
                    from repositories import stock_almacen_repository
                    alm_id = id_almacen
                    if alm_id:
                        # actualizar stock por almacén/variante
                        # manejar NULL variante
                        stock_almacen_repository.upsert_stock(it["id_producto"], id_variante, alm_id, id_caja, -it["cantidad"])
                    # lote FIFO si existe (perecederos)
                    try:
                        from repositories import lote_repository
                        if it.get("id_lote"):
                            # descuento directo lote
                            pass
                        else:
                            # FIFO auto si producto tiene lotes vigentes
                            lote_repository.descontar_fifo(it["id_producto"], id_variante, alm_id or 1, it["cantidad"])
                    except Exception:
                        pass
                except Exception:
                    pass
                from models.movimiento_inventario import MovimientoInventario
                from utils.dates import get_now
                movimiento_inventario_repository.insertar(
                    MovimientoInventario(
                        id_producto=it["id_producto"],
                        id_usuario=id_usuario,
                        tipo_movimiento="SALIDA",
                        cantidad=it["cantidad"],
                        stock_anterior=stock_ant,
                        stock_nuevo=stock_nuevo,
                        fecha_movimiento=get_now(),
                        motivo=f"Venta {tipo_venta} recibo {venta.numero_recibo}",
                    )
                )

            auditoria_service.registrar_insert(id_usuario, "venta", id_venta, f"recibo={venta.numero_recibo}, total={total}, tipo={tipo_venta}")

        logger.info(f"Venta registrada: {venta.numero_recibo} total={total}")
        return True, f"Venta registrada. Recibo: {venta.numero_recibo}", id_venta
    except ValueError as e:
        return False, str(e), None
    except RuntimeError as e:
        return False, str(e), None
    except Exception as e:
        logger.error(f"Error en venta: {e}", exc_info=True)
        return False, "Error al registrar venta", None


def listar_ventas(fecha_inicio: str | None = None, fecha_fin: str | None = None, tipo_venta: str | None = None) -> list[dict]:
    return venta_repository.obtener_todos(fecha_inicio, fecha_fin, tipo_venta)


def obtener_venta(id_venta: int) -> dict | None:
    return venta_repository.obtener_por_id(id_venta)
