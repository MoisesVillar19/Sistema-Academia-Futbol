"""Plantillas CSV por tipo de importación (descargables desde la UI).

Cada plantilla: encabezados exactos que el importador reconoce + fila de
ejemplo + descripción. Futuros tipos (Pagos, Productos, Compras) agregan su
entrada aquí sin tocar la vista.
"""

PLANTILLAS = {
    "Estudiantes": {
        "descripcion": "Un alumno por fila. DNI obligatorio (8 dígitos) o vacío "
                       "para DNI provisional (solo si lo activas en Revisión).",
        "headers": ["DNI", "Nombres", "Apellidos", "Fecha_Nacimiento", "Sexo",
                    "Telefono", "Correo", "Tipo_Documento", "Direccion",
                    "DNI_Apoderado", "Nombres_Apoderado", "Apellidos_Apoderado",
                    "Parentesco"],
        "ejemplo": ["12345678", "Juan", "Pérez", "2015-04-10", "M", "999888777",
                    "", "DNI", "", "", "", "", ""],
    },
    "Tienda": {
        "descripcion": "Un producto por fila. QUEDAN debe ser CANTIDAD−VENDIDO.",
        "headers": ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "COSTO X UNIDAD",
                    "COSTO VENTA", "YAPE", "EFECTIVO", "CANTIDAD VENDIDO",
                    "QUEDAN", "CATEGORIA", "FECHA"],
        "ejemplo": ["Gaseosa 500ml", "12", "21.00", "1.75", "3.30",
                    "13.20", "26.40", "12", "0", "Bebidas", "2026-05-01"],
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
