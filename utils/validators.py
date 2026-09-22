import re


def validate_dni(dni: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", dni))


def validate_carnet(carnet: str) -> bool:
    return bool(re.fullmatch(r"\d{9}", carnet))


def validate_documento(documento: str, tipo_documento: str = "DNI") -> bool:
    if tipo_documento == "CARNET":
        return validate_carnet(documento)
    return validate_dni(documento)


def validate_email(email: str) -> bool:
    if not email:
        return True
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))


def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    return bool(re.fullmatch(r"\d{9,12}", phone))


def validate_sex(sex: str) -> bool:
    return sex in ("M", "F")


def validate_rol(rol: str) -> bool:
    # Solo 2 roles (RN-002 v2.1): CAJA/INVENTARIO legacy se migran a SECRETARIA al arrancar
    return rol in ("ADMIN", "SECRETARIA")


def validate_estado_estudiante(estado: str) -> bool:
    return estado in ("ACTIVO", "RETIRADO", "REINGRESANTE")


def validate_estado_cuota(estado: str) -> bool:
    return estado in ("PENDIENTE", "PARCIAL", "PAGADO", "VENCIDO")


def validate_metodo_pago(metodo: str) -> bool:
    return metodo in ("EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA")


def validate_tipo_beca(tipo: str) -> bool:
    return tipo in ("PORCENTAJE", "MONTO_FIJO")


def validate_tipo_movimiento(tipo: str) -> bool:
    return tipo in ("ENTRADA", "SALIDA", "AJUSTE")


CANALES_VALIDOS = ("TIENDITA", "ALMACEN")


def validate_canal(canal: str) -> bool:
    return canal in CANALES_VALIDOS


def validate_tipo_uso(tipo: str) -> bool:
    # Compat legacy: CONSUMO_INTERNO/VENTA → ALMACEN/TIENDITA
    return tipo in CANALES_VALIDOS or tipo in ("CONSUMO_INTERNO", "VENTA")


def validate_dia_vencimiento(dia: int) -> bool:
    return 1 <= dia <= 31


def validate_not_empty(value: str, field_name: str = "Campo") -> str | None:
    if not value or not value.strip():
        return f"{field_name} es obligatorio"
    return None
