from database.connection import get_connection


TABLES_SQL = """
CREATE TABLE IF NOT EXISTS persona (
    id_persona INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT UNIQUE NOT NULL,
    tipo_documento TEXT DEFAULT 'DNI',
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    fecha_nacimiento TEXT,
    sexo TEXT,
    direccion TEXT,
    telefono TEXT,
    correo TEXT,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_persona INTEGER UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('ADMIN', 'SECRETARIA')),
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT,
    FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
);

CREATE TABLE IF NOT EXISTS apoderado (
    id_apoderado INTEGER PRIMARY KEY AUTOINCREMENT,
    id_persona INTEGER UNIQUE NOT NULL,
    tipo_documento TEXT DEFAULT 'DNI',
    parentesco TEXT,
    ocupacion TEXT,
    telefono TEXT,
    direccion TEXT,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT,
    FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
);

CREATE TABLE IF NOT EXISTS estudiante (
    id_estudiante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_persona INTEGER UNIQUE NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK(estado IN ('ACTIVO', 'RETIRADO', 'REINGRESANTE')),
    fecha_ingreso TEXT NOT NULL,
    fecha_retiro TEXT,
    es_nuevo INTEGER DEFAULT 0 CHECK(es_nuevo IN (0,1)),
    foto_path TEXT,
    comprobante_pago_path TEXT,
    fecha_matricula TEXT,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
);

CREATE TABLE IF NOT EXISTS estudiante_apoderado (
    id_estudiante_apoderado INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER NOT NULL,
    id_apoderado INTEGER NOT NULL,
    es_principal INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_apoderado) REFERENCES apoderado(id_apoderado)
);

CREATE TABLE IF NOT EXISTS categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    edad_min INTEGER,
    edad_max INTEGER,
    tipo TEXT DEFAULT 'ACADEMIA',
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rol_permiso (
    rol TEXT NOT NULL,
    modulo TEXT NOT NULL,
    PRIMARY KEY (rol, modulo)
);

CREATE TABLE IF NOT EXISTS tarifa (
    id_tarifa INTEGER PRIMARY KEY AUTOINCREMENT,
    id_categoria INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    monto REAL NOT NULL,
    descripcion TEXT,
    observaciones TEXT,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
);

CREATE TABLE IF NOT EXISTS beca (
    id_beca INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('PORCENTAJE', 'MONTO_FIJO')),
    valor REAL NOT NULL,
    observacion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS matricula (
    id_matricula INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER NOT NULL,
    id_tarifa INTEGER NOT NULL,
    monto_pactado REAL,
    pago_matricula TEXT DEFAULT 'AHORA',
    monto_matricula REAL DEFAULT 0,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    dia_vencimiento INTEGER NOT NULL DEFAULT 1 CHECK(dia_vencimiento BETWEEN 1 AND 31),
    estado TEXT NOT NULL DEFAULT 'ACTIVO',
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_tarifa) REFERENCES tarifa(id_tarifa)
);

CREATE TABLE IF NOT EXISTS matricula_beca (
    id_matricula_beca INTEGER PRIMARY KEY AUTOINCREMENT,
    id_matricula INTEGER NOT NULL,
    id_beca INTEGER NOT NULL,
    fecha_asignacion TEXT NOT NULL,
    activo INTEGER DEFAULT 1,
    observacion TEXT,
    FOREIGN KEY (id_matricula) REFERENCES matricula(id_matricula),
    FOREIGN KEY (id_beca) REFERENCES beca(id_beca)
);

CREATE TABLE IF NOT EXISTS cuota (
    id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
    id_matricula INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    monto_total REAL NOT NULL,
    monto_pagado REAL DEFAULT 0,
    monto_mora REAL DEFAULT 0,
    saldo REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'VENCIDO')),
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_matricula) REFERENCES matricula(id_matricula)
);

CREATE TABLE IF NOT EXISTS pago (
    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    numero_recibo TEXT UNIQUE NOT NULL,
    fecha_pago TEXT NOT NULL,
    monto_total REAL NOT NULL,
    metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('EFECTIVO', 'YAPE', 'PLIN', 'TRANSFERENCIA')),
    observacion TEXT,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS detalle_pago (
    id_detalle_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pago INTEGER NOT NULL,
    id_cuota INTEGER NOT NULL,
    monto_pagado REAL NOT NULL,
    FOREIGN KEY (id_pago) REFERENCES pago(id_pago),
    FOREIGN KEY (id_cuota) REFERENCES cuota(id_cuota)
);

CREATE TABLE IF NOT EXISTS categoria_producto (
    id_categoria_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS producto (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    id_categoria_producto INTEGER NOT NULL,
    tipo_uso TEXT NOT NULL CHECK(tipo_uso IN ('CONSUMO_INTERNO', 'VENTA')),
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 0,
    precio REAL DEFAULT 0,
    precio_compra REAL DEFAULT 0,
    precio_venta REAL DEFAULT 0,
    id_tipo_uniforme INTEGER REFERENCES tipo_uniforme(id_tipo_uniforme),
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_categoria_producto) REFERENCES categoria_producto(id_categoria_producto)
);

CREATE TABLE IF NOT EXISTS movimiento_inventario (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_nuevo INTEGER NOT NULL,
    fecha_movimiento TEXT NOT NULL,
    motivo TEXT,
    id_variante INTEGER REFERENCES producto_variante(id_variante),
    id_almacen INTEGER REFERENCES almacen(id_almacen),
    id_caja INTEGER REFERENCES caja(id_caja),
    id_lote INTEGER REFERENCES lote(id_lote),
    FOREIGN KEY (id_producto) REFERENCES producto(id_producto),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS tipo_uniforme (
    id_tipo_uniforme INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS talla (
    id_talla INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS almacen (
    id_almacen INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    direccion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS caja (
    id_caja INTEGER PRIMARY KEY AUTOINCREMENT,
    id_almacen INTEGER NOT NULL REFERENCES almacen(id_almacen),
    nombre TEXT NOT NULL,
    responsable TEXT,
    activo INTEGER DEFAULT 1,
    UNIQUE(id_almacen, nombre)
);

CREATE TABLE IF NOT EXISTS proveedor (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    telefono TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS producto_variante (
    id_variante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    id_talla INTEGER REFERENCES talla(id_talla),
    sku TEXT UNIQUE NOT NULL,
    codigo_barras TEXT,
    stock_minimo INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS stock_almacen (
    id_stock INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    id_variante INTEGER REFERENCES producto_variante(id_variante),
    id_almacen INTEGER NOT NULL REFERENCES almacen(id_almacen),
    id_caja INTEGER REFERENCES caja(id_caja),
    stock INTEGER DEFAULT 0,
    UNIQUE(id_producto, id_variante, id_almacen, id_caja)
);

CREATE TABLE IF NOT EXISTS lote (
    id_lote INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    id_variante INTEGER REFERENCES producto_variante(id_variante),
    id_almacen INTEGER NOT NULL REFERENCES almacen(id_almacen),
    codigo_lote TEXT,
    fecha_ingreso TEXT,
    fecha_caducidad TEXT,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor),
    cantidad INTEGER NOT NULL,
    stock_restante INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS venta (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER REFERENCES estudiante(id_estudiante),
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
    fecha_venta TEXT NOT NULL,
    monto_total REAL NOT NULL,
    metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('EFECTIVO', 'YAPE', 'PLIN', 'TRANSFERENCIA')),
    tipo_venta TEXT NOT NULL CHECK(tipo_venta IN ('UNIFORME', 'TIENDA', 'CAMPEONATO', 'INSCRIPCION')),
    numero_recibo TEXT UNIQUE NOT NULL,
    comprobante_path TEXT,
    id_almacen INTEGER REFERENCES almacen(id_almacen),
    id_caja INTEGER REFERENCES caja(id_caja),
    id_tarifa INTEGER REFERENCES tarifa(id_tarifa),
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id_detalle_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL REFERENCES venta(id_venta),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    id_variante INTEGER REFERENCES producto_variante(id_variante),
    id_lote INTEGER REFERENCES lote(id_lote)
);

CREATE TABLE IF NOT EXISTS egreso (
    id_egreso INTEGER PRIMARY KEY AUTOINCREMENT,
    concepto TEXT NOT NULL CHECK(concepto IN ('PROFESOR', 'PERSONAL', 'CAMPEONATO_FIJO', 'ARBITRAJE', 'VIATICOS')),
    monto REAL NOT NULL CHECK(monto > 0),
    fecha TEXT NOT NULL,
    responsable TEXT,
    id_usuario INTEGER REFERENCES usuario(id_usuario),
    observacion TEXT,
    comprobante_path TEXT,
    id_tarifa INTEGER REFERENCES tarifa(id_tarifa),
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS configuracion (
    id_configuracion INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_academia TEXT,
    direccion TEXT,
    telefono TEXT,
    correo TEXT,
    mora_habilitada INTEGER DEFAULT 0,
    tipo_mora TEXT DEFAULT 'PORCENTAJE',
    porcentaje_mora REAL DEFAULT 0,
    monto_mora REAL DEFAULT 0,
    dias_por_vencer INTEGER DEFAULT 3,
    permitir_multiples_becas INTEGER DEFAULT 1,
    backup_automatico INTEGER DEFAULT 1,
    frecuencia_backup INTEGER DEFAULT 7,
    ruta_backup TEXT DEFAULT 'backups/',
    correo_onedrive TEXT DEFAULT '',
    pin_emergencia TEXT DEFAULT '',
    precio_inscripcion REAL DEFAULT 100,
    precio_mensualidad REAL DEFAULT 100,
    precio_uniforme REAL DEFAULT 20,
    precio_reingreso REAL DEFAULT 100,
    tasa_campeonato REAL DEFAULT 15,
    arbitraje_por_equipo REAL DEFAULT 15,
    pago_profesor REAL DEFAULT 200,
    fecha_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS log (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    tabla_afectada TEXT NOT NULL,
    id_registro INTEGER NOT NULL,
    accion TEXT NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS concepto_cobro (
    id_concepto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('INSCRIPCION', 'MENSUALIDAD', 'REINGRESO', 'PROMOCION', 'CAMPEONATO', 'OTRO')),
    monto REAL NOT NULL CHECK(monto >= 0),
    descripcion TEXT,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS concepto_item (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_concepto INTEGER NOT NULL REFERENCES concepto_cobro(id_concepto),
    id_producto INTEGER NOT NULL REFERENCES producto(id_producto),
    cantidad INTEGER NOT NULL DEFAULT 1 CHECK(cantidad > 0),
    UNIQUE(id_concepto, id_producto)
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_persona_dni ON persona(dni);
CREATE INDEX IF NOT EXISTS idx_usuario_username ON usuario(username);
CREATE INDEX IF NOT EXISTS idx_cuota_estado ON cuota(estado);
CREATE INDEX IF NOT EXISTS idx_cuota_vencimiento ON cuota(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_pago_fecha ON pago(fecha_pago);
CREATE INDEX IF NOT EXISTS idx_producto_codigo ON producto(codigo);
CREATE INDEX IF NOT EXISTS idx_estudiante_apoderado_estudiante ON estudiante_apoderado(id_estudiante);
CREATE INDEX IF NOT EXISTS idx_matricula_beca_matricula ON matricula_beca(id_matricula);
CREATE INDEX IF NOT EXISTS idx_producto_categoria ON producto(id_categoria_producto);
CREATE INDEX IF NOT EXISTS idx_movimiento_producto ON movimiento_inventario(id_producto);
CREATE INDEX IF NOT EXISTS idx_venta_fecha ON venta(fecha_venta);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_venta ON detalle_venta(id_venta);
CREATE INDEX IF NOT EXISTS idx_egreso_fecha ON egreso(fecha);
CREATE INDEX IF NOT EXISTS idx_tipo_uniforme_nombre ON tipo_uniforme(nombre);
CREATE INDEX IF NOT EXISTS idx_talla_codigo ON talla(codigo);
CREATE INDEX IF NOT EXISTS idx_producto_variante_sku ON producto_variante(sku);
CREATE INDEX IF NOT EXISTS idx_stock_almacen_producto ON stock_almacen(id_producto);
CREATE INDEX IF NOT EXISTS idx_lote_caducidad ON lote(fecha_caducidad);
"""


def create_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript(TABLES_SQL)
    cursor.executescript(INDEXES_SQL)
    _migrar_columnas_faltantes(cursor)
    conn.commit()


def _migrar_columnas_faltantes(cursor) -> None:
    columnas_cuota = _obtener_columnas(cursor, "cuota")
    if "monto_mora" not in columnas_cuota:
        cursor.execute("ALTER TABLE cuota ADD COLUMN monto_mora REAL DEFAULT 0")

    columnas_config = _obtener_columnas(cursor, "configuracion")
    if "pin_emergencia" not in columnas_config:
        cursor.execute("ALTER TABLE configuracion ADD COLUMN pin_emergencia TEXT DEFAULT ''")
    for col, sql in [
        ("precio_inscripcion", "ALTER TABLE configuracion ADD COLUMN precio_inscripcion REAL DEFAULT 100"),
        ("precio_mensualidad", "ALTER TABLE configuracion ADD COLUMN precio_mensualidad REAL DEFAULT 100"),
        ("precio_uniforme", "ALTER TABLE configuracion ADD COLUMN precio_uniforme REAL DEFAULT 20"),
        ("precio_reingreso", "ALTER TABLE configuracion ADD COLUMN precio_reingreso REAL DEFAULT 100"),
        ("tasa_campeonato", "ALTER TABLE configuracion ADD COLUMN tasa_campeonato REAL DEFAULT 15"),
        ("arbitraje_por_equipo", "ALTER TABLE configuracion ADD COLUMN arbitraje_por_equipo REAL DEFAULT 15"),
        ("pago_profesor", "ALTER TABLE configuracion ADD COLUMN pago_profesor REAL DEFAULT 200"),
    ]:
        if col not in columnas_config:
            cursor.execute(sql)

    columnas_est = _obtener_columnas(cursor, "estudiante")
    for col, sql in [
        ("es_nuevo", "ALTER TABLE estudiante ADD COLUMN es_nuevo INTEGER DEFAULT 0 CHECK(es_nuevo IN (0,1))"),
        ("foto_path", "ALTER TABLE estudiante ADD COLUMN foto_path TEXT"),
        ("comprobante_pago_path", "ALTER TABLE estudiante ADD COLUMN comprobante_pago_path TEXT"),
        ("fecha_matricula", "ALTER TABLE estudiante ADD COLUMN fecha_matricula TEXT"),
    ]:
        if col not in columnas_est:
            cursor.execute(sql)

    columnas_prod = _obtener_columnas(cursor, "producto")
    for col, sql in [
        ("precio_compra", "ALTER TABLE producto ADD COLUMN precio_compra REAL DEFAULT 0"),
        ("precio_venta", "ALTER TABLE producto ADD COLUMN precio_venta REAL DEFAULT 0"),
        ("id_tipo_uniforme", "ALTER TABLE producto ADD COLUMN id_tipo_uniforme INTEGER REFERENCES tipo_uniforme(id_tipo_uniforme)"),
    ]:
        if col not in columnas_prod:
            cursor.execute(sql)

    columnas_egreso = _obtener_columnas(cursor, "egreso")
    if "activo" not in columnas_egreso:
        cursor.execute("ALTER TABLE egreso ADD COLUMN activo INTEGER DEFAULT 1")
    if "comprobante_path" not in columnas_egreso:
        cursor.execute("ALTER TABLE egreso ADD COLUMN comprobante_path TEXT")
    if "id_tarifa" not in columnas_egreso:
        cursor.execute("ALTER TABLE egreso ADD COLUMN id_tarifa INTEGER REFERENCES tarifa(id_tarifa)")

    # v2 escalable: nuevas columnas para multi-almacén/variante/lote (si tabla ya existe)
    try:
        cols_mov = _obtener_columnas(cursor, "movimiento_inventario")
        for col, sql in [
            ("id_variante", "ALTER TABLE movimiento_inventario ADD COLUMN id_variante INTEGER REFERENCES producto_variante(id_variante)"),
            ("id_almacen", "ALTER TABLE movimiento_inventario ADD COLUMN id_almacen INTEGER REFERENCES almacen(id_almacen)"),
            ("id_caja", "ALTER TABLE movimiento_inventario ADD COLUMN id_caja INTEGER REFERENCES caja(id_caja)"),
            ("id_lote", "ALTER TABLE movimiento_inventario ADD COLUMN id_lote INTEGER REFERENCES lote(id_lote)"),
        ]:
            if col not in cols_mov:
                cursor.execute(sql)
    except Exception:
        pass

    try:
        cols_venta = _obtener_columnas(cursor, "venta")
        for col, sql in [
            ("id_almacen", "ALTER TABLE venta ADD COLUMN id_almacen INTEGER REFERENCES almacen(id_almacen)"),
            ("id_caja", "ALTER TABLE venta ADD COLUMN id_caja INTEGER REFERENCES caja(id_caja)"),
            ("id_tarifa", "ALTER TABLE venta ADD COLUMN id_tarifa INTEGER REFERENCES tarifa(id_tarifa)"),
        ]:
            if col not in cols_venta:
                cursor.execute(sql)
    except Exception:
        pass

    # v2.2: categoria con tipo + edad opcional (campeonatos/servicios van por Tarifas)
    try:
        cols_cat = _obtener_columnas(cursor, "categoria")
        if "tipo" not in cols_cat:
            cursor.execute("ALTER TABLE categoria ADD COLUMN tipo TEXT DEFAULT 'ACADEMIA'")
            cursor.execute("UPDATE categoria SET tipo='ACADEMIA' WHERE tipo IS NULL")
        pragma = cursor.execute("PRAGMA table_info(categoria)").fetchall()
        edad_notnull = any(f[1] in ("edad_min", "edad_max") and f[3] == 1 for f in pragma)
        if edad_notnull:
            cursor.execute("ALTER TABLE categoria RENAME TO categoria_old")
            cursor.execute("""
                CREATE TABLE categoria (
                    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    edad_min INTEGER,
                    edad_max INTEGER,
                    tipo TEXT DEFAULT 'ACADEMIA',
                    activo INTEGER DEFAULT 1
                )
            """)
            cursor.execute("INSERT INTO categoria (id_categoria, nombre, edad_min, edad_max, tipo, activo) SELECT id_categoria, nombre, edad_min, edad_max, COALESCE(tipo,'ACADEMIA'), activo FROM categoria_old")
            cursor.execute("DROP TABLE categoria_old")
    except Exception:
        pass

    # v2.2: seed tarifas desde Precios Flexibles (migra valores actuales, idempotente)
    try:
        seed_tarifas_desde_config(cursor)
    except Exception:
        pass

    # Matriz de permisos editable (defaults desde PERMISOS_ROL, idempotente)
    try:
        from utils.constants import PERMISOS_ROL
        for rol, modulos in PERMISOS_ROL.items():
            for modulo in modulos:
                cursor.execute(
                    "INSERT OR IGNORE INTO rol_permiso (rol, modulo) VALUES (?, ?)",
                    (rol, modulo),
                )
    except Exception:
        pass


def seed_tarifas_desde_config(cursor=None) -> None:
    """Crea categorías Servicios/Campeonatos + 5 tarifas desde los precios
    de CONFIGURACION. Idempotente (no duplica). Se llama desde la migración
    (BD existentes) y desde seed_database (BD nuevas)."""
    from database.connection import get_connection
    cerrar = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        cerrar = True
    try:
        cfg = cursor.execute("SELECT precio_inscripcion, precio_reingreso, precio_uniforme, tasa_campeonato, arbitraje_por_equipo FROM configuracion LIMIT 1").fetchone()
        if not cfg:
            return

        def _cat(nombre, tipo):
            row = cursor.execute("SELECT id_categoria FROM categoria WHERE nombre=?", (nombre,)).fetchone()
            if row:
                return row[0]
            cur = cursor.execute("INSERT INTO categoria (nombre, edad_min, edad_max, tipo) VALUES (?, NULL, NULL, ?)", (nombre, tipo))
            return cur.lastrowid

        def _tar(id_cat, nombre, monto):
            import sqlite3 as _sq
            row = cursor.execute("SELECT id_tarifa FROM tarifa WHERE nombre=? AND id_categoria=?", (nombre, id_cat)).fetchone()
            try:
                monto_f = float(monto or 0)
            except (TypeError, ValueError):
                return
            if row or monto_f <= 0:
                return
            try:
                cursor.execute("INSERT INTO tarifa (id_categoria, nombre, monto, descripcion, activo) VALUES (?,?,?,?,1)", (id_cat, nombre, monto_f, "Migrado desde Precios Flexibles"))
            except _sq.IntegrityError:
                pass  # carrera: otra PC lo creó primero

        id_serv = _cat("Servicios", "SERVICIO")
        id_camp = _cat("Campeonatos", "CAMPEONATO")
        _tar(id_serv, "Inscripción", cfg[0])
        _tar(id_serv, "Reingreso", cfg[1])
        _tar(id_serv, "Uniforme base", cfg[2])
        _tar(id_camp, "Tasa base", cfg[3])
        _tar(id_camp, "Arbitraje por equipo", cfg[4])
        if cerrar:
            cursor.connection.commit()
    finally:
        pass

    try:
        cols_det = _obtener_columnas(cursor, "detalle_venta")
        for col, sql in [
            ("id_variante", "ALTER TABLE detalle_venta ADD COLUMN id_variante INTEGER REFERENCES producto_variante(id_variante)"),
            ("id_lote", "ALTER TABLE detalle_venta ADD COLUMN id_lote INTEGER REFERENCES lote(id_lote)"),
        ]:
            if col not in cols_det:
                cursor.execute(sql)
    except Exception:
        pass

    # Índices v2.1
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estudiante_es_nuevo ON estudiante(es_nuevo)")
    except Exception:
        pass
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepto_tipo ON concepto_cobro(tipo)")
    except Exception:
        pass
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepto_item_concepto ON concepto_item(id_concepto)")
    except Exception:
        pass

    # Índices escalables (si columnas ya existen)
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimiento_almacen ON movimiento_inventario(id_almacen, id_producto)")
    except Exception:
        pass
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_venta_almacen ON venta(id_almacen)")
    except Exception:
        pass

    # v2.1: restringir CHECK rol a ADMIN/SECRETARIA (migra CAJA/INVENTARIO → SECRETARIA)
    try:
        row = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usuario'").fetchone()
        if row and row[0] and "CAJA" in row[0]:
            # mapear legacy antes de recrear
            try:
                cursor.execute("UPDATE usuario SET rol='SECRETARIA' WHERE rol IN ('CAJA','INVENTARIO')")
            except Exception:
                pass
            cursor.execute("ALTER TABLE usuario RENAME TO usuario_old")
            cursor.execute("""
                CREATE TABLE usuario (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_persona INTEGER UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK(rol IN ('ADMIN', 'SECRETARIA')),
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL,
                    fecha_actualizacion TEXT,
                    FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
                )
            """)
            cursor.execute("INSERT INTO usuario (id_usuario, id_persona, username, password_hash, rol, activo, fecha_creacion, fecha_actualizacion) SELECT id_usuario, id_persona, username, password_hash, rol, activo, fecha_creacion, fecha_actualizacion FROM usuario_old")
            cursor.execute("DROP TABLE usuario_old")
    except Exception:
        pass


def _obtener_columnas(cursor, tabla: str) -> list[str]:
    cursor.execute(f"PRAGMA table_info({tabla})")
    return [fila[1] for fila in cursor.fetchall()]


if __name__ == "__main__":
    create_tables()
    print("Tablas creadas correctamente.")
