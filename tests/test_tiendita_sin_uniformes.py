"""B5: Tiendita oculta uniformes COM/ENT (viven en Uniformes)."""
import pytest

pytestmark = pytest.mark.ui


def _prod(codigo, canal="TIENDITA"):
    from services import inventario_service
    from repositories import producto_repository
    previo = producto_repository.obtener_por_codigo(codigo)
    if previo:
        return previo["id_producto"]
    cats = inventario_service.listar_categorias()
    ok, _, pid = inventario_service.crear_producto({
        "id_categoria_producto": cats[0]["id_categoria_producto"],
        "nombre": codigo, "codigo": codigo, "canal": canal,
        "precio_venta": 10.0, "stock_inicial": 1})
    assert ok
    return pid


def test_buscar_paginado_excluye_codigos():
    from repositories import producto_repository
    _prod("UNIFORME-COM")
    _prod("TIENDA-X")
    rows, total = producto_repository.buscar_paginado(
        q="", excluir_codigos=("UNIFORME-COM", "CAMISETA-ENT"))
    codigos = {r["codigo"] for r in rows}
    assert "UNIFORME-COM" not in codigos
    assert "TIENDA-X" in codigos
    assert total == len(rows)


def test_tiendita_oculta_uniformes(crear_vista, usuario_admin):
    from views.tiendita.tiendita_view import TienditaView
    _prod("UNIFORME-COM")
    _prod("CAMISETA-ENT")
    _prod("TIENDA-Y")
    vista = crear_vista(TienditaView)
    vista.update_idletasks()

    def _textos(w):
        out = []
        try:
            t = w.cget("text")
            if t:
                out.append(str(t))
        except Exception:
            pass
        for ch in w.winfo_children():
            out += _textos(ch)
        return out

    todo = " ".join(_textos(vista.scroll_productos))
    assert "UNIFORME-COM" not in todo
    assert "CAMISETA-ENT" not in todo
    assert "TIENDA-Y" in todo


def test_almacen_no_excluye(crear_vista, usuario_admin):
    from views.almacen.almacen_view import AlmacenView
    vista = crear_vista(AlmacenView)
    vista.update_idletasks()
    assert getattr(vista, "_excluir_codigos", ()) == ()
