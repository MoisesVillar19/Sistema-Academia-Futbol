# 2026-08-02 — Diagnóstico de usabilidad

> **Fecha:** 2026-08-02 · **Estado:** diagnosticado (parte implementado después)
> **Fuente completa:** `../archivo/diagnostico_usabilidad.md`
> **Índice:** `../TIMELINE.md`

## Problemas detectados (PRO)
- **PRO-001:** IDs crudos en ComboBoxes (`matricula_view`, `pago_view`, `estudiante_view`).
- **PRO-002:** sin búsqueda en listados.
- **PRO-003:** diálogos básicos encadenados (`CTkInputDialog` uno por campo).
- **PRO-004:** sin marcar campos obligatorios.
- **PRO-005:** fechas en texto manual.

## Mejoras aplicadas entonces (MEJORA-001..004)
- ComboBoxes limpios, búsqueda en listados, diálogos mejorados, obligatorios señalados.

## Quedó sugerido (se retoma el 2026-09-21)
- Búsquedas normalizadas con debounce, paginados SQL, modo tabla denso → ver `2026-09-21_inventario-ux-ejecutado.md`.
