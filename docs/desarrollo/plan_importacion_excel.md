# Plan — Ganancias en Tiendita + Importación del Excel + Filtro Becados

> Estado: EJECUTADO 2026-09-22/26 (A+B+C+D). Ver §Ejecutado y §Nuevo plan abajo.
> Fuente: `INFORMACION ACADEMIA RONCALLI.xlsx` (NO versionado, ver `.gitignore`).
> CSVs fieles generados en `importacion/` (tampoco versionados) vía `tools/excel_a_csv.py`.
> Sin el importador, la única vía de carga masiva es manual por UI
> (los scripts SQL directos se desaconsejan: saltan validaciones y auditoría).

## Ejecutado (commits)

- A. Tab Ganancias en Tiendita (`87e7236`): balance estilo Excel + fila TOTAL,
  filtros período/método, `tests/test_balance_tienda.py`.
- B. Importar BALANCE (`21945f1`): `MAPEO_TIENDA`, flujo producto→compra→ventas,
  `tests/test_importar_tienda.py`.
- C. Filtro Becados (`48dce68`): `listar_becados`, segmento, badge, columna,
  marca en grilla, `tests/test_becados.py`.
- D. Historial (`8d33242` + `01cf656`): `services/importar_historial.py`
  (RELACIÓN/INGRESOS/VENTA, DNI `9000000N`, C.M→enero, 100/120 temporal,
  120–150 pre-SET = NUEVO, vacío = no viene), UI Historial + Revisión visible,
  `anular_cuota`, bypass RN-042 documentado para importados.
- Hover raíz (`8649690` + `d6c4835`): `aplicar_hover_borde` sin reflow en todas
  las cards + debounce 80ms en salida + `bind_click_unico` (1 disparo por
  serial; reemplaza la recursión con `add="+"` del dashboard y perfil).
- E1 autodetección (`a18ce10`), E2 revisión con opciones (`ee9c697`),
  E3 avisos navegables (`8f5e8c3`), E4a–c visuales (`e87a2a1`, `4abf36f`, `ff53e32`).
- Importar: flujo automático (Cargar→Revisión sin clickear tabs), bulk
  omitir/generar/corregir, segmentado eliminado (override solo si no detecta),
  restyle morado, preview paginado (`467322d`).
- Limpieza: `format_money` se conserva; resto de helpers muertos fuera.

## Auditoría temporales/memoria/rendimiento (2026-09-27)

- Temporales: `updater` limpia su `mkdtemp` en `finally`; logs rotan 5MB×5;
  backups rotan 30 días; sin fugas (vistas destruidas al navegar, matplotlib
  con `Figure` sin registro pyplot + `plt.close` al salir).
- Módulos independientes: cada vista carga bajo demanda con paginación 50;
  índices cubren FKs y fechas + 5 nuevos (`matricula.estudiante`,
  `cuota.matricula`, `detalle_pago.*`, `producto.canal`).
- Parpadeo: causa = ráfaga Enter/Leave por cruce padre↔hijo + redibujado Canvas
  + scrollbar auto-oculto que re-empaqueta + multi-disparo de clic.
  Fix en `utils/ui_helpers.py` (`aplicar_hover_borde` con debounce,
  `bind_click_unico` con serial). Nota: `bind()`-query y `event_generate`
  sintético no operan en CTk6 en este entorno; los tests usan ganchos
  `_hover_enter/_click_unico`.

## Nuevo plan — importación unificada + revisión con opciones + avisos navegables

> Decisiones: un solo Importar con autodetección (adiós 3 opciones fijas);
> revisión PREVIA con acciones por hallazgo (nada se adivina en silencio);
> avisos con botón Ir-al-origen + omitir/posponer (legado archivable).

### E1. Importación unificada (adiós segmentado fijo)
- Registro `TIPOS_IMPORTACION`: cada tipo = {nombre, detectar(headers|hojas),
  campos, validar, ejecutar}. Tipos: Estudiantes, Tienda, Historial (+Pagos,
  Productos, Compras a futuro sin tocar UI).
- Vista: subes archivo → cartel "Detecté: X" (o pregunta si ambiguo) →
  preview/mapeo/revisión según tipo. Historial exige XLSX con 3 hojas.
- Tests: detección por headers/hojas + registro extensible.

### E2. Revisión previa con opciones
- Botón Validar (en seco) → pantalla Revisión con hallazgos accionables:
  falta DNI → [generar provisional | omitir]; nombre ambiguo → (radio
  candidato | omitir); QUEDAN ≠ CANT−VEND → [corregir | omitir];
  fecha inválida → [usar hoy | omitir]. Resoluciones en `resoluciones={}`
  que el ejecutor respeta. Ejecutar bloqueado hasta resolver todo.
- Checkbox "DNI provisional" (Estudiantes): vacíos → `9000000N` + aviso.
- Tests por hallazgo y resolución.

### E3. Avisos navegables (legado)
- Cada aviso lleva `origen` (tabla+id) y botón **Ir**: publica navegación
  (patrón `abrir_tarifas` en `main.py`) y abre el módulo filtrado en el registro
  (Pagos/Estudiantes/Tienda).
- Foto/comprobante pendiente: Ir abre edición con selector listo; al guardar
  el aviso se resuelve solo.
- **Omitir/Posponer** con motivo: archiva el aviso (no borra) para que lo
  revisado deje de molestar. Tabla `aviso_omitido` + tests.

### E4. Visuales pendientes (impacto)
Reportes a morado, Apoderados (tabla+badges+vacios), Morosos (tabla+pag),
Tarifas/Becas (tabla), Auditoría (tabla densa), preview Importar paginado.

## Decisiones tomadas

1. Mensualidad temporal: MAY–AGO = 100, SET–DIC = 120 (tarifa seed 120 = actual).
2. Montos 120/150 antes de septiembre = nuevos (matrícula + uniforme).
3. Fila verde (theme6) = beca `1/2 BECA`; fila celeste (theme7) = `BECA COMPLETA`.
4. `dd/C.M` = ese día de enero 2026; fecha `1900-01-07` se ignora (vacía).
5. Mes vacío = alumno que ya no viene (NO genera deuda ni cuota).
6. DNI provisional `90000001…` secuencial; se regulariza editando en Estudiantes.
7. Ganancia con costo vigente (igual que el dashboard).
8. YAPE/EFECTIVO del Excel = dos operaciones (una por método), columnas separadas.
9. Becado = cualquiera con `matricula_beca` activa, mostrando cuál (1/2 o completa).

## A. Tab Ganancias en Tiendita (réplica del BALANCE + GANANCIA)

Columnas: `PRODUCTOS | CANTIDAD | COSTO TOTAL | COSTO X UNIDAD | COSTO VENTA |
YAPE | EFECTIVO | CANTIDAD VENDIDO | QUEDAN | GANANCIA` + fila TOTAL.
Filtro de período (mes) y método (Todas/Yape/Efectivo).
Ganancia = vendidas × (costo venta − costo unitario vigente).

Cambios:
- `repositories/venta_repository.py`: `ventas_por_producto(fecha_inicio, fecha_fin)`
  (`detalle_venta JOIN venta JOIN producto GROUP BY producto`, split por método).
- `repositories/movimiento_inventario_repository.py`: `compras_por_producto(...)` igual.
- `services/reporte_service.py` o nuevo `balance_tienda(...)`: une ambas,
  calcula QUEDAN y GANANCIA.
- `views/tiendita/tiendita_view.py`: tab "Ganancias" con período + `crear_tabla_densa`.
- Tests: `tests/test_balance_tienda.py` (datos estilo Excel, split por método,
  fila TOTAL, filtro).

## B. Importar BALANCE (tienda)

Nuevo tipo "Tienda" en Importar (ADMIN, con mapeo + preview existentes):
- `MAPEO_TIENDA`: PRODUCTOS→nombre, CANTIDAD→cantidad, COSTO TOTAL→total,
  COSTO X UNIDAD→unitario, COSTO VENTA→venta, YAPE/EFECTIVO→montos por método,
  CANTIDAD VENDIDO→vendidas, QUEDAN→verificación (`CANTIDAD−VENDIDO`).
- Por fila: `crear_producto` (TIENDITA) → compra por método (fecha del lote,
  dos operaciones si hay ambos) → venta de VENDIDO repartida por método.
- Validación: números ≥ 0, QUEDAN coherente; nombres normalizados
  (CHETO/CHETOS) + reporte de revisión.
- Tests: `tests/test_importar_tienda.py`.

## C. Filtro Becados

- Backend: `listar_becados()` (JOIN `matricula` + `matricula_beca` + `beca`
  activas, con nombre de beca; sin N+1).
- UI Estudiantes: segmento "Becados" + badge `🎓 1/2 BECA` / `🎓 BECA COMPLETA`
  en cards + columna Beca en tabla + marca en grilla anual.
- Tests: `tests/test_becados.py`.

## D. Importador del sistema con datos del Excel (orden)

1. **BALANCE ×3** (crea productos; ver §B).
2. **RELACIÓN (55 alumnos)**: estudiante (DNI provisional) + matrícula
   (INICIO / C.M→enero / REIN=2da / TERMINÓ=retiro) + beca por color de fila
   + cuota+pago por celda marcada (100 MAY–AGO, 120 SET+, montos literales,
   método Y/EF, `P. dd/mm` = fecha; 120–150 pre-SET = express NUEVO).
   Vacíos no generan cuota. `JACOBO` (sin INICIO ni marcas) → revisión.
3. **INGRESOS (14 nuevos)**: express NUEVO + beca 1/2 si dice `S/50`.
4. **VENTA UNIFORME (~50)**: COM/ENT a 70 (método+fecha); ADELANTO → total +
   partes en observación; `YAPE/EF. ENTR.` → regalo S/0; `ENTREG. 2025` se omite.
- Todo atómico por fila, con preview, y **reporte final de revisión**
  (duplicados: dos IGNACIO FRANCO, MIKAEL ×2; nombres cortos entre hojas;
  discrepancias QUEDAN).
- Nuevo `MAPEO_*` por hoja + tests `tests/test_importar_excel.py`.
- Nombres se cruzan normalizados (mayúsculas, sin tildes); lo ambiguo NO se adivina.

## Ejecución propuesta

C (pequeño) → A (mediano) → B+D (mediano-grande), tests y commit por bloque,
suite verde al cierre.

## Ronda importación directa (2026-09-27, ejecutada)

- Flujo automático: Cargar → Revisión validada sin clickear tabs; wizard
  estricto por pasos; override de tipo solo si no detecta.
- Bulk estilo Windows: Omitir/Generar/Corregir para todos + banner de
  sugerencia + checkbox DNI provisional.
- Plantillas descargables (`services/importar_plantillas.py`): Estudiantes,
  Tienda (+Pagos/Productos/Compras a futuro sin tocar UI).
- Normalizador (`tools/normalizar_roncalli.py`): relee el XLSX y genera
  `importacion/normalizados/` con columnas de plantilla (MAYO fusionado,
  AGOSTO posicional, duplicados fusionados, QUEDAN recalculado). Los 4 CSVs
  validan limpio contra el importador.
- Productos reutilizados entre meses (no duplica).
- Mapeo visible (De→A + faltantes) + messagebox final siempre (éxito/parcial/error).
- Docs de esquema y auditorías previas en este mismo archivo.

## Dónde está cada cosa (índice)

- Flujos: `services/importar_service.py` (Estudiantes/Tienda),
  `services/importar_historial.py` (RELACIÓN/INGRESOS/VENTA),
  `services/importar_revision.py` (hallazgos+resoluciones),
  `services/importar_plantillas.py` (plantillas).
- UI: `views/importar/importar_view.py` (wizard, preview paginado, revisión,
  resultados+revisión manual). Permiso: `controllers/importar_controller.py`.
- Parsers: `utils/csv_parser.py`, `utils/excel_parser.py`.
- Datos (NO versionados): `INFORMACION ACADEMIA RONCALLI.xlsx` (raíz),
  `importacion/*.csv` (fieles), `importacion/normalizados/*.csv` (listos).
- Herramientas: `tools/excel_a_csv.py` (fiel), `tools/normalizar_roncalli.py`.
- Tests: `tests/test_importar*.py` (7 archivos).
- Precios/becas/grilla usados por el import: `services/matricula_service.py`,
  `services/cuota_service.py`, `views/matriculas/matricula_view.py` (tab Año).

## Nuevos tipos: Productos / Compras / Pagos (2026-09-29, ejecutado)

- **Productos** (catálogo, sin movimientos): `PRODUCTO, CATEGORIA, COSTO,
  PRECIO_VENTA`. Crea en canal TIENDITA con stock 0; existente en BD se
  informa sin cambios (como Tienda). Sin control de movimientos.
- **Compras** (entradas a proveedor): `PRODUCTO, CANTIDAD, COSTO TOTAL
  (o X UNIDAD × CANTIDAD), METODO (vacío=EFECTIVO), FECHA (vacía=hoy),
  CATEGORIA`. Crea el producto si no existe. Sin control de duplicados
  (varias compras del mismo producto son válidas).
- **Pagos** (cuotas): `DNI + PERIODO (AAAA-MM, acepta MM/AAAA) + MONTO
  (+ METODO/FECHA)`. Localiza la cuota del estudiante en ese periodo;
  `MONTO ≤ saldo`. `METODO vacío = EFECTIVO`; YAPE/PLIN/TRANSFERENCIA se
  importan con `permitir_sin_comprobante` (igual que el historial) y quedan
  visibles en avisos "comprobante pendiente" (RN-042). Mismo periodo en 2
  matrículas (reingreso) → `CUOTA_AMBIGUA` (omitir).
- **Regla columnas distintivas** (resuelve la ambigüedad PRODUCTOS):
  Tienda exige clave + señal de venta (`YAPE/EFECTIVO/VENDIDO/QUEDAN`);
  sin señal de venta, `PRODUCTOS+CANTIDAD+COSTO` = Compras (mismo resultado
  que Tienda sin ventas) y `PRODUCTO+PRECIO` sin cantidad = Productos.
  Pagos = `DNI+PERIODO+MONTO`; con `NOMBRES/APELLIDOS` extra → ambiguo
  (elegir tipo manual, el override aparece solo si no detecta).
- Wiring por registro: `TIPOS_IMPORTACION` (service) + `TIPOS_IMPORTACION`
  (controller) + `PLANTILLAS` + `revisar()`/`aplicar_resoluciones()`.
  La vista no tiene `if` por tipo (campos, obligatorios, plantilla,
  validar, ejecutar y revisión salen del registro).
- Tests: `test_importar_productos.py`, `test_importar_compras.py`,
  `test_importar_pagos.py` (21 tests) + `test_importar_detectar.py`
  actualizado (Tienda con set completo de venta; set sin venta = Compras).
- Índice: tipos en `services/importar_service.py` (`MAPEO_*`, `validar_*`,
  `importar_*`, `_detectar_*`, `_localizar_cuota`), revisión en
  `services/importar_revision.py`, plantillas en
  `services/importar_plantillas.py`, permiso/dispatch en
  `controllers/importar_controller.py`, UI en
  `views/importar/importar_view.py` (selector + nota + equivalencias).

## Estudiantes: BECA + INICIO + nav Siguiente (2026-09-29, ejecutado)

- **Navegación por pasos**: se quitó el salto auto Cargar→Revisión.
  `Siguiente →` en Selección (habilitado al cargar), Vista Previa y Mapeo
  (re-valida al avanzar); `← Anterior` para volver. La Revisión se
  pre-valida al cargar pero el usuario decide cuándo ir.
- **INICIO** (AAAA-MM-DD, vacío=hoy) = inicio de clases → `fecha_ingreso`
  del estudiante. `crear_estudiante` acepta `fecha_ingreso` (antes siempre hoy).
- **BECA** (nombre exacto, vacío=sin beca): crea **matrícula** (tarifa
  mensualidad ACADEMIA, si no la primera activa; `fecha_inicio`=INICIO o hoy;
  `dia_vencimiento`=día del INICIO) + asigna la beca, y **retrotrae la
  primera cuota al AAAA-MM del INICIO** (el motor genera mes actual; sin
  retroceso el inicio no anclaría vencimientos). Sin tarifa → solo
  estudiante + nota (no falla la fila). Beca inexistente → hallazgo
  `BECA_NO_EXISTE` con `Omitir fila` o `Sin beca (solo estudiante)`.
- Fix: el resumen de mapeo comparaba con mayúsculas mezcladas y marcaba
  "Faltan obligatorios" falsos (tu captura); ahora insensible a caso.
- Plantilla Estudiantes suma `BECA, INICIO`. Tests:
  `tests/test_importar_beca_inicio.py` (5 tests).

## Re-importe idempotente + matrícula para todos (2026-09-29, ejecutado)

- **Antes**: recargar duplicaba (provisionales nuevos cada vez) y solo
  creaba matrícula con BECA (45 vs 7 en carga real).
- **Ahora**: todo importado sale **matriculado** (INICIO=fecha_inicio,
  día de vencimiento=día del INICIO, primera cuota retrotraída al AAAA-MM).
  `Sin beca` (revisión) sigue entrando solo el estudiante.
- **YA_EXISTE** (Nombres+Apellidos normalizados): opciones `Actualizar
  datos` (default) u `Omitir`. Actualizar corrige persona (incluye cambio
  DNI provisional→real si está libre), fecha_ingreso y crea matrícula solo
  si no tiene activa; nunca duplica. Provisional no se inyecta en filas a
  actualizar (pre-escaneo en `aplicar_resoluciones`).
- `crear_estudiante` acepta `fecha_ingreso`; `_beca_de_fila`,
  `_nombres_de_fila`, `_buscar_estudiante_por_nombre`,
  `_actualizar_fila_existente`, `_importar_matricula_fila` en
  `services/importar_service.py`; `OPC_ACTUALIZAR` en revisión.
- Tests: `test_importar_beca_inicio.py` (7 tests: inicio+matrícula,
  beca, sin_beca, nav, actualizar sin duplicar, omitir).

## Crash re-ejecución + Actualizar en DNI + filtros visibles (2026-09-29)

- **Crash TclError al ejecutar 2 veces**: `label_resultados` vivía dentro
  del scroll y `_mostrar_resultados` lo destruía; la 2da ejecución
  crasheaba. Movido fuera del scroll + `_set_estado_resultados` con guard
  `winfo_exists`. Test doble ejecución en `test_importar_p0.py`.
- **DNI duplicado de la misma persona** (re-importe con DNIs): ofrece
  `Actualizar datos` además de Omitir; si el DNI es de otra persona, solo
  Omitir (no se puede robar DNI). El actualizar resuelve por nombre y el
  cambio de DNI valida que esté libre.
- **Bulk "Actualizar todos"** en Revisión (1 clic para re-importes de 55 filas).
- **Estudiantes**: filtros en 2 filas (estado+búsqueda / fechas+vista) para
  que el toggle Cards/Tabla siempre se vea en ventanas angostas.
  Test `tests/test_estudiantes_filtros.py`.

## Uniformes: COM/ENT + adelantos (2026-09-29, ejecutado)

- **Modelo del sistema** (convención del historial): ENT = entrenamiento →
  `CAMISETA-ENT` (venta UNIFORME); COM = competencia → `UNIFORME-COM`
  (venta TIENDA). Aranceles de campeonato (COM como cobro, sin prenda) van
  por Ventas CAMPEONATO por tarifa, fuera de este tipo.
- **Tipo Uniformes**: `DNI + TIPO (COM/ENT) + MONTO + FECHA (+ METODO)`.
  1 fila = 1 pago = 1 venta (adelanto y resto son 2 filas, una por mes).
  FECHA con solo mes → día 01 (regla del historial). Estudiante debe
  existir (DNI real). Stock auto: compra + venta atómicas; producto se
  crea por código si falta. `monto_total` explícito admite parciales.
- Detección `DNI+TIPO+MONTO` (no choca con Pagos ni Estudiantes).
- Tests: `tests/test_importar_uniformes.py` (7 tests).

## Mapeo UI sys-names + bulk claro + beca rgb en normalizador (2026-09-30)

- **Causa raíz del balance**: `_sugerir_mapeo` devolvía cabeceras
  (`PRODUCTOS→PRODUCTOS`) en vez de nombres sys (`→nombre`); los services
  no resolvían y Tienda fallaba entero por UI (a nivel service con
  `mapeo=None` sí pasaba, por eso los tests no lo veían). Ahora retorna sys
  usando el MAPEO del tipo + resumen sin falsos faltantes. Tests
  `test_importar_mapeo_ui.py` (3, incluye `;`).
- **Bulk claro**: `_aplicar_bulk` informa aplicables y cuántos "sin esa
  opción" (antes parecía no hacer nada; FALTA_NOMBRE solo admite Omitir:
  generar nombres inventados ensuciaría el catálogo).
- **Beca rgb en normalizador** (`tools/normalizar_roncalli.py::fill_beca`):
  verdes/celestes directos → 1/2 / COMPLETA (JAHZIEL salía vacío). Test
  `test_normalizar_beca.py`.
- Nota: montos 120/150/50 por mes y becas por color solo viajan en el XLSX
  historial (el CSV es 1 cuota a tarifa); re-correr CSV no los cambia.

## Escala central + tipo_uso + INICIO + tarifa-era + grilla + cuotas-alumno (2026-09-30)

- **F0 escala**: `cuota_service.ESCALA_MENSUALIDAD` ((2026-01→100, 2026-09→120))
  + `monto_mensualidad(periodo)`; historial y era la usan. Futuros
  incrementos = agregar entrada (las cuotas guardan su monto: lo histórico
  no cambia).
- **F1 tipo_uso**: `producto_repository.insertar` arma columnas dinámico y
  rellena legacy `tipo_uso` (VENTA si TIENDITA incl. uniformes, si no
  CONSUMO_INTERNO). Nada la lee (columna dormida). Test
  `test_producto_tipouso.py`.
- **F2 INICIO**: `FECHA_INICIO_DEFAULT = 2026-05-15` (vacío nunca es hoy);
  `C.M`→enero también en CSV (`_normalizar_inicio_csv`); caso Kenzo:
  INICIO posterior a pagos → manda el primer pago (historial + nota).
- **F3 tarifa-era**: genéricas 100/120 por era (preferencia por monto entre
  ACADEMIA); `_aplicar_tarifa_era` re-tariféa la activa en actualizar/adopt
  (cuotas intactas, rige futuras).
- **F4 grilla Año**: `!` gris pendiente / rojo vencido (X/S/ igual); clic en
  celda → diálogo con periodo, montos, estado, vencimiento y pagos.
  Tab Cuotas por alumno: combo por estudiante, grupos por matrícula
  (matrícula = primer pago que genera mensualidades), badge reingresante /
  retirado, detalle por cuota. Regla hallada: crear matrícula consume
  REINGRESANTE→ACTIVO (intencional, `matricula_service:141`).
- Tests: `test_matricula_cuotas_detalle.py` (3), paginación dashboard
  `test_dashboard_paginacion.py` (2).

## CSV sniff + crear-beca + adopt + retiros + paginación (2026-09-29)

- **Delimitador**: `parse_csv`/`obtener_columnas_csv` autodetectan `, ; tab |`
  (el Excel ES guarda con `;` y el balance fallaba entero). Tests
  `test_csv_delimitador.py` (3).
- **Crear beca**: `BECA_NO_EXISTE` suma opción/bulk "Crear beca"
  (MEDIA→MONTO_FIJO 50, COMPLETA→PORCENTAJE 100, con número→ese valor;
  `_inferir_beca`/`_crear_beca_inferida`, reusa si existe).
- **Historial adopta**: `_fila_relacion`/`importar_ingresos` reutilizan
  estudiante y matrícula activa (cobertura por meses pagados → "sin
  cambios"); reingreso automático si hay actividad nueva en retirado.
- **Retiros**: auto por 2+ meses vacíos (fecha = último día del último mes
  con pago); manual con fecha editable (default hoy);
  `estudiante_controller.registrar_retiro(..., fecha)`. VENCIDO = impago
  con fecha pasada (confirma interpretación).
- **Paginación dashboard**: `crear_tabla_cards(paginar=True)` + wrapper del
  dashboard (14 detalles); `test_dashboard_paginacion.py` (2).

## Historial gaps + vista Uniformes (2026-09-29, ejecutado)

- **Beca por color directo**: `_leer_hoja` ignoraba rellenos rgb; JAHZIEL
  (verde directo) quedaba en Beca —. Nueva `_fill_verde_celeste` (verde→
  1/2, celeste→completa) + sinónimos de texto en `_beca_id_por_nombre`
  (MEDIA/1-2→1/2 BECA; COMPLETA/ENTERA→BECA COMPLETA, cubre CSV).
- **Split 150** (`_fila_relacion`): celda > tarifa del mes (100/120) →
  cuota por tarifa + venta UNIFORME-COM (tipo TIENDA) por el resto
  (adelanto), misma fecha/método. 150 en SET = 120 + 30. Helpers
  `_pagar_con_partes` / `_venta_resto_uniforme`.
- **Beca completa autopagada**: meses INICIO→CULMINO (default marcas o
  ENE→DIC) sin cuota → `crear_cuota` + pago EFECTIVO con observación
  "Beca completa (sin cobro)" (suma a caja; identificable por obs.).
- **Sin duplicados**: `_adoptar_o_crear_cuota` reutiliza cuota activa sin
  pagos del periodo (auto-cuota y cadena RN-014; ajusta monto al histórico).
  La cadena RN-014 (pagar genera el mes siguiente) se adopta, no se duplica.
- **Idempotencia**: `_existe_estudiante` (match exacto) omite filas ya
  importadas en RELACIÓN e INGRESOS (nota en revisión).
- **Vista Uniformes** (`views/uniformes/`): entrada 🎽 en sidebar grupo
  ALMACÉN (permiso `uniformes`: SECRETARIA como Tiendita, ADMIN todo;
  seed idempotente lo otorga). Tabs: lista (UNIFORME + TIENDA con COM/ENT)
  y registro (reusa validación/ejecución del tipo Uniformes).
- Activo=0: `_localizar_cuota` (Pagos) ignora anuladas.
- Tests: `test_importar_historial_gaps.py` (5) + `test_uniformes_view.py` (4).
- Pre-existentes CORREGIDOS 2026-09-29 (suite 604/604):
  `test_migracion_canal_backfill_legacy` (+ nuevo
  `test_arranque_sobre_bd_legacy_sin_canal`): `create_tables()` creaba
  `idx_producto_canal` ANTES de migrar columnas → en BD legacy sin `canal`
  el arranque reventaba; ahora migran columnas primero. En el test se
  dropea el índice (simulación fiel de legacy).
  `test_toggle_egreso/venta`: constructor de card directo (el render auto
  va en modo Tabla densa con ▾, igual que los tests hermanos).
  `test_tiendita_tabs_y_filtro`: expectativa a 5 tabs (Ganancias).
  `test_importar_ui_historial.py`: faltaba mockear `showinfo` (el modal real
  colgaba la suite).

## Re-importe con beca + detalle cuota + tarifas auto + form matrícula (2026-09-29)

- **B1 beca automática en re-importe**: con matrícula activa y BECA válida
  no asignada → `asignar_beca` (recalcula pendientes) en vez de nota manual
  (CSV `_importar_matricula_fila` e historial `_backfill_beca` en skips de
  RELACIÓN/INGRESOS). Beca inválida → nota manual (se mantiene).
- **B2 detalle por cuota**: tab Cuotas de Matrículas con expandible de pagos
  (recibo/fecha/monto/método) vía `pago_service.obtener_detalles_por_cuota`
  + `matricula_controller.obtener_pagos_por_cuota`. Test
  `test_matricula_cuotas_detalle.py`.
- **B3 tarifas 100/120 auto**: `_tarifa_para_beca(inicio)` elige genérica por
  era (pre-SET 100, SET+ 120) y la crea (`Mensualidad {monto}`, primera
  categoría ACADEMIA) si falta. Tests en `test_importar_beca_inicio.py`.
- **B4 form matrícula sin productos**: fuera sección −1/+1 y su bus handler
  (service conserva `data["productos"]`, la UI no lo envía). Nuevo: checkbox
  es-nuevo (edita al estudiante: `actualizar_es_nuevo` + auditoría) y
  selector uniforme [Entrenamiento default, Competencia, Ninguno] →
  `venta_controller.registrar_venta_uniforme` (asegura producto + pre-compra;
  nunca bloquea por stock). Tests `test_matricula_form.py` (5).
- **B5 Tiendita sin uniformes**: `InventarioView._excluir_codigos` (default
  vacío) + `buscar_paginado(excluir_codigos)`; Tiendita excluye
  COM/ENT (listas y combos; Almacén intacto; Ganancias no se toca).
  Test `test_tiendita_sin_uniformes.py` (3).
- **Stock 0**: la venta bloquea (`Stock insuficiente`, nunca negativo); la
  compra suma. Import/Uniformes/matrícula pre-compran.
- **Avisos/Ir**: E3 intacto; `uniformes` agregado a rutas del bus.

## G1/G2 beca-cuota PAGADO + monto neto (2026-09-30)

- **G1**: `crear_cuota` con monto 0 nace PAGADA; `_recalcular` deja PAGADO
  si saldo 0 (antes PENDIENTE con ruido en Vencidas/grilla). Tests
  `test_cuota_cero_pagada.py` (3).
- **G2**: `buscar_paginado` trae `becas_info` (GROUP_CONCAT) +
  `monto_mensual` (pactado o tarifa menos becas); lista/detalle muestran
  "A pagar". Tests `test_matricula_monto_neto.py` (3).
- Suite: 629/629 en verde, sin ignores ni excludes.

## Propuesta: documentación por módulos (futura)

Hoy hay ~25 md sueltos en `docs/` (sistema/desarrollo/despliegue/testing/manuales).
Propuesta sin romper nada: mantener `docs/sistema/` (fuente de verdad) y crear
`docs/modulos/<modulo>.md` (estudiantes, pagos, matricula, tiendita, inventario,
ventas, egresos, tarifas, importar, dashboard, reportes, usuarios, configuracion,
auditoria) con: qué hace, reglas RN, flujos UI, seeds/tarifas, tests y releases
que lo tocaron. Los docs de desarrollo pasarían a `docs/historial/` como bitácora.
Ejecutarlo es 1 tarea de reordenamiento con índice en `docs/README.md`.
