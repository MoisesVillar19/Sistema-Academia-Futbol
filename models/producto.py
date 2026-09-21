from dataclasses import dataclass


@dataclass
class Producto:
    id_producto: int | None = None
    id_categoria_producto: int = 0
    tipo_uso: str = ""
    codigo: str = ""
    nombre: str = ""
    stock_actual: int = 0
    stock_minimo: int = 0
    precio: float = 0.0
    precio_compra: float = 0.0
    precio_venta: float = 0.0
    tipo_empaque: str = "Unidad"
    cantidad_por_caja: int = 1
    precio_compra_total: float = 0.0
    id_tipo_uniforme: int | None = None
    activo: int = 1
