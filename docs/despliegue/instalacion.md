> NOTA v1.0.3: para instalar hoy lee guia_instalacion.md (Setup + ZIP + red LAN + bloqueos).
> Este archivo es registro historico/tecnico de v1.0.1 (OneDrive).

# GuÃ­a de InstalaciÃ³n â€” AcademiaFutbol v1.0.1

> **VersiÃ³n:** 1.0.1 Â· **Fecha:** 2026-09-06 Â· **BD Central:** `OneDrive\Academia\academia.db` (virgen producciÃ³n) Â· **Instalador:** `AcademiaFutbol-Setup-1.0.1.exe` (42 MB) Â· **Portable:** `AcademiaFutbol-v1.0.1.zip` (57 MB) Â· **Relacionado:** `despliegue_produccion.md`, `manual_sistema.md`, `AcademiaFutbol.spec`

---

## Resumen despliegue actual

- **Build generado:** 2026-09-06 21:47 con `build.bat` `v1.0.1` â†’ `dist/AcademiaFutbol/AcademiaFutbol.exe` (17.5 MB, 1922 archivos) â€” **no contiene BD** (`AcademiaFutbol.spec:18` excluye `academia.db` y `config.ini`), `version.txt` y `upx=False` para menos falsos positivos
- **Instalador:** `installer/Output/AcademiaFutbol-Setup-1.0.1.exe` (42.1 MB) via Inno Setup 6.7 â€” `setup.iss:23` `OutputDir=Output` (fix) + `setup.iss:82` `CurStepChanged` genera `config.ini` y estructura OneDrive solo si no existe
- **BD central producciÃ³n:** `C:\Users\{usuario}\OneDrive\Academia\academia.db` **virgen** (294 KB) â€” `create_db:370` + `seed:13` â†’ 0 alumnos, 1 usuario `admin`, 5 categorÃ­as edad, 2 `categoria_producto`, 1 `CAMISETA-ENT` stock 50, 4 `tipo_uniforme`, precios `100/100/100/20`. BD de prueba respaldada en `OneDrive\BackupsAcademia\academia_TEST_20260906_210703.db` + `fotos_TEST_*` / `comprobantes_TEST_*`
- **Carpetas OneDrive:** `Academia\fotos\` y `Academia\comprobantes\` vacÃ­as (listas para fotos `FOTOS_DIR` y comprobantes `COMPROBANTES_DIR` `utils/constants.py:95`), `BackupsAcademia\` para backups cada 6h `main.py:242`
- **Tests:** 234 passed `pytest`

---

## 1. InstalaciÃ³n con Inno Setup (Recomendado) â€” 6 pasos deja funcional

### Requisitos previos
- Windows 10+ Â· OneDrive instalado y sincronizado con cuenta empresa (ej `admin@roncalli.onmicrosoft.com` con carpeta `Academia` compartida `lectura/escritura` a SECRETARIA)
- Si OneDrive no estÃ¡: el wizard avisa `Instalar OneDrive recomendado` y usa fallback local `APP_DIR\database\academia.db` (no central)

### Paso 1: Descargar el instalador
**No se commitea al repo** (`.gitignore:17` `*.zip` y `installer/Output/` ignorados). Descargar desde **GitHub Releases** (ver Â§5) o recibir por OneDrive/USB:

- `AcademiaFutbol-Setup-1.0.0.exe` (42 MB) â€” instalador wizard
- Opcional: `AcademiaFutbol-v1.0.0.zip` (56 MB) â€” `dist\` portable sin wizard

### Paso 2: Ejecutar el instalador
1. Doble clic en `AcademiaFutbol-Setup-1.0.0.exe` (en v1.0.1 es `AcademiaFutbol-Setup-1.0.1.exe`)
2. Si SmartScreen: `MÃ¡s informaciÃ³n â†’ Ejecutar de todas formas` (exe sin firma â€” ver Â§2.1 si estÃ¡ bloqueado)
3. Aparece wizard `AcademiaFutbol v1.0.1`

### Paso 2.1: Si Windows bloquea el EXE (SmartScreen / Antivirus / Permisos) â€” sin firma, cualquier PC

> **Por dinero no se usa firma de cÃ³digo.** El exe es legÃ­timo (PyInstaller) pero Windows lo marca `Editor desconocido`. **Todas** las PCs pueden instalar: elige **A, B, C o D** segÃºn tu caso. Si tu PC no tiene permiso de admin para `C:\Program Files\`, usa **D) ZIP** (no pide permisos).

**A) SmartScreen azul `Windows protegiÃ³ su PC` (mÃ¡s comÃºn):**
1. Clic `MÃ¡s informaciÃ³n`
2. Clic `Ejecutar de todas formas`
3. ContinÃºa wizard normal (6 pasos)
> Tip: tras ~50-100 descargas y con el archivo desbloqueado, SmartScreen gana reputaciÃ³n y deja de advertir.

**B) Archivo bloqueado `No se puede ejecutar / Zone.Identifier` (descargado de internet):**
- OpciÃ³n grÃ¡fica: clic derecho `AcademiaFutbol-Setup-1.0.1.exe` â†’ `Propiedades` â†’ marcar `Desbloquear` â†’ `Aplicar` â†’ doble clic de nuevo
- OpciÃ³n PowerShell (recomendado si copias por OneDrive/USB):
  ```powershell
  Unblock-File -Path ".\AcademiaFutbol-Setup-1.0.1.exe"
  # verificar:
  Get-Content ".\AcademiaFutbol-Setup-1.0.1.exe:Zone.Identifier" -ErrorAction SilentlyContinue
  # si existe, borrar ADS:
  Remove-Item -Path ".\AcademiaFutbol-Setup-1.0.1.exe:Zone.Identifier" -ErrorAction SilentlyContinue
  ```
- Si viene de ZIP, desbloquear tambiÃ©n el ZIP antes de extraer: `Unblock-File AcademiaFutbol-v1.0.1.zip`

**C) Windows Defender / Antivirus `Amenaza encontrada / Trojan:Win32/Wacatac` (falso positivo PyInstaller):**
1. `Seguridad de Windows â†’ ProtecciÃ³n antivirus â†’ Historial de protecciÃ³n â†’ Acciones â†’ Permitir`
2. Agregar exclusiÃ³n permanente (evita que lo borre de nuevo):
   `Seguridad de Windows â†’ ProtecciÃ³n antivirus â†’ Administrar configuraciÃ³n â†’ Exclusiones â†’ Agregar â†’ Carpeta â†’ C:\Program Files\AcademiaFutvol\` (o la carpeta donde extrajiste el ZIP)
3. Volver a descargar/extraer `Setup` o `ZIP` si Defender lo puso en cuarentena
> VerificaciÃ³n hash SHA256 (publicado en Release notes) para confirmar que no fue modificado:
  ```bat
  certutil -hashfile AcademiaFutbol-Setup-1.0.1.exe SHA256
  # comparar con hash del Release
  ```

**D) Sin permiso de admin / PC bloqueada para instaladores (cualquier PC sin `C:\Program Files`):**
- **No uses el Setup.** Usa el **portable ZIP** (ver Â§2) que no pide permisos:
  1. Desbloquear ZIP: `Unblock-File AcademiaFutbol-v1.0.1.zip`
  2. Extraer a `C:\AcademiaFutbol\` o `Documentos\AcademiaFutbol\` (no necesita admin, elige `Extraer todo...` â†’ `C:\AcademiaFutbol`)
  3. Doble clic `AcademiaFutbol.exe` â†’ funciona igual (BD sigue en `OneDrive\Academia\academia.db`)
  4. Crear acceso directo manual: clic derecho `AcademiaFutbol.exe` â†’ `Crear acceso directo` â†’ mover a Escritorio
> Este ZIP es la alternativa oficial para PCs de cabina, colegio o sin OneDrive admin.

### Paso 3: Wizard (6 pantallas)
1. **Bienvenida** â†’ `Siguiente`
2. **Licencia** â†’ Aceptar â†’ `Siguiente`
3. **Carpeta** â†’ default `C:\Program Files\AcademiaFutbol\` (editable) â†’ `Siguiente`
4. **(AutomÃ¡tico, sin pantalla extra)** â€” `setup.iss:92` detecta OneDrive vÃ­a `GetEnv('OneDrive')` â†’ crea si no existen:
   ```
   OneDrive\Academia\academia.db          (si no existe, se crea vacÃ­a al primer arranque)
   OneDrive\Academia\fotos\
   OneDrive\Academia\comprobantes\
   OneDrive\BackupsAcademia\
   ```
   Escribe `C:\Program Files\AcademiaFutbol\config.ini`:
   ```ini
   [database]
   path=C:\Users\{user}\OneDrive\Academia\academia.db
   [backup]
   dir=C:\Users\{user}\OneDrive\BackupsAcademia
   [rutas]
   # fotos/comprobantes resuelven a OneDrive\Academia\fotos si no hay clave explÃ­cita
   ```
   Si `config.ini` ya existe (update), **no se sobreescribe**.
5. **Acceso directo** â†’ marcar `Crear acceso directo en el escritorio` â†’ `Siguiente`
6. **Instalar** â†’ copiar `dist\AcademiaFutbol\*` (recursivo) â†’ `Finalizar` â†’ marcar `Abrir AcademiaFutbol ahora`

### Paso 4: VerificaciÃ³n deja funcional (checklist)
- [ ] `C:\Program Files\AcademiaFutbol\config.ini` existe y `path` apunta a `OneDrive\Academia\academia.db`
- [ ] Doble clic `AcademiaFutbol.exe` abre sin error `DB_PATH`
- [ ] Login `admin` / `admin123` â†’ **obliga cambio de contraseÃ±a** `auth_service:73` (hash bcrypt)
- [ ] `ConfiguraciÃ³n` muestra precios `InscripciÃ³n 100, Mensualidad 100, Reingreso 100, Uniforme 20, Tasa 15, Arbitraje 15, Pago profesor 200`
- [ ] `Estudiantes` â†’ 0 alumnos (BD virgen) â€” registrar 1 alumno prueba descuenta `CAMISETA-ENT` 50â†’49 visible en `Inventario`
- [ ] `OneDrive` icono verde (no `academia (conflicto).db`) Â· `PRAGMA journal_mode=WAL`

### Paso 5: Segundo PC (validaciÃ³n central)
Repetir wizard en PC 2 con misma cuenta OneDrive sincronizada:
- `Probar conexiÃ³n` implÃ­cita: `Main` lee `OneDrive\Academia\academia.db` con alumno creado en PC1
- Login `admin` (o crear `secretaria`) â†’ `Estudiantes` ve alumno + `Inventario` stock 49 en ambas

---

## 2. InstalaciÃ³n sin Inno Setup (portable ZIP)

### Paso 1: Descargar ZIP desde GitHub Release
`AcademiaFutbol-v1.0.0.zip` (56 MB)

### Paso 2: Extraer
1. Crear `C:\AcademiaFutbol\`
2. Descomprimir ZIP completo (mantener `_internal\` y `AcademiaFutbol.exe` juntos)
3. **No copiar** `academia.db` ni `config.ini` manualmente â€” se generan

### Paso 3: Inicializar OneDrive manual (si wizard no usado)
```bat
xcopy AcademiaFutbol C:\AcademiaFutbol\ /E
echo [database] > C:\AcademiaFutbol\config.ini
echo path=C:\Users\%USERNAME%\OneDrive\Academia\academia.db >> C:\AcademiaFutbol\config.ini
echo [backup] >> C:\AcademiaFutbol\config.ini
echo dir=C:\Users\%USERNAME%\OneDrive\BackupsAcademia >> C:\AcademiaFutbol\config.ini
mkdir "%USERPROFILE%\OneDrive\Academia\fotos"
mkdir "%USERPROFILE%\OneDrive\Academia\comprobantes"
mkdir "%USERPROFILE%\OneDrive\BackupsAcademia"
C:\AcademiaFutbol\AcademiaFutbol.exe
```

### Paso 4: Acceso directo
Clic derecho `AcademiaFutbol.exe` â†’ `Crear acceso directo` â†’ mover a Escritorio

---

## 3. Ejecutar desde cÃ³digo fuente (Desarrolladores)

### Requisitos
- Python 3.13+ Â· pip Â· OneDrive opcional

### Pasos
```bash
git clone https://github.com/MoisesVillar19/Sistema-Academia-Futbol.git
cd AcademiaFutbol
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
# DB_PATH resuelve: config.ini â†’ OneDrive\Academia\academia.db â†’ database\academia.db fallback
```

---

## 4. Construir ejecutable e instalador (Desarrolladores)

```bash
# 1. Ejecutable (2-3 min)
build.bat
# â†’ dist\AcademiaFutbol\AcademiaFutbol.exe + _internal\VERSION + assets\images\logo_roncalli.png
# Verifica: dist sin academia.db ni config.ini (AcademiaFutbol.spec:104 COLLECT)

# 2. Instalador (requiere Inno Setup 6.7+)
installer\build_installer.bat
# â†’ installer\Output\AcademiaFutbol-Setup-1.0.0.exe
# En este proyecto: normalizar si queda en installer\installer\Output\ â†’ copiar a installer\Output\

# 3. ZIP Release
Compress-Archive -Path dist\AcademiaFutbol\* -DestinationPath AcademiaFutbol-v1.0.0.zip -Force
```

**Regla de oro `despliegue_produccion.md:192`:** `dist` y `installer\Output` **nunca** llevan `academia.db` ni `config.ini` fijo. Se generan en PC destino.

---

## 5. Â¿QuÃ© hacer con el Setup? (GitHub Release)

> **No hacer `git add` del `.exe` ni `.zip`** â€” estÃ¡n ignorados (`.gitignore:17` `*.zip`, `installer/Output/`). Se publican como **Assets de Release**, no como cÃ³digo.

### Flujo publicaciÃ³n `publicacion_release.md:3`

```bash
# 1. VersiÃ³n y changelog
echo 1.0.0 > VERSION
# editar docs/desarrollo/changelog.md

# 2. Commit + push cÃ³digo (sin binarios)
git add docs/ VERSION AcademiaFutbol.spec installer/setup.iss
git commit -m "feat: v1.0.0 BD virgen producciÃ³n OneDrive + wizard"
git push origin main

# 3. Tag
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub â†’ Releases â†’ Draft a new release
#    - Tag: v1.0.0 Â· Title: v1.0.0 Â· Description: copiar changelog
#    - Arrastrar assets:
#      â€¢ AcademiaFutbol-Setup-1.0.0.exe (42 MB) â€” instalador wizard
#      â€¢ AcademiaFutbol-v1.0.0.zip (56 MB) â€” portable
#    - Publish release
```

**SECRETARIA recibe update automÃ¡tico:** `main.py:344` `after(2000, verificar_y_mostrar)` cada 24h `updater/config.py:1` `GITHUB_REPO` compara `VERSION` â†’ diÃ¡logo `Nueva versiÃ³n v1.1.0 â†’ Descargar`.

Si el repo es privado, el updater requiere `GITHUB_REPO` pÃºblico o token.

### Alternativas si no usas GitHub
- Compartir `AcademiaFutbol-Setup-1.0.0.exe` por OneDrive (carpeta compartida) / USB / correo
- El ZIP portable para PCs sin permiso de instalaciÃ³n

---

## 6. ConfiguraciÃ³n OneDrive (detalle)

### Si OneDrive sincronizado (recomendado prod)
`utils/constants.py:72` resuelve `DB_PATH` â†’ `OneDrive\Academia\academia.db`:
```
C:\Users\{user}\OneDrive\Academia\academia.db        (BD central WAL)
C:\Users\{user}\OneDrive\Academia\fotos\             (FOTOS_DIR)
C:\Users\{user}\OneDrive\Academia\comprobantes\      (COMPROBANTES_DIR)
C:\Users\{user}\OneDrive\BackupsAcademia\            (BACKUP_DIR, backups cada 6h)
```
Permisos OneDrive: `ADMIN` full, `SECRETARIA` edit (misma carpeta `Academia` compartida). Verificar icono verde sincronizado tras crear alumno.

### Si OneDrive no instalado (fallback dev)
```
C:\Program Files\AcademiaFutbol\database\academia.db  (local por PC, no central)
C:\Program Files\AcademiaFutbol\backups\
```
Wizard deja aviso `Instalar OneDrive recomendado` pero permite instalar.

### Restaurar backup de prueba (si necesitas ver datos antiguos)
```bat
copy "C:\Users\%USERNAME%\OneDrive\BackupsAcademia\academia_TEST_20260906_210703.db" "C:\Users\%USERNAME%\OneDrive\Academia\academia.db" /Y
xcopy "C:\Users\%USERNAME%\OneDrive\BackupsAcademia\fotos_TEST_20260906_210703" "C:\Users\%USERNAME%\OneDrive\Academia\fotos" /E /Y
```

---

## 7. Primer arranque (BD virgen)

1. Ejecutar acceso directo â†’ `Login`
2. `admin` / `admin123` â†’ obliga `Cambiar contraseÃ±a` `auth_service:73`
3. `ConfiguraciÃ³n` (ADMIN) verificar 8 secciones: precios flexibles, mora, categorÃ­as `3-5..16-18`, tipos uniforme `Entrenamiento/Competencia/Completo/Media` (seed 4)
4. Registrar alumno prueba â†’ `Ventas` `UNIFORME` stock `50â†’49` â†’ cerrar y reabrir en 2Âª PC y verificar `49`

---

## 8. Actualizaciones automÃ¡ticas â€” instalar una vez, luego acopla solo

> **Flujo ideal:** Instalar **una vez** con `AcademiaFutbol-Setup-1.0.2.exe` (superior, sin errores manuales) â†’ luego `ConfiguraciÃ³n â†’ Buscar actualizaciones` o auto-check 24h `main.py:445` lo acopla sin reemplazo manual.

- **Si instalaste con Setup en `Program Files`:** el updater detecta `es_instalacion_programfiles()` â†’ descarga **`Setup-*.exe`** y lo lanza **silencioso `/SILENT`** (`updater/update_service.py:197` `es_setup`). **Pedira UAC** (permiso Administrador, es normal) â†’ `setup.iss:145` `CloseApplications=yes` cierra la app, actualiza `_internal` y vuelve a abrir. Documentado y con alerta en la ventana de actualizaciÃ³n.
- **Si instalaste portable ZIP en `C:\AcademiaFutbol\`:** usa **ZIP** sin UAC â†’ streaming 32KB con `MB/s` y `ETA` (`update_view.py:192`), extrae preservando `config.ini/db/logs` (`update_service.py:160`), reinicia.
- `.exe` nuevo **no borra** `OneDrive\Academia\academia.db` / `fotos/` / `comprobantes/` / `config.ini` (`constants.py:9` `APP_DIR` vs `_internal`, `updater` excluye `database/`).
- BotÃ³n manual: `ConfiguraciÃ³n â†’ Actualizaciones â†’ Buscar actualizaciones ahora` (`configuracion_view.py:185` `verificar_y_mostrar(forzar=True)`) ignora las 24h.
- BD migra con `create_db.py:379` `_migrar_columnas_faltantes` `ALTER ADD COLUMN IF NOT EXISTS` (ej `1.0.2â†’1.0.3` `egreso.activo`)
- Rollback: re-ejecutar `Setup-X.Y.Z.exe` anterior; BD intacta (nunca se toca).

---

## 9. Desinstalar

### Con Inno Setup
Panel de Control â†’ Programas y caracterÃ­sticas â†’ `AcademiaFutbol` â†’ Desinstalar â†’ wizard (no borra `OneDrive\Academia\academia.db` ni `BackupsAcademia`)

### Portable
Eliminar carpeta `C:\AcademiaFutbol\` + acceso directo

---

## 10. SoluciÃ³n de problemas

| Problema | Causa | SoluciÃ³n |
|---|---|---|
| `Permiso denegado _internal/logs` | v1.0.0 instalado en `Program Files` sin fallback | Actualizar a **v1.0.1** (fix `utils/logger.py:8` â†’ `LOCALAPPDATA\AcademiaFutbol\logs`) |
| `Windows protegiÃ³ su PC` (SmartScreen) | Exe sin firma (sin dinero para certificado) | `MÃ¡s informaciÃ³n â†’ Ejecutar` o **B) Desbloquear** `Unblock-File` (ver Â§2.1) |
| `No se puede ejecutar / Zone.Identifier` | Archivo descargado bloqueado | `Propiedades â†’ Desbloquear` o `Unblock-File -Path Setup.exe` (ver Â§2.1 B) |
| `Defender lo borra / Trojan` | Falso positivo PyInstaller | `Historial â†’ Permitir` + `ExclusiÃ³n Carpeta C:\Program Files\AcademiaFutbol\` + verificar `certutil -hashfile` SHA256 |
| `No tengo permiso admin` | PC sin `Program Files` | Usar **ZIP portable Â§2.1 D** en `C:\AcademiaFutbol\` (no pide admin) |
| `database is locked` | 2 PCs escriben sin sync OneDrive | Esperar icono verde, WAL + `transaccion:43` reintenta |
| `academia (conflicto).db` | EdiciÃ³n offline simultÃ¡nea | Cerrar apps, OneDrive resuelve, restaurar `academia_TEST_*.db` |
| `No se encontrÃ³ OneDrive` | OneDrive no instalado | Instalar OneDrive o usa fallback `LOCALAPPDATA\AcademiaFutbol\backups` |
| `admin123` no entra | Ya cambiÃ³ contraseÃ±a | Usar nueva o PIN emergencia `roncalli2026` `seed:64` |
| Foto no se ve | `FOTOS_DIR` sin permiso | Verificar `OneDrive\Academia\fotos` existe y `PIL` instalado |

> **ReputaciÃ³n SmartScreen:** sin firma, el exe gana confianza tras varias instalaciones y si se publica hash SHA256 en el Release. No es virus â€” PyInstaller + `bcrypt` a veces da falso positivo `Wacatac`.

---

*PDF v1.0.2 con Setup UAC + ZIP dual. Artefactos: `installer/Output/AcademiaFutbol-Setup-1.0.2.exe` + `AcademiaFutbol-v1.0.2.zip` + `README_BLOQUEO.txt` + `SHA256` + alerta UAC documentada.*
