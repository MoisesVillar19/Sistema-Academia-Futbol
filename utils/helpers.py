def generate_receipt_number() -> str:
    """Genera un numero de recibo unico: timestamp con microsegundos + aleatorio.

    Los microsegundos evitan colisiones entre pagos registrados en el mismo segundo.
    """
    from datetime import datetime
    import random
    now = datetime.now()
    rand = random.randint(100, 999)
    return now.strftime("R%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}" + str(rand)


def generate_product_code() -> str:
    """Genera código único con microsegundos + aleatorio para evitar colisión."""
    from datetime import datetime
    import random
    now = datetime.now()
    rand = random.randint(100, 999)
    return now.strftime("PRD%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}" + str(rand)


# Limpieza: clean_dni/clean_phone/truncate_text sin uso se retiraron.
# format_money se conserva (formato moneda estándar a futuro).

def format_money(amount: float) -> str:
    return f"S/{amount:.2f}"
