from repositories import cuota_repository, pago_repository, estudiante_repository
from repositories import matricula_repository, beca_repository, producto_repository
from repositories import matricula_beca_repository
from utils.dates import get_today
from utils.excel_exporter import exportar_a_excel
import os


def reporte_morosos(ruta_archivo: str) -> tuple[bool, str]:
    cuotas = cuota_repository.obtener_vencidas()

    morosos = {}
    for c in cuotas:
        dni = c.get("dni", "")
        if dni not in morosos:
            morosos[dni] = {
                "dni": dni,
                "nombres": c.get("nombres", ""),
                "apellidos": c.get("apellidos", ""),
                "total_deuda": 0,
                "cuotas_vencidas": 0,
                "periodos": [],
            }
        morosos[dni]["total_deuda"] += c.get("saldo", 0)
        morosos[dni]["cuotas_vencidas"] += 1
        morosos[dni]["periodos"].append(c.get("periodo", ""))

    datos = []
    for m in morosos.values():
        datos.append({
            "dni": m["dni"],
            "estudiante": f"{m['nombres']} {m['apellidos']}",
            "cuotas_vencidas": m["cuotas_vencidas"],
            "total_deuda": round(m["total_deuda"], 2),
            "periodos": ", ".join(m["periodos"]),
        })

    columnas = [
        ("dni", "DNI"),
        ("estudiante", "Estudiante"),
        ("cuotas_vencidas", "Cuotas Vencidas"),
        ("total_deuda", "Total Deuda (S/)"),
        ("periodos", "Periodos"),
    ]

    return exportar_a_excel(datos, columnas, "Reporte de Morosos", ruta_archivo)


def reporte_pagos_por_fecha(fecha_inicio: str, fecha_fin: str,
                            ruta_archivo: str) -> tuple[bool, str]:
    pagos = pago_repository.obtener_por_fecha(fecha_inicio, fecha_fin)

    datos = []
    for p in pagos:
        datos.append({
            "numero_recibo": p.get("numero_recibo", ""),
            "fecha_pago": p.get("fecha_pago", ""),
            "monto_total": round(p.get("monto_total", 0), 2),
            "metodo_pago": p.get("metodo_pago", ""),
            "usuario": p.get("username", ""),
        })

    columnas = [
        ("numero_recibo", "N° Recibo"),
        ("fecha_pago", "Fecha de Pago"),
        ("monto_total", "Monto (S/)"),
        ("metodo_pago", "Método de Pago"),
        ("usuario", "Registrado por"),
    ]

    titulo = f"Pagos del {fecha_inicio} al {fecha_fin}"
    return exportar_a_excel(datos, columnas, titulo, ruta_archivo)


def reporte_ingresos_mensuales(ruta_archivo: str) -> tuple[bool, str]:
    today = get_today()
    fecha_inicio = today[:7] + "-01"

    from datetime import datetime, timedelta
    fecha = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    if fecha.month == 12:
        siguiente = fecha.replace(year=fecha.year + 1, month=1, day=1)
    else:
        siguiente = fecha.replace(month=fecha.month + 1, day=1)
    ultimo_dia = (siguiente - timedelta(days=1)).day
    fecha_fin = f"{today[:7]}-{ultimo_dia:02d}"

    pagos = pago_repository.obtener_por_fecha(fecha_inicio, fecha_fin)

    resumen_por_dia = {}
    for p in pagos:
        dia = p.get("fecha_pago", "")[:10]
        if dia not in resumen_por_dia:
            resumen_por_dia[dia] = {"fecha": dia, "cantidad": 0, "total": 0}
        resumen_por_dia[dia]["cantidad"] += 1
        resumen_por_dia[dia]["total"] += p.get("monto_total", 0)

    datos = []
    for dia_data in sorted(resumen_por_dia.values(), key=lambda x: x["fecha"]):
        datos.append({
            "fecha": dia_data["fecha"],
            "cantidad_pagos": dia_data["cantidad"],
            "total_ingresos": round(dia_data["total"], 2),
        })

    total_general = sum(d["total_ingresos"] for d in datos)
    total_pagos = sum(d["cantidad_pagos"] for d in datos)
    datos.append({
        "fecha": "TOTAL",
        "cantidad_pagos": total_pagos,
        "total_ingresos": round(total_general, 2),
    })

    columnas = [
        ("fecha", "Fecha"),
        ("cantidad_pagos", "Cantidad de Pagos"),
        ("total_ingresos", "Total Ingresos (S/)"),
    ]

    titulo = f"Ingresos Mensuales - {today[:7]}"
    return exportar_a_excel(datos, columnas, titulo, ruta_archivo)


def reporte_alumnos_por_categoria(ruta_archivo: str) -> tuple[bool, str]:
    matriculas = matricula_repository.obtener_activas()

    por_categoria = {}
    for m in matriculas:
        cat = m.get("categoria_nombre", "Sin categoría")
        if cat not in por_categoria:
            por_categoria[cat] = {"categoria": cat, "cantidad": 0, "estudiantes": []}
        por_categoria[cat]["cantidad"] += 1
        nombre = f"{m.get('nombres', '')} {m.get('apellidos', '')}"
        por_categoria[cat]["estudiantes"].append(nombre)

    datos = []
    for cat_data in por_categoria.values():
        datos.append({
            "categoria": cat_data["categoria"],
            "cantidad_alumnos": cat_data["cantidad"],
            "estudiantes": ", ".join(cat_data["estudiantes"][:5]) + (
                "..." if len(cat_data["estudiantes"]) > 5 else ""
            ),
        })

    total = sum(d["cantidad_alumnos"] for d in datos)
    datos.append({
        "categoria": "TOTAL",
        "cantidad_alumnos": total,
        "estudiantes": "",
    })

    columnas = [
        ("categoria", "Categoría"),
        ("cantidad_alumnos", "Cantidad de Alumnos"),
        ("estudiantes", "Estudiantes (muestra)"),
    ]

    return exportar_a_excel(datos, columnas, "Alumnos por Categoría", ruta_archivo)


def reporte_inventario(ruta_archivo: str, filtro: str = "todos", id_almacen: int | None = None) -> tuple[bool, str]:
    """Reporte valorizado (stock * precio_venta) con filtro opcional."""
    productos = producto_repository.obtener_todos(activo=1)
    # si filtro por almacén, usar stock_almacen
    stock_por_producto = {}
    if id_almacen is not None:
        try:
            from repositories import stock_almacen_repository
            for sa in stock_almacen_repository.obtener_bajo_stock_por_almacen(id_almacen):
                # no usado aquí, solo para valorizado se recalcula abajo
                pass
        except Exception:
            pass

    datos = []
    total_valorizado = 0
    for p in productos:
        stock = p.get("stock_actual", 0)
        # filtro bajo
        if filtro == "bajo" and not (stock <= p.get("stock_minimo", 0) and stock >=0):
            continue
        # filtro uniformes
        if filtro == "uniformes" and not p.get("id_tipo_uniforme"):
            continue
        estado = "OK"
        if stock <= 0:
            estado = "SIN STOCK"
        elif stock <= p.get("stock_minimo", 0):
            estado = "STOCK BAJO"

        precio_compra = p.get("precio_compra", p.get("precio", 0))
        precio_venta = p.get("precio_venta", p.get("precio", 0))
        valorizado = round(stock * (precio_venta or 0), 2)
        total_valorizado += valorizado
        ganancia = round((precio_venta or 0) - (precio_compra or 0), 2)

        # talla si tiene variantes
        talla_txt = ""
        try:
            from repositories import producto_variante_repository
            vars = producto_variante_repository.obtener_por_producto(p["id_producto"])
            if vars:
                talla_txt = ", ".join([v.get("talla_codigo","") for v in vars if v.get("talla_codigo")])
        except Exception:
            pass

        datos.append({
            "codigo": p.get("codigo", ""),
            "nombre": p.get("nombre", ""),
            "categoria": p.get("categoria_nombre", ""),
            "canal": p.get("canal", ""),
            "talla": talla_txt,
            "stock_actual": stock,
            "stock_minimo": p.get("stock_minimo", 0),
            "precio_compra": round(precio_compra or 0, 2),
            "precio_venta": round(precio_venta or 0, 2),
            "ganancia": ganancia,
            "valorizado": valorizado,
            "estado": estado,
        })

    # fila total
    if datos:
        datos.append({
            "codigo": "TOTAL",
            "nombre": "",
            "categoria": "",
            "canal": "",
            "talla": "",
            "stock_actual": sum(d["stock_actual"] for d in datos),
            "stock_minimo": "",
            "precio_compra": "",
            "precio_venta": "",
            "ganancia": "",
            "valorizado": round(total_valorizado, 2),
            "estado": "",
        })

    columnas = [
        ("codigo", "Código"),
        ("nombre", "Nombre"),
        ("categoria", "Categoría"),
        ("canal", "Canal"),
        ("talla", "Talla(s)"),
        ("stock_actual", "Stock Actual"),
        ("stock_minimo", "Stock Mínimo"),
        ("precio_compra", "Compra (S/)"),
        ("precio_venta", "Venta (S/)"),
        ("ganancia", "Ganancia (S/)"),
        ("valorizado", "Valorizado (S/)"),
        ("estado", "Estado"),
    ]

    return exportar_a_excel(datos, columnas, "Reporte de Inventario Valorizado", ruta_archivo)


def reporte_becas_activas(ruta_archivo: str) -> tuple[bool, str]:
    becas = beca_repository.obtener_todas(activo=1)

    datos = []
    for b in becas:
        datos.append({
            "nombre": b.get("nombre", ""),
            "tipo": b.get("tipo", ""),
            "valor": round(b.get("valor", 0), 2),
            "descripcion": b.get("descripcion", ""),
        })

    columnas = [
        ("nombre", "Nombre de Beca"),
        ("tipo", "Tipo"),
        ("valor", "Valor"),
        ("descripcion", "Descripción"),
    ]

    return exportar_a_excel(datos, columnas, "Becas Activas", ruta_archivo)


def contar_nuevos(fecha_inicio: str, fecha_fin: str) -> int:
    from database.connection import fetch_all
    rows = fetch_all("SELECT id_estudiante FROM estudiante WHERE fecha_ingreso BETWEEN ? AND ? AND activo=1", (fecha_inicio, fecha_fin))
    return len(rows)


def contar_matriculas_periodo(fecha_inicio: str, fecha_fin: str) -> int:
    from database.connection import fetch_all
    rows = fetch_all("SELECT id_matricula FROM matricula WHERE fecha_inicio BETWEEN ? AND ? AND activo=1", (fecha_inicio, fecha_fin))
    return len(rows)


def reporte_regalos_matricula(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    from database.connection import fetch_all
    # regalos: venta INSCRIPCION monto 0 con detalle camiseta
    rows = fetch_all("""
        SELECT v.fecha_venta as fecha, p.nombre as producto, dv.cantidad, per.nombres || ' ' || per.apellidos as estudiante
        FROM venta v
        JOIN detalle_venta dv ON dv.id_venta=v.id_venta
        JOIN producto p ON p.id_producto=dv.id_producto
        LEFT JOIN estudiante e ON e.id_estudiante=v.id_estudiante
        LEFT JOIN persona per ON per.id_persona=e.id_persona
        WHERE v.tipo_venta='INSCRIPCION' AND v.monto_total=0 AND v.fecha_venta BETWEEN ? AND ?
        ORDER BY v.fecha_venta
    """, (fecha_inicio, fecha_fin))
    return rows


def listar_reportes() -> list[dict]:
    return [
        {"id": "morosos", "nombre": "Morosos", "descripcion": "Estudiantes con cuotas vencidas"},
        {"id": "pagos_fecha", "nombre": "Pagos por Fecha", "descripcion": "Historial de pagos en rango de fechas"},
        {"id": "ingresos_mensuales", "nombre": "Ingresos Mensuales", "descripcion": "Resumen de ingresos por mes"},
        {"id": "alumnos_categoria", "nombre": "Alumnos por Categoría", "descripcion": "Estudiantes activos por categoría"},
        {"id": "inventario", "nombre": "Inventario", "descripcion": "Estado actual del stock"},
        {"id": "becas_activas", "nombre": "Becas Activas", "descripcion": "Becas asignadas vigentes"},
        {"id": "ingresos_vs_egresos", "nombre": "Ingresos vs Egresos", "descripcion": "Ingresos (pagos+ventas) vs egresos y neto por periodo"},
        {"id": "stock_bajo_uniformes", "nombre": "Stock Bajo Uniformes", "descripcion": "Productos con stock ≤ mínimo, por tipo uniforme"},
        {"id": "nuevos_vs_antiguos", "nombre": "Nuevos vs Antiguos", "descripcion": "Alumnos nuevos vs reingresos/antiguos por periodo"},
        {"id": "regalos_matricula", "nombre": "Regalos por Matrícula", "descripcion": "Camisetas y productos entregados como regalo (monto 0) por periodo"},
    ]
