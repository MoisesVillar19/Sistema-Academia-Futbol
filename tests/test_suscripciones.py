"""Sin suscriptores fantasma: destruir la vista desuscribe y cancela."""
import pytest

pytestmark = pytest.mark.ui

from utils import event_bus as eb_mod


def _n_suscriptores(evento: str) -> int:
    return len(eb_mod._default_bus._handlers.get(evento, []))


def test_pago_no_acumula_suscriptores(crear_vista, usuario_admin, ctk_root):
    from views.pagos.pago_view import PagoView
    base = _n_suscriptores("pago_registrado")
    for _ in range(3):
        v = crear_vista(PagoView)
        ctk_root.update_idletasks()
        v.destroy()
        ctk_root.update_idletasks()
    assert _n_suscriptores("pago_registrado") == base
    v = crear_vista(PagoView)
    assert _n_suscriptores("pago_registrado") == base + 1
    eb_mod.publish("pago_registrado")  # la viva recarga, sin errores
    ctk_root.update_idletasks()
    v.destroy()


def test_matricula_inventario_desuscriben(crear_vista, usuario_admin, ctk_root):
    from views.matriculas.matricula_view import MatriculaView
    from views.inventario.inventario_view import InventarioView
    b_m, b_i = _n_suscriptores("matricula_creada"), _n_suscriptores("producto_actualizado")
    vm = crear_vista(MatriculaView)
    vi = crear_vista(InventarioView)
    assert _n_suscriptores("matricula_creada") == b_m + 1
    assert _n_suscriptores("producto_actualizado") == b_i + 1
    vm.destroy()
    vi.destroy()
    ctk_root.update_idletasks()
    assert _n_suscriptores("matricula_creada") == b_m
    assert _n_suscriptores("producto_actualizado") == b_i
    eb_mod.publish("matricula_creada")  # sin vistas vivas: no debe fallar
    eb_mod.publish("producto_actualizado")
    ctk_root.update_idletasks()


def test_error_log_acotado(tmp_path, monkeypatch):
    import os
    import utils.crashlog as cl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    ruta = cl.ruta_error_log()
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("X" * (300 * 1024))
    cl.instalar()
    assert os.path.getsize(cl.ruta_error_log()) <= 210 * 1024
    cl.registrar_fase("sigue escribiendo tras podar")
    with open(cl.ruta_error_log(), encoding="utf-8") as f:
        assert "sigue escribiendo tras podar" in f.read()
