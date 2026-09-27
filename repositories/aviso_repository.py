"""E3: avisos omitidos/pospuestos (legado archivable, no borrable)."""
from database.connection import get_connection, fetch_all
from utils.dates import get_now


def omitir(codigo: str, origen_tipo: str = "", origen_id: int = 0,
           motivo: str = "", id_usuario: int | None = None) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO aviso_omitido (codigo, origen_tipo, origen_id, motivo,
                                      id_usuario, fecha, activo)
           VALUES (?, ?, ?, ?, ?, ?, 1)
           ON CONFLICT(codigo, origen_tipo, origen_id)
           DO UPDATE SET motivo = excluded.motivo, fecha = excluded.fecha,
                         activo = 1, id_usuario = excluded.id_usuario""",
        (codigo, origen_tipo or "", origen_id or 0, motivo or "",
         id_usuario, get_now()),
    )
    conn.commit()


def reactivar(codigo: str, origen_tipo: str = "", origen_id: int = 0) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE aviso_omitido SET activo = 0
           WHERE codigo = ? AND origen_tipo = ? AND origen_id = ?""",
        (codigo, origen_tipo or "", origen_id or 0),
    )
    conn.commit()


def listar_omitidos() -> list[dict]:
    return fetch_all(
        """SELECT * FROM aviso_omitido WHERE activo = 1 ORDER BY fecha DESC""")


def esta_omitido(codigo: str, origen_tipo: str = "", origen_id: int = 0) -> bool:
    rows = fetch_all(
        """SELECT id_omitido FROM aviso_omitido
           WHERE activo = 1 AND codigo = ? AND origen_tipo = ? AND origen_id = ?""",
        (codigo, origen_tipo or "", origen_id or 0),
    )
    return bool(rows)
