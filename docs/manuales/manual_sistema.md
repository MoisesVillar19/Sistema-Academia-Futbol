# Manual del Sistema — Academia Deportiva v1.2.0

> Guía de uso diario para administradores y secretaría. Instalación y
> bloqueos: ver `guia_instalacion.md`. Paso a paso con casos:
> ver `manual_flujos.md`.

---

## 1. Qué es y cómo trabajan las 4 PCs

El programa se instala en cada PC, pero todas abren la **misma base de datos**
ubicada en la PC principal (carpeta compartida en red local). Lo que cobra
una PC lo ven las demás al instante. Reglas de oro:

- **Nunca copies** el archivo `academia.db` entre PCs.
- Si la principal está apagada, el programa avisa y no deja operar
  (no crea datos locales silenciosos).
- Cada PC guarda respaldos automáticos; con frecuencia de 1 día siempre hay
  copia fresca.

## 2. Roles: qué puede cada uno

| Módulo | ADMIN | SECRETARIA |
|---|---|---|
| Dashboard, Estudiantes, Matrículas, Mensualidades, Cobros, Tienda, Uniformes, Campeonatos (cobro), Egresos, Reportes, Respaldo manual | Sí | Sí |
| Almacén, Usuarios, Tarifas, Auditoría, Configuración, Importar, Restaurar/Rotar | Sí | No |

- Solo existen ADMIN y SECRETARIA. El ADMIN puede ajustar qué módulos ve
  SECRETARIA en **Usuarios → Permisos por rol** (ADMIN siempre ve todo).
- Primer acceso: usuario `admin`, contraseña `admin123` (te obliga a cambiarla).
- Guarda el **PIN de emergencia** fuera del sistema: restablece contraseñas.

## 3. Módulos (uso diario)

**Dashboard.** Tarjetas resumen; clic en cualquiera para ver tabla y
gráfico (interruptor Tabla/Gráfico/Ambos). La tarjeta MoM compara el mes
actual contra el anterior. Botón Volver para regresar.

**Estudiantes.** Lista con filtros y buscador (paginada de 50 en 50); cada
tarjeta se expande con contacto y apoderados. Al registrar, el check
**"¿Es REALMENTE nuevo?"** solo se marca en altas nuevas reales (regala
camiseta y cuenta en Nuevos del Mes); en carga masiva de existentes va
**desmarcado**. Retirar, reingresar (crea matrícula nueva, no reactiva) y
desactivar (solo ADMIN).

**Matrículas.** Registrar elige estudiante (sugiere tarifa por edad),
tarifa o monto libre, beca opcional y diferido. El check **Incluye uniforme**
muestra tipo (Entrenamiento/Competencia) y **talla con stock**; al confirmar
registra la venta del uniforme en esa talla. La pestaña **Rápida** matricula
y cobra en un solo paso.

**Mensualidades.** Historial de cuotas por alumno (**Por estudiante**, con
orden Más reciente/antiguo) y grilla **General** del año estilo Excel
(X = cancelado, S/ = adelanto, ! = pendiente/vencido, ⚙ = generada,
⬇ = importada; clic en celda = detalle). Cada tarjeta tiene botón
**Editar** para corregir monto, vencimiento, período, estado o anular
(queda en auditoría).

**Cobros (antes Pagos).** Pestañas:
- **Historial**: todo lo cobrado, con filtro de año, meses y orden.
- **Registrar cobro**: estudiante → cuota pendiente → monto (acepta
  parciales) → método. Comprobante **opcional** (si falta, queda pendiente).
- **Mensualidades**: cuotas con saldo y botón **Cobrar aquí** (precarga el
  formulario). Inscripciones y reingresos se cobran aquí (son cuotas).
- **Campeonatos**: división (tarifa) → jala el monto → registra el cobro.
- **Morosos**: vencidas.

**Tienda.** Solo productos de consumo (sin uniformes ni campeonatos).
Pestañas Productos, Registrar, Compras, Ventas y **Ganancias** con doble
vista: **Por venta** (cada venta suelta) y **Por producto** (agrupado del
mes), con filtros de producto, mes/año y método. Cada venta se puede
**Editar** (fecha, método, comprobante; ítems y stock no se tocan).

**Uniformes.** Ventas COM (competencia) y ENT (entrenamiento) con talla y
stock visible; pestaña **Productos** para ver precios, stock por talla,
editar precio y agregar tallas. Las compras de stock se hacen en Almacén.

**Egresos.** Pestañas por grupo: **Profesores** (monto libre por
responsable), **Operativos** (personal, viáticos), **Campeonatos**
(arbitraje y fijos por división) e **Historial**, con subtotal por grupo.
El sistema **recuerda** el pago mensual a cada profesor según la frecuencia
configurada (mensual, quincenal o personalizada en días). Eliminar: ADMIN.

**Almacén (ADMIN).** Productos con stock, compras a proveedor (con campo
proveedor opcional), movimientos de entrada/salida/ajuste con motivo e
historial, alerta de stock bajo, variantes por talla.

**Tarifas.** Precios de cobro: mensualidades por edad (con vigencia
desde/hasta), inscripción, reingreso, divisiones de campeonato. Pestaña
**Becas** para crear descuentos por porcentaje o monto fijo.

**Reportes.** Reportes a Excel (morosos, pagos por fecha, ingresos
mensuales, alumnos por categoría, inventario, becas, balance de tienda):
elige fechas y carpeta.

**Importar (ADMIN).** Carga masiva desde CSV/Excel con mapeo de columnas y
previsualización. Reglas del historial: celda 150 = matrícula de nuevo
(cuota 120 + uniforme 30); 70 solo = uniforme aparte sin cuota; retiros
automáticos con 2+ meses vacíos (todo queda en el reporte de importación).

**Configuración (ADMIN).** Datos de la academia, mora, frecuencia de pago
a profesores (mensual/quincenal/personalizada en días), actualizaciones,
respaldos (con Probar conexión y Examinar carpetas), categorías, tipos de
uniforme, conceptos flexibles.

**Respaldo.** Botón manual en el menú + automático según frecuencia.
Restaurar pide PIN y exige que las demás PCs cierren el programa.

**Auditoría (ADMIN, solo lectura).** Quién hizo qué y cuándo, con nombre de
usuario; filtros por tabla, usuario y fecha; exporta a Excel. Registra
altas, ediciones, anular/reactivar y rotación de backups.

**Actualizaciones.** Al haber versión nueva, descarga en segundo plano y
ofrece **Actualizar y reiniciar**: cierra la app, aplica (sin tocar BD ni
configuración) y reabre sola. En Program Files pide permiso de
administrador (normal). Forzar desde Configuración.

## 4. Rutina diaria sugerida

1. Abrir y verificar que entra sin errores (si dice que no hay red, encender la principal).
2. Cobrar y registrar como siempre; el comprobante es opcional pero recomendable.
3. Atender los avisos (vencidas, pago a profesores, stock bajo, comprobantes).
4. Fin de jornada: revisar Dashboard (vencidas, neto, stock bajo).
5. Semanal: verificar que existan backups recientes en Configuración.

## 5. Si algo sale mal (resumen)

| Síntoma | Qué hacer |
|---|---|
| No accede a la base de datos | Encender la principal, revisar red y recurso compartido |
| App no reabre | Terminar `AcademiaFutbol.exe` en Administrador de tareas |
| Bloqueo de Windows/antivirus | Ver `guia_instalacion.md` §7 (SmartScreen, exclusión, ZIP) |
| Dato borrado o corrupto | Restaurar backup con PIN (ADMIN, demás PCs cerradas) |
| Olvidó su contraseña | ADMIN la restablece, o PIN de emergencia en el login |
| Dato mal pasado (cuota/venta) | Editar desde Mensualidades o Ganancias (queda en auditoría) |

> Flujos detallados con casuísticas: `manual_flujos.md`.
> Matriz de pruebas por release: anexo de `manual_flujos.md`.
