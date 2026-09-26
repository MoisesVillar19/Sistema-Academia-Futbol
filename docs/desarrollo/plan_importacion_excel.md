# Plan — Ganancias en Tiendita + Importación del Excel + Filtro Becados

> Estado: PLANIFICADO (documentado 2026-09-22, aún no ejecutado).
> Fuente: `INFORMACION ACADEMIA RONCALLI.xlsx` (NO versionado, ver `.gitignore`).
> CSVs fieles generados en `importacion/` (tampoco versionados) vía `tools/excel_a_csv.py`.
> Sin el importador, la única vía de carga masiva es manual por UI
> (los scripts SQL directos se desaconsejan: saltan validaciones y auditoría).

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
