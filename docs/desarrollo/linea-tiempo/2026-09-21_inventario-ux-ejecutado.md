# 2026-09-21 — Inventario UX + búsquedas (EJECUTADO)

> **Fecha:** 2026-09-21 · **Estado:** EJECUTADO (bloques A → C → B → D, commit por bloque, suite 419 en verde)
> **Fuente completa:** `../archivo/plan_inventario_ux.md`
> **Índice:** `../TIMELINE.md`

## Qué se hizo
- **Búsquedas normalizadas** (tildes/espacios, multi-campo) con debounce en Estudiantes (incl. carnet), Apoderados, Pagos, Matrículas, Productos (`utils/busqueda.py` nuevo).
- **Paginados SQL reales** en producto/pago/matrícula; combos de compra/movimiento al abrir Inventario.
- **Inventario modo Excel:** toggle Cards/Tabla, filtro por categoría, stock solo-lectura al editar + nota de flujo (el stock se mueve solo en Compras/Movimiento).
- **Perfil y config:** MiPerfil para todos los roles; `catalogos` (secretaria ve secciones 7-10, globales siguen ADMIN); diálogo Categoría scrolleable.
- **Updater y express:** `comparar_versiones` tolerante, descarga truncada con error claro, cancelar sí cancela, ZIP anti zip-slip; matrícula express acepta DNI (8) o CARNET (9).

## Sin cambio de esquema (compatible con BD existentes).
