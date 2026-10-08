from dataclasses import dataclass


@dataclass
class Cuota:
    id_cuota: int | None = None
    id_matricula: int = 0
    periodo: str = ""
    fecha_vencimiento: str = ""
    monto_total: float = 0.0
    monto_pagado: float = 0.0
    monto_mora: float = 0.0
    saldo: float = 0.0
    estado: str = "PENDIENTE"
    origen: str = "MANUAL"
    activo: int = 1
