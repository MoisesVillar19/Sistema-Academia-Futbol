# Changelog — AcademiaFutbol

## v1.2.0 — Consolidación (sin ruptura)

**Fecha:** 2026-10-01

> Decisión: se consolida sobre la arquitectura vigente (Fase 6b). Los módulos
> Campeonatos/Profesores con lógica propia y la migración de datos quedan como
> épicas v1.3.0. Nada existente se rompe: 629/629 tests.

### Nuevas Funcionalidades

- **Filtro de período unificado** (`widgets/periodo_filter.py`): año + checkboxes
  por mes + toggle de orden (más nuevo / más antiguo). Integrado en Pagos y
  Tienda → Ganancias.
- **Indicador de carga** (`widgets/loading_dialog.py`): helper síncrono
  `con_indicador_ocupado` cableado en Registrar de Pagos, Matrículas, Ventas y
  Uniformes. La ventana muestra "Guardando…" en vez de parecer colgada. El helper
  asíncrono `ejecutar_con_loading` queda disponible para flujos pesados futuros.
- **Tabla de compras** (`compra`): compras a proveedor con campo `proveedor`
  opcional y comprobante.
- **Origen de cuotas**: campo `origen` en tabla `cuota` (MANUAL/GENERADA/IMPORTADA).

### Cambios de UI (sin ruptura de datos)

- **Ventas**: combo de tipo solo UNIFORME/TIENDA; pestaña y código muerto de
  Campeonatos eliminados de la vista. El servicio sigue aceptando CAMPEONATO
  (lo usan importador, resumen y data histórica).
- **Tienda**: NO es Ventas. Alcance limitado a productos canal TIENDITA con
  uniformes excluidos (`UNIFORME-COM`, `CAMISETA-ENT`). Campeonatos tampoco va
  en Tienda: vive en el módulo Campeonatos (menú FINANZAS).
- **Matrículas**: el formulario ya no vende uniforme al registrar (esa venta se
  hace en Ventas/Uniformes).
- **Pagos**: comprobante opcional (aviso naranja, ya no bloquea).
- **Sidebar**: se conservan Tiendita/Uniformes/Almacén y se añaden
  Campeonatos/Profesores/Compras.

### Correcciones

- **Grilla anual de matrículas**: crash `None.get("origen")` corregido; cada celda
  muestra origen (⚙=generada, ⬇=importada). Explica cuotas en diciembre con datos
  importados hasta septiembre (cadena automática RN-014).
- **Tarifas dinámicas**: columnas `fecha_vigencia_desde/hasta` en `tarifa` +
  `obtener_vigente(tipo, fecha)`. Las cuotas futuras usan la tarifa vigente.
- **Importador**: el resto de celda bundled (ej. 150 = 120 + 30) detecta tipo de
  uniforme ENT/COM por texto en vez de asumir siempre COM.
- **Pagos**: `buscar_paginado` acepta `anio/meses/orden` (filtros del PeriodoFilter).

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

### Épicas v1.3.0 (ejecutadas)

- **Mensualidades**: pestañas Cuotas/Año mudadas de Matrículas a módulo propio
  (Por estudiante + General), etiqueta "Mensualidad", edición manual de
  mensualidad (monto/vencimiento/periodo/estado/activo, ambos roles, auditoría),
  navegación con preselección desde Matrículas y avisos (`abrir_modulo`).
- **Uniformes**: asegurador único `uniforme_service.asegurar_producto` (antes
  triplicado, misma autocreación), tab Productos (CRUD + tallas/stock),
  tallas en formularios de Uniformes y Matrícula (checkbox + stock en vivo),
  venta con `id_variante` de punta a punta.
- **Tienda**: Ganancias con doble vista Por venta / Por producto + filtros
  producto/mes/método; `venta_service.editar_venta` (fecha/método/comprobante,
  sin tocar ítems/stock, con auditoría).
- **Importación**: bundle 150 = cuota 120 + uniforme 30 (mensualidad siempre
  120); 70 explícito = venta standalone sin cuota; resto ≠ 30 → revisión;
  `es_nuevo` persistido post-matrícula (sin regalo doble RN-051).
- **Filtros**: presets Completa/T1–T4/Elegir + desplegable de meses en Pagos,
  Ganancias, Ventas, Egresos, Uniformes y Estudiantes.
- **Updater**: flujo automático (descarga → aplica al salir → relanza),
  anti-downgrade garantizado, SSL con reintentos, diálogo scrollable.
- **Rendimiento Matrículas**: Año perezoso, becas en batch, timeout LAN,
  test de grilla adaptado.

Pendiente v1.4.0: Campeonatos con lógica propia + Profesores/Nómina
(migración de datos incluida).

## v1.3.0 (en curso) — Cobros, Egresos por pestañas, recordatorio profesores

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

### Módulos Reorganizados

```
ACADEMIA
├── Estudiantes
├── Matrículas (con Cuotas)
├── Pagos (Cuotas, Inscripción, Conceptos, Historial)
└── Reportes

FINANZAS
├── Tiendita (productos TIENDITA, sin uniformes, con Ganancias)
├── Uniformes (COM/ENT por estudiante)
├── Campeonatos (nuevo módulo base; lógica completa en v1.3.0)
├── Egresos (Operación)
├── Profesores (nuevo módulo base; nómina en v1.3.0)
└── Reportes

ALMACÉN (solo ADMIN)
├── Almacén (movimientos, stock)
└── Compras (con proveedor)

SISTEMA
├── Importar
├── Usuarios
├── Tarifas (con vigencia)
├── Becas
├── Categorías
├── Auditoría
├── Configuración
└── Respaldo
```

---

## v1.1.0 — Importación Masiva y Flexibilidad

**Fecha:** 2026-09

- Importación masiva CSV/Excel (estudiantes, pagos, cuotas, historial)
- Tarifas flexibles (ACADEMIA, CAMPEONATO, SERVICIO)
- Tipos de uniforme configurables
- Becas múltiples por matrícula
- Conceptos flexibles (RN-052)
- Dashboard con 14 cards
- 9 reportes Excel

---

## v1.0.0 — Sistema Base

**Fecha:** 2026-08

- CRUD Estudiantes, Apoderados, Matrículas
- Cuotas mensuales con mora
- Pagos (efectivo, YAPE, PLIN, transferencia)
- Ventas (uniformes, tienda)
- Inventario con stock
- Reportes básicos
- Roles ADMIN/SECRETARIA
- Auditoría
- Backups
