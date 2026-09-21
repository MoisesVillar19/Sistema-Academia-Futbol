from dataclasses import dataclass


@dataclass
class MovimientoInventario:
    id_movimiento: int | None = None
    id_producto: int = 0
    id_usuario: int = 0
    tipo_movimiento: str = ""
    cantidad: int = 0
    stock_anterior: int = 0
    stock_nuevo: int = 0
    fecha_movimiento: str = ""
    motivo: str = ""
    metodo_pago: str | None = None
    monto_total: float = 0.0
