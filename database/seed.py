from database.connection import get_connection, fetch_one
from utils.constants import (
    CATEGORIA_INICIAL,
    CATEGORIA_PRODUCTO_INICIAL,
    DEFAULT_ADMIN_USER,
    DEFAULT_ADMIN_PASS,
    PIN_EMERGENCIA_DEFECTO,
)
from utils.security import hash_password
from utils.dates import get_now
import sqlite3


def _fila(conn, sql, params):
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([d[0] for d in cur.description], row))


def _asegurar(conn, sql_check, params_check, sql_insert, params_insert):
    """Check-then-insert ATÓMICO ante arranques simultáneos (red LAN).

    Si otra PC inserta entre el SELECT y el INSERT, el UNIQUE choca:
    se ignora y se re-lee (la otra PC ganó). Retorna la fila o None.
    Usa la conexión pasada (no la global) para ser testeable por hilos.
    """
    row = _fila(conn, sql_check, params_check)
    if row:
        return row
    try:
        conn.execute(sql_insert, params_insert)
    except sqlite3.IntegrityError:
        pass  # carrera: otra PC insertó primero
    return _fila(conn, sql_check, params_check)


def seed_database() -> None:
    conn = get_connection()
    now = get_now()

    admin_user = fetch_one(
        "SELECT id_usuario FROM usuario WHERE username = ?",
        (DEFAULT_ADMIN_USER,),
    )
    if not admin_user:
        _asegurar(
            conn,
            "SELECT id_persona FROM persona WHERE dni = ?",
            ("00000000",),
            """INSERT INTO persona (dni, nombres, apellidos, fecha_creacion)
               VALUES (?, ?, ?, ?)""",
            ("00000000", "Admin", "Sistema", now),
        )
        persona = fetch_one(
            "SELECT id_persona FROM persona WHERE dni = ?",
            ("00000000",),
        )
        if persona:
            _asegurar(
                conn,
                "SELECT id_usuario FROM usuario WHERE username = ?",
                (DEFAULT_ADMIN_USER,),
                """INSERT INTO usuario (id_persona, username, password_hash, rol, fecha_creacion)
                   VALUES (?, ?, ?, ?, ?)""",
                (persona["id_persona"], DEFAULT_ADMIN_USER,
                 hash_password(DEFAULT_ADMIN_PASS), "ADMIN", now),
            )

    for nombre, edad_min, edad_max in CATEGORIA_INICIAL:
        _asegurar(
            conn,
            "SELECT id_categoria FROM categoria WHERE nombre = ?",
            (nombre,),
            "INSERT INTO categoria (nombre, edad_min, edad_max) VALUES (?, ?, ?)",
            (nombre, edad_min, edad_max),
        )

    for nombre in CATEGORIA_PRODUCTO_INICIAL:
        _asegurar(
            conn,
            "SELECT id_categoria_producto FROM categoria_producto WHERE nombre = ?",
            (nombre,),
            "INSERT INTO categoria_producto (nombre) VALUES (?)",
            (nombre,),
        )

    config = _fila(conn, "SELECT id_configuracion, pin_emergencia FROM configuracion WHERE id_configuracion = 1", ())
    if not config:
        try:
            conn.execute(
                """INSERT INTO configuracion
                   (id_configuracion, nombre_academia, dias_por_vencer, permitir_multiples_becas,
                    backup_automatico, frecuencia_backup, ruta_backup, pin_emergencia,
                    precio_inscripcion, precio_mensualidad, precio_uniforme, precio_reingreso, fecha_actualizacion)
                   VALUES (1, 'Academia Deportiva', 3, 1, 1, 7, 'backups/', ?, 100, 100, 20, 100, ?)""",
                (hash_password(PIN_EMERGENCIA_DEFECTO), now),
            )
        except sqlite3.IntegrityError:
            config = _fila(conn, "SELECT id_configuracion, pin_emergencia FROM configuracion WHERE id_configuracion = 1", ())
            if not config:
                raise
    if config and not config.get("pin_emergencia"):
        conn.execute(
            "UPDATE configuracion SET pin_emergencia = ? WHERE id_configuracion = 1",
            (hash_password(PIN_EMERGENCIA_DEFECTO),),
        )

    # Tipos de uniforme (flexibles, RN-039)
    for nombre, desc in [
        ("Uniforme Entrenamiento", "Camiseta de entrenamiento incluida en inscripción"),
        ("Uniforme Competencia", "Uniforme para competencias"),
        ("Uniforme Completo", "Paquete completo - S/30"),
        ("Uniforme Media", "Media uniforme - S/20"),
    ]:
        _asegurar(
            conn,
            "SELECT id_tipo_uniforme FROM tipo_uniforme WHERE nombre = ?", (nombre,),
            "INSERT INTO tipo_uniforme (nombre, descripcion) VALUES (?, ?)", (nombre, desc),
        )

    # Tallas escalables (S1)
    for codigo, desc in [("S","Small"),("M","Medium"),("L","Large"),("XL","Extra Large"),("UNICA","Talla única")]:
        _asegurar(
            conn,
            "SELECT id_talla FROM talla WHERE codigo = ?", (codigo,),
            "INSERT INTO talla (codigo, descripcion) VALUES (?, ?)", (codigo, desc),
        )

    # Almacén y Caja principal (S2, si solo 1 no se muestra)
    alm = _asegurar(
        conn,
        "SELECT id_almacen FROM almacen WHERE nombre = 'Principal'", (),
        "INSERT INTO almacen (nombre, direccion) VALUES ('Principal', 'Sede principal')", (),
    )
    if alm:
        _asegurar(
            conn,
            "SELECT id_caja FROM caja WHERE id_almacen = ? AND nombre = 'Caja 1'",
            (alm["id_almacen"],),
            "INSERT INTO caja (id_almacen, nombre, responsable) VALUES (?, 'Caja 1', 'Admin')",
            (alm["id_almacen"],),
        )

    # Producto inicial: Camiseta Entrenamiento (RN-036) + stock escalable (incluso si producto ya existe)
    cat_dep = fetch_one("SELECT id_categoria_producto FROM categoria_producto WHERE nombre = 'INSUMO_DEPORTIVO'")
    if cat_dep:
        tipo_ent = fetch_one("SELECT id_tipo_uniforme FROM tipo_uniforme WHERE nombre = 'Uniforme Entrenamiento'")
        id_tipo_ent = tipo_ent["id_tipo_uniforme"] if tipo_ent else None
        prod = _asegurar(
            conn,
            "SELECT id_producto FROM producto WHERE codigo = 'CAMISETA-ENT'", (),
            """INSERT INTO producto (id_categoria_producto, tipo_uso, codigo, nombre, stock_actual, stock_minimo, precio, precio_compra, precio_venta, id_tipo_uniforme)
               VALUES (?, 'VENTA', 'CAMISETA-ENT', 'Camiseta Entrenamiento', 50, 5, 20, 8, 20, ?)""",
            (cat_dep["id_categoria_producto"], id_tipo_ent),
        ) if id_tipo_ent else fetch_one("SELECT id_producto FROM producto WHERE codigo = 'CAMISETA-ENT'")
        id_prod = prod["id_producto"] if prod else None
        # asegurar variantes y stock_almacen para producto existente (migración)
        if id_prod:
            alm = fetch_one("SELECT id_almacen FROM almacen WHERE nombre='Principal'")
            if alm:
                _asegurar(
                    conn,
                    "SELECT id_stock FROM stock_almacen WHERE id_producto=? AND id_almacen=? AND id_variante IS NULL",
                    (id_prod, alm["id_almacen"]),
                    "INSERT INTO stock_almacen (id_producto, id_almacen, stock) VALUES (?, ?, ?)",
                    (id_prod, alm["id_almacen"], (fetch_one("SELECT stock_actual FROM producto WHERE id_producto=?", (id_prod,)) or {}).get("stock_actual", 50) or 50),
                )
            for talla_code in ["S","M","L"]:
                t = fetch_one("SELECT id_talla FROM talla WHERE codigo=?", (talla_code,))
                if t:
                    sku = f"CAMISETA-ENT-{talla_code}"
                    var = _asegurar(
                        conn,
                        "SELECT id_variante FROM producto_variante WHERE sku=?", (sku,),
                        "INSERT INTO producto_variante (id_producto, id_talla, sku, stock_minimo) VALUES (?, ?, ?, 5)",
                        (id_prod, t["id_talla"], sku),
                    )
                    if alm and var:
                        _asegurar(
                            conn,
                            "SELECT id_stock FROM stock_almacen WHERE id_variante=?", (var["id_variante"],),
                            "INSERT INTO stock_almacen (id_producto, id_variante, id_almacen, stock) VALUES (?, ?, ?, 10)",
                            (id_prod, var["id_variante"], alm["id_almacen"]),
                        )

    # v2.2: tarifas desde Precios Flexibles (BD nuevas; en existentes lo hace la migración)
    try:
        from database.create_db import seed_tarifas_desde_config
        seed_tarifas_desde_config(conn.cursor())
    except Exception:
        pass

    conn.commit()


if __name__ == "__main__":
    seed_database()
    print("Datos iniciales insertados correctamente.")
