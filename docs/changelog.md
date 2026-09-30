# Changelog — AcademiaFutbol

## v1.1.0 - 2026-09-30

### Importacion masiva (Estudiantes/Tienda/Productos/Compras/Pagos/Uniformes/Historial)
- Autodeteccion por columnas distintivas + plantillas descargables por tipo.
- Wizard por pasos (Siguiente/Anterior sin saltos), mapeo auto con resumen, revision previa con opciones (omitir/provisional/corregir/actualizar/sin-beca/crear-beca) y bulk.
- Re-importe idempotente (actualiza por nombre/DNI, nunca duplica) + matricula para todos + beca automatica + tarifas 100/120 por era + INICIO (C.M=enero, vacio=15-may, manda primer pago).
- Historial XLSX: cuotas mensuales por monto, split 150 (120+uniforme), beca completa autopagada, retiros/reingresos, idempotencia.
- BECA/INICIO en Estudiantes; retiros con fecha (auto por 2 vacios + manual editable).
- CSV con autodeteccion de delimitador (, ; tab |).

### Ventas, matricula e inventario
- Vista Uniformes separada (COM/ENT) + tipo de importacion Uniformes; Tiendita oculta uniformes.
- Matricula sin productos (-1/+1 fuera): checkbox es-nuevo editable + selector uniforme con pre-compra de stock.
- Cuota S/0 nace PAGADA; mensualidad neta (tarifa menos becas) visible; detalle de pagos por cuota; historial por alumno; grilla con ! pendiente y dialogo por celda.
- Tablas del dashboard paginadas.

### Correcciones
- Crash TclError al re-ejecutar importacion; resumen de mapeo con falsos faltantes.
- Cards estaticas (sin parpadeo) + clic reparado en dashboard; filtros estudiantes en 2 filas.
- Migracion: columnas antes que indices (BD legacy abren); tipo_uso legacy compat.
- Suite 629/629 en verde.

## v1.0.8 - 2026-09-22

### Refactorización v2 (plan `docs/desarrollo/plan_refactorizacion_v2.md` ejecutado fases 0–8)
- Split Tiendita (secretaria) / Almacén (solo admin): módulos estancos por `canal`, Ventas dentro de Tiendita, guards en services.
- Precios Excel: Inscripción 150, Uniforme 70, Mensualidad 120 (editables en Tarifas); express lee tarifa; becas 1/2 (S/50) y COMPLETA (100%).
- Avisos por módulo (comprobantes pendientes, vencidas, stock bajo, sin apoderado) + Pendientes en Dashboard.
- Fechas editables en pagos, compras, ventas, movimientos y matrículas; comprobantes validados y centralizados.
- Matrícula sin camiseta visible (regalo RN-051 intacto); conceptos flexibles fuera del flujo.
- Tabla densa modo Excel en 6 módulos; dashboard por bloques; grilla anual de cuotas (X/ADELANTO); vocabulario COSTO TOTAL/X UNIDAD/COSTO VENTA.
- `pago.comprobante_path` persiste (antes se descartaba).

### Limpieza
- Sin código muerto (vistas legacy, helpers huérfanos); event_bus loggea handlers rotos.
- Logs resumidos (importar/CSV) y sin PII en guardado de estudiantes.
- Timers seguros: backup único, recargas diferidas con `winfo_exists`, reinicio cancelable.

## v1.0.7 - 2026-09-21

### Updater mejorado
- `comparar_versiones` tolerante: acepta `v`, espacios y sufijos (`1.0.7-beta`); ya no revienta con tags atípicos.
- Descarga truncada (bytes ≠ Content-Length) ahora falla con error claro y reintenta una vez (antes se aceptaba en silencio).
- Cancelar sí cancela: el diálogo pasa `debe_cancelar` y el hilo aborta, limpia el temporal y avisa.
- Estado del updater por fusión: ya no se pierden `rechazado_version` ni `setup_pendiente` al guardar.
- Extracción ZIP endurecida contra zip-slip (exige separador bajo la carpeta de la app).
- Limpieza de rama muerta en `verificar_y_mostrar`.

### Inventario UX (plan `docs/desarrollo/plan_inventario_ux.md` ejecutado A→C→B→D)
- Búsquedas normalizadas (tildes/espacios, multi-campo) con debounce en Estudiantes (incl. carnet), Apoderados, Pagos, Matrículas y Productos; `utils/busqueda.py` nuevo.
- Paginados SQL reales en producto/pago/matrícula; combo de compra y movimiento cargados al abrir Inventario.
- Toggle Cards/Tabla modo Excel, filtro por categoría, stock solo-lectura al editar + nota de flujo.
- MiPerfil para todos los roles (clic en el usuario del sidebar); diálogo Categoría 360x520 scrolleable.
- Módulo `catalogos`: secretaria ve secciones 7–10 de Configuración; globales siguen ADMIN.

### Matrícula express con carnet de extranjería
- El express acepta DNI (8) o CARNET (9, solo números) con combo de tipo y validación por tipo.
- Etiquetas de buscadores y documentos unificadas a "documento".

### Correcciones
- Sin cambios de esquema: todo compatible con BD existentes (seed idempotente para `catalogos`).

## v1.0.6
- Guardar deriva rutas (fotos/comprobantes/backups junto a la BD) + Estado visible de BD/red.
- Ver `docs/desarrollo/plan_accion_cierre.md` y releases anteriores en GitHub.
