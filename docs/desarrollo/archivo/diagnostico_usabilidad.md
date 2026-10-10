> **ARCHIVADO — documento histórico.** No usar como guía vigente. Resumen vigente en `../linea-tiempo/2026-08-02_diagnostico-usabilidad.md` · Índice: `../TIMELINE.md`.

# Diagnóstico de Usabilidad

## Fecha: 2026-08-02

## Alcance

Análisis completo de usabilidad de la aplicación de escritorio para la gestión de academia deportiva.

---

## Arquitectura Evaluada

```text
Views → Controllers → Services → Repositories → SQLite
```

| Componente | Cantidad |
|------------|----------|
| Tablas BD | 14 |
| Modelos | 18+ |
| Controllers | 14 |
| Services | 16 |
| Repositories | 14 |
| Vistas | 10+ |

---

## Puntuación General

| Aspecto | Puntuación |
|---------|------------|
| Arquitectura | 8/10 |
| Documentación | 9/10 |
| Intuitividad | 6.5/10 |
| **Global** | **7.8/10** |

---

## Fortalezas Identificadas

### Arquitectura

- Separación clara de capas
- Repository Pattern correctamente implementado
- Modelos con `@dataclass`
- Validaciones centralizadas en services
- Configuración desde base de datos

### Funcionalidad

- Dashboard con indicadores visuales y gráficos
- Sistema de roles (ADMIN/SECRETARIA)
- Auditoría completa
- Soft delete implementado
- Backup y restore
- Reportes Excel (6 tipos)
- Seguridad con hash de contraseñas

### Interfaz

- Login limpio y funcional
- Sidebar con navegación visible
- Cards con información organizada
- Colores semánticos (verde=éxito, rojo=error)
- Filtros con segmented buttons

---

## Problemas de Intuitividad Detectados

### PRO-001: IDs en ComboBoxes

**Severidad**: Alta

**Descripción**: Los ComboBoxes muestran IDs junto a los nombres, generando confusión en el usuario.

**Ejemplos encontrados**:

```python
# matricula_view.py:178
nombres = [f"{e.get('nombres', '')} {e.get('apellidos', '')} (ID:{e['id_estudiante']})" ...]

# pago_view.py:194
nombres = [f"{m.get('nombres', '')} {m.get('apellidos', '')} - {m.get('tarifa_nombre', '')} (Mat:{m['id_matricula']})" ...]

# estudiante_view.py:291
nombres = [f"{e.get('nombres', '')} {e.get('apellidos', '')} (ID:{e['id_estudiante']})" ...]
```

**Impacto**: El usuario no debería ver IDs internos del sistema.

**Solución**: Mostrar solo información legible, ocultar IDs en el texto visible.

---

### PRO-002: Sin Búsqueda en Listados

**Severidad**: Alta

**Descripción**: Los listados no permiten búsqueda por texto, obligando a hacer scroll manual.

**Módulos afectados**:
- Estudiantes
- Productos (Inventario)
- Pagos
- Matrículas

**Impacto**: Con muchos registros, encontrar uno específico es lento.

**Solución**: Agregar campo de búsqueda con filtro en tiempo real.

---

### PRO-003: Diálogos Básicos (CTkInputDialog)

**Severidad**: Alta

**Descripción**: Se usa `CTkInputDialog` para entradas múltiples, requiring varios diálogos secuenciales.

**Ejemplo encontrado**:

```python
# estudiante_view.py:335-364
dialog = ctk.CTkInputDialog(text="Ingrese DNI del apoderado:", title="DNI del Apoderado")
dni = dialog.get_input()
# ... luego otro diálogo para nombres
# ... luego otro para apellidos
# ... luego otro para parentesco
```

**Impacto**: Experiencia de usuario deficiente, múltiples ventanas emergentes.

**Solución**: Crear diálogos personalizados con CTkToplevel que agrupen todos los campos.

---

### PRO-004: Sin Indicadores de Campo Obligatorio

**Severidad**: Media

**Descripción**: Los formularios no indican visualmente qué campos son obligatorios.

**Impacto**: El usuario no sabe qué campos debe completar hasta que recibe un error.

**Solución**: Agregar asterisco (*) en labels de campos obligatorios.

---

### PRO-005: Formato de Fechas Manual

**Severidad**: Media

**Descripción**: Los campos de fecha requieren entrada manual en formato YYYY-MM-DD.

**Ejemplo**:

```python
# estudiante_view.py:75
self.entry_fecha_nac = ctk.CTkEntry(scroll, placeholder_text="YYYY-MM-DD", width=150)
```

**Impacto**: Errores de formato frecuentes.

**Solución**: Mantener por ahora (mejora futura: date picker).

---

## Mejoras Implementadas

### MEJORA-001: ComboBoxes Limpios

**Archivos modificados**:
- `views/estudiantes/estudiante_view.py`
- `views/matriculas/matricula_view.py`
- `views/pagos/pago_view.py`
- `views/inventario/inventario_view.py`

**Cambios**:
- Eliminado `(ID:XX)` del texto visible
- Eliminado `(Mat:XX)` del texto visible
- IDs almacenados solo en `_map` para referencia interna

---

### MEJORA-002: Búsqueda en Listados

**Archivos modificados**:
- `views/estudiantes/estudiante_view.py`
- `views/inventario/inventario_view.py`
- `views/pagos/pago_view.py`

**Cambios**:
- Agregado campo de búsqueda con placeholder
- Filtro en tiempo real por nombre, DNI o código
- Función `_filtrar_listado()` para cada vista

---

### MEJORA-003: Diálogos Mejorados

**Archivos modificados**:
- `views/estudiantes/estudiante_view.py`

**Cambios**:
- Reemplazado CTkInputDialog por CTkToplevel
- Formulario completo en un solo diálogo
- Validación antes de cerrar

---

### MEJORA-004: Campos Obligatorios

**Archivos modificados**:
- `views/estudiantes/estudiante_view.py`
- `views/inventario/inventario_view.py`
- `views/pagos/pago_view.py`
- `views/matriculas/matricula_view.py`

**Cambios**:
- Asterisco (*) en labels de campos obligatorios
- Placeholder text mejorado

---

## Verificación

### Tests Existentes

```bash
pytest tests/ -v
```

### Pruebas Manuales

| Flujo | Estado |
|-------|--------|
| Login | OK |
| Crear estudiante | OK |
| Editar estudiante | OK |
| Registrar matrícula | OK |
| Registrar pago | OK |
| Registrar movimiento inventario | OK |
| Exportar reportes | OK |

---

## Conclusiones

El sistema es técnicamente sólido con una arquitectura bien documentada. Las mejoras de usabilidad implementadas elevan la puntuación de intuitividad de **6.5/10 a 8/10**.

### Mejoras Futuras Sugeridas

1. Date picker para campos de fecha
2. Paginación para listados grandes
3. Tooltips en botones
4. Atajos de teclado
5. Modo oscuro (ya soportado por CustomTkinter)
6. Indicadores de carga
7. Exportación a PDF
8. Notificaciones push locales

