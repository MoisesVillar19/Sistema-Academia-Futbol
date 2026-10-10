# Changelog — AcademiaFutbol (canónico)

> **Unificado 2026-10-09** desde `docs/changelog.md` + este archivo. Este es el canónico.
> `docs/changelog.md` solo redirige aquí. Línea de tiempo: `TIMELINE.md`.

## v1.2.2 - 2026-10-10 (updater SSL + ZIP plano + retiro anula actual)

### Updater (error SSL)
- `certifi` empaquetado en el exe (`_contexto_ssl` ya lo prefería; faltaba la
  dependencia). TLS con bundle propio en PCs escolares.
- Si persiste SSL: revisar fecha/hora del PC, firewall con inspección TLS y
  conexión a internet (la red LAN sola no alcanza a GitHub).

### Actualización (ZIP no cambiaba versión)
- Causa: el ZIP v1.2.1 traía carpeta raíz y la extracción (manual o automática
  al salir) anidaba `app/AcademiaFutbol/...` sin tocar el exe.
- Fix: `_normalizar_zip_sin_raiz()` aplana el ZIP antes del actualizador
  externo + ZIP v1.2.2 empaquetado plano (contenido en raíz, verificado).
- En la PC afectada: borrar la subcarpeta anidada si existe antes de actualizar.

### Retiros (deuda fantasma de 40+ retirados)
- Al retirar (manual o importación) se anula solo la cuota actual pendiente sin
  pagos (activo=0 + auditoría); anteriores y parciales se conservan.
- Diálogo con check activado por defecto mostrando la cuota exacta.
- Reingreso no reactiva la anulada; la nueva matrícula genera cuotas frescas.
- Deuda histórica de retirados se conserva (decisión negocio v1.2.2).
- Suite `tests/test_retiro_anula_cuota.py` (6) + 3 tests de normalización ZIP.

## v1.2.1 - 2026-10-10 (hotfix uniformes N tipos, sin DDL)

### Bug
- Uniformes solo mostraba COM/ENT aunque `tipo_uniforme` admite N tipos: un 3er
  tipo creado en Configuración nunca aparecía (sin producto, sin tallas, sin venta).
- Tiendita excluía uniformes por tuple fijo de códigos → un tipo nuevo se filtraba a Tienda.
- Ninguna Compra UI alcanzaba a productos de uniforme (Almacén filtra por canal,
  Tiendita los excluía) → solo entraba stock vía pre-compra automática.
- Ventas embebida en Tiendita listaba productos de uniforme.

### Fix (Uniformes autosuficiente, sin pasar por Configuración/Almacén/Tiendita)
- `uniforme_service`: `tipos_vendibles()` dinámico, slug `UNI-XXX` único (sufijo
  `-2` ante choque), `asegurar_producto()` acepta clave legacy o nombre de tipo
  activo, `crear_producto_uniforme()` (tipo + producto + precio + stock),
  `desactivar_producto_uniforme()` (soft delete, reactiva en vez de duplicar).
- Uniformes: tab Productos con + Nuevo producto, Editar precio, + Talla,
  Registrar Compra (stock propio) y Desactivar; combo de venta y segmentado de
  Matrícula dinámicos. Regalo RN-051 intacto (solo Entrenamiento).
- Independencia: Tiendita/Ventas excluyen por `id_tipo_uniforme` (fallback legacy
  por código); Almacén ya excluía por canal. Dato sigue en `canal=TIENDITA`
  (guard de `venta_service`); sin cambios de esquema.
- Importador: acepta nombres de tipos activos; validación lista tipos válidos;
  alias legacy COM/ENT intactos; código de tienda existente no colisiona.
- Corrección lateral: `agregar_talla()` usaba `auditoria_service.id_usuario_sesion_or_system()`
  (inexistente, bug enmascarado por el seed) → `id_usuario_sesion()`.
- Suite `tests/test_uniformes_n_tipos.py`: 18 tests en verde; total 662/662.

## v1.2.0 - 2026-10-08

### Nuevos módulos y nombres
- **Mensualidades**: historial por estudiante + grilla general del año, edición de mensualidad (monto/vencimiento/período/estado/anular) con auditoría. Matrículas queda con 3 pestañas.
- **Cobros** (antes Pagos): pestañas Historial, Registrar cobro, Mensualidades (botón Cobrar que precarga) y Campeonatos (división → monto); comprobante opcional.
- **Egresos** por grupos (Profesores/Operativos/Campeonatos) con subtotal + recordatorio de pago a profesores según frecuencia configurable (mensual/quincenal/personalizada).
- **Uniformes**: pestaña Productos (precios, tallas/stock, +talla) y tallas con stock en formularios de Uniformes y Matrícula (checkbox + venta inmediata en talla).

### Importación y datos
- Bundle 150 = cuota 120 + uniforme 30 (mensualidad siempre 120); 70 solo = venta sin cuota; resto inusual → revisión; `es_nuevo` persistido sin regalo doble.
- Origen de cuota (manual/generada/importada) visible en grilla y tarjetas.
- Tarifas con vigencia desde/hasta; aviso de recordatorio de profesores por responsable.

### Rendimiento y actualización
- Carga perezosa (Año, Ventas/Ganancias de Tienda, tabs de Cobros), paginación en Estudiantes, N+1 eliminados (Uniformes, becas), mora 1 vez/hora, avisos con caché, topes anti-instancias.
- Actualizador automático: descarga → aplica al cerrar → relanza; anti-downgrade; diálogo redimensionable.
- Auditoría completa: cuotas, tarifas, categorías, tallas, importaciones directas, rotación de backups y avisos omitidos.
- Suite 642/642 en verde.

## v1.2.0-rc — Consolidación (detalle técnico previo 2026-10-01)

> Decisión: se consolida sobre la arquitectura vigente (Fase 6b). Los módulos
> Campeonatos/Profesores con lógica propia y la migración de datos quedan como
> épicas siguientes. Nada existente se rompe: 629/629 tests.

### Nuevas Funcionalidades
- **Filtro de período unificado** (`widgets/periodo_filter.py`): año + checkboxes
  por mes + toggle de orden (más nuevo / más antiguo). Integrado en Pagos y
  Tienda → Ganancias.
- **Indicador de carga** (`widgets/loading_dialog.py`): helper síncrono
  `con_indicador_ocupado` cableado en Registrar de Pagos, Matrículas, Ventas y
  Uniformes. El helper asíncrono `ejecutar_con_loading` queda para flujos pesados futuros.
- **Tabla de compras** (`compra`): compras a proveedor con campo `proveedor`
  opcional y comprobante.
- **Origen de cuotas**: campo `origen` en tabla `cuota` (MANUAL/GENERADA/IMPORTADA).

### Cambios de UI (sin ruptura de datos)
- **Ventas**: combo de tipo solo UNIFORME/TIENDA; pestaña y código muerto de
  Campeonatos eliminados de la vista. El servicio sigue aceptando CAMPEONATO
  (lo usan importador, resumen y data histórica).
- **Tienda**: NO es Ventas. Alcance limitado a productos canal TIENDITA con
  uniformes excluidos (`UNIFORME-COM`, `CAMISETA-ENT`). Campeonatos vive en el
  módulo Campeonatos (menú FINANZAS).
- **Matrículas**: el formulario ya no vende uniforme al registrar (esa venta se
  hace en Ventas/Uniformes).
- **Pagos**: comprobante opcional (aviso naranja, ya no bloquea).
- **Sidebar**: se conservan Tiendita/Uniformes/Almacén y se añaden
  Campeonatos/Profesores/Compras.

### Correcciones
- **Grilla anual de matrículas**: crash `None.get("origen")` corregido; cada celda
  muestra origen (⚙=generada, ⬇=importada).
- **Tarifas dinámicas**: columnas `fecha_vigencia_desde/hasta` en `tarifa` +
  `obtener_vigente(tipo, fecha)`. Las cuotas futuras usan la tarifa vigente.
- **Importador**: el resto de celda bundled (ej. 150 = 120 + 30) detecta tipo de
  uniforme ENT/COM por texto en vez de asumir siempre COM.
- **Pagos**: `buscar_paginado` acepta `anio/meses/orden` (filtros del PeriodoFilter).
- **Filtros**: presets Completa/T1–T4/Elegir + desplegable de meses en Pagos,
  Ganancias, Ventas, Egresos, Uniformes y Estudiantes.
- **Updater**: flujo automático (descarga → aplica al salir → relanza),
  anti-downgrade garantizado, SSL con reintentos, diálogo scrollable.
- **Rendimiento Matrículas**: Año perezoso, becas en batch, timeout LAN,
  test de grilla adaptado.

### Migraciones de BD
- `cuota.origen TEXT DEFAULT 'MANUAL'`
- `tarifa.fecha_vigencia_desde TEXT`
- `tarifa.fecha_vigencia_hasta TEXT`
- Nueva tabla `compra`

### Separación vigente Tienda / Uniformes / Almacén

```
Tienda (SECRETARIA+ADMIN)  → solo canal TIENDITA, sin uniformes,
                             con balance/ganancia por mes y método (YAPE/EFECTIVO)
Uniformes (SECRETARIA+ADMIN)→ solo COM/ENT asociados a estudiantes
Almacén (solo ADMIN)       → movimientos, compras, stock; no vende
```

### Épicas v1.3.0 (ejecutadas en v1.2.0 final)
- **Mensualidades**: pestañas Cuotas/Año mudadas de Matrículas a módulo propio
  (Por estudiante + General), etiqueta "Mensualidad", edición manual de
  mensualidad (monto/vencimiento/periodo/estado/activo, ambos roles, auditoría).
- **Uniformes**: asegurador único `uniforme_service.asegurar_producto`, tab
  Productos (CRUD + tallas/stock), tallas en formularios con stock en vivo,
  venta con `id_variante` de punta a punta.
- **Tienda**: Ganancias con doble vista Por venta / Por producto + filtros
  producto/mes/método; `venta_service.editar_venta` (fecha/método/comprobante,
  sin tocar ítems/stock, con auditoría).
- **Importación**: bundle 150 = cuota 120 + uniforme 30 (mensualidad siempre
  120); 70 explícito = venta standalone sin cuota; resto ≠ 30 → revisión;
  `es_nuevo` persistido post-matrícula (sin regalo doble RN-051).

## v1.3.0 (épicas en curso) — Cobros, Egresos por pestañas, recordatorio profesores

- Sidebar "Pagos" → **"Cobros"** (solo etiqueta; permiso/tabla intactos).
- Cobros con pestañas Historial / Registrar cobro / **Mensualidades**
  (cuotas con saldo + botón Cobrar que precarga el formulario) /
  **Campeonatos** (división por tarifa → jala monto al cobro).
- Egresos con filtro Todos / Profesores / Operativos / Campeonatos + subtotal.
- Recordatorio de pago a profesores **sin tablas nuevas**: frecuencia
  MENSUAL/QUINCENAL/PERSONALIZADA en CONFIGURACION (migración idempotente),
  configurable en Configuración; aviso por responsable según último egreso
  PROFESOR, omitible como los demás avisos.
- Updater: log local-vs-remota para diagnosticar el diálogo fantasma.
- Auditoría: creación de tallas registra en log (editar cuota/venta ya lo hacían).
- Pendiente siguiente: Campeonatos con lógica propia + Profesores/Nómina
  (migración de datos incluida).

### Módulos (referencia)

```
ACADEMIA: Estudiantes, Matrículas (con Cuotas), Pagos/Cobros, Reportes
FINANZAS: Tiendita, Uniformes, Campeonatos, Egresos, Profesores, Reportes
ALMACÉN (solo ADMIN): Almacén, Compras
SISTEMA: Importar, Usuarios, Tarifas (con vigencia), Becas, Categorías, Auditoría, Configuración, Respaldo
```

## v1.1.0 - 2026-09-30

### Importacion masiva (Estudiantes/Tienda/Productos/Compras/Pagos/Uniformes/Historial)
- Autodeteccion por columnas distintivas + plantillas descargables por tipo.
- Wizard por pasos (Siguiente/Anterior sin saltos), mapeo auto con resumen, revision previa con opciones (omitir/provisional/corregir/actualizar/sin-beca/crear-beca) y bulk.
- Re-importe idempotente (actualiza por nombre/DNI, nunca duplica) + matricula para todos + beca automatica + tarifas 100/120 por era + INICIO (C.M=enero, vacio=15-may, manda primer pago).
- Historial XLSX: cuotas mensuales por monto, split 150 (120+uniforme), beca completa autopagada, retiros/reingresos, idempotencia.
- BECA/INICIO en Estudiantes; retiros con fecha (auto por 2 vacios + manual editable).
- CSV con autodeteccion de delimitador (, ; tab |).
- Flexibilidad v2: tarifas flexibles (ACADEMIA, CAMPEONATO, SERVICIO), tipos de uniforme configurables, becas múltiples por matrícula, conceptos flexibles (RN-052), dashboard 14 cards, 9 reportes Excel.

### Ventas, matricula e inventario
- Vista Uniformes separada (COM/ENT) + tipo de importacion Uniformes; Tiendita oculta uniformes.
- Matricula sin productos (-1/+1 fuera): checkbox es-nuevo editable + selector uniforme con pre-compra de stock.
- Cuota S/0 nace PAGADA; mensualidad neta (tarifa menos becas) visible; detalle de pagos por cuota; historial por alumno; grilla con ! pendiente y dialogo por celda.
- Tablas del dashboard paginadas.

### Correcciones
- Crash TclError al re-ejecutar importacion; resumen de mapeo con falsos faltantes.
- Cards estaticas (sin parpadeo) + clic reparado en dashboard; filtros estudiantes en 2 filas.
- Migracion: columnas antes que indices (BD legacy abren); tipo_uso legacy compat.
- Suite 629/629 en verde.

## v1.0.8 - 2026-09-22

### Refactorización v2 (plan `archivo/plan_refactorizacion_v2.md` ejecutado fases 0–8)
- Split Tiendita (secretaria) / Almacén (solo admin): módulos estancos por `canal`, Ventas dentro de Tiendita, guards en services.
- Precios Excel: Inscripción 150, Uniforme 70, Mensualidad 120 (editables en Tarifas); express lee tarifa; becas 1/2 (S/50) y COMPLETA (100%).
- Avisos por módulo (comprobantes pendientes, vencidas, stock bajo, sin apoderado) + Pendientes en Dashboard.
- Fechas editables en pagos, compras, ventas, movimientos y matrículas; comprobantes validados y centralizados.
- Matrícula sin camiseta visible (regalo RN-051 intacto); conceptos flexibles fuera del flujo.
- Tabla densa modo Excel en 6 módulos; dashboard por bloques; grilla anual de cuotas (X/ADELANTO); vocabulario COSTO TOTAL/X UNIDAD/COSTO VENTA.
- `pago.comprobante_path` persiste (antes se descartaba).

### Limpieza
- Sin código muerto (vistas legacy, helpers huérfanos); event_bus loggea handlers rotos.
- Logs resumidos (importar/CSV) y sin PII en guardado de estudiantes.
- Timers seguros: backup único, recargas diferidas con `winfo_exists`, reinicio cancelable.

## v1.0.7 - 2026-09-21

### Updater mejorado
- `comparar_versiones` tolerante: acepta `v`, espacios y sufijos (`1.0.7-beta`); ya no revienta con tags atípicos.
- Descarga truncada (bytes ≠ Content-Length) ahora falla con error claro y reintenta una vez (antes se aceptaba en silencio).
- Cancelar sí cancela: el diálogo pasa `debe_cancelar` y el hilo aborta, limpia el temporal y avisa.
- Estado del updater por fusión: ya no se pierden `rechazado_version` ni `setup_pendiente` al guardar.
- Extracción ZIP endurecida contra zip-slip (exige separador bajo la carpeta de la app).
- Limpieza de rama muerta en `verificar_y_mostrar`.

### Inventario UX (plan `archivo/plan_inventario_ux.md` ejecutado A→C→B→D)
- Búsquedas normalizadas (tildes/espacios, multi-campo) con debounce en Estudiantes (incl. carnet), Apoderados, Pagos, Matrículas y Productos; `utils/busqueda.py` nuevo.
- Paginados SQL reales en producto/pago/matrícula; combo de compra y movimiento cargados al abrir Inventario.
- Toggle Cards/Tabla modo Excel, filtro por categoría, stock solo-lectura al editar + nota de flujo.
- MiPerfil para todos los roles (clic en el usuario del sidebar); diálogo Categoría 360x520 scrolleable.
- Módulo `catalogos`: secretaria ve secciones 7–10 de Configuración; globales siguen ADMIN.

### Matrícula express con carnet de extranjería
- El express acepta DNI (8) o CARNET (9, solo números) con combo de tipo y validación por tipo.
- Etiquetas de buscadores y documentos unificadas a "documento".

### Correcciones
- Sin cambios de esquema: todo compatible con BD existentes (seed idempotente para `catalogos`).

## v1.0.6
- Guardar deriva rutas (fotos/comprobantes/backups junto a la BD) + Estado visible de BD/red.
- Ver `plan_accion_cierre.md` y releases anteriores en GitHub.

## v1.0.0 — Sistema Base (2026-08)

- CRUD Estudiantes, Apoderados, Matrículas
- Cuotas mensuales con mora
- Pagos (efectivo, YAPE, PLIN, transferencia)
- Ventas (uniformes, tienda)
- Inventario con stock
- Reportes básicos
- Roles ADMIN/SECRETARIA
- Auditoría
- Backups
