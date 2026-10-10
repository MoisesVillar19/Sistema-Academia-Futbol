# 2026-09-05 — v2 reglas flexibles (RN-036..RN-050)

> **Fecha:** 2026-09-05 · **Estado:** entregado (v2, sept 2026)
> **Fuente completa:** `../cambios_RN_v2.md`
> **Base:** `../../sistema/reglas_negocio.md` RN-001..035 → nuevas RN-036..050
> **Índice:** `../TIMELINE.md`

## Qué cambió
- **Inscripción vs mensualidad separadas:** nuevos pagan inscripción (incluye 1 camiseta entrenamiento, descuenta stock, atómico); antiguos pagan mensualidad recurrente (diferible 2-3 meses → N cuotas).
- **Uniformes ampliables sin código:** `tipo_uniforme` CRUD ADMIN → `producto` (`precio_compra/venta`, `ganancia` en Service).
- **Descuentos configurables:** becas PORCENTAJE/MONTO_FIJO + `monto_pactado` (admite 0) + `permitir_multiples_becas`.
- **Egresos nuevos:** profesores/personal/campeonatos (tasas, arbitraje, viáticos parametrizados).
- **Fotos/comprobantes:** 1 foto alumno + foto comprobante por pago (OneDrive `fotos/`, `comprobantes/`).
- **Principio:** ningún precio hardcodeado; todo en `CONFIGURACION` vía `configuracion_service.obtener_valor()`, edición solo ADMIN.

## Impacto BD
- `tipo_uniforme`, `venta`+`detalle_venta`, `egreso`, `estudiante.foto_path`, `pago/venta.comprobante_path`. DDL solo en `database/create_db.py`.
