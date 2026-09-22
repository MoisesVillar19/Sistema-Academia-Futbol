from utils.validators import (
    validate_dni, validate_email, validate_phone, validate_sex,
    validate_rol, validate_estado_estudiante, validate_estado_cuota,
    validate_metodo_pago, validate_tipo_beca, validate_tipo_movimiento,
    validate_canal, validate_dia_vencimiento, validate_not_empty
)


def test_validate_dni_valid():
    assert validate_dni("12345678") is True
    assert validate_dni("00000000") is True
    assert validate_dni("99999999") is True


def test_validate_dni_invalid():
    assert validate_dni("12345") is False
    assert validate_dni("123456789") is False
    assert validate_dni("abcdefgh") is False
    assert validate_dni("") is False


def test_validate_email_valid():
    assert validate_email("test@test.com") is True
    assert validate_email("user@domain.org") is True


def test_validate_email_invalid():
    assert validate_email("invalid") is False
    assert validate_email("test@") is False
    assert validate_email("@test.com") is False


def test_validate_email_optional():
    assert validate_email("") is True
    assert validate_email(None) is True


def test_validate_phone_valid():
    assert validate_phone("123456789") is True
    assert validate_phone("123456789012") is True


def test_validate_phone_invalid():
    assert validate_phone("12345") is False
    assert validate_phone("abcdefghi") is False


def test_validate_phone_optional():
    assert validate_phone("") is True
    assert validate_phone(None) is True


def test_validate_sex():
    assert validate_sex("M") is True
    assert validate_sex("F") is True
    assert validate_sex("X") is False
    assert validate_sex("") is False


def test_validate_rol():
    assert validate_rol("ADMIN") is True
    assert validate_rol("SECRETARIA") is True
    assert validate_rol("USER") is False


def test_validate_estado_estudiante():
    assert validate_estado_estudiante("ACTIVO") is True
    assert validate_estado_estudiante("RETIRADO") is True
    assert validate_estado_estudiante("REINGRESANTE") is True
    assert validate_estado_estudiante("INVALIDO") is False


def test_validate_estado_cuota():
    assert validate_estado_cuota("PENDIENTE") is True
    assert validate_estado_cuota("PARCIAL") is True
    assert validate_estado_cuota("PAGADO") is True
    assert validate_estado_cuota("VENCIDO") is True
    assert validate_estado_cuota("INVALIDO") is False


def test_validate_metodo_pago():
    assert validate_metodo_pago("EFECTIVO") is True
    assert validate_metodo_pago("YAPE") is True
    assert validate_metodo_pago("PLIN") is True
    assert validate_metodo_pago("TRANSFERENCIA") is True
    assert validate_metodo_pago("TARJETA") is False


def test_validate_tipo_beca():
    assert validate_tipo_beca("PORCENTAJE") is True
    assert validate_tipo_beca("MONTO_FIJO") is True
    assert validate_tipo_beca("INVALIDO") is False


def test_validate_tipo_movimiento():
    assert validate_tipo_movimiento("ENTRADA") is True
    assert validate_tipo_movimiento("SALIDA") is True
    assert validate_tipo_movimiento("AJUSTE") is True
    assert validate_tipo_movimiento("INVALIDO") is False


def test_validate_canal():
    assert validate_canal("TIENDITA") is True
    assert validate_canal("ALMACEN") is True
    assert validate_canal("INVALIDO") is False
    assert validate_canal("VENTA") is False


def test_validate_dia_vencimiento():
    assert validate_dia_vencimiento(1) is True
    assert validate_dia_vencimiento(31) is True
    assert validate_dia_vencimiento(0) is False
    assert validate_dia_vencimiento(32) is False


def test_validate_not_empty():
    assert validate_not_empty("test", "Campo") is None
    assert validate_not_empty("  ", "Campo") is not None
    assert validate_not_empty("", "Campo") is not None
    assert validate_not_empty(None, "Campo") is not None
