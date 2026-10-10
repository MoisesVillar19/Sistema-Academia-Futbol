> **ARCHIVADO — documento histórico.** No usar como guía vigente. Resumen vigente en `../linea-tiempo/2026-08-05_retroalimentacion.md` · Índice: `../TIMELINE.md`.

# Documento de Implementación - Retroalimentación AcademiaFutbol

## Fecha: 2026-08-05

## Propósito

Este documento consolida toda la retroalimentación recibida, las consultas realizadas, las decisiones tomadas y el plan de implementación resultante. Sirve como referencia completa para la ejecución de las mejoras al sistema.

---

## Tabla de Contenidos

1. [Retroalimentación Original](#1-retroalimentación-original)
2. [Consultas y Respuestas](#2-consultas-y-respuestas)
3. [Problemas Identificados por Fase](#3-problemas-identificados-por-fase)
4. [Plan de Implementación](#4-plan-de-implementación)
5. [Cambios en Base de Datos](#5-cambios-en-base-de-datos)
6. [Orden de Ejecución](#6-orden-de-ejecución)
7. [Criterios de Aceptación](#7-criterios-de-aceptación)

---

## 1. Retroalimentación Original

### FASE 1: Configuración y Admin

| # | Problema | Descripción |
|---|----------|-------------|
| 1.1 | Perfil Admin | No se puede editar el perfil del admin (nombre, contraseña, teléfono, DNI) |
| 1.2 | Mora | No se entiende su alcance, cómo funciona, a qué tarifas afecta |
| 1.3 | Categorías | Botón guardar no funciona, editar no tiene guardar, desactivar elimina en vez de desactivar |
| 1.4 | Tarifas | Sin indicadores de obligatorio, fechas innecesarias, guardar datos incompletos, editar/desactivar no funcionan |

### FASE 2: Estudiantes y Apoderados

| # | Problema | Descripción |
|---|----------|-------------|
| 2.1 | Documentos | Solo acepta DNI, debería aceptar Carnet de Extranjería |
| 2.2 | Filtro Activos | Muestra retirados en la pestaña "Activos" |
| 2.3 | Reingresante | Confusión con matrícula, no permite retirar por segunda vez |
| 2.4 | Búsqueda | No hay búsqueda por DNI para editar estudiantes |
| 2.5 | Apoderados | Solo campo DNI, sin opciones de parentesco, sin campos de contacto, no se puede agregar apoderado |

### FASE 3: Matrículas y Cuotas

| # | Problema | Descripción |
|---|----------|-------------|
| 3.1 | Búsqueda | No se puede buscar por DNI en cuotas |
| 3.2 | Historial | No se ve historial de pagos en cuotas |
| 3.3 | Limpieza | Formulario no se limpia después de registrar |

### FASE 4 y 5: Pagos

| # | Problema | Descripción |
|---|----------|-------------|
| 4.1 | Confusión | El sistema fusiona monto de matrícula con cuotas mensuales |
| 4.2 | Pago | No se puede registrar pago |
| 4.3 | Fecha | Botón de fecha no funciona |

### FASE 6: Reportes y Dashboard

| # | Problema | Descripción |
|---|----------|-------------|
| 6.1 | Tarifas | No permite editar tarifas |
| 6.2 | Reportes | Sin filtro de periodo, falta lista de matriculados por periodo |
| 6.3 | Dashboard | Muestra S/0 cuando debería tener datos |

---

## 2. Consultas y Respuestas

### Consulta 1: Mora

**Pregunta:** ¿Deseas que la mora se calcule automáticamente o solo sea visual?

**Respuesta:** Debe poder ponerse de monto o un % según seleccionen. Cuando esté la opción de monto seleccionada, debería salir en la mensualidad.

**Decisión:** La mora se aplica al vencer la cuota. El admin puede configurar:
- Tipo: PORCENTAJE o MONTO FIJO
- Valor: porcentaje (%) o monto fijo (S/)

### Consulta 2: Matrícula vs Cuotas

**Pregunta:** ¿La matrícula es un pago único separado de las cuotas mensuales?

**Respuesta:** Matrícula es aparte a la cuota. Se da cuando es nuevo estudiante. Luego solo son mensualidades.

**Decisión:**
- **Matrícula:** Pago ÚNICO de inscripción (estudiantes nuevos)
- **Cuota:** Pago MENSUAL recurrente
- Al matricular, preguntar si se pagará AHORA o AL FINALIZAR (después de un mes)

### Consulta 3: Reingreso de Estudiantes

**Pregunta:** ¿Al reingresar, el estudiante DEBE crear nueva matrícula?

**Respuesta:** Sí, se debe hacer una nueva matrícula. (Pendiente de confirmación final)

**Decisión:** Asumir que se debe realizar matrícula para reingresante. En matrícula se puede poner monto libre.

### Consulta 4: Formato de Importación

**Pregunta:** ¿Qué formato prefieres para importar datos?

**Respuesta:** CSV y Excel (que permita ambos).

**Decisión:** Implementar soporte para CSV y XLSX con vista previa y mapeo de columnas.

### Consulta 5: Límite de Apoderados

**Pregunta:** ¿Cuántos apoderados máximo por estudiante?

**Respuesta:** Máximo 2 apoderados por estudiante.

**Decisión:** 
- 1 apoderado principal (obligatorio)
- 1 apoderado secundario (opcional)
- Debe haber la opción de seleccionar cuál es principal

---

## 3. Problemas Identificados por Fase

### 3.1 FASE 1: Configuración y Admin

#### 3.1.1 Perfil del Admin
- **Estado actual:** No existe vista de perfil
- **Problema:** El admin no puede editar su información personal
- **Solución:** Crear vista de perfil con edición de nombre, apellidos, teléfono, correo y contraseña

#### 3.1.2 Mora
- **Estado actual:** Solo configuración visual (ON/OFF y porcentaje)
- **Problema:** No hay lógica de cálculo, no se muestra en cuotas
- **Solución:** 
  - Agregar tipo de mora (PORCENTAJE/MONTO)
  - Agregar campo monto_mora en tabla cuota
  - Calcular al vencer la cuota
  - Mostrar desglose en vista de cuotas

#### 3.1.3 Categorías
- **Estado actual:** Diálogos sin botón guardar, desactivar elimina registro
- **Problemas:**
  - Nueva categoría: no cierra diálogo al guardar
  - Editar: no tiene botón guardar
  - Desactivar: usa DELETE en vez de soft delete
- **Solución:** 
  - Agregar botón "Guardar" en diálogos
  - Usar `activo=0` para desactivar

#### 3.1.4 Tarifas
- **Estado actual:** CRUD incompleto
- **Problemas:**
  - Sin indicadores de campos obligatorios
  - Campos de fecha innecesarios
  - Guarda datos incompletos
  - Editar/desactivar no funcionan
- **Solución:**
  - Agregar asteriscos (*) en campos obligatorios
  - Quitar campos fecha_inicio/fecha_fin
  - Implementar editar y desactivar

### 3.2 FASE 2: Estudiantes y Apoderados

#### 3.2.1 Documentos de Identidad
- **Estado actual:** Solo DNI (8 dígitos)
- **Problema:** No acepta Carnet de Extranjería
- **Solución:**
  - Agregar campo `tipo_documento` (DNI/CARNET)
  - DNI: 8 dígitos, CARNET: 9 dígitos
  - Actualizar validaciones

#### 3.2.2 Filtro de Activos
- **Estado actual:** Muestra todos los activos incluyendo retirados
- **Problema:** El filtro "Activos" no distingue entre ACTIVO y RETIRADO
- **Solución:** Filtrar `activo=1 AND estado='ACTIVO'`

#### 3.2.3 Estado Reingresante
- **Estado actual:** REINGRESANTE no muestra botón de retirar
- **Problema:** Confusión sobre si requiere nueva matrícula
- **Solución:** 
  - En estado REINGRESANTE, mostrar botón "Crear Matrícula"
  - Confirmar que se debe crear nueva matrícula

#### 3.2.4 Búsqueda para Editar
- **Estado actual:** No hay búsqueda
- **Problema:** No se puede cargar datos por DNI para editar
- **Solución:** Agregar campo de búsqueda por DNI o nombre

#### 3.2.5 Apoderados (CRÍTICO)
- **Estado actual:** Solo campo DNI, sin campos de contacto
- **Problemas:**
  - Solo acepta DNI (falta carnet)
  - Parentesco sin opciones predefinidas
  - Sin campos: nombre, apellido, teléfono, dirección
  - No se puede agregar apoderado
- **Solución:**
  - ComboBox para tipo documento
  - ComboBox parentesco: Madre, Padre, Hermano, Tutor, Otro
  - Agregar campos de contacto
  - Máximo 2 apoderados por estudiante

### 3.3 FASE 3: Matrículas y Cuotas

#### 3.3.1 Búsqueda en Cuotas
- **Estado actual:** ComboBox sin búsqueda
- **Problema:** No se puede buscar por DNI
- **Solución:** Agregar campo de búsqueda en ComboBox

#### 3.3.2 Historial de Pagos
- **Estado actual:** No se ve historial
- **Problema:** No hay forma de ver pagos asociados a una cuota
- **Solución:** Botón "Ver Pagos" en cada cuota

#### 3.3.3 Limpieza de Formulario
- **Estado actual:** No se limpia después de registrar
- **Problema:** Los campos quedan con datos anteriores
- **Solución:** Llamar `_limpiar_formulario()` después de guardar

### 3.4 FASE 4 y 5: Pagos (CRÍTICO)

#### 3.4.1 Confusión Matrícula vs Cuota
- **Estado actual:** El sistema fusiona ambos conceptos
- **Problema:** No se distingue entre pago de inscripción y pago mensual
- **Solución:**
  - **Matrícula:** Pago ÚNICO de inscripción (estudiantes nuevos)
  - **Cuota:** Pago MENSUAL recurrente
  - Separar visualmente en la interfaz

#### 3.4.2 Pago No Funciona
- **Estado actual:** No se puede registrar pago
- **Problema:** Flujo incompleto o validaciones incorrectas
- **Solución:** Revisar y corregir flujo completo

#### 3.4.3 Campo de Fecha
- **Estado actual:** Campo de texto manual
- **Problema:** Formato incorrecto, no funciona botón
- **Solución:** Usar fecha actual automática o date picker

### 3.5 FASE 6: Reportes y Dashboard

#### 3.5.1 Tarifas Editar
- **Estado actual:** Botón editar no funciona
- **Problema:** No hay implementación de edición
- **Solución:** Implementar función de edición en service y repository

#### 3.5.2 Reportes por Periodo
- **Estado actual:** Sin filtro de periodo
- **Problema:** No se puede filtrar por mes/año
- **Solución:**
  - Agregar selector de periodo
  - Nuevo reporte: "Matrículas por periodo"
  - Filtrar datos según periodo

#### 3.5.3 Dashboard S/0
- **Estado actual:** Muestra S/0
- **Problema:** Cálculos incorrectos o queries defectuosas
- **Solución:** Verificar queries y cálculos

---

## 4. Plan de Implementación

### 4.1 Importar Datos (ALTA PRIORIDAD)

**Archivos a crear:**
- `views/importar/importar_view.py`
- `controllers/importar_controller.py`
- `services/importar_service.py`
- `utils/csv_parser.py`
- `utils/excel_parser.py`

**Funcionalidad:**
1. Seleccionar archivo (CSV o Excel)
2. Vista previa de los datos (primeras 10 filas)
3. Mapeo de columnas a campos del sistema
4. Validación de datos (DNI único, campos obligatorios)
5. Importar con IDs generados automáticamente
6. Relacionar tablas entre sí

**Formato esperado:**
```csv
DNI,Nombres,Apellidos,Fecha_Nacimiento,Sexo,Telefono,Correo,Tipo_Documento,Parentesco_Apoderado,DNI_Apoderado
12345678,Juan,Pérez,2018-05-15,M,987654321,juan@email.com,DNI,Padre,87654321
```

### 4.2 Apoderados Completos

**Campos del apoderado:**
```
Tipo documento: [DNI | CARNET] (ComboBox, obligatorio)
Nro. documento: ____________ (obligatorio, 8-9 dígitos)
Nombres: ____________ (obligatorio)
Apellidos: ____________ (obligatorio)
Parentesco: [Madre | Padre | Hermano | Tutor | Otro] (ComboBox)
  └─ Si "Otro": campo de texto adicional
Teléfono: ____________ (opcional)
Dirección: ____________ (opcional)
¿Es principal? [Sí | No] (Radio button, obligatorio)
```

**Validaciones:**
- Máximo 2 apoderados por estudiante
- Siempre debe haber 1 principal
- El principal no se puede eliminar (solo cambiar)

### 4.3 DNI / Carnet de Extranjería

**Validación:**
- DNI: 8 dígitos numéricos
- CARNET: 9 dígitos numéricos

**Archivos a modificar:**
- `database/create_db.py`
- `models/persona.py`
- `utils/validators.py`
- `views/estudiantes/estudiante_view.py`

### 4.4 Mora (Monto o Porcentaje)

**Configuración:**
```
Habilitar Mora: [ON/OFF]
Tipo de Mora: [PORCENTAJE | MONTO] (ComboBox)
  └─ Si PORCENTAJE: [___]% 
  └─ Si MONTO: S/[___]
```

**Cálculo:**
```
Cuando cuota pasa a VENCIDA:
  Si tipo = PORCENTAJE:
    monto_mora = saldo * (porcentaje / 100)
  Si tipo = MONTO:
    monto_mora = monto_fijo

Saldo total = saldo + monto_mora
```

**Visualización:**
```
Cuota Enero 2026
  Monto original: S/100.00
  Mora (5%): S/5.00
  Saldo total: S/105.00
```

### 4.5 Categorías y Tarifas

**Categorías:**
- Diálogos con botón "Guardar"
- Desactivar usa `activo=0`

**Tarifas:**
```
Nombre * (obligatorio)
Categoría * (obligatorio, ComboBox)
Monto * (obligatorio, numérico)
Descripción (opcional)
Observaciones (opcional)
```

### 4.6 Estudiantes - Filtros y Búsqueda

**Filtro Activos:**
```python
# Actual (incorrecto)
estudiantes = estudiante_controller.listar_estudiantes(activo=1)

# Corregido
estudiantes = estudiante_controller.listar_estudiantes(activo=1, estado='ACTIVO')
```

**Búsqueda:**
- Campo de búsqueda por DNI o nombre
- Filtrado en tiempo real

### 4.7 Matrículas (CRÍTICO)

**Nuevos campos:**
```
Estudiante * (ComboBox)
Tarifa * (ComboBox, auto-seleccionada por edad)
Monto libre (opcional, sobreescribe tarifa)
Día vencimiento * (1-31)
Beca (opcional, ComboBox)

¿Cuándo se pagará la matrícula?
  ○ Ahora (pago inmediato)
  ○ Al finalizar (después de un mes)
```

**Flujo:**
```
1. Seleccionar estudiante
2. Auto-seleccionar tarifa por edad
3. Si monto libre: usar ese monto
4. Preguntar cuándo se pagará
5. Si "Ahora": registrar pago inmediato
6. Si "Al finalizar": crear cuota pendiente para el mes siguiente
7. Generar primera cuota mensual
```

**Validaciones:**
- Máximo 2 apoderados
- Debe tener apoderado principal
- Solo una matrícula activa por estudiante

### 4.8 Pagos (CRÍTICO)

**Flujo corregido:**
```
1. Seleccionar estudiante
2. Sistema muestra:
   - Matrícula (si está pendiente de pago)
   - Cuotas mensuales pendientes
3. Seleccionar qué pagar
4. Ingresar monto
5. Método de pago
6. Registrar
```

**Historial:**
- Botón "Ver Pagos" en cada cuota
- Lista de pagos asociados

### 4.9 Reportes por Periodo

**Mejoras:**
- Selector de periodo (mes/año)
- Nuevo reporte: "Matrículas por periodo"
- Filtrar datos según periodo

### 4.10 Dashboard S/0

**Verificar:**
- Query de ingresos por mes
- Cálculo de saldo vencido
- Cálculo de morosos

### 4.11 Perfil Admin

**Funcionalidad:**
- Editar nombre, apellidos, teléfono, correo
- Cambiar contraseña (requiere contraseña actual)
- DNI y username de solo lectura

---

## 5. Cambios en Base de Datos

### Script de Migración

```sql
-- ============================================
-- MIGRACIÓN: Retroalimentación AcademiaFutbol
-- Fecha: 2026-08-05
-- ============================================

-- 1. Persona: tipo documento
ALTER TABLE persona ADD COLUMN tipo_documento TEXT DEFAULT 'DNI';

-- 2. Apoderado: campos adicionales
ALTER TABLE apoderado ADD COLUMN tipo_documento TEXT DEFAULT 'DNI';
ALTER TABLE apoderado ADD COLUMN telefono TEXT;
ALTER TABLE apoderado ADD COLUMN direccion TEXT;

-- 3. Configuración: mora
ALTER TABLE configuracion ADD COLUMN tipo_mora TEXT DEFAULT 'PORCENTAJE';
ALTER TABLE configuracion ADD COLUMN monto_mora REAL DEFAULT 0;

-- 4. Cuota: mora
ALTER TABLE cuota ADD COLUMN monto_mora REAL DEFAULT 0;

-- 5. Matrícula: pago de matrícula
ALTER TABLE matricula ADD COLUMN pago_matricula TEXT DEFAULT 'AHORA';
ALTER TABLE matricula ADD COLUMN monto_matricula REAL DEFAULT 0;
```

### Script de Creación Actualizado

```sql
-- Tabla persona (actualizada)
CREATE TABLE IF NOT EXISTS persona (
    id_persona INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT UNIQUE NOT NULL,
    tipo_documento TEXT DEFAULT 'DNI',
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    fecha_nacimiento TEXT,
    sexo TEXT CHECK(sexo IN ('M', 'F')),
    direccion TEXT,
    telefono TEXT,
    correo TEXT,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT
);

-- Tabla apoderado (actualizada)
CREATE TABLE IF NOT EXISTS apoderado (
    id_apoderado INTEGER PRIMARY KEY AUTOINCREMENT,
    id_persona INTEGER UNIQUE NOT NULL,
    tipo_documento TEXT DEFAULT 'DNI',
    parentesco TEXT,
    ocupacion TEXT,
    telefono TEXT,
    direccion TEXT,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT,
    FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
);

-- Tabla configuracion (actualizada)
CREATE TABLE IF NOT EXISTS configuracion (
    id_configuracion INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_academia TEXT,
    direccion TEXT,
    telefono TEXT,
    correo TEXT,
    mora_habilitada INTEGER DEFAULT 0,
    tipo_mora TEXT DEFAULT 'PORCENTAJE',
    porcentaje_mora REAL DEFAULT 0,
    monto_mora REAL DEFAULT 0,
    dias_por_vencer INTEGER DEFAULT 3,
    permitir_multiples_becas INTEGER DEFAULT 1,
    backup_automatico INTEGER DEFAULT 1,
    frecuencia_backup INTEGER DEFAULT 7,
    ruta_backup TEXT DEFAULT 'backups/',
    correo_onedrive TEXT DEFAULT '',
    fecha_actualizacion TEXT
);

-- Tabla cuota (actualizada)
CREATE TABLE IF NOT EXISTS cuota (
    id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
    id_matricula INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    monto_total REAL NOT NULL,
    monto_pagado REAL DEFAULT 0,
    monto_mora REAL DEFAULT 0,
    saldo REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'VENCIDO')),
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_matricula) REFERENCES matricula(id_matricula)
);

-- Tabla matricula (actualizada)
CREATE TABLE IF NOT EXISTS matricula (
    id_matricula INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER NOT NULL,
    id_tarifa INTEGER NOT NULL,
    monto_pactado REAL,
    pago_matricula TEXT DEFAULT 'AHORA',
    monto_matricula REAL DEFAULT 0,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    dia_vencimiento INTEGER NOT NULL DEFAULT 1 CHECK(dia_vencimiento BETWEEN 1 AND 31),
    estado TEXT NOT NULL DEFAULT 'ACTIVO',
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_tarifa) REFERENCES tarifa(id_tarifa)
);
```

---

## 6. Orden de Ejecución

| Paso | Fase | Descripción | Archivos Principales | Dependencias |
|------|------|-------------|---------------------|--------------|
| 1 | DB | Actualizar esquema de BD | `create_db.py` | Ninguna |
| 2 | 1 | Importar datos (CSV/Excel) | Nuevos archivos | Paso 1 |
| 3 | 2 | Apoderados completos | `estudiante_view.py` | Paso 1 |
| 4 | 3 | DNI/Carnet | `validators.py`, `estudiante_view.py` | Paso 1 |
| 5 | 7 | Matrículas | `matricula_view.py`, `matricula_service.py` | Paso 3, 4 |
| 6 | 8 | Pagos | `pago_view.py`, `pago_service.py` | Paso 5 |
| 7 | 4 | Mora | `cuota_service.py`, `configuracion_view.py` | Paso 1 |
| 8 | 5 | Categorías y Tarifas | `configuracion_view.py`, `tarifa_view.py` | Ninguna |
| 9 | 6 | Estudiantes (filtro, búsqueda) | `estudiante_view.py` | Paso 4 |
| 10 | 9 | Reportes por periodo | `reporte_view.py` | Paso 6 |
| 11 | 10 | Dashboard S/0 | `dashboard_service.py` | Paso 6 |
| 12 | 11 | Perfil Admin | Nuevos archivos | Ninguna |

---

## 7. Criterios de Aceptación

### Importar Datos
- [ ] Soporta archivos CSV y XLSX
- [ ] Muestra vista previa de los datos
- [ ] Permite mapear columnas a campos
- [ ] Valida datos duplicados (DNI)
- [ ] Genera IDs automáticamente
- [ ] Relaciona tablas correctamente

### Apoderados
- [ ] ComboBox para tipo documento (DNI/CARNET)
- [ ] Campos: nombre, apellido, parentesco, teléfono, dirección
- [ ] ComboBox para parentesco con opción "Otro"
- [ ] Radio button para seleccionar principal
- [ ] Máximo 2 apoderados por estudiante
- [ ] Siempre debe haber 1 principal

### DNI/Carnet
- [ ] Acepta DNI (8 dígitos)
- [ ] Acepta Carnet (9 dígitos)
- [ ] Validación correcta según tipo

### Mora
- [ ] Configurable: PORCENTAJE o MONTO
- [ ] Se calcula al vencer la cuota
- [ ] Se muestra en vista de cuotas
- [ ] Se considera al registrar pago

### Categorías
- [ ] Botón "Guardar" funciona en nuevos diálogos
- [ ] Botón "Guardar" funciona en edición
- [ ] Desactivar usa soft delete (activo=0)

### Tarifas
- [ ] Indicadores de campos obligatorios (*)
- [ ] Sin campos de fecha
- [ ] No guarda datos incompletos
- [ ] Editar funciona correctamente
- [ ] Desactivar funciona correctamente

### Estudiantes
- [ ] Filtro "Activos" solo muestra activos
- [ ] Búsqueda por DNI para editar
- [ ] Estado REINGRESANTE muestra botón "Crear Matrícula"

### Matrículas
- [ ] Campo monto libre (opcional)
- [ ] Pregunta: Pago AHORA o AL FINALIZAR
- [ ] Valida máximo 2 apoderados
- [ ] Valida apoderado principal
- [ ] Auto-selecciona tarifa por edad

### Pagos
- [ ] Distingue entre matrícula y cuota
- [ ] Muestra cuotas pendientes
- [ ] Registra pago correctamente
- [ ] Muestra historial de pagos

### Reportes
- [ ] Selector de periodo
- [ ] Reporte "Matrículas por periodo"
- [ ] Filtrado correcto por periodo

### Dashboard
- [ ] Muestra montos correctos (no S/0)
- [ ] Indicadores actualizados

### Perfil Admin
- [ ] Editar nombre, apellidos, teléfono, correo
- [ ] Cambiar contraseña con validación
- [ ] DNI y username de solo lectura

---

## 8. Notas Adicionales

### Decisiones Pendientes
1. **Reingresante:** Confirmar si DEBE crear nueva matrícula (actualmente asumido que sí)
2. **Mora:** Confirmar si se aplica automáticamente o requiere acción del admin

### Mejoras Futuras
1. Generación automática de cuotas mensuales (batch job)
2. Notificaciones de vencimiento
3. Exportación de reportes a PDF
4. Modo oscuro
5. Atajos de teclado

### Documentación Actualizada
- `docs/diagnostico_usabilidad.md` - Diagnóstico de usabilidad
- `docs/plan_implementacion.md` - Este documento
- `docs/reglas_negocio.md` - Reglas de negocio (actualizar)
- `docs/casos_uso.md` - Casos de uso (actualizar)

---

## 9. Aprobación

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Desarrollador | | | |
| Product Owner | | | |
| Tester | | | |

---

**Documento generado:** 2026-08-05
**Última actualización:** 2026-08-05
**Versión:** 1.0

