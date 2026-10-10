# 2026-08-01 — Sprints 1-10 + estabilización (base v1.0)

> **Fecha:** 2026-08-01 · **Estado:** ejecutado (base operativa v1.0)
> **Fuentes completas:** `../archivo/sprint7_estado.md`, `../archivo/sprint10_plan.md`, `../plan_sprints.md`
> **Índice:** `../TIMELINE.md`

## Qué fue
- Sprints 1-9: BD (`connection/create_db/seed/backup/restore`), seguridad (CRUD usuarios, login, roles ADMIN/SECRETARIA), gestión académica, matrículas/cuotas, pagos, inventario, reportes, configuración, auditoría.
- Sprint 10 (estabilización): tests con `pytest` + `:memory:` (`conftest.py`), unitarios (`validators/security/dates`), services (`cuota/estudiante`), integración (`login/matrículas`).

## Bugs críticos corregidos en el sprint
- `id_usuario=1` hardcodeado (17 ocurrencias) → sesión real.
- SHA-256 débil → `bcrypt`.
- Filtro "Retirados" erróneo.
- Violaciones de capas: `pago_view`/`estudiante_view` → Repository directo; `dashboard_service` → Database directo.

## Impacto
- Base v1.0 estable. Los pendientes medios/bajos de `sprint7_estado.md` (cursos, archivos faltantes, dependencias no usadas) pasan a deuda posterior.
