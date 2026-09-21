# Guía de Actualización

## Cómo funciona el auto-updater

La aplicación verifica automáticamente si hay nuevas versiones cada vez que se inicia (una vez al día como máximo).

### Flujo de actualización

```
App inicia
    │
    ▼
¿Pasaron 24h desde la última verificación? ──No──► No hace nada
    │
    Sí
    ▼
Consulta GitHub API
    │
    ▼
¿Hay versión nueva? ──No──► Guarda fecha, continúa normal
    │
    Sí
    ▼
Muestra diálogo:
┌──────────────────────────────────────┐
│  Nueva versión disponible           │
│                                      │
│  Versión actual: v1.0.0             │
│  Nueva versión: v1.1.0              │
│                                      │
│  [Ahora no]        [Actualizar]     │
└──────────────────────────────────────┘
```

### Si el usuario dice "Actualizar"

1. La app descarga el nuevo `.exe` automáticamente
2. Muestra una barra de progreso
3. Al completar, se reinicia automáticamente
4. La app se abre con la nueva versión

### Si el usuario dice "Ahora no"

- No se vuelve a preguntar hasta la próxima versión
- La app continúa funcionando normalmente

## Actualización manual

Si la actualización automática no funciona:

### Paso 1: Descargar la nueva versión

Descargar `AcademiaFutbol-Setup-X.X.X.exe` o el ZIP desde:
- GitHub Releases: `https://github.com/MoisesVillar19/Sistema-Academia-Futbol/releases`
- OneDrive (compartido por el administrador)
- USB

### Paso 2: Reemplazar archivos

**Si usa Inno Setup:**
1. Ejecutar el nuevo instalador
2. Seleccionar la misma carpeta de instalación
3. Aceptar sobrescribir archivos

**Si usa ejecutable directo:**
1. Cerrar la app
2. Copiar todos los archivos nuevos a la carpeta de instalación
3. Reemplazar archivos existentes
4. Ejecutar `AcademiaFutbol.exe`

### Paso 3: Verificar

1. Abrir la app
2. Ir a Configuración
3. Verificar que la versión sea la nueva

## Base de datos y actualizaciones

**IMPORTANTE:** Las actualizaciones NO borran la base de datos existente.

La app usa `CREATE TABLE IF NOT EXISTS` para crear tablas que no existen. Si ya hay datos:
- Los datos existentes se mantienen intactos
- Solo se agregan tablas o columnas nuevas si faltan
- No hay conflictos con registros existentes

### Si hay cambios importantes en la BD

Si la nueva versión requiere cambios estructurales mayores:
1. La app mostrará un mensaje antes de actualizar
2. Se creará un backup automático
3. Los cambios se aplicarán de forma segura

## Troubleshooting

### "No se pudo descargar la actualización"

**Causas posibles:**
- Sin conexión a internet
- GitHub no está accesible
- El repo es privado (debe ser público)

**Solución:**
1. Verificar conexión a internet
2. Intentar actualizar manualmente
3. Si el repo es privado, hacerlo público en GitHub

### "La app no abre después de actualizar"

**Solución:**
1. Ir a la carpeta de instalación
2. Eliminar la carpeta `_internal` si existe
3. Ejecutar el instalador nuevamente
4. Si persiste, reinstalar desde cero

### "Versión antigua después de actualizar"

**Solución:**
1. Verificar que se descargó la versión correcta
2. Limpiar la caché del updater:
   - Ir a `%USERPROFILE%\.academia_futbol\`
   - Eliminar `updater_state.json`
3. Reiniciar la app

## Configuración del updater

Los archivos de configuración están en `updater/config.py`:

```python
# Frecuencia de verificación (en horas)
FRECUENCIA_VERIFICACION_HORAS = 24

# Si el usuario dice "no", no molestar hasta nueva versión
RECORDAR_RECHAZO = True
```

Para cambiar la frecuencia:
1. Editar `updater/config.py`
2. Cambiar `FRECUENCIA_VERIFICACION_HORAS` al valor deseado
3. Rebuild con `build.bat`
