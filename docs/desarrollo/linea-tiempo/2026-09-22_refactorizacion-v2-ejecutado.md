# 2026-09-22 — Refactorización v2 Tiendita/Almacén (EJECUTADO)

> **Fecha:** 2026-09-22 · **Estado:** EJECUTADO (fases 0-8, commit por fase, suite 467 passed)
> **Fuente completa:** `../archivo/plan_refactorizacion_v2.md`
> **Índice:** `../TIMELINE.md`

## Decisiones (no reabrir salvo objeción)
- **2 inventarios estancos, 1 sola tabla:** `producto` se mantiene, discriminador `canal` (TIENDITA vs ALMACÉN). Ventas vive dentro de Tiendita; guards en services.

## Qué se hizo
- Precios Excel operativos: Inscripción 150, Uniforme 70, Mensualidad 120 (editables en Tarifas); express lee tarifa; becas 1/2 y COMPLETA.
- Avisos por módulo (comprobantes pendientes, vencidas, stock bajo, sin apoderado) + Pendientes en Dashboard.
- Fechas editables (pagos, compras, ventas, movimientos, matrículas); comprobantes validados y centralizados (`pago.comprobante_path` persiste).
- Matrícula sin camiseta visible (regalo RN-051 intacto); conceptos flexibles fuera del flujo; tabla densa modo Excel en 6 módulos; grilla anual de cuotas (X/ADELANTO).
- Limpieza: sin código muerto, `event_bus` loggea handlers rotos, logs sin PII, timers seguros.
