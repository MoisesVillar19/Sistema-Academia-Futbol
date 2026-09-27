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
