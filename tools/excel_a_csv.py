"""Uso único: convierte el Excel Roncalli a CSVs fieles en importacion/.

Cada hoja -> un CSV con todas las filas/columnas tal cual (fechas en ISO).
Los CSVs son el insumo de carga del importador (Fase import-Excel).
"""
import csv
import datetime
import glob
import os

ORIGEN = glob.glob("D:/Hp/Desktop/AcademiaFutbol/*.xlsx")[0]
DESTINO = "importacion"


def celda(v):
    if v is None:
        return ""
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def main():
    import openpyxl
    os.makedirs(DESTINO, exist_ok=True)
    wb = openpyxl.load_workbook(ORIGEN, read_only=True, data_only=True)
    for ws in wb.worksheets:
        seguro = "".join(c if (c.isalnum() or c in ("_", "-")) else "_" for c in ws.title)
        ruta = os.path.join(DESTINO, seguro + ".csv")
        filas = [r for r in ws.iter_rows(values_only=True)
                 if any(v not in (None, "") for v in r)]
        with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            for r in filas:
                w.writerow([celda(v) for v in r])
        print(f"{ws.title} -> {ruta} ({len(filas)} filas)")


if __name__ == "__main__":
    main()
