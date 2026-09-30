import csv
import os
from utils.logger import logger


def _detectar_delimitador(ruta_archivo: str) -> str:
    """Excel en español guarda con ';'. Sniffer con fallback a coma."""
    try:
        with open(ruta_archivo, "r", encoding="utf-8-sig") as f:
            muestra = f.read(4096)
        if not muestra.strip():
            return ","
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=[",", ";", "\t", "|"])
            if dialecto.delimiter in (",", ";", "\t", "|"):
                return dialecto.delimiter
        except Exception:
            pass
        conteos = {d: muestra.count(d) for d in (",", ";", "\t", "|")}
        mejor = max(conteos, key=conteos.get)
        return mejor if conteos[mejor] > 0 else ","
    except Exception:
        return ","


def parse_csv(ruta_archivo: str) -> tuple[bool, str, list[dict]]:
    if not os.path.exists(ruta_archivo):
        return False, "El archivo no existe", []

    if not ruta_archivo.lower().endswith(".csv"):
        return False, "El archivo no es un CSV", []

    try:
        filas = []
        encabezados = None

        with open(ruta_archivo, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=_detectar_delimitador(ruta_archivo))
            filas_malas = []
            for idx, row in enumerate(reader):
                if not row or all(c.strip() == "" for c in row):
                    continue

                if encabezados is None:
                    encabezados = [c.strip() for c in row]
                    continue

                if len(row) != len(encabezados):
                    # Limpieza: contador + resumen (no 1 línea por fila)
                    filas_malas.append(idx + 1)
                    continue

                fila = {}
                for i, h in enumerate(encabezados):
                    fila[h] = row[i].strip()
                filas.append(fila)

        if not encabezados:
            return False, "El archivo está vacío o no tiene encabezados", []

        if not filas:
            return False, "El archivo no tiene datos", []

        logger.info(f"CSV parseado: {len(filas)} filas, {len(encabezados)} columnas")
        if filas_malas:
            logger.warning(f"CSV: {len(filas_malas)} fila(s) con columnas distintas "
                           f"(primeras: {filas_malas[:5]})")
        return True, f"{len(filas)} registros encontrados", filas

    except Exception as e:
        logger.error(f"Error al parsear CSV: {e}")
        return False, f"Error al leer el archivo: {str(e)}", []


def obtener_columnas_csv(ruta_archivo: str) -> tuple[bool, str, list[str]]:
    if not os.path.exists(ruta_archivo):
        return False, "El archivo no existe", []

    try:
        with open(ruta_archivo, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=_detectar_delimitador(ruta_archivo))
            for row in reader:
                if row and any(c.strip() != "" for c in row):
                    return True, "OK", [c.strip() for c in row]

        return False, "No se encontraron encabezados", []

    except Exception as e:
        logger.error(f"Error al leer encabezados CSV: {e}")
        return False, f"Error: {str(e)}", []
