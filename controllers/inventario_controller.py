from services import inventario_service
from utils.validators import validate_not_empty, validate_tipo_uso, validate_tipo_movimiento


def crear_categoria(data: dict) -> tuple[bool, str, int | None]:
    error = validate_not_empty(data.get("nombre", ""), "Nombre")
    if error:
        return False, error, None
    return inventario_service.crear_categoria(data)


def editar_categoria(id_categoria: int, data: dict) -> tuple[bool, str]:
    return inventario_service.editar_categoria(id_categoria, data)


def listar_categorias(activo: int | None = None) -> list[dict]:
    return inventario_service.listar_categorias(activo=activo)


def crear_producto(data: dict) -> tuple[bool, str, int | None]:
    error = validate_not_empty(data.get("nombre", ""), "Nombre")
    if error:
        return False, error, None

    tipo_uso = data.get("tipo_uso", "")
    if tipo_uso and not validate_tipo_uso(tipo_uso):
        return False, "Tipo de uso no válido. Use CONSUMO_INTERNO o VENTA", None

    return inventario_service.crear_producto(data)


def editar_producto(id_producto: int, data: dict) -> tuple[bool, str]:
    tipo_uso = data.get("tipo_uso", "")
    if tipo_uso and not validate_tipo_uso(tipo_uso):
        return False, "Tipo de uso no válido. Use CONSUMO_INTERNO o VENTA"
    return inventario_service.editar_producto(id_producto, data)


def registrar_compra(data: dict) -> tuple[bool, str, int | None]:
    try:
        cantidad = int(data.get("cantidad", 0))
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a 0", None
        data["cantidad"] = cantidad
    except (ValueError, TypeError):
        return False, "Cantidad no válida", None
    return inventario_service.registrar_compra(data)


def registrar_movimiento(data: dict) -> tuple[bool, str, int | None]:
    tipo = data.get("tipo_movimiento", "")
    if not validate_tipo_movimiento(tipo):
        return False, "Tipo de movimiento no válido. Use ENTRADA, SALIDA o AJUSTE", None

    try:
        cantidad = int(data.get("cantidad", 0))
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a 0", None
        data["cantidad"] = cantidad
    except (ValueError, TypeError):
        return False, "Cantidad no válida", None

    return inventario_service.registrar_movimiento(data)


def obtener_producto(id_producto: int) -> dict | None:
    return inventario_service.obtener_producto(id_producto)


def listar_productos(activo: int | None = None) -> list[dict]:
    return inventario_service.listar_productos(activo=activo)


def obtener_bajo_stock() -> list[dict]:
    return inventario_service.obtener_bajo_stock()


def listar_movimientos(limit: int = 100, offset: int = 0) -> list[dict]:
    return inventario_service.listar_movimientos(limit=limit, offset=offset)


def listar_movimientos_por_producto(id_producto: int) -> list[dict]:
    return inventario_service.listar_movimientos_por_producto(id_producto)


def listar_movimientos_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return inventario_service.listar_movimientos_por_fecha(fecha_inicio, fecha_fin)
