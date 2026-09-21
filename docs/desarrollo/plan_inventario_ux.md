# Plan Inventario UX + Búsquedas + Perfil + Config granular + Botones Guardar

> Estado: EJECUTADO 2026-09-21 (bloques A → C → B → D, commit por bloque,
> suite 419 tests en verde). Ver notas de ejecución al final.

## Decisiones tomadas

- Inventario: toggle Cards/Tabla + solo reorganizar flujo.
- Stock se mueve SOLO en Compras/Movimiento; Editar lo muestra solo-lectura.
- Catálogo = pestaña Productos + filtro por categoría.
- Config: secretaria ve secciones 7, 8, 9 y 10 (módulo `catalogos`).
- Perfil: diálogo Mi perfil para todos (datos + cambiar contraseña).

## Bloque A — Búsquedas (bugs confirmados)

A1. `inventario_view.py:9-21,380`: llamar `_cargar_productos_compra()` en
    `__init__` + `_productos_compra_map = {}` por defecto. Hoy el combo de
    compra queda en "Cargando..." hasta la primera compra (causa del
    "registra pero no lo encuentra").
A2. Nuevo `utils/busqueda.py`: normaliza (minúsculas, tildes, espacios),
    multi-campo, pensado para usarse con `Debouncer`. Aplicar en:
    Estudiantes (+carnet; hoy solo nombre+DNI y sin debounce),
    Apoderados, Pagos, Matrículas.
A3. `producto_repository.buscar_paginado()` real (nombre/código, SQL) —
    hoy cae a fallback silencioso en `inventario_view.py:477-498`.
- Tests: `tests/test_buscador.py` (matriz de normalización + multi-campo),
  compra combo cargado al instanciar, paginado producto con datos.

## Bloque B — Inventario modo Excel + flujo claro

B1. Toggle Cards/Tabla en `tab_productos`: tabla densa (código, nombre,
    categoría, stock, compra unit., venta, ganancia %, total inventario)
    con clic→mismo detalle expandible; respeta paginación y filtros.
B2. Filtro por categoría (segmentado Todas + cada una) junto al buscador.
B3. Regla de stock: en Editar, stock solo-lectura + nota/link a Compras;
    AJUSTE se mantiene (corrección con motivo obligatorio).
B4. Nota de objetivo en la pestaña: "El stock se mueve en Compras y
    Movimiento; aquí se consulta y se crean productos."
- Tests: toggle renderiza ambas vistas, filtro por categoría, stock
  solo-lectura presente, compra suma stock (ya cubierto en parte).

## Bloque C — Perfil y diálogos (incl. botón Guardar)

C1. `main.py:187-200`: propagar `<Button-1>` + cursor a los 3 labels hijos
    del `user_frame` (hoy el clic cae en labels sin binding y no pasa nada).
C2. Nuevo `MiPerfilDialog` (en `views/usuarios/usuario_view.py`): datos del
    usuario en sesión + cambiar contraseña (reusa `CambiarPasswordView`);
    para TODOS los roles. Usuarios sigue ADMIN.
C3. **Botones Guardar/Cancelar en diálogos** (auditoría 2026-09):
    - ✅ Crear/Editar Usuario, Tarifa, Beca, Categoría (lógica), Reporte,
      Updater, Egreso/Pago/etc. en pestaña: tienen ambos.
    - ❌ Diálogo Categoría: botones **cortados** (ventana 350x330 chica para
      el contenido con Tipo) → hacer contenido scrolleable + ventana 360x520.
    - ✅ Detalle Auditoría solo Cerrar (correcto: es solo lectura).
    - ✅ Cambiar Contraseña solo acción (correcto: flujo obligatorio).
    - Regla a futuro: todo diálogo de registro/edición usa
      `crear_boton_interactivo` (Guardar) + gris (Cancelar), nunca solo X.
- Tests: clic en hijo abre MiPerfil; MiPerfil cambia clave; categoría muestra
  ambos botones (smoke con geometría suficiente).

## Bloque D — Configuración granular

D1. `MODULOS_SISTEMA` += `catalogos`; migración seed (`INSERT OR IGNORE`).
D2. Menú Configuración visible si `configuracion|catalogos` (`main.py:268`).
D3. Render condicional por sección en `configuracion_view.py`: 7, 8, 9, 10
    con `catalogos`; resto con `configuracion`. Matriz UI lo lista con
    descripción.
D4. Tests: gates (secretaria con/sin `catalogos`, admin todo), render por
    sección, matriz guarda el módulo nuevo.

## Orden y criterios de cierre

A → C (bugs) → B → D. Commit por bloque + suite completa (>330 tests) en
verde antes de pasar al siguiente. Release ZIP solo al cerrar D.

## Notas de ejecución 2026-09-21 (desviaciones y conflictos detectados)

- A1: además del combo de compra, el combo de Movimiento tenía el mismo bug
  (vacío hasta el primer uso); se carga también al instanciar.
- A2: Pagos y Matrículas YA tenían Debouncer + intento de paginado (el plan
  los listaba como pendientes). Solo faltaban Estudiantes (sin debounce,
  sin normalizar) y Apoderados (sin buscador: se agregó en su pestaña).
  "Carnet" no es columna: vive en `persona.dni` con `tipo_documento=CARNET`,
  así que buscar por documento ya lo cubre (DNI 8 + carnet 9 dígitos).
- A3: `pago_repository.buscar_paginado` y `matricula_repository.buscar_paginado`
  NO existían (las vistas caían siempre al fallback); se implementaron junto
  al de producto. B2 extendió el de producto con `id_categoria_producto`.
- C2: no se reutilizó `CambiarPasswordView` como pedía el plan: su `_on_cerrar`
  hace `sys.exit` (flujo obligatorio de primer acceso); incrustarlo cerraría
  la app. `MiPerfilDialog` implementa el cambio vía `login_controller`.
- C1: el clic abre MiPerfil (diálogo, todos los roles), no Usuarios.
- B3 sin conflicto: `inventario_service.editar_producto` ya preservaba
  `stock_actual`; solo faltaba la UI solo-lectura.
- D1: `catalogos` se agregó al default de SECRETARIA (seed idempotente
  `INSERT OR IGNORE` lo migra en BD existentes). Quitarlo es reversible desde
  Usuarios → Permisos. `actualizar_configuracion`/backups/restaurar siguen
  exigiendo `configuracion` (ADMIN).
- D3: sección Apariencia ganó botón propio "Guardar apariencia" para que
  solo-catálogos pueda persistirla sin el Guardar global (oculto sin permiso).
