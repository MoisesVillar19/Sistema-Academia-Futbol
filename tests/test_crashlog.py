"""Diagnóstico anti-muerte-muda: hooks, fases y diálogo fatal."""
import os


def test_ruta_error_log_escribible(tmp_path, monkeypatch):
    import utils.crashlog as cl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    ruta = cl.ruta_error_log()
    assert ruta.endswith("error_log.txt")
    assert os.path.isfile(ruta)


def test_instalar_hooks_idempotente(tmp_path, monkeypatch):
    import sys
    import utils.crashlog as cl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    r1 = cl.instalar()
    r2 = cl.instalar()
    assert r1 == r2
    assert callable(sys.excepthook)


def test_hook_excepcion_escribe_archivo(tmp_path, monkeypatch, capsys):
    import utils.crashlog as cl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cl.instalar()
    try:
        raise RuntimeError("falla sintetica QA")
    except RuntimeError:
        import sys
        sys.excepthook(*sys.exc_info())
    with open(cl.ruta_error_log(), encoding="utf-8") as f:
        contenido = f.read()
    assert "falla sintetica QA" in contenido


def test_registrar_fase(tmp_path, monkeypatch):
    import utils.crashlog as cl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cl.registrar_fase("fase_qa_unica")
    with open(cl.ruta_error_log(), encoding="utf-8") as f:
        assert "fase_qa_unica" in f.read()
