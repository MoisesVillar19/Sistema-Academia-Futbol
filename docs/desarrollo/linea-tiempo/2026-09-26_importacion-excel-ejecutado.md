# 2026-09-22/30 — Importación Excel + ganancias Tiendita (EJECUTADO)

> **Fechas:** 2026-09-22/26 (A+B+C+D) + rondas hasta 2026-09-30 · **Estado:** EJECUTADO
> **Fuente completa:** `../archivo/plan_importacion_excel.md`
> **Fuente operativa (no versionada):** `INFORMACION ACADEMIA RONCALLI.xlsx` + CSVs en `importacion/`
> **Índice:** `../TIMELINE.md`

## Qué se hizo
- **Tab Ganancias en Tiendita** (réplica BALANCE + GANANCIA, fila TOTAL, filtros período/método).
- **Importador unificado:** autodetección por columnas + plantillas por tipo; wizard por pasos con mapeo auto, revisión previa con opciones (omitir/provisional/corregir/actualizar/sin-beca/crear-beca) y bulk.
- **Reglas de negocio del import:** re-importe idempotente (actualiza por nombre/DNI, nunca duplica) + matrícula para todos + beca automática + tarifas 100/120 por era + INICIO; bundle **150 = cuota 120 + uniforme 30** (mensualidad siempre 120); 70 explícito = venta standalone; resto inusual → revisión; `es_nuevo` persistido sin regalo doble (RN-051).
- **Historial XLSX:** cuotas por monto, split 150, beca completa autopagada, retiros/reingresos; BECA/INICIO en Estudiantes; retiros con fecha (auto por 2 vacíos + manual); CSV con sniff de delimitador; Uniformes COM/ENT + adelantos; cuota S/0 nace PAGADA.
- Sin el importador, la única vía de carga masiva es manual por UI (SQL directo desaconsejado: salta validaciones y auditoría).
