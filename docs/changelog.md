# Changelog — AcademiaFutbol

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
