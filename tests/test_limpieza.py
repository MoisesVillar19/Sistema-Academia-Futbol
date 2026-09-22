"""Limpieza: sin código muerto, bus con log, logs resumidos, backup único."""
import logging


def test_sin_metodos_muertos_en_main():
    import main as main_mod
    assert not hasattr(main_mod.App, "_mostrar_inventario")
    assert not hasattr(main_mod.App, "_mostrar_ventas")
    assert hasattr(main_mod.App, "_mostrar_tiendita")
    assert hasattr(main_mod.App, "_mostrar_almacen")


def test_sin_helpers_muertos():
    import utils.ui_helpers as uh
    assert not hasattr(uh, "crear_header_vista")
    import utils.helpers as helpers
    assert not hasattr(helpers, "clean_dni")
    assert not hasattr(helpers, "clean_phone")
    assert not hasattr(helpers, "truncate_text")
    assert helpers.format_money(10) == "S/10.00"  # se conserva


def test_event_bus_loggea_handler_roto(caplog):
    from utils import event_bus
    from utils.logger import logger

    def _roto(*a, **k):
        raise RuntimeError("boom QA")

    event_bus.subscribe("qa_roto_limpieza", _roto)
    try:
        with caplog.at_level(logging.WARNING, logger=logger.name):
            event_bus.publish("qa_roto_limpieza")  # no debe lanzar
        assert any("qa_roto_limpieza" in r.message for r in caplog.records)
    finally:
        event_bus.unsubscribe("qa_roto_limpieza", _roto)


def test_csv_resume_filas_malas(caplog, tmp_path):
    from utils import csv_parser
    from utils.logger import logger
    p = tmp_path / "mal.csv"
    p.write_text("a,b\n1,2\n1,2,3\n4,5,6,7\n", encoding="utf-8-sig")
    with caplog.at_level(logging.WARNING, logger=logger.name):
        ok, _, filas = csv_parser.parse_csv(str(p))
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert ok and len(filas) == 1
    assert sum("columnas" in r.message or "fila" in r.message for r in warnings) <= 1


def test_importar_resume_errores(caplog):
    from services import importar_service
    from utils.logger import logger
    with caplog.at_level(logging.INFO, logger=logger.name):
        ok, _, res = importar_service.importar_estudiantes(
            [{"dni": "x"} for _ in range(3)], id_usuario=1)
    assert ok
    assert len(res["errores"]) == 3
    assert sum("fila" in r.message.lower() for r in caplog.records
               if r.levelno >= logging.ERROR) == 0
