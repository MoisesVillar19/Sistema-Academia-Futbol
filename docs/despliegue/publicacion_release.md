# Guía para Publicar Nuevas Versiones

Esta guía es para el desarrollador. Explica cómo publicar una nueva versión de AcademiaFutbol.

## Flujo completo

```
1. Desarrollar nuevas funcionalidades / bugs
2. Probar localmente
3. Actualizar VERSION
4. Actualizar changelog.md
5. Commit + push
6. Crear tag de Git
7. Crear release en GitHub
8. La secretaria recibe la actualización automáticamente
```

## Paso 1: Actualizar la versión

Editar el archivo `VERSION` en la raíz del proyecto:

```
1.0.0
```

Cambiar a:
```
1.1.0
```

**Reglas de Semantic Versioning:**
- `MAJOR` (1.0.0 → 2.0.0): Cambios grandes, incompatible con versiones anteriores
- `MINOR` (1.0.0 → 1.1.0): Nuevas funcionalidades, compatible
- `PATCH` (1.0.0 → 1.0.1): Corrección de bugs, compatible

## Paso 2: Actualizar el changelog

Editar `docs/changelog.md`:

```markdown
# Changelog

## v1.1.0 - 2026-08-15

### Nuevas funcionalidades
- Agregada función de exportar pagos a Excel
- Nueva vista de reportes mensuales

### Correcciones de bugs
- Corregido error al guardar apoderado sin teléfono
- Mejorado rendimiento del dashboard

### Cambios
- Actualizada interfaz de configuración
```

## Paso 3: Commit y push

```bash
# Agregar cambios
git add .

# Commit
git commit -m "feat: v1.1.0 - Nuevas funcionalidades y correcciones"

# Push
git push origin main
```

## Paso 4: Crear tag de Git

```bash
# Crear tag
git tag v1.1.0

# Push del tag
git push origin v1.1.0
```

## Paso 5: Construir el ejecutable

```bash
# Ejecutar script de construcción
build.bat
```

Esto generará:
- `dist/AcademiaFutbol/AcademiaFutbol.exe`
- `dist/AcademiaFutbol/` (carpeta completa)

## Paso 6: Construir el instalador

```bash
cd installer
build_installer.bat
```

Esto generará:
- `installer/Output/AcademiaFutbol-Setup-1.1.0.exe`

## Paso 7: Crear release en GitHub

1. Ir a `https://github.com/MoisesVillar19/Sistema-Academia-Futbol/releases`
2. Hacer clic en "Draft a new release"
3. Seleccionar el tag `v1.1.0`
4. Título: `v1.1.0`
5. Descripción: copiar del changelog
6. Arrastrar el archivo ZIP:
   - Comprimir la carpeta `dist/AcademiaFutbol/` en un `.zip`
   - Nombre: `AcademiaFutbol-v1.1.0.zip`
7. Hacer clic en "Publish release"

## Paso 8: Notificar a la secretaria

Opcionalmente, enviar un mensaje:
```
Hay una nueva versión de AcademiaFutbol (v1.1.0).
La app se actualizará automáticamente la próxima vez que la abra.
```

## Archivos que cambian por versión

| Archivo | Cambio |
|---------|--------|
| `VERSION` | Actualizar número |
| `docs/changelog.md` | Agregar entrada |
| `main.py` | Solo si hay cambios en la UI |
| `updater/config.py` | Solo si cambia el repo |

## Releasing rápido (sin cambios en código)

Si solo es un fix menor:

```bash
# 1. Actualizar VERSION
echo 1.0.1 > VERSION

# 2. Commit
git add . && git commit -m "fix: v1.0.1 - Corrección menor" && git push

# 3. Tag
git tag v1.0.1 && git push origin v1.0.1

# 4. Build
build.bat

# 5. Crear release en GitHub con el ZIP
```

## Troubleshooting

### "La secretaria no recibe la actualización"

**Verificar:**
1. ¿El repo es público?
2. ¿El tag está creado?
3. ¿La release tiene assets (archivos adjuntos)?
4. ¿La app de la secretaria tiene conexión a internet?

### "La actualización falla al descargar"

**Verificar:**
1. ¿El nombre del archivo ZIP es correcto? (`AcademiaFutbol-vX.X.X.zip`)
2. ¿El archivo está en la release?
3. ¿El tag es correcto?

### "Quiero cambiar el repo"

Editar `updater/config.py`:
```python
GITHUB_REPO = "nuevo-usuario/nuevo-repo"
```

Luego rebuild y nueva release.
