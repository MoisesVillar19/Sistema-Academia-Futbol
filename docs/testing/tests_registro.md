# Registro de Tests — AcademiaFutbol

**Fecha inicio:** 2026-08-01
**Framework:** pytest
**Base de datos:** SQLite `:memory:` (en memoria)

---

## Configuración

### `tests/conftest.py`

- Fixture `test_db`: Crea DB en memoria para cada test, ejecuta seed, limpia al terminar
- Fixture `usuario_admin`: Login como admin para tests que requieren sesión

### Ejecución

```powershell
# Todos los tests
python -m pytest tests/ -v

# Un archivo específico
python -m pytest tests/test_validators.py -v

# Un test específico
python -m pytest tests/test_validators.py::test_validate_dni_valid -v
```

---

## Tests Unitarios

### `test_validators.py` — 18 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_validate_dni_valid` | DNI válido (8 dígitos) | ✅ PASSED |
| `test_validate_dni_invalid` | DNI inválido | ✅ PASSED |
| `test_validate_email_valid` | Email válido | ✅ PASSED |
| `test_validate_email_invalid` | Email inválido | ✅ PASSED |
| `test_validate_email_optional` | Email opcional (vacío) | ✅ PASSED |
| `test_validate_phone_valid` | Teléfono válido | ✅ PASSED |
| `test_validate_phone_invalid` | Teléfono inválido | ✅ PASSED |
| `test_validate_phone_optional` | Teléfono opcional | ✅ PASSED |
| `test_validate_sex` | Sexo (M/F) | ✅ PASSED |
| `test_validate_rol` | Rol (ADMIN/SECRETARIA) | ✅ PASSED |
| `test_validate_estado_estudiante` | Estado estudiante | ✅ PASSED |
| `test_validate_estado_cuota` | Estado cuota | ✅ PASSED |
| `test_validate_metodo_pago` | Método de pago | ✅ PASSED |
| `test_validate_tipo_beca` | Tipo de beca | ✅ PASSED |
| `test_validate_tipo_movimiento` | Tipo movimiento inventario | ✅ PASSED |
| `test_validate_tipo_uso` | Tipo uso producto | ✅ PASSED |
| `test_validate_dia_vencimiento` | Día vencimiento (1-31) | ✅ PASSED |
| `test_validate_not_empty` | Campo obligatorio | ✅ PASSED |

---

### `test_security.py` — 7 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_hash_password` | Hash de password | ✅ PASSED |
| `test_verify_password_correct` | Verificar password correcta | ✅ PASSED |
| `test_verify_password_incorrect` | Verificar password incorrecta | ✅ PASSED |
| `test_verify_password_invalid_hash` | Hash inválido | ✅ PASSED |
| `test_generate_temp_password` | Generar password temporal | ✅ PASSED |
| `test_generate_temp_password_custom_length` | Password con longitud custom | ✅ PASSED |
| `test_hash_unique` | Cada hash es único | ✅ PASSED |

---

### `test_dates.py` — 15 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_get_today` | Obtener fecha actual | ✅ PASSED |
| `test_get_now` | Obtener fecha/hora actual | ✅ PASSED |
| `test_parse_date_valid` | Parsear fecha válida | ✅ PASSED |
| `test_parse_date_invalid` | Parsear fecha inválida | ✅ PASSED |
| `test_parse_datetime_valid` | Parsear datetime válido | ✅ PASSED |
| `test_parse_datetime_invalid` | Parsear datetime inválido | ✅ PASSED |
| `test_format_date` | Formatear fecha | ✅ PASSED |
| `test_format_datetime` | Formatear datetime | ✅ PASSED |
| `test_calculate_age` | Calcular edad | ✅ PASSED |
| `test_calculate_age_invalid` | Edad con fecha inválida | ✅ PASSED |
| `test_is_expired` | Verificar vencimiento | ✅ PASSED |
| `test_is_expired_invalid` | Vencimiento con fecha inválida | ✅ PASSED |
| `test_days_until` | Días hasta fecha futura | ✅ PASSED |
| `test_days_until_past` | Días desde fecha pasada | ✅ PASSED |
| `test_days_until_invalid` | Días con fecha inválida | ✅ PASSED |

---

## Resumen (actualizado 2026-09-06)

| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_validators.py` | 18 | ✅ TODOS PASARON |
| `test_security.py` | 7 | ✅ TODOS PASARON |
| `test_dates.py` | 15 | ✅ TODOS PASARON |
| `test_cuota_service.py` | 11 | ✅ TODOS PASARON |
| `test_estudiante_service.py` | 8 | ✅ TODOS PASARON |
| `test_pago_service.py` | 7 | ✅ TODOS PASARON |
| `test_login.py` | 6 | ✅ TODOS PASARON |
| `test_matriculas.py` | 6 | ✅ TODOS PASARON |
| `test_inventario.py` | 13 | ✅ TODOS PASARON |
| `test_inventario_escalable.py` | 8 | ✅ TODOS PASARON |
| **TOTAL** | **99** | **✅ 99/99** |

---

## Tests de Services

### `test_cuota_service.py` — 11 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_crear_cuota` | Crear cuota mensual | ✅ PASSED |
| `test_crear_cuota_detalle` | Verificar campos de cuota | ✅ PASSED |
| `test_actualizar_pago` | Pago parcial | ✅ PASSED |
| `test_actualizar_pago_total` | Pago completo (PAGADO) | ✅ PASSED |
| `test_actualizar_pago_excede_saldo` | Rechazar pago mayor al saldo | ✅ PASSED |
| `test_actualizar_pago_cuota_no_existe` | Cuota inexistente | ✅ PASSED |
| `test_contar_por_estado` | Contar cuotas por estado | ✅ PASSED |
| `test_obtener_cuotas_por_matricula` | Listar cuotas de matrícula | ✅ PASSED |
| `test_obtener_cuotas_pendientes` | Listar cuotas pendientes | ✅ PASSED |
| `test_obtener_vencidas` | Obtener cuotas vencidas | ✅ PASSED |
| `test_obtener_por_vencer` | Obtener cuotas por vencer | ✅ PASSED |

### `test_estudiante_service.py` — 8 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_crear_estudiante` | Crear estudiante | ✅ PASSED |
| `test_crear_estudiante_duplicado` | Rechazar DNI duplicado | ✅ PASSED |
| `test_crear_estudiante_sin_dni` | Rechazar sin DNI | ✅ PASSED |
| `test_editar_estudiante` | Editar datos | ✅ PASSED |
| `test_editar_estudiante_no_existe` | Estudiante inexistente | ✅ PASSED |
| `test_listar_estudiantes` | Listar todos | ✅ PASSED |
| `test_obtener_estudiante` | Obtener por ID | ✅ PASSED |
| `test_obtener_estudiante_no_existe` | ID inexistente | ✅ PASSED |

### `test_pago_service.py` — 7 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_registrar_pago` | Registrar pago | ✅ PASSED |
| `test_registrar_pago_monto_excede` | Rechazar monto > saldo | ✅ PASSED |
| `test_registrar_pago_cuota_no_existe` | Cuota inexistente | ✅ PASSED |
| `test_registrar_pago_metodo_invalido` | Método no válido | ✅ PASSED |
| `test_registrar_pago_monto_cero` | Rechazar monto $0 | ✅ PASSED |
| `test_listar_pagos` | Listar pagos | ✅ PASSED |
| `test_obtener_pago_no_existe` | Pago inexistente | ✅ PASSED |

---

## Tests de Integración

### `test_login.py` — 6 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_login_exitoso` | Login con credenciales correctas | ✅ PASSED |
| `test_login_fallido_password` | Rechazar password incorrecta | ✅ PASSED |
| `test_login_fallido_usuario` | Rechazar usuario inexistente | ✅ PASSED |
| `test_logout` | Cerrar sesión | ✅ PASSED |
| `test_obtener_usuario_actual` | Obtener datos del usuario logueado | ✅ PASSED |
| `test_es_admin` | Verificar rol ADMIN | ✅ PASSED |

### `test_matriculas.py` — 6 tests ✅

| Test | Función | Resultado |
|------|---------|-----------|
| `test_crear_matricula` | Crear matrícula | ✅ PASSED |
| `test_matricula_con_cuota_generada` | Verificar cuota generada al matricular | ✅ PASSED |
| `test_matricula_estudiante_ya_activo` | Rechazar segunda matrícula activa | ✅ PASSED |
| `test_matricula_estudiante_no_existe` | Estudiante inexistente | ✅ PASSED |
| `test_listar_matriculas_activas` | Listar matrículas activas | ✅ PASSED |
| `test_obtener_matricula_por_estudiante` | Obtener matrículas de estudiante | ✅ PASSED |

---

### `test_inventario_escalable.py` — 8 tests ✅ (v2 escalable, 2026-09-06)

| Test | Qué verifica (simple) | Resultado |
|------|---|---|
| `test_talla_seed_existen` | Seed crea S/M/L/XL/UNICA | ✅ PASSED |
| `test_almacen_caja_seed_principal` | Seed crea Almacén Principal y Caja 1 (si 1, UI oculta) | ✅ PASSED |
| `test_crear_producto_con_talla_crea_variante_y_stock` | `talla M` → `sku PROD-M` + `stock_almacen 10` | ✅ PASSED |
| `test_crear_producto_sin_talla_no_crea_variante` | `UNICA` no crea variante | ✅ PASSED |
| `test_venta_con_talla_descuenta_variante` | Vender `2 M` → `stock 10→8` solo variante M | ✅ PASSED |
| `test_venta_stock_insuficiente_variante_rechazada` | `stock 1` pedir 5 → `Stock insuficiente` | ✅ PASSED |
| `test_valorizado_stock_por_almacen` | `3×30 + 2×20 =130` valorizado | ✅ PASSED |
| `test_lote_fifo_descuento` | Lote vence `2026-10-01` primero (FIFO) | ✅ PASSED |

> **Para Dayanna y asistente:** Estos tests prueban lo que ves en `Inventario → Registrar Producto` (elegir `Talla M` y `Stock inicial 10`), luego `Ventas → Uniforme M 2 unidades` y ver que el stock baja solo de esa talla. Si cambias a `UNICA`, no crea variante. `Lote` es para alimentos que vencen.

## Próximos Tests

- Inventario escalable S1 completo ✅ (arriba)
- Falta: test multi-almacén explícito con 2 sedes (cuando haya 2 `almacen`)

---

## Cambios Realizados

| Archivo | Cambio |
|---------|--------|
| `utils/helpers.py` | Agregada función `generate_product_code()` |
| `services/inventario_service.py` | Código de producto ahora es opcional (se auto-genera) |
| `tests/conftest.py` | Fixture `test_db` (:memory:) con patch de `conn_module.DB_PATH` |
| `database/connection.py` | `get_connection()` maneja `:memory:` (dirname vacío) |
| `tests/test_validators.py` | Creado - 18 tests |
| `tests/test_security.py` | Creado - 7 tests |
| `tests/test_dates.py` | Creado - 15 tests |
| `tests/test_cuota_service.py` | Creado - 11 tests |
| `tests/test_estudiante_service.py` | Creado - 8 tests |
| `tests/test_pago_service.py` | Creado - 7 tests |
| `tests/test_login.py` | Creado - 6 tests |
| `tests/test_matriculas.py` | Creado - 6 tests |
| `tests/test_uniformes_n_tipos.py` | Creado v1.2.1 (2026-10-10) - 18 tests: tipos_vendibles dinámico, slug UNI-XXX único, CRUD producto uniforme, venta con talla, independencia Tiendita/Almacén/Ventas, combos dinámicos Uniformes/Matrícula, importador con tipos nuevos y choques de código |
| `tests/test_retiro_anula_cuota.py` | Creado v1.2.2 (2026-10-10) - 6 tests: anula solo actual sin pagos, conserva anteriores/parciales, flag opt-out, reingreso no reactiva, UI propaga check |
| `tests/test_update_service.py` | +3 tests v1.2.2: normalización ZIP con raíz única (aplana), plano y multi-raíz intactos |
| `tests/test_edicion_exclusiva.py` | Creado v1.2.3 (2026-10-10) - 10 tests: activar solo ADMIN, bloqueo import/historial/restore ajenos, liberar dueño/ADMIN, stale 2h, cobros no afectados |

---

## Notas

### AJUSTE en Inventario

El tipo de movimiento `AJUSTE` establece el stock al valor absoluto de `cantidad`.
Ejemplo: Stock actual = 50, AJUSTE con cantidad = 30 → Nuevo stock = 30 (no 50+30 ni 50-30).

Se usa para corregir discrepancias de inventario.

### Código de Producto

El sistema ahora genera automáticamente códigos con formato `PRDYYYYMMDDHHMMSS`.
Si el usuario proporciona un código, se usa ese. Si no, se genera uno automático.
