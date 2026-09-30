"""CSV con ';' (Excel ES) o tab: el parser debe detectarlo (balance fallaba)."""
TIENDA_ROW = ["Gaseosa 500ml", "12", "21.00", "1.75", "3.30",
              "13.20", "26.40", "12", "0", "Bebidas", "2026-05-01"]
TIENDA_HDR = ["PRODUCTOS", "CANTIDAD", "COSTO TOTAL", "COSTO X UNIDAD",
              "COSTO VENTA", "YAPE", "EFECTIVO", "CANTIDAD VENDIDO",
              "QUEDAN", "CATEGORIA", "FECHA"]


def _escribir(path, delim):
    import csv
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=delim)
        w.writerow(TIENDA_HDR)
        w.writerow(TIENDA_ROW)


def test_parse_punto_y_coma(tmp_path):
    from utils.csv_parser import parse_csv, obtener_columnas_csv
    p = str(tmp_path / "t.csv")
    _escribir(p, ";")
    ok, _, cols = obtener_columnas_csv(p)
    assert ok and cols == TIENDA_HDR, cols
    ok, msg, filas = parse_csv(p)
    assert ok, msg
    assert filas[0]["PRODUCTOS"] == "Gaseosa 500ml"
    assert filas[0]["CANTIDAD"] == "12"


def test_parse_tab(tmp_path):
    from utils.csv_parser import parse_csv
    p = str(tmp_path / "t.csv")
    _escribir(p, "\t")
    ok, msg, filas = parse_csv(p)
    assert ok, msg
    assert filas[0]["PRODUCTOS"] == "Gaseosa 500ml"


def test_balance_puntoycoma_valida_tienda(tmp_path):
    from controllers import importar_controller
    p = str(tmp_path / "tienda_MAYO.csv")
    _escribir(p, ";")
    tipo, _ = importar_controller.detectar_tipo(p)
    assert tipo == "Tienda", tipo
    ok, _, filas = importar_controller.cargar_archivo(p)
    assert ok
    ok, _, errores = importar_controller.validar_datos(filas, None, "Tienda")
    assert ok, errores
