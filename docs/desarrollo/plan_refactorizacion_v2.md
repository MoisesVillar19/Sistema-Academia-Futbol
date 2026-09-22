# Plan de Refactorización v2 — Tiendita / Almacén + Avisos + Precios Excel

> Estado: EJECUTADO 2026-09-22 (fases 0–8, commit por fase/subfase).
> Cierre: suite completa 467 passed. Conceptos fuera del flujo (tabla dormida).
> Updater apunta a Sistema-Academia-Futbol (fix previo incluido en release).
> Fuente operativa: `D:\Hp\Desktop\AcademiaFutbol\INFORMACION ACADEMIA RONCALLI.xlsx`
> (hojas: RELACIÓN DE ALUMNOS, INGRESOS, VENTA UNIFORME, BALANCE TIENDA MAYO/JUNIO/AGOSTO).
> Directriz: una acción en los menos pasos posibles.

## Decisiones tomadas (no reabrir salvo objeción)

1. **2 inventarios estancos, 1 sola tabla.** `producto` se mantiene; el discriminador
   se renombra `tipo_uso` → `canal` (`TIENDITA`/`ALMACEN`, BD vacía = renombre libre).
   Cada lado tiene su service con su gate de permisos; comparten solo repository.
   Tablas separadas descartadas: mismoosk costo de código sin beneficio (ver §Riesgos).
2. **Roles:** `tiendita` visible para SECRETARIA; `almacen` solo ADMIN.
   Nuevos módulos en `MODULOS_SISTEMA` + `PERMISOS_ROL` (matriz Bloque D).
3. **Precios flexibles (`concepto_cobro`) eliminados del flujo.** Se quita sec. 9 de
   Configuración, combo de Matrícula y precedencia en `matricula_service`.
   Tabla dormida con datos (sin DROP). Tests de concepto se retiran/reescriben.
4. **Esquema de precios Excel:** Inscripción 150 (tarifa configurable) =
   paquete uniforme+mensualidad nuevos; Uniforme suelto 70 (`precio_venta` en Tienda,
   editable); Mensualidad 120 (tarifa ACADEMIA configurable).
5. **Becas presets exactos del Excel:** "1/2 BECA" = MONTO_FIJO S/50,
   "BECA COMPLETA" = PORCENTAJE 100 (editables). Visibles en Tarifas (secretaria
   ya tiene el permiso).
6. **Tabla densa modo Excel en todos los módulos** (helper `crear_tabla_densa` en
   `ui_helpers`, toggle Cards/Tabla en Pagos, Estudiantes, Matrículas, Ventas,
   Egresos, Tiendita, Almacén).
7. **Tarifas por módulo = acceso filtrado** (botón "Tarifas de este módulo" abre
   Tarifas ya filtrado). Sin CRUD duplicado.
8. **Ventas vive dentro de Tiendita** (tab). Egresos-gastos se queda módulo aparte.
9. **Vocabulario Excel adoptado:** COSTO TOTAL (caja), COSTO X UNIDAD, COSTO VENTA
   (precio venta), QUEDAN (stock), CANCELADO (=pagado), ADELANTO (=parcial),
   INICIO (fecha). Grilla anual de cuotas MAYO…DICIEMBRE estilo RELACIÓN DE ALUMNOS.
10. **Volumen no limita tabla única** (confirmado por usuario).

## Fase 0 — BD y seeds (único toque estructural)

- `ALTER TABLE pago ADD COLUMN comprobante_path TEXT` (migración en
  `database/create_db.py`, patrón `_migrar_columnas_faltantes`).
- Renombre `producto.tipo_uso` → `producto.canal` con CHECK (`TIENDITA`,`ALMACEN`)
  + backfill (`VENTA`→`TIENDITA`, `CONSUMO_INTERNO`→`ALMACEN`). Actualizar
  services/repositories/views/tests que referencian `tipo_uso`.
- Seeds exactos (solo si faltan, no sobrescribir): tarifa Inscripción 150
  (SERVICIO), Uniforme base 70, mensualidad ACADEMIA 120, becas 1/2 (FIJO 50)
  y COMPLETA (100%), `MODULOS_SISTEMA` += `tiendita`, `almacen`.
- Tests: migración aplica en BD vacía y con datos legacy; seeds idempotentes.
- Commit: `feat(fase-0): BD canal + comprobante_path + seeds Excel`.

## Fase 1 — Notificaciones / avisos

- Nuevo `services/avisos_service.py::obtener_avisos()` → lista
  `{modulo, texto, cantidad, severidad}`:
  pagos YAPE/PLIN/TRANSFERENCIA sin comprobante (históricos quedan pendientes),
  stock bajo, cuotas vencidas / por vencer, matrícula sin apoderado principal.
- Dashboard: sección "Pendientes" (severidad por color) + chips por módulo
  (ej. Pagos: "N comprobantes pendientes" con filtro directo).
- Regla: sin toast invasivo; avisos visibles al entrar a cada módulo.
- Tests: matriz de avisos con datos de prueba.
- Commit: `feat(fase-1): sistema de avisos por módulo`.

## Fase 2 — Fechas asíncronas editables

- `DatePicker` (default hoy) en: Pagos, Compras, Ventas, Movimientos,
  Matrícula normal + express (`services/*`: aceptar `fecha_*` o defaultear hoy;
  `pago_service.py:55`, `inventario_service.py:364`, `venta_service.py:106`,
  `matricula_service.py:41`).
- Pagos parciales con fecha+método propios por parte (caso ADELANTO 30+20+20
  de VENTA UNIFORME).
- Tests: fecha explícita persiste; default sigue siendo hoy.
- Commit: `feat(fase-2): fechas editables por operación`.

## Fase 3 — Imágenes con aviso real

- Validar al **seleccionar**: PIL verify + extensiones (jpg/png; pdf solo egresos).
  `messagebox` claro al rechazar (hoy solo tamaño, y en ventas/matrícula ni eso).
- Conservar extensión real al guardar (fin del `.jpg` forzado en
  `venta_view.py:442-450`); preview con mensaje si el archivo es inválido
  (fin de los `except: pass` silenciosos en `pago/estudiante/egreso/matricula/venta`).
- Pago: copiar comprobante a COMPROBANTES_DIR al registrar (hoy se descarta).
- Tests: rechazo de formato inválido, conservación de extensión.
- Commit: `fix(fase-3): validación visible de imágenes`.

## Fase 4 — Precios y becas (ya decididos en §Decisiones)

- Express NUEVO lee tarifa Inscripción (fin del 120 fijo
  `matricula_service.py:266` + labels fijos `matricula_view.py:81,108-110`).
- Presets beca 1/2 y completa (idempotentes) + visibles en Tarifas/Becas.
- Tests: express con tarifa 150; presets crean y aplican.
- Commit: `feat(fase-4): precios Excel + presets de beca`.

## Fase 5 — Matrícula sin confusión de camiseta

- Excluir producto camiseta-regalo (`id_tipo_uniforme` Entrenamiento) de extras
  siempre; nota "incluye camiseta de regalo — uniformes extra en Tienda".
  Antiguos: sin sección camiseta.
- Mantener bloqueo RN-051 (regalo atómico, rollback sin stock) +
  `es_nuevo` inmutable.
- Tests: nuevos no ven camiseta comprable; antiguos tampoco; regalo intacto.
- Commit: `fix(fase-5): matrícula sin confusión de camiseta`.

## Fase 6 — Split Tiendita / Almacén

- Sidebar: `TIENDITA` (secretaria+admin: Productos, Registrar, Compras, **Ventas**,
  Ganancias con detalle compra-vs-venta por producto estilo BALANCE TIENDA)
  y `ALMACEN` (solo admin: Productos, Registrar, Compras, Movimientos, Historial).
- Scoping por `canal` en services + gates `tiene_permiso("tiendita"/"almacen")`.
  `venta_service` rechaza `ALMACEN`; movimientos solo Almacén (Tiendita: sin tab).
- Categorías y tipos de producto → Configuración (extender sec. catálogos).
- Form empaque con vocabulario Excel: Unidad → "COSTO X UNIDAD" único;
  Caja → "COSTO TOTAL + cantidad" con unitario solo-lectura (legacy `precio`
  se deja de pedir, columna conservada).
- Ventas filtrables por categoría (segmentado como inventario).
- `event_bus`: `publish("producto_actualizado")` real en CRUD de producto/compra/
  movimiento/venta + refresco de combos en Tiendita, Almacén, Ventas, Matrícula
  (fix "creado no aparece").
- Tests: scoping (tiendita no ve almacén y viceversa), gates por rol, publish/refresh.
- Commit: `feat(fase-6): split Tiendita/Almacén estancos`.

## Fase 7 — Formato, dashboard, limpieza

- `ui_helpers.crear_tabla_densa` + toggle Cards/Tabla en Pagos, Estudiantes,
  Matrículas, Ventas, Egresos (+ Tiendita/Almacén de Fase 6).
- Dashboard por bloques colapsables: Academia / Dinero / Tienda-Almacén / Avisos
  (mismas fuentes `dashboard_service`, solo reagrupar).
- **Grilla anual de cuotas** MAYO…DICIEMBRE (X=CANCELADO, monto=ADELANTO,
  vacío=pendiente) en Matrículas/Pagos.
- Auditoría a cards estándar (fin del rayado por bordes).
- Quitar `concepto_cobro` del flujo (§Decisiones.3) + botón "Tarifas de este módulo".
- Tests por cada pieza; commit(s): `feat(fase-7): ...`.

## Fase 8 — Excel final + QA general

- Solo cuando llegue el archivo correcto (el actual ya se mapeó en §Vocabulario).
- Revisión integral ("revisada a todo"): flujos secretaria de punta a punta,
  suite completa verde, commit por hallazgo.

## Riesgos y notas

- **Cruce de datos entre lados:** mitigado con scoping en services + tests;
  riesgo residual solo ante bug (aceptado; alternativa 2 tablas descartada en §Decisiones.1).
- **Históricos sin comprobante:** YAPE/PLIN/TRANSFERENCIA viejos quedarán como
  "pendiente" sin archivo recuperable; se comunican como tales, no se inventan.
- **Tests que se moverán:** `test_inventario*.py`, `test_ventas` (si existe),
  `test_matricula_express.py`, `test_becas.py`, `test_concepto*` (si existe),
  `test_ui_smoke.py` (nuevos módulos), `test_roles.py` (nueva matriz).
- **Sin cambios en:** auditoría (solo lectura), soft-delete, roles base,
  arquitectura por capas (`AGENTS.md` manda).
