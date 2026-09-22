from dataclasses import dataclass


@dataclass
class Pago:
    id_pago: int | None = None
    id_usuario: int = 0
    numero_recibo: str = ""
    fecha_pago: str = ""
    monto_total: float = 0.0
    metodo_pago: str = ""
    observacion: str = ""
    comprobante_path: str = ""
    activo: int = 1
