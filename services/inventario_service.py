from repositories import (categoria_producto_repository, producto_repository,
                           movimiento_inventario_repository)
from models.categoria_producto import CategoriaProducto
from models.producto import Producto
from models.movimiento_inventario import MovimientoInventario
from services import auditoria_service
from utils.dates import get_now
from utils.logger import logger


def crear_categoria(data: dict) -> tuple[bool, str, int | None]:
    nombre = data.get("nombre", "")
    if not nombre:
        return False, "El nombre es obligatorio", None

    if categoria_producto_repository.existe_nombre(nombre):
        return False, "Ya existe una categoría con ese nombre", None

    categoria = CategoriaProducto(nombre=nombre)
    id_categoria = categoria_producto_repository.insertar(categoria)

    auditoria_service.registrar_insert(
        id_usuario=1,
        tabla="categoria_producto",
        id_registro=id_categoria,
        valores_nuevos=f"nombre={nombre}",
    )

    logger.info(f"Categoría de producto creada: {nombre}")
    return True, "Categoría creada correctamente", id_categoria


def editar_categoria(id_categoria: int, data: dict) -> tuple[bool, str]:
    categoria = categoria_producto_repository.obtener_por_id(id_categoria)
    if not categoria:
        return False, "Categoría no encontrada"

    nombre = data.get("nombre", categoria["nombre"])
    if categoria_producto_repository.existe_nombre(nombre, exclude_id=id_categoria):
        return False, "Ya existe otra categoría con ese nombre"

    categoria_obj = CategoriaProducto(
        id_categoria_producto=id_categoria,
        nombre=nombre,
        activo=categoria["activo"],
    )
    categoria_producto_repository.actualizar(categoria_obj)

    auditoria_service.registrar_update(
        id_usuario=auditoria_service.id_usuario_sesion(),
        tabla="categoria_producto",
        id_registro=id_categoria,
        valores_anteriores=f"nombre={categoria['nombre']}",
        valores_nuevos=f"nombre={nombre}",
    )

    return True, "Categoría actualizada correctamente"


def listar_categorias(activo: int | None = None) -> list[dict]:
    return categoria_producto_repository.obtener_todas(activo=activo)


def crear_producto(data: dict) -> tuple[bool, str, int | None]:
    codigo = data.get("codigo", "")
    nombre = data.get("nombre", "")
    id_categoria = data.get("id_categoria_producto")

    if not nombre:
        return False, "El nombre es obligatorio", None
    if not id_categoria:
        return False, "La categoría es obligatoria", None

    if not codigo:
        from utils.helpers import generate_product_code
        codigo = generate_product_code()

    if producto_repository.existe_codigo(codigo):
        return False, "Ya existe un producto con ese código", None

    stock_minimo = data.get("stock_minimo", 0)
    try:
        stock_minimo = int(stock_minimo)
    except (ValueError, TypeError):
        stock_minimo = 0

    precio = data.get("precio", 0)
    try:
        precio = float(precio)
    except (ValueError, TypeError):
        precio = 0

    # v2 flexible: precio_compra/venta y tipo_uniforme
    precio_compra = data.get("precio_compra", precio)
    try:
        precio_compra = float(precio_compra)
    except (ValueError, TypeError):
        precio_compra = precio
    precio_venta = data.get("precio_venta", precio)
    try:
        precio_venta = float(precio_venta)
    except (ValueError, TypeError):
        precio_venta = precio

    # Empaque y costo: unitario = total / cantidad (Unidad => 1)
    TIPOS_EMPAQUE = ("Unidad", "Caja x12", "Caja x100", "Personalizado")
    tipo_empaque = data.get("tipo_empaque", "Unidad")
    if tipo_empaque not in TIPOS_EMPAQUE:
        return False, f"Tipo de empaque no válido. Use: {', '.join(TIPOS_EMPAQUE)}", None
    crudo_cant = data.get("cantidad_por_caja", 1)
    if crudo_cant in (None, ""):
        crudo_cant = 1
    try:
        cantidad_por_caja = int(crudo_cant)
    except (ValueError, TypeError):
        return False, "Cantidad por caja inválida", None
    if tipo_empaque == "Unidad":
        cantidad_por_caja = 1
    if cantidad_por_caja <= 0:
        return False, "Cantidad por caja debe ser mayor a 0", None
    precio_total = data.get("precio_compra_total")
    try:
        precio_total = float(precio_total) if precio_total not in (None, "") else None
    except (ValueError, TypeError):
        return False, "Precio total de compra inválido", None
    if precio_total is not None:
        if precio_total <= 0:
            return False, "Precio total de compra debe ser mayor a 0", None
        precio_compra = round(precio_total / cantidad_por_caja, 2)
    else:
        precio_compra_total_calc = round(precio_compra * cantidad_por_caja, 2)
        precio_total = precio_compra_total_calc
    # Compat: precio_venta 0 permitido a nivel servicio (la UI rápida lo exige)

    from utils.validators import validate_canal
    canal = data.get("canal") or {"VENTA": "TIENDITA", "CONSUMO_INTERNO": "ALMACEN"}.get(
        data.get("tipo_uso", ""), "ALMACEN")
    if not validate_canal(canal):
        return False, "Canal no válido. Use TIENDITA o ALMACEN", None
    producto = Producto(
        id_categoria_producto=id_categoria,
        canal=canal,
        codigo=codigo,
        nombre=nombre,
        stock_actual=0,
        stock_minimo=stock_minimo,
        precio=precio,
        precio_compra=precio_compra,
        precio_venta=precio_venta,
        tipo_empaque=tipo_empaque,
        cantidad_por_caja=cantidad_por_caja,
        precio_compra_total=round(precio_total, 2),
        id_tipo_uniforme=data.get("id_tipo_uniforme"),
    )
    id_producto = producto_repository.insertar(producto)
    # Stock inicial opcional: genera ENTRADA con costo y método (alimenta ganancias)
    try:
        stock_inicial = int(data.get("stock_inicial", 0) or 0)
    except (ValueError, TypeError):
        stock_inicial = 0
    if stock_inicial > 0:
        modo = data.get("modo_compra") or data.get("metodo_pago")
        ok_m, msg_m, _ = registrar_movimiento({
            "id_producto": id_producto,
            "tipo_movimiento": "ENTRADA",
            "cantidad": stock_inicial,
            "motivo": data.get("motivo_compra", "Stock inicial"),
            "metodo_pago": modo,
            "monto_total": round(precio_compra * stock_inicial, 2),
            "id_usuario": data.get("id_usuario", 1),
        })
        if not ok_m:
            logger.warning(f"Stock inicial no registrado: {msg_m}")

    # S1 escalable: crear variantes si se especifica talla + stock_almacen
    try:
        from repositories import producto_variante_repository, stock_almacen_repository, almacen_repository
        talla_codigo = data.get("talla") or data.get("talla_codigo")
        stock_inicial = int(data.get("stock_actual", 0) or data.get("stock_inicial", 0) or 0)
        if talla_codigo and talla_codigo != "UNICA":
            from repositories import talla_repository
            t = talla_repository.obtener_por_codigo(talla_codigo)
            if t:
                sku = f"{codigo}-{talla_codigo}"
                if not producto_variante_repository.existe_sku(sku):
                    from models.producto_variante import ProductoVariante
                    var = ProductoVariante(id_producto=id_producto, id_talla=t["id_talla"], sku=sku, stock_minimo=stock_minimo)
                    id_var = producto_variante_repository.insertar(var)
                    # stock para variante
                    alm = almacen_repository.obtener_por_nombre("Principal")
                    if alm:
                        stock_almacen_repository.upsert_stock(id_producto, id_var, alm["id_almacen"], None, stock_inicial)
                        # también mantener producto.stock_actual para compatibilidad 1 sede
                        if stock_inicial > 0:
                            producto_repository.actualizar_stock(id_producto, stock_inicial)
                else:
                    # variante ya existe, actualizar stock si se dio inicial
                    if stock_inicial > 0:
                        var = producto_variante_repository.obtener_por_sku(sku)
                        alm = almacen_repository.obtener_por_nombre("Principal")
                        if var and alm:
                            stock_almacen_repository.upsert_stock(id_producto, var["id_variante"], alm["id_almacen"], None, stock_inicial)
        else:
            # sin talla: stock_almacen para producto base
            alm = almacen_repository.obtener_por_nombre("Principal")
            if alm:
                stock_almacen_repository.upsert_stock(id_producto, None, alm["id_almacen"], None, stock_inicial)
                if stock_inicial > 0:
                    producto_repository.actualizar_stock(id_producto, stock_inicial)
    except Exception as e:
        logger.warning(f"Variante/stock escalable no creado: {e}")

    auditoria_service.registrar_insert(
        id_usuario=1,
        tabla="producto",
        id_registro=id_producto,
        valores_nuevos=f"codigo={codigo}, nombre={nombre}",
    )

    logger.info(f"Producto creado: {codigo} - {nombre}")
    return True, "Producto creado correctamente", id_producto


def editar_producto(id_producto: int, data: dict) -> tuple[bool, str]:
    producto = producto_repository.obtener_por_id(id_producto)
    if not producto:
        return False, "Producto no encontrado"

    codigo = data.get("codigo", producto["codigo"])
    if producto_repository.existe_codigo(codigo, exclude_id=id_producto):
        return False, "Ya existe otro producto con ese código"

    stock_minimo = data.get("stock_minimo", producto["stock_minimo"])
    try:
        stock_minimo = int(stock_minimo)
    except (ValueError, TypeError):
        stock_minimo = producto["stock_minimo"]

    precio = data.get("precio", producto["precio"])
    try:
        precio = float(precio)
    except (ValueError, TypeError):
        precio = producto["precio"]

    precio_compra = data.get("precio_compra", producto.get("precio_compra", precio))
    try:
        precio_compra = float(precio_compra)
    except (ValueError, TypeError):
        precio_compra = producto.get("precio_compra", precio)
    precio_venta = data.get("precio_venta", producto.get("precio_venta", precio))
    try:
        precio_venta = float(precio_venta)
    except (ValueError, TypeError):
        precio_venta = producto.get("precio_venta", precio)

    tipo_empaque = data.get("tipo_empaque", producto.get("tipo_empaque", "Unidad"))
    if tipo_empaque not in ("Unidad", "Caja x12", "Caja x100", "Personalizado"):
        return False, "Tipo de empaque no válido", None
    crudo_cant = data.get("cantidad_por_caja", producto.get("cantidad_por_caja", 1))
    if crudo_cant in (None, ""):
        crudo_cant = 1
    try:
        cantidad_por_caja = int(crudo_cant)
    except (ValueError, TypeError):
        return False, "Cantidad por caja inválida", None
    if tipo_empaque == "Unidad":
        cantidad_por_caja = 1
    if cantidad_por_caja <= 0:
        return False, "Cantidad por caja debe ser mayor a 0", None
    precio_total = data.get("precio_compra_total", None)
    if precio_total in (None, ""):
        # legacy/omitido: usar guardado si > 0, si no recalcular del unitario
        guardado = producto.get("precio_compra_total") or 0
        try:
            precio_total = float(guardado) if float(guardado) > 0 else None
        except (ValueError, TypeError):
            precio_total = None
    else:
        try:
            precio_total = float(precio_total)
        except (ValueError, TypeError):
            return False, "Precio total de compra inválido", None
    if precio_total is not None:
        if precio_total <= 0:
            return False, "Precio total de compra debe ser mayor a 0", None
        precio_compra = round(precio_total / cantidad_por_caja, 2)
    else:
        precio_total = round(precio_compra * cantidad_por_caja, 2)
    # Compat: precio_venta 0 permitido a nivel servicio (la UI rápida lo exige)

    from utils.validators import validate_canal
    canal = data.get("canal") or {"VENTA": "TIENDITA", "CONSUMO_INTERNO": "ALMACEN"}.get(
        data.get("tipo_uso", ""), producto.get("canal", "ALMACEN"))
    if not validate_canal(canal):
        return False, "Canal no válido. Use TIENDITA o ALMACEN"
    producto_obj = Producto(
        id_producto=id_producto,
        id_categoria_producto=data.get("id_categoria_producto", producto["id_categoria_producto"]),
        canal=canal,
        codigo=codigo,
        nombre=data.get("nombre", producto["nombre"]),
        stock_actual=producto["stock_actual"],
        stock_minimo=stock_minimo,
        precio=precio,
        precio_compra=precio_compra,
        precio_venta=precio_venta,
        tipo_empaque=tipo_empaque,
        cantidad_por_caja=cantidad_por_caja,
        precio_compra_total=round(precio_total, 2),
        id_tipo_uniforme=data.get("id_tipo_uniforme", producto.get("id_tipo_uniforme")),
        activo=producto["activo"],
    )
    producto_repository.actualizar(producto_obj)

    auditoria_service.registrar_update(
        id_usuario=auditoria_service.id_usuario_sesion(),
        tabla="producto",
        id_registro=id_producto,
        valores_anteriores=f"codigo={producto['codigo']}, nombre={producto['nombre']}, precio={producto['precio']}",
        valores_nuevos=f"codigo={codigo}, nombre={producto_obj.nombre}, precio={precio}",
    )

    return True, "Producto actualizado correctamente"


def registrar_movimiento(data: dict) -> tuple[bool, str, int | None]:
    id_producto = data.get("id_producto")
    tipo_movimiento = data.get("tipo_movimiento", "")
    cantidad = data.get("cantidad", 0)

    if not id_producto:
        return False, "El producto es obligatorio", None
    if tipo_movimiento not in ("ENTRADA", "SALIDA", "AJUSTE"):
        return False, "Tipo de movimiento no válido", None
    if cantidad <= 0:
        return False, "La cantidad debe ser mayor a 0", None

    producto = producto_repository.obtener_por_id(id_producto)
    if not producto:
        return False, "Producto no encontrado", None

    stock_anterior = producto["stock_actual"]

    if tipo_movimiento == "ENTRADA":
        stock_nuevo = stock_anterior + cantidad
    elif tipo_movimiento == "SALIDA":
        if cantidad > stock_anterior:
            return False, f"Stock insuficiente. Disponible: {stock_anterior}", None
        stock_nuevo = stock_anterior - cantidad
    else:
        stock_nuevo = cantidad

    producto_repository.actualizar_stock(id_producto, stock_nuevo)

    usuario = data.get("id_usuario", 1)
    metodo_pago = data.get("metodo_pago")
    if metodo_pago is not None:
        metodo_pago = str(metodo_pago).strip().upper()
        if metodo_pago not in ("YAPE", "EFECTIVO"):
            return False, "Método no válido. Use Yape o Efectivo", None
    try:
        monto_total = float(data.get("monto_total", 0) or 0)
    except (ValueError, TypeError):
        return False, "Monto total inválido", None
    if monto_total < 0:
        return False, "Monto total no puede ser negativo", None
    movimiento = MovimientoInventario(
        id_producto=id_producto,
        id_usuario=usuario,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        fecha_movimiento=get_now(),
        motivo=data.get("motivo", ""),
        metodo_pago=metodo_pago,
        monto_total=round(monto_total, 2),
    )
    id_movimiento = movimiento_inventario_repository.insertar(movimiento)

    auditoria_service.registrar_insert(
        id_usuario=usuario,
        tabla="movimiento_inventario",
        id_registro=id_movimiento,
        valores_nuevos=f"producto={id_producto}, tipo={tipo_movimiento}, cantidad={cantidad}",
    )

    logger.info(f"Movimiento registrado: {tipo_movimiento} x{cantidad} producto={id_producto}")
    return True, f"Movimiento registrado. Stock: {stock_nuevo}", id_movimiento


def registrar_compra(data: dict) -> tuple[bool, str, int | None]:
    """Compra a proveedor: ENTRADA con monto total y método (Yape/Efectivo).

    Requerido para Total Compras por método y ganancias del dashboard.
    """
    metodo = str(data.get("metodo_pago", "") or "").strip().upper()
    if metodo not in ("YAPE", "EFECTIVO"):
        return False, "Método de compra no válido. Use Yape o Efectivo", None
    try:
        monto = float(data.get("monto_total", 0) or 0)
    except (ValueError, TypeError):
        return False, "Monto total inválido", None
    if monto <= 0:
        return False, "Monto total debe ser mayor a 0", None
    return registrar_movimiento({
        "id_producto": data.get("id_producto"),
        "tipo_movimiento": "ENTRADA",
        "cantidad": data.get("cantidad", 0),
        "motivo": data.get("motivo", "Compra a proveedor"),
        "metodo_pago": metodo,
        "monto_total": round(monto, 2),
        "id_usuario": data.get("id_usuario", 1),
    })


def calcular_unitario_y_ganancia(precio_total: float, cantidad_por_caja: int, precio_venta: float) -> dict:
    """Cálculos de la ficha (misma fórmula que crear/editar producto)."""
    cant = max(int(cantidad_por_caja or 1), 1)
    unitario = round(float(precio_total or 0) / cant, 2)
    gan_u = round(float(precio_venta or 0) - unitario, 2)
    pct = round(gan_u / unitario * 100, 1) if unitario else 0
    return {"unitario": unitario, "ganancia_unitaria": gan_u, "ganancia_pct": pct}


def obtener_producto(id_producto: int) -> dict | None:
    return producto_repository.obtener_por_id(id_producto)


def listar_productos(activo: int | None = None) -> list[dict]:
    return producto_repository.obtener_todos(activo=activo)


def obtener_bajo_stock() -> list[dict]:
    return producto_repository.obtener_bajo_stock()


def listar_movimientos(limit: int = 100, offset: int = 0) -> list[dict]:
    return movimiento_inventario_repository.obtener_todos(limit=limit, offset=offset)


def listar_movimientos_por_producto(id_producto: int) -> list[dict]:
    return movimiento_inventario_repository.obtener_por_producto(id_producto)


def listar_movimientos_por_fecha(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    return movimiento_inventario_repository.obtener_por_fecha(fecha_inicio, fecha_fin)
