# Manual de Flujos y Casuísticas — Academia Deportiva

> Recorre **todos** los flujos del sistema paso a paso, con sus casuísticas
> (variaciones) y el resultado esperado en cada una. Sirve como guía de uso
> y como matriz de pruebas manuales antes de cada release.
>
> Convenciones: ADMIN = acceso total. SECRETARIA = todo excepto Usuarios,
> Tarifas, Auditoría, Configuración, Restaurar/Rotar backups e Importar.

---

## F0. Roles y accesos

| Módulo | ADMIN | SECRETARIA |
|---|---|---|
| Dashboard, Estudiantes, Matrículas, Pagos, Ventas, Egresos, Inventario, Reportes, Respaldo (manual) | ✅ | ✅ |
| Importar, Usuarios, Tarifas, Auditoría, Configuración, Restaurar/Rotar | ✅ | ❌ |

- Solo existen `ADMIN` y `SECRETARIA`. Los roles viejos `CAJA`/`INVENTARIO`
  se migran solos a SECRETARIA al arrancar; el combo de Usuarios ya no los ofrece.
- Primer login `admin/admin123` obliga a cambiar contraseña.
- PIN de emergencia (`roncalli2026` por defecto, configurable): restablece
  cualquier contraseña desde el login. Guárdalo fuera del sistema.

---

## F1. Estudiantes (ACADEMIA → Estudiantes)

**Pestañas:** Estudiantes (lista) · Registrar/Editar · Apoderados.

### F1.1 Registrar estudiante nuevo real
1. `+ Nuevo` → Tipo Doc (DNI 8 / CARNET 9) + documento.
2. Nombres, apellidos, fecha nacimiento, sexo, dirección, teléfono, correo.
3. Foto (opcional, ≤2MB jpg/png).
4. **🆕 ¿Es REALMENTE nuevo? → MARCAR** solo si es alta nueva real.
5. Guardar → aparece en lista Activos.

### F1.2 Carga masiva de existentes
- Mismo formulario con el check **DESMARCADO** → no contarán en
  Dashboard › Nuevos del Mes ni regalarán camiseta.

### F1.3 Casuísticas
| Caso | Resultado esperado |
|---|---|
| DNI duplicado | Error "ya registrado" |
| DNI 7 dígitos / Carnet 8 | Error de longitud |
| Editar (clic Editar) | Formulario precargado; `es_nuevo` bloqueado (no se puede cambiar después) |
| Retirar (ACTIVO/REINGRESANTE) | Estado RETIRADO, pide confirmación |
| Reingreso (RETIRADO) | Estado REINGRESANTE; la **próxima matrícula crea registro nuevo** (no reactiva la anterior) |
| Desactivar (solo ADMIN) | Soft delete (`activo=0`), desaparece de listas |
| Apoderados | Tab Apoderados: asociar con principal único (al asociar otro principal, el anterior pasa a secundario); no se puede desasociar al principal si es el único |
| Filtros Todos/Activos/Retirados/Reingresantes + búsqueda | Lista filtra en vivo (con debounce 300ms) |
| ▾ Ver detalle en tarjeta | Dirección, teléfono, correo, nacimiento, edad, sexo + apoderados |

---

## F2. Matrículas (ACADEMIA → Matrículas)

**Pestañas:** Matrículas (lista) · Registrar · Cuotas.

### F2.1 Nueva matrícula estándar
1. `+ Nueva` → Estudiante (al elegirlo, sugiere tarifa por edad).
2. Tarifa (solo tipo ACADEMIA) **o** Concepto flexible (si eliges concepto, su monto manda y trae ítems incluidos) **o** Monto pactado libre (puede ser 0 = gratuito).
3. Día vencimiento (1-31), Beca opcional, Pago diferido (Ahora/2/3 meses).
4. Productos adicionales ±1 (bloqueados si es estudiante nuevo con regalo).
5. Confirmar en el diálogo de desglose → se crea matrícula + cuota(s) PENDIENTE.

### F2.2 Casuísticas
| Caso | Resultado esperado |
|---|---|
| Estudiante ya con matrícula ACTIVA | Error, no duplica |
| Concepto elegido | Monto = concepto; stock de cada ítem descuenta; precede a tarifa/monto |
| Beca PORCENTAJE/MONTO_FIJO | Descuenta del monto base (múltiples solo si Config lo permite) |
| Diferir 2-3 meses | Genera 2-3 cuotas en lugar de 1 |
| Estudiante nuevo (🆕) en 1ª matrícula, no reingreso | Venta INSCRIPCION S/0 + **-1 Camiseta Entrenamiento** de stock + movimiento SALIDA. Sin stock → error y rollback total |
| Producto sin stock | Error "Stock insuficiente (disp: N)", no crea nada |
| Reingresante | Matrícula NUEVA (la anterior queda histórica) |
| Ver Cuotas | Salta a tab Cuotas con la matrícula seleccionada |

---

## F3. Pagos (FINANZAS → Pagos)

**Pestañas:** Pagos (historial) · Registrar Pago · Morosos.

### F3.1 Registrar pago
1. `+ Nuevo Pago` → Estudiante → Cuota pendiente (muestra saldo).
2. Monto (puede ser **parcial**), método (EFECTIVO/YAPE/PLIN/TRANSFERENCIA).
3. Comprobante foto **obligatorio** si YAPE/PLIN/TRANSFERENCIA.
4. Registrar → cuota pasa a PARCIAL (resta saldo) o PAGADO (saldo 0).

### F3.2 Casuísticas
| Caso | Resultado esperado |
|---|---|
| Pago parcial | Cuota PARCIAL, saldo = total − pagado; admite más pagos |
| Pago que cubre saldo | Cuota PAGADO |
| Monto > saldo | Error, no permite sobrepago |
| YAPE sin comprobante | Error, lo exige |
| Filtros fecha + búsqueda recibo/DNI/método | Historial filtra; Morosos lista VENCIDAS conActualizar |
| ▾ Ver detalle | IDs, cuota/período, observación, comprobante, usuario, fecha |

---

## F4. Ventas (FINANZAS → Ventas)

Tipos: `UNIFORME` · `TIENDA` · `CAMPEONATO` · `INSCRIPCION` (esta última solo automática).

### F4.1 Venta UNIFORME/TIENDA
1. Producto (valida stock, con variante/talla si aplica) + cantidad.
2. Método + comprobante si no es efectivo + ID estudiante opcional.
3. Registrar → descuenta stock (global + almacén + FIFO lotes) + movimiento SALIDA.

### F4.2 Venta CAMPEONATO (por tarifa)
1. Tipo CAMPEONATO → aparece combo **Tarifa campeonato** (divisiones de la categoría Campeonatos).
2. Al elegir tarifa se prellena el monto (**editable**).
3. Registrar **sin producto obligatorio** → venta con `id_tarifa` para trazabilidad.

### F4.3 Casuísticas
| Caso | Resultado esperado |
|---|---|
| Stock insuficiente (incl. variante) | Error con disponible, no vende |
| Monto CAMPEONATO ≤ 0 o sin tarifa | Error |
| YAPE/PLIN/TRANSFERENCIA sin comprobante | Aviso RN-042 (según configuración de obligatoriedad) |
| Recibo duplicado | Reintenta con nuevo número (3 intentos) |
| ▾ Ver detalle | Producto/cantidad/precio, método, estudiante, comprobante |

---

## F5. Egresos (FINANZAS → Egresos)

Conceptos: `PROFESOR` · `PERSONAL` · `CAMPEONATO_FIJO` · `ARBITRAJE` · `VIATICOS`.

### F5.1 Registrar
1. Concepto → si es PROFESOR/ARBITRAJE y el monto está vacío, se **prellena** con el default de Configuración (**editable**: cada profesor/árbitro cobra distinto).
2. Monto > 0, fecha, responsable, observación, comprobante opcional (≤5MB).
3. Guardar. Eliminar: solo ADMIN.

### F5.2 Casuísticas
| Caso | Resultado esperado |
|---|---|
| Monto vacío + concepto PROFESOR | Sugiere pago_profesor; se puede cambiar |
| Monto ≤ 0 / concepto inválido | Error de validación |
| Comprobante > 5MB | Rechazado |
| SECRETARIA | Puede registrar/editar (v2.1), no eliminar |

---

## F6. Inventario (ALMACÉN → Inventario)

**Pestañas:** Productos · Categorías · Registrar Producto · Movimiento · Historial.

### F6.1 Casuísticas
| Caso | Resultado esperado |
|---|---|
| Registrar producto | Código auto si se deja vacío; precio compra/venta; tipo uso VENTA (se vende) o CONSUMO_INTERNO (no sale en ventas) |
| Movimiento ENTRADA/SALIDA/AJUSTE | Actualiza stock + historial con motivo y usuario |
| Salida > stock | Rechazada |
| Stock ≤ mínimo | Alerta en Dashboard › Stock Bajo (rojo) |
| Variante/talla | Ventas descuentan variante + stock_almacén; valorizado = stock × precio_venta |
| ▾ Ver detalle | Compra/venta, ganancia, valorizado, categoría, uniforme, estado stock |

---

## F7. Tarifas y categorías (SISTEMA → Tarifas, solo ADMIN)

- **Categorías con tipo:** `ACADEMIA` (exige rango de edad, sugiere tarifa por edad en matrícula), `CAMPEONATO` y `SERVICIO` (sin edad: divisiones, inscripción, reingreso, uniforme base, tasa, arbitraje).
- **Tarifas:** nombre + monto + categoría + descripción. `▾ Ver detalle` muestra uso (n° matrículas activas que la usan).
- Regla: tarifa con matrículas activas **no se elimina** (solo desactiva).
- Las 5 tarifas migradas (Inscripción, Reingreso, Uniforme base, Tasa base, Arbitraje) nacen de tus Precios Flexibles anteriores; se editan como cualquier tarifa.

## F8. Conceptos flexibles (Configuración → sección 9, solo ADMIN)

Bundles con título + precio + ítems incluidos (ej. "Matrícula Promocional S/150 incluye Camiseta"). Al elegirlo en matrícula: su monto precede a tarifa/monto pactado y descuenta stock de cada ítem. Tipos: INSCRIPCION/MENSUALIDAD/REINGRESO/PROMOCION/CAMPEONATO/OTRO.

## F9. Becas

- Se **asignan** en la matrícula (combo Beca): PORCENTAJE o MONTO_FIJO.
- Configuración › Cuotas y Becas define si se permiten **múltiples** por matrícula.
- Reporte de becas activas en Reportes › Excel.
- *Nota:* no hay CRUD visual de becas (se gestionan por BD/seed); si necesitas crear nuevas avísame y agrego la UI.

---

## F6b. Compras a proveedor (ALMACÉN → Inventario → Registrar Compra)

1. Producto + cantidad (uds) + monto total pagado + método (Yape/Efectivo).
2. Suma stock y guarda monto+método en el movimiento (alimenta Compras y Ganancias).
3. Al crear producto: empaque (Unidad/Caja x12/Caja x100/Personalizado) +
   cantidad por caja + precio total + venta unitaria; la app calcula costo
   unitario y ganancia sola. Unidad fuerza cantidad 1.

## F2b. Matrícula rápida (ACADEMIA → Matrículas → Rápida)

1. Toggle NUEVO (default, S/120 editable, incluye uniforme) o ANTIGUO (monto libre obligatorio, sin uniforme).
2. Nombres + apellidos + DNI 8 + método Yape/Efectivo (+ comprobante si Yape).
3. Guardar y Matricular: crea/usa estudiante, matrícula (tipo guardado),
   cobra primera cuota. Todo atómico. Apoderado queda pendiente (aviso).

## F10. Dashboard (PANEL → Dashboard)

15 cards clickeables (toda la tarjeta responde). Cada detalle trae segmentado **Tabla/Gráfico/Ambos**:

| Card | Detalle |
|---|---|
| Alumnos Activos | Tabla DNI/Nombre/Edad/Teléfono |
| Cuotas Vencidas / Por Vencer | Tabla + saldos en rojo |
| Pagos Hoy / Ingresos Hoy | Tabla recibos + gráfico por transacción |
| Ingresos Mes | Gráfico por día + tabla |
| Monto Vencido / Por Vencer | Gráfico por estudiante + tabla |
| Stock Bajo | Tabla código/nombre/categoría/stocks |
| Ventas Mes | Gráficos por día + por tipo + tabla |
| Egresos Mes | Gráficos por día + por concepto + tabla |
| Neto Mes | Resumen ingresos (pagos+ventas) − egresos |
| Nuevos Mes | Gráfico por día + tabla (**solo `es_nuevo=1`**; la carga masiva desmarcada no contamina) |
| Antiguos / Matrículas Mes | Gráficos por día + por tarifa + tabla con columna **Condición (🆕 Nuevo/Antiguo)** |
| MoM Ingresos | **Comparativa real**: barras actual vs anterior + tabla día a día con diferencia + % delta |
| Compras/Ventas/Ganancias (mes) | 4 cards Yape/Efectivo + Ganancia Total; tablas y gráficos por día/tipo |

- [ ] Compras con método + dashboard dinero cuadra; matrícula rápida NUEVO/ANTIGUO con comprobante Yape

---

## F11. Reportes (ANÁLISIS → Reportes)

6 reportes a Excel (elige rango de fechas y carpeta):
morosos · pagos por fecha · ingresos mensuales · alumnos por categoría ·
inventario · becas activas. El archivo se genera con openpyxl y se confirma la ruta.

## F12. Importar (SISTEMA → Importar, solo ADMIN)

1. Elegir archivo CSV/XLSX + hoja.
2. Mapear columnas del archivo → campos del sistema (sugerencia automática; `(No importar)` para ignorar).
3. Previsualizar → Importar. Filas inválidas se reportan sin tumbar las válidas.

## F13. Configuración (SISTEMA → Configuración, solo ADMIN)

| Sección | Qué hace |
|---|---|
| 1. Información General | Nombre/dirección/teléfono/correo → aparecen en reportes |
| 2. Precios y Tarifas | Explica que los cobros viven en Tarifas (sin campos editables) |
| 3. Mora y Vencimientos | `mora_habilitada` + `porcentaje_mora`: al vencer la cuota aplica recargo sobre saldo |
| 4. Cuotas y Becas | `dias_por_vencer` (alerta Dashboard) + múltiples becas sí/no |
| 5. Actualizaciones | Versión/instalación + **Buscar actualizaciones ahora** (ignora las 24h) |
| 6. Respaldo y OneDrive | Automático sí/no, frecuencia (días), **ruta (con 📁 Examinar…)**, correo; lista backups con Verificar/Restaurar (PIN) y Rotar >30 días |
| 7. Categorías de Edad | CRUD categorías ACADEMIA (rango) + CAMPEONATO/SERVICIO (sin edad) |
| 8. Tipos de Uniforme | Catálogo que genera productos con stock |
| 9. Conceptos Flexibles | Bundles (ver F8) |

## F13b. Red LAN: 4 PCs con BD única (Modelo A+C)

- **Topología:** PC1 comparte `\\PC1\Academia\` (`academia.db`, fotos,
  comprobantes, backups). PC2–PC4 abren el **mismo archivo** (ver
  `docs/despliegue/despliegue_red.md`). Prohibido copiar la BD entre PCs.
- **Instalación:** `setup_red "\\PC1\Academia"` en cada PC (verifica
  lectura/escritura, escribe `config.ini`); primera apertura siembra **una**
  sola vez. En ZIP bloqueado funciona igual (sin admin).
- **Configuración → Respaldo:** campo Ruta BD + Examinar… + Probar conexión
  (muestra latencia y journal); línea de Estado (modo red/local, accesible,
  tamaño). Cambiar ruta exige reiniciar.
- **Cobros simultáneos:** el segundo espera (hasta 20s), no da error.
- **Servidor apagado:** la app avisa y no crea datos locales. Plan:
  encender servidor → Probar conexión → seguir; si se atendió manual,
  re-digitar con folios para no duplicar. Sin auto-merge a propósito.
- **Cierre:** siempre con X (apagado limpio); si no reabre, terminar
  `AcademiaFutbol.exe` en Administrador de tareas.

## F14. Respaldo (FINANZAS → Respaldo + Configuración)

- **Manual:** sidebar Respaldo → copia inmediata a la ruta (OneDrive ideal).
- **Fallback local:** si el destino central no es escribible (servidor apagado/sin permiso), la copia se guarda en la carpeta local y el mensaje lo dice ("copia LOCAL…"). Cada PC conserva así su última foto útil.
- **Automático:** cada 6h verifica; crea si pasaron `frecuencia_backup` días.
- **Restaurar:** solo ADMIN, pide PIN, sobreescribe `academia.db` → reiniciar app.
- **Rotar:** borra backups >30 días. **Verificar:** comprueba hash del archivo.

## F15. Actualizaciones (Configuración → Actualizaciones)

- Auto cada 24h al abrir (silencioso si no hay nada) + botón manual.
- **Program Files (Setup):** descarga instalador, avisa UAC (normal, es Microsoft), instala silencioso cerrando la app.
- **Portable (ZIP):** descarga con progreso MB/s + ETA, reemplaza conservando `config.ini`/BD/logs.
- Ventana muestra % y permite Cancelar/Reintentar con el motivo si falla.

## F16. Auditoría (SISTEMA → Auditoría, solo ADMIN, solo lectura)

Filtra por tabla/usuario/fecha. Registra INSERT/UPDATE/DESACTIVACIÓN + LOGINS + restauraciones. Ni ADMIN puede editarla.

---

## Anexo. Matriz de pruebas por release (checklist)

Marcar ✅/❌ en cada publicación:

- [ ] Login admin/secretaria + cambio password obligatorio + PIN emergencia
- [ ] Estudiante nuevo (🆕, regala camiseta −1 stock) vs carga masiva (no contamina Nuevos)
- [ ] Retirar → Reingreso → matrícula nueva (no reactiva)
- [ ] Matrícula: tarifa / monto 0 / concepto bundle / beca % y monto / diferir 2-3 / sin stock → rollback
- [ ] Pago completo → PAGADO; parcial → PARCIAL + segundo pago; exceso → error; YAPE sin comprobante → error
- [ ] Venta UNIFORME sin stock → error; CAMPEONATO por tarifa sin items → OK con id_tarifa
- [ ] Egreso PROFESOR prellena y permite otro monto; eliminar solo ADMIN
- [ ] Tarifa con matrículas no se elimina; categoría CAMPEONATO sin edad OK
- [ ] Dashboard: 16 detalles abren (toggle Tabla/Gráfico), MoM compara, Matrículas muestra 🆕
- [ ] Reportes generan 6 Excel; Importar mapea e importa; Backup manual + restaurar con PIN
- [ ] SECRETARIA no ve Usuarios/Tarifas/Auditoría/Configuración/Importar/Restaurar
- [ ] Suite automatizada: `.\.venv\Scripts\python -m pytest tests/ -q` en verde
