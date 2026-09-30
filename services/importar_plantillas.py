"""Plantillas CSV por tipo de importación (descargables desde la UI).

Cada plantilla: encabezados exactos que el importador reconoce + fila de
ejemplo + descripción. Nuevos tipos agregan su entrada aquí sin tocar la vista.
"""

PLANTILLAS = {
    "Estudiantes": {
        "descripcion": "Un alumno por fila. DNI obligatorio (8 dígitos) o vacío "
                       "para DNI provisional (solo si lo activas en Revisión). "
                       "BECA (nombre exacto) crea matrícula + beca; INICIO "
                       "(AAAA-MM-DD) es el inicio de clases y referencia de "
                       "vencimientos (vacío = hoy).",
        "headers": ["DNI", "Nombres", "Apellidos", "Fecha_Nacimiento", "Sexo",
                    "Telefono", "Correo", "Tipo_Documento", "Direccion",
                    "DNI_Apoderado", "Nombres_Apoderado", "Apellidos_Apoderado",
                    "Parentesco", "BECA", "INICIO"],
        "ejemplo": ["12345678", "Juan", "Pérez", "2015-04-10", "M", "999888777",
                    "", "DNI", "", "", "", "", "", "", "2026-03-10"],
    },
    "Tienda": {
        "descripcion": "Un producto por fila. QUEDAN debe ser CANTIDAD−VENDIDO.",
        "headers": ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "COSTO X UNIDAD",
                    "COSTO VENTA", "YAPE", "EFECTIVO", "CANTIDAD VENDIDO",
                    "QUEDAN", "CATEGORIA", "FECHA"],
        "ejemplo": ["Gaseosa 500ml", "12", "21.00", "1.75", "3.30",
                    "13.20", "26.40", "12", "0", "Bebidas", "2026-05-01"],
    },
    "Productos": {
        "descripcion": "Catálogo sin movimientos. PRODUCTO obligatorio; "
                       "COSTO y PRECIO_VENTA números ≥ 0 (vacío = 0). "
                       "Sin CANTIDAD ni columnas de venta (eso es Tienda/Compras).",
        "headers": ["PRODUCTO", "CATEGORIA", "COSTO", "PRECIO_VENTA"],
        "ejemplo": ["Gaseosa 500ml", "Bebidas", "1.75", "3.00"],
    },
    "Compras": {
        "descripcion": "Una compra por fila. Crea el producto si no existe. "
                       "COSTO_TOTAL manda; si no, COSTO X UNIDAD × CANTIDAD. "
                       "METODO vacío = EFECTIVO. Sin columnas de venta (eso es Tienda).",
        "headers": ["PRODUCTO", "CANTIDAD", "COSTO TOTAL", "COSTO X UNIDAD",
                    "METODO", "FECHA", "CATEGORIA"],
        "ejemplo": ["Gaseosa 500ml", "12", "21.00", "", "EFECTIVO", "2026-05-01", "Bebidas"],
    },
    "Pagos": {
        "descripcion": "Un pago por fila. DNI+PERIODO (AAAA-MM) localizan la cuota; "
                       "MONTO la imputa (≤ saldo). METODO vacío = EFECTIVO; "
                       "YAPE/PLIN/TRANSFERENCIA quedan en avisos sin comprobante. "
                       "Sin columnas Nombres/Apellidos (eso es Estudiantes).",
        "headers": ["DNI", "PERIODO", "MONTO", "METODO", "FECHA"],
        "ejemplo": ["12345678", "2026-05", "50.00", "EFECTIVO", "2026-05-04"],
    },
    "Uniformes": {
        "descripcion": "1 fila = 1 pago = 1 venta. TIPO COM (competencia) o ENT "
                       "(entrenamiento). Adelanto y resto son 2 filas (cada una "
                       "en su mes). FECHA con solo mes → día 01. Sin stock: el "
                       "sistema crea producto y compra. Aranceles de campeonato "
                       "van por Ventas CAMPEONATO, no aquí.",
        "headers": ["DNI", "TIPO", "MONTO", "FECHA", "METODO"],
        "ejemplo": ["12345678", "COM", "30.00", "2026-05-15", "EFECTIVO"],
    },
}


def listar_plantillas() -> list[str]:
    return list(PLANTILLAS.keys())


def generar_csv(tipo: str, ruta: str) -> tuple[bool, str]:
    """Escribe la plantilla (headers + ejemplo). Retorna (ok, msg)."""
    import csv
    spec = PLANTILLAS.get(tipo)
    if not spec:
        return False, f"Sin plantilla para {tipo}"
    try:
        with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(spec["headers"])
            w.writerow(spec["ejemplo"])
        return True, f"Plantilla {tipo} guardada en {ruta}"
    except OSError as e:
        return False, f"No se pudo guardar: {e}"
