# Línea de tiempo — Academia Deportiva

> Árbol de cambios ordenado por **fecha**, no por versión.
> Cada hito resume qué pasó; el detalle completo vive en `archivo/` o en el doc vigente enlazado.
> Fuente de verdad del sistema: `../sistema/` (ver `AGENTS.md`).

## Cómo leer

```text
TIMELINE.md (este índice cronológico)
 └── linea-tiempo/YYYY-MM-DD_hito.md (resumen 20-40 líneas)
      └── archivo/*.md o doc vigente (detalle completo, solo si lo necesitas)
```

## Hitos

| Fecha | Hito | Estado | Resumen | Detalle |
|---|---|---|---|---|
| 2026-08-01 | Sprints 1-10 + estabilización (base v1.0) | ejecutado | [ver](linea-tiempo/2026-08-01_sprints-7-10-estabilizacion.md) | `archivo/sprint7_estado.md`, `archivo/sprint10_plan.md`, `plan_sprints.md` |
| 2026-08-02 | Diagnóstico de usabilidad | diagnosticado | [ver](linea-tiempo/2026-08-02_diagnostico-usabilidad.md) | `archivo/diagnostico_usabilidad.md` |
| 2026-08-05 | Retroalimentación por fases | documentado | [ver](linea-tiempo/2026-08-05_retroalimentacion.md) | `archivo/plan_implementacion.md` |
| 2026-09-05 | v2 reglas flexibles RN-036..050 | entregado | [ver](linea-tiempo/2026-09-05_v2-reglas-flexibles.md) | `cambios_RN_v2.md` |
| 2026-09-06 | v2.1 + cierre + deuda + inventario escalable | diseño | [ver](linea-tiempo/2026-09-06_dayanna-v2.1-cierre-deuda.md) | `plan_dayanna_v2.1.md`, `plan_accion_cierre.md`, `plan_deuda_tecnica.md`, `plan_inventario_escalable.md` |
| 2026-09-11/14 | Red LAN (diseño + evaluación) | evaluado | [ver](linea-tiempo/2026-09-11_red-lan.md) | `plan_red_lan.md`, `red_lan_evaluacion.md` |
| 2026-09-21 | Inventario UX + búsquedas | EJECUTADO | [ver](linea-tiempo/2026-09-21_inventario-ux-ejecutado.md) | `archivo/plan_inventario_ux.md` |
| 2026-09-22 | Refactorización v2 Tiendita/Almacén | EJECUTADO | [ver](linea-tiempo/2026-09-22_refactorizacion-v2-ejecutado.md) | `archivo/plan_refactorizacion_v2.md` |
| 2026-09-22/30 | Importación Excel + ganancias | EJECUTADO | [ver](linea-tiempo/2026-09-26_importacion-excel-ejecutado.md) | `archivo/plan_importacion_excel.md` |
| 2026-09-30 | v1.1.0 importación masiva | release 629/629 | [ver](linea-tiempo/2026-09-30_v1.1-importacion-masiva.md) | `changelog.md` |
| 2026-10-08 | v1.2.0 consolidación | release 642/642 | [ver](linea-tiempo/2026-10-08_v1.2-consolidacion.md) | `changelog.md` |
| 2026-10-10 | v1.2.1 hotfix uniformes N tipos | release 662/662 | [ver](linea-tiempo/2026-10-10_v1.2.1-uniformes-n-tipos.md) | `changelog.md`, `tests/test_uniformes_n_tipos.py` |

## Vigentes (no son historia)

- `roadmap.md` — hacia dónde va el producto.
- `plan_sprints.md` — cómo se trabaja por sprints.
- `changelog.md` — qué trae cada release (canónico; `../changelog.md` solo redirige aquí).
- `plan_red_lan.md` / `red_lan_evaluacion.md` — referencia operativa de red.
- `cambios_RN_v2.md`, `plan_dayanna_v2.1.md`, `plan_accion_cierre.md`, `plan_deuda_tecnica.md`, `plan_inventario_escalable.md` — diseño vigente hasta que se ejecuten o se descarten.

## Agregar un hito nuevo

1. Crear `linea-tiempo/YYYY-MM-DD_slug.md` con el formato de los existentes (`Fecha / Estado / Fuente / Qué / Impacto`).
2. Añadir la fila en la tabla de arriba.
3. Si el doc fuente queda superado o ejecutado, moverlo a `archivo/` con `git mv` y añadirle el header `> **ARCHIVADO…**`.
