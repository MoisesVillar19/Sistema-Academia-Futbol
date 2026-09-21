from dataclasses import dataclass


@dataclass
class Matricula:
    id_matricula: int | None = None
    id_estudiante: int = 0
    id_tarifa: int = 0
    monto_pactado: float | None = None
    pago_matricula: str = "AHORA"
    monto_matricula: float = 0.0
    fecha_inicio: str = ""
    fecha_fin: str = ""
    dia_vencimiento: int = 1
    tipo: str | None = None
    estado: str = "ACTIVO"
    activo: int = 1
