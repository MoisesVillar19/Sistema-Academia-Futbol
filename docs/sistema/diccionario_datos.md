# Diccionario de Datos

> **v2 (2026-09):** `estudiante.foto_path/comprobante_pago_path/fecha_matricula`, `producto.precio_compra/venta/id_tipo_uniforme`, `tipo_uniforme`, `venta/detalle_venta`, `egreso`, `configuracion` +7 precios (`precio_inscripcion` etc.) + `pin_emergencia`. Fuente DDL: `database/create_db.py`.

## Convenciones Generales

### Claves Primarias

Todas las tablas utilizarán:

```sql
INTEGER PRIMARY KEY AUTOINCREMENT
```

### Fechas

Tipo:

```text
TEXT
```

Formato:

```text
YYYY-MM-DD
```

Ejemplo:

```text
2026-07-26
```

### Fecha y Hora

Tipo:

```text
TEXT
```

Formato:

```text
YYYY-MM-DD HH:MM:SS
```

### Booleanos

SQLite no tiene un tipo BOOLEAN real.

Se utilizará:

```text
INTEGER
```

Valores:

```text
1 = Activo
0 = Inactivo
```

---

# PERSONA

| Campo | Tipo | Restricciones |
|---------|---------|---------|
| id_persona | INTEGER | PK |
| dni | TEXT | UNIQUE NOT NULL |
| nombres | TEXT | NOT NULL |
| apellidos | TEXT | NOT NULL |
| fecha_nacimiento | TEXT | |
| sexo | TEXT | CHECK('M','F') |
| direccion | TEXT | |
| telefono | TEXT | |
| correo | TEXT | |
| activo | INTEGER | DEFAULT 1 |
| fecha_creacion | TEXT | NOT NULL |
| fecha_actualizacion | TEXT | |

---

# USUARIO

| Campo | Tipo |
|---------|---------|
| id_usuario | INTEGER PK |
| id_persona | INTEGER FK |
| username | TEXT UNIQUE |
| password_hash | TEXT |
| rol | TEXT |
| activo | INTEGER |
| fecha_creacion | TEXT |
| fecha_actualizacion | TEXT |

### Restricción (v2.1 solo 2 roles, migración CAJA/INVENTARIO→SECRETARIA)

```sql
CHECK(
    rol IN ('ADMIN','SECRETARIA')
)
```

---

# APODERADO

| Campo | Tipo |
|---------|---------|
| id_apoderado | INTEGER PK |
| id_persona | INTEGER FK |
| parentesco | TEXT |
| ocupacion | TEXT |
| activo | INTEGER |

---

# CATEGORIA

| Campo | Tipo |
|---------|---------|
| id_categoria | INTEGER PK |
| nombre | TEXT UNIQUE |
| edad_min | INTEGER |
| edad_max | INTEGER |
| activo | INTEGER |

### Ejemplos

```text
3-5
6-8
9-12
13-15
```

---

# TARIFA

| Campo | Tipo |
|---------|---------|
| id_tarifa | INTEGER PK |
| id_categoria | INTEGER FK |
| nombre | TEXT |
| monto | REAL |
| fecha_inicio | TEXT |
| fecha_fin | TEXT |
| activo | INTEGER |

### Ejemplo

```text
Sub 8 2026
S/120
```

---

# BECA

| Campo | Tipo |
|---------|---------|
| id_beca | INTEGER PK |
| nombre | TEXT |
| tipo | TEXT |
| valor | REAL |
| observacion | TEXT |
| activo | INTEGER |

### Restricción

```sql
CHECK(
    tipo IN (
        'PORCENTAJE',
        'MONTO_FIJO'
    )
)
```

---

# ESTUDIANTE (v2.1: + es_nuevo RN-051 + foto)

| Campo | Tipo |
|---------|---------|
| id_estudiante | INTEGER PK |
| id_persona | INTEGER FK |
| estado | TEXT |
| fecha_ingreso | TEXT |
| fecha_retiro | TEXT |
| es_nuevo | INTEGER DEFAULT 0 CHECK(0,1) — RN-051, checkbox única vez en registro estudiante, si 1 primera matrícula regala Camiseta 0 |
| foto_path | TEXT |
| comprobante_pago_path | TEXT |
| fecha_matricula | TEXT |
| activo | INTEGER |

### Restricción

```sql
CHECK(
    estado IN (
        'ACTIVO',
        'RETIRADO',
        'REINGRESANTE'
    )
)
```

---

# MATRICULA

| Campo | Tipo |
|---------|---------|
| id_matricula | INTEGER PK |
| id_estudiante | INTEGER FK |
| id_tarifa | INTEGER FK |
| monto_pactado | REAL NULL |
| fecha_inicio | TEXT |
| fecha_fin | TEXT |
| dia_vencimiento | INTEGER |
| estado | TEXT |
| activo | INTEGER |


### Validación

```sql
dia_vencimiento BETWEEN 1 AND 31
```
---

# MATRICULA_BECA

| Campo | Tipo |
|---------|---------|
| id_matricula_beca | INTEGER PK |
| id_matricula | INTEGER FK |
| id_beca | INTEGER FK |
| fecha_asignacion | TEXT |
| activo | INTEGER |
| observacion | TEXT |
---

# ESTUDIANTE_APODERADO

| Campo | Tipo |
|---------|---------|
| id_estudiante_apoderado | INTEGER PK |
| id_estudiante | INTEGER FK |
| id_apoderado | INTEGER FK |
| es_principal | INTEGER |
| activo | INTEGER |

Restricción lógica:

Solo puede existir un apoderado principal
por estudiante.

---

# CUOTA

| Campo | Tipo |
|---------|---------|
| id_cuota | INTEGER PK |
| id_matricula | INTEGER FK |
| periodo | TEXT |
| fecha_vencimiento | TEXT |
| monto_total | REAL |
| monto_pagado | REAL |
| saldo | REAL |
| estado | TEXT |
| activo | INTEGER |

### Restricción

```sql
CHECK(
    estado IN (
        'PENDIENTE',
        'PARCIAL',
        'PAGADO',
        'VENCIDO'
    )
)
```

### Ejemplos de período

```text
2026-07
2026-08
2026-09
```

Observaciones:

- saldo = monto_total - monto_pagado
- No puede ser negativo.

---

# PAGO

| Campo | Tipo |
|---------|---------|
| id_pago | INTEGER PK |
| id_usuario | INTEGER FK |
| numero_recibo | TEXT UNIQUE |
| fecha_pago | TEXT |
| monto_total | REAL |
| metodo_pago | TEXT |
| observacion | TEXT |
| comprobante_path | TEXT |
| activo | INTEGER |

### Métodos de Pago

```sql
CHECK(
    metodo_pago IN (
        'EFECTIVO',
        'YAPE',
        'PLIN',
        'TRANSFERENCIA'
    )
)
```

---

# DETALLE_PAGO

| Campo | Tipo |
|---------|---------|
| id_detalle_pago | INTEGER PK |
| id_pago | INTEGER FK |
| id_cuota | INTEGER FK |
| monto_pagado | REAL |

---

# PRODUCTO (v2)

| Campo | Tipo |
|---------|---------|
| id_producto | INTEGER PK |
| id_categoria_producto | INTEGER FK |
| canal | TEXT |
| codigo | TEXT UNIQUE |
| nombre | TEXT |
| stock_actual | INTEGER |
| stock_minimo | INTEGER |
| precio | REAL |
| precio_compra | REAL |
| precio_venta | REAL |
| id_tipo_uniforme | INTEGER FK → tipo_uniforme |
| activo | INTEGER |


### Restricción

```sql

CHECK(
    canal IN (
        'TIENDITA',
        'ALMACEN'
    )
)
```
---

# CATEGORIA_PRODUCTO

| Campo | Tipo |
|---------|---------|
| id_categoria_producto | INTEGER PK |
| nombre | TEXT UNIQUE |
| activo | INTEGER |

---

# MOVIMIENTO_INVENTARIO

| Campo | Tipo |
|---------|---------|
| id_movimiento | INTEGER PK |
| id_producto | INTEGER FK |
| id_usuario | INTEGER FK |
| tipo_movimiento | TEXT |
| cantidad | INTEGER |
| stock_anterior | INTEGER |
| stock_nuevo | INTEGER |
| fecha_movimiento | TEXT |
| motivo | TEXT |

### Restricción

```sql
CHECK(
    tipo_movimiento IN (
        'ENTRADA',
        'SALIDA',
        'AJUSTE'
    )
)
```

---

# TIPO_UNIFORME (v2)

| Campo | Tipo |
|---------|---------|
| id_tipo_uniforme | INTEGER PK |
| nombre | TEXT UNIQUE |
| descripcion | TEXT |
| activo | INTEGER |

# VENTA (v2)

| Campo | Tipo |
|---------|---------|
| id_venta | INTEGER PK |
| id_estudiante | INTEGER FK |
| id_usuario | INTEGER FK |
| fecha_venta | TEXT |
| monto_total | REAL |
| metodo_pago | TEXT CHECK(EFECTIVO,YAPE,PLIN,TRANSFERENCIA) |
| tipo_venta | TEXT CHECK(UNIFORME,TIENDA,CAMPEONATO,INSCRIPCION) |
| numero_recibo | TEXT UNIQUE |
| comprobante_path | TEXT |
| activo | INTEGER |

# DETALLE_VENTA (v2)

| Campo | Tipo |
|---------|---------|
| id_detalle_venta | INTEGER PK |
| id_venta | INTEGER FK |
| id_producto | INTEGER FK |
| cantidad | INTEGER |
| precio_unitario | REAL |
| subtotal | REAL |

# EGRESO (v2)

| Campo | Tipo |
|---------|---------|
| id_egreso | INTEGER PK |
| concepto | TEXT CHECK(PROFESOR,PERSONAL,CAMPEONATO_FIJO,ARBITRAJE,VIATICOS) |
| monto | REAL |
| fecha | TEXT |
| responsable | TEXT |
| id_usuario | INTEGER FK |
| observacion | TEXT |
| activo | INTEGER |

# CONFIGURACION (v2: +7 precios, v2.1 fallback para RN-052)

Solo existirá una fila. `precio_*` se mantienen como fallback; catálogo nuevo `concepto_cobro` evita redundancia (precedencia en `plan_dayanna_v2.1.md:1.2`).

| Campo | Tipo |
|---------|---------|
| id_configuracion | INTEGER PK |
| nombre_academia | TEXT |
| direccion | TEXT |
| telefono | TEXT |
| correo | TEXT |
| mora_habilitada | INTEGER |
| porcentaje_mora | REAL |
| tipo_mora | TEXT |
| monto_mora | REAL |
| dias_por_vencer | INTEGER |
| permitir_multiples_becas | INTEGER |
| backup_automatico | INTEGER |
| frecuencia_backup | INTEGER |
| ruta_backup | TEXT |
| correo_onedrive | TEXT |
| pin_emergencia | TEXT |
| precio_inscripcion | REAL |
| precio_mensualidad | REAL |
| precio_uniforme | REAL |
| precio_reingreso | REAL |
| tasa_campeonato | REAL |
| arbitraje_por_equipo | REAL |
| pago_profesor | REAL |
| fecha_actualizacion | TEXT |

# CONCEPTO_COBRO (v2.1 RN-052 — catálogo flexible sin redundancia)

| Campo | Tipo | Restricción |
|---------|---------|---------|
| id_concepto | INTEGER PK | |
| nombre | TEXT UNIQUE NOT NULL | |
| tipo | TEXT NOT NULL | CHECK(INSCRIPCION,MENSUALIDAD,REINGRESO,PROMOCION,CAMPEONATO,OTRO) |
| monto | REAL NOT NULL | >=0 |
| descripcion | TEXT | |
| activo | INTEGER DEFAULT 1 | |

# CONCEPTO_ITEM (v2.1)

| Campo | Tipo |
|---------|---------|
| id_item | INTEGER PK |
| id_concepto | INTEGER FK → concepto_cobro |
| id_producto | INTEGER FK → producto |
| cantidad | INTEGER >0 |


### Ejemplo de registro inicial

```text
id_configuracion = 1

nombre_academia = Academia XYZ
direccion = Av. Principal 123
telefono = 999888777
correo = contacto@academia.com

mora_habilitada = 0
porcentaje_mora = 0

dias_por_vencer = 3

permitir_multiples_becas = 1

backup_automatico = 1
frecuencia_backup = 7

ruta_backup = backups/
correo_onedrive = ""

fecha_actualizacion = 2026-07-31 20:00:00
```
---

# LOG

| Campo | Tipo |
|---------|---------|
| id_log | INTEGER PK |
| id_usuario | INTEGER FK |
| tabla_afectada | TEXT |
| id_registro | INTEGER |
| accion | TEXT |
| valor_anterior | TEXT |
| valor_nuevo | TEXT |
| fecha | TEXT |
---

# Índices Recomendados

```sql
CREATE INDEX idx_persona_dni
ON persona(dni);

CREATE INDEX idx_usuario_username
ON usuario(username);

CREATE INDEX idx_cuota_estado
ON cuota(estado);

CREATE INDEX idx_cuota_vencimiento
ON cuota(fecha_vencimiento);

CREATE INDEX idx_pago_fecha
ON pago(fecha_pago);

CREATE INDEX idx_producto_codigo
ON producto(codigo);

CREATE INDEX idx_cuota_estado
ON cuota(estado);

CREATE INDEX idx_estudiante_apoderado_estudiante
ON estudiante_apoderado(id_estudiante);

CREATE INDEX idx_matricula_beca_matricula
ON matricula_beca(id_matricula);

CREATE INDEX idx_producto_categoria
ON producto(id_categoria_producto);
```

---

# Datos Iniciales (Seed)

## Categorías

```text
3-5
6-8
9-12
13-15
16-18
```

## Usuario Administrador

Usuario:

```text
admin
```

Contraseña:

```text
admin123
```

> ⚠️ Solo para desarrollo.  
> Al primer inicio debería obligarse al usuario a cambiar la contraseña.