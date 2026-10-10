> **ARCHIVADO — documento histórico.** No usar como guía vigente. Resumen vigente en `../linea-tiempo/2026-08-01_sprints-7-10-estabilizacion.md` · Índice: `../TIMELINE.md`.

# Sprint 10 — Estabilización

**Fecha:** 2026-08-01
**Objetivo:** Preparar versión 1.0 estable

---

## Orden de Ejecución

| Paso | Prioridad | Descripción |
|------|-----------|-------------|
| 1 | ALTA | Configurar tests (conftest.py, pytest, :memory:) |
| 2 | ALTA | Tests unitarios (validators, security, dates) |
| 3 | ALTA | Tests de services (cuota, pago, estudiante) |
| 4 | ALTA | Tests de integración (login, matrícula) |
| 5 | ALTA | Bugs críticos (#7, #12, #18) |
| 6 | MEDIA | Violaciones de arquitectura (#8-10, #16) |
| 7 | MEDIA | Limpieza de código |
| 8 | MEDIA | Documentación (README, renombrar archivos) |
| 9 | BAJA | Seguridad (.env, bcrypt) |
| 10 | BAJA | Git (commit + tag v1.0) |

---

## Nota sobre la Base de Datos

La `academia.db` **NO se sube al repositorio** porque:
- Es datos locales de cada usuario
- Contiene passwords hasheados
- Se crea automáticamente al ejecutar `python main.py`

Para tests se usa SQLite `:memory:` (en memoria) porque:
- Es rápida (no toca disco)
- No necesita limpieza
- Está aislada de datos reales
- Se destruye automáticamente al terminar

---

## Paso 1 — Configurar Tests

### Instalar pytest

```powershell
pip install pytest
pip freeze > requirements.txt
```

### `tests/conftest.py`

```python
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(autouse=True)
def test_db():
    """Base de datos en memoria para cada test."""
    import database.connection as conn_module
    import utils.constants as const_module

    # Guardar valores originales
    original_db_name = const_module.DB_NAME
    original_db_path = const_module.DB_PATH

    # Forzar base de datos en memoria
    conn_module._connection = None
    const_module.DB_NAME = ":memory:"
    const_module.DB_PATH = ":memory:"

    # Recrear tablas y seed
    from database.create_db import create_tables
    from database.seed import seed_database
    create_tables()
    seed_database()

    yield

    # Cleanup
    from database.connection import close_connection
    close_connection()
    const_module.DB_NAME = original_db_name
    const_module.DB_PATH = original_db_path


@pytest.fixture
def usuario_admin():
    """Login como admin para tests que requieren sesión."""
    from services import auth_service
    auth_service.login("admin", "admin123")
    yield
    auth_service.logout()
```

---

## Paso 2 — Tests Unitarios

### `tests/test_validators.py`

```python
from utils.validators import validate_dni, validate_not_empty, validate_sex

def test_validate_dni_valid():
    assert validate_dni("12345678") is True

def test_validate_dni_invalid():
    assert validate_dni("12345") is False
    assert validate_dni("abcdefgh") is False

def test_validate_not_empty():
    assert validate_not_empty("test", "Campo") is None
    assert validate_not_empty("", "Campo") is not None

def test_validate_sex():
    assert validate_sex("M") is True
    assert validate_sex("F") is True
    assert validate_sex("X") is False
```

### `tests/test_security.py`

```python
from utils.security import hash_password, verify_password

def test_hash_password():
    hashed = hash_password("test123")
    assert hashed != "test123"
    assert len(hashed) > 0

def test_verify_password():
    hashed = hash_password("test123")
    assert verify_password("test123", hashed) is True
    assert verify_password("wrong", hashed) is False
```

### `tests/test_dates.py`

```python
from utils.dates import get_today, get_now

def test_get_today():
    today = get_today()
    assert len(today) == 10
    assert today.count("-") == 2

def test_get_now():
    now = get_now()
    assert len(now) >= 19
```

---

## Paso 3 — Tests de Services

### `tests/test_cuota_service.py`

```python
from services import cuota_service

def test_crear_cuota():
    id_cuota = cuota_service.crear_cuota(
        id_matricula=1,
        monto_total=100.0,
        fecha_vencimiento="2026-08-15",
        periodo="2026-08"
    )
    assert id_cuota is not None
    assert id_cuota > 0

def test_contar_por_estado():
    cuota_service.crear_cuota(1, 100.0, "2026-08-15", "2026-08")
    total = cuota_service.contar_por_estado("PENDIENTE")
    assert total >= 1
```

### `tests/test_estudiante_service.py`

```python
from services import estudiante_service

def test_crear_estudiante():
    exito, msg, id_est = estudiante_service.crear_estudiante({
        "dni": "99999999",
        "nombres": "Test",
        "apellidos": "User",
    })
    assert exito is True
    assert id_est is not None

def test_crear_estudiante_duplicado():
    estudiante_service.crear_estudiante({
        "dni": "88888888",
        "nombres": "Test",
        "apellidos": "User",
    })
    exito, msg, id_est = estudiante_service.crear_estudiante({
        "dni": "88888888",
        "nombres": "Test2",
        "apellidos": "User2",
    })
    assert exito is False
```

---

## Paso 4 — Tests de Integración

### `tests/test_login.py`

```python
from services import auth_service

def test_login_exitoso():
    usuario = auth_service.login("admin", "admin123")
    assert usuario is not None
    assert usuario["username"] == "admin"
    auth_service.logout()

def test_login_fallido():
    usuario = auth_service.login("admin", "wrongpass")
    assert usuario is None

def test_logout():
    auth_service.login("admin", "admin123")
    auth_service.logout()
    assert auth_service.esta_logueado() is False
```

### `tests/test_matriculas.py`

```python
from services import matricula_service

def test_listar_matriculas_activas():
    matriculas = matricula_service.listar_matriculas_activas()
    assert isinstance(matriculas, list)
```

---

## Paso 5 — Bugs Críticos

### Bug #7: `id_usuario=1` hardcodeado (17 ocurrencias)

**Problema:** Todos los services usan `id_usuario=1` en llamadas a auditoría.

**Solución:** Modificar cada función para aceptar `id_usuario` como parámetro.

**Archivos a modificar:**

| Archivo | Líneas | Funciones |
|---------|--------|-----------|
| `services/usuario_service.py` | 48, 93, 123, 150, 170 | `crear_usuario`, `editar_usuario`, `activar_usuario`, `desactivar_usuario`, `restablecer_password` |
| `services/persona_service.py` | 36, 70 | `crear_persona`, `editar_persona` |
| `services/estudiante_service.py` | 47, 96, 118 | `crear_estudiante`, `registrar_retiro`, `registrar_reingreso` |
| `services/apoderado_service.py` | 48, 92 | `crear_apoderado`, `asociar_a_estudiante` |
| `services/matricula_service.py` | 74 | `crear_matricula` |
| `services/tarifa_service.py` | 31 | `crear_tarifa` |
| `services/beca_service.py` | 31 | `crear_beca` |
| `services/inventario_service.py` | 23, 95, 185 | `registrar_producto`, `registrar_movimiento`, `registrar_ajuste` |

**Patrón de cambio:**

```python
# ANTES
def crear_estudiante(data: dict) -> tuple[bool, str, int | None]:
    ...
    auditoria_service.registrar_insert(id_usuario=1, ...)

# DESPUÉS
def crear_estudiante(data: dict, id_usuario: int) -> tuple[bool, str, int | None]:
    ...
    auditoria_service.registrar_insert(id_usuario=id_usuario, ...)
```

**Controllers a modificar:**

Cada controller debe obtener `id_usuario` de `auth_service.obtener_usuario_actual()` y pasarlo al service.

```python
# En cada controller
from services import auth_service

def crear_estudiante(data: dict):
    usuario = auth_service.obtener_usuario_actual()
    id_usuario = usuario["id_usuario"] if usuario else 1
    return estudiante_service.crear_estudiante(data, id_usuario)
```

---

### Bug #18: SHA-256 débil → bcrypt

**Problema:** `utils/security.py` usa `hashlib.sha256` que es inseguro para passwords.

**Solución:** Migrar a `bcrypt` (ya instalado).

**Archivo a modificar:** `utils/security.py`

**Cambios:**

```python
# ANTES
import hashlib
import os

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    hash_obj = hashlib.sha256(salt + password.encode())
    return (salt + hash_obj.digest()).hex()

def verify_password(password: str, stored_hash: str) -> bool:
    # Comparación incorrecta por salt aleatorio

# DESPUÉS
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash.encode())
```

**Nota:** Se debe recrear el seed con passwords hasheados con bcrypt.

---

### Bug #12: Filtro "Retirados" erróneo

**Problema:** `estudiante_view.py:284-285` filtra por `activo=0` en vez de `estado='RETIRADO'`.

**Archivo:** `views/estudiantes/estudiante_view.py`

**Cambio:**

```python
# ANTES
elif valor == "Retirados":
    self._cargar_estudiantes(activo=0)

# DESPUÉS
elif valor == "Retirados":
    self._cargar_estudiantes(estado="RETIRADO")
```

**Requiere:** Agregar parámetro `estado` a `_cargar_estudiantes()` y modificar `listar_estudiantes()` en el service.

---

## Paso 6 — Violaciones de Arquitectura

### Bug #8-9: View → Repository/Service en `pago_view.py`

**Archivo:** `views/pagos/pago_view.py`

**Cambios en `pago_controller.py`:**

```python
# Agregar funciones
def listar_matriculas_activas():
    from services import matricula_service
    return matricula_service.listar_matriculas_activas()

def listar_cuotas_pendientes(id_matricula: int):
    from services import cuota_service
    return cuota_service.obtener_cuotas_pendientes(id_matricula)
```

**Cambios en `pago_view.py`:**

```python
# ANTES
from repositories import matricula_repository
matriculas = matricula_repository.obtener_activas()

# DESPUÉS
from controllers import pago_controller
matriculas = pago_controller.listar_matriculas_activas()
```

---

### Bug #10: View → Repository en `estudiante_view.py`

**Archivo:** `views/estudiantes/estudiante_view.py:379`

**Cambios en `estudiante_controller.py`:**

```python
# Agregar función
def obtener_apoderado_por_persona(id_persona: int):
    from repositories import apoderado_repository
    return apoderado_repository.obtener_por_persona(id_persona)
```

---

### Bug #16: Service → Database en `dashboard_service.py`

**Archivo:** `services/dashboard_service.py:115`

**Cambio:**

```python
# ANTES
def _obtener_configuracion():
    from database.connection import fetch_one
    return fetch_one("SELECT * FROM configuracion WHERE id_configuracion = 1")

# DESPUÉS
def _obtener_configuracion():
    from repositories import configuracion_repository
    return configuracion_repository.obtener_configuracion()
```

---

## Paso 7 — Limpieza de Código

| Acción | Archivo | Línea |
|--------|---------|-------|
| Eliminar código muerto | `matricula_service.py` | 39 |
| Eliminar import redundante | `matricula_service.py` | 69 |
| Eliminar función muerta | `database/connection.py` | 27-32 |
| Eliminar import muerto | `repositories/estudiante_apoderado_repository.py` | 2 |
| Agregar `__init__.py` | `views/dashboard/`, `views/estudiantes/`, `views/inventario/`, `views/matriculas/`, `views/pagos/`, `views/reportes/`, `views/configuracion/` |
| Usar constantes | Múltiples archivos | `METODO_EFECTIVO`, `METODO_YAPE`, etc. |

---

## Paso 8 — Documentación

### `README.md` — Reescritura completa

```markdown
# AcademiaFutbol

Sistema de Gestión para Academia Deportiva.

## Tecnologías
- Python 3.x
- SQLite
- CustomTkinter
- openpyxl
- matplotlib

## Instalación
```bash
pip install -r requirements.txt
```

## Ejecución
```bash
python main.py
```

## Credenciales por defecto
- Usuario: `admin`
- Contraseña: `admin123`

## Arquitectura
- Views → Controllers → Services → Repositories → SQLite

## Estructura del proyecto
...
```

### Renombrar `sprint7_estado.md` → `estado_actual.md`

### Actualizar `AGENTS.md`

Corregir referencia de `arquitectura_bd.md` a `AcademiaFutbol_Arquitectura_BD.md`.

---

## Paso 9 — Seguridad y Config

### `.env`

```
DB_NAME=academia.db
DEFAULT_ADMIN_USER=admin
DEFAULT_ADMIN_PASS=admin123
BACKUP_DIR=backups/
```

### `utils/constants.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "academia.db")
DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "admin123")
```

---

## Paso 10 — Git

1. **Commit de Sprint 10:**
```bash
git add .
git commit -m "feat: Sprint 10 - Estabilización

- Configurar tests con SQLite :memory:
- Tests unitarios (validators, security, dates)
- Tests de services (cuota, pago, estudiante)
- Tests de integración (login, matrícula)
- Fix bugs críticos (#7, #12, #18)
- Corregir violaciones de arquitectura
- Limpiar código muerto
- Actualizar documentación
- Migrar a bcrypt para passwords
- Implementar variables de entorno"
```

2. **Tag v1.0:**
```bash
git tag -a v1.0 -m "Versión 1.0 estable"
git push origin main
git push origin v1.0
```

---

## Checklist de Verificación

- [x] pytest instalado
- [x] conftest.py creado con DB :memory:
- [x] Tests unitarios escritos y pasando (40 tests)
- [x] Tests de services escritos y pasando (26 tests)
- [x] Tests de integración escritos y pasando (12 tests)
- [x] Bug #7 corregido (id_usuario dinámico)
- [x] Bug #18 corregido (bcrypt)
- [x] Bug #12 corregido (filtro retirados)
- [x] Bugs #8-10 corregidos (violaciones arquitectura)
- [x] Bug #16 corregido (dashboard_service)
- [x] Bug #19 corregido (DB path + __pycache__ bcrypt)
- [x] Bug #20 corregido (login ventana al frente)
- [x] Login GUI mejorada (centrado, diseño)
- [x] Main window mejorada (centrado, pantalla bienvenida)
- [x] Auto-categoría por edad en matrícula
- [x] Tarifas más configurables (descripcion, observaciones)
- [x] Categorías de edad en módulo Configuración (admin)
- [x] Git commit + tag v1.0 + push

---

## Resumen de Cambios — Sprint 10 (hasta ahora)

### Tests (78 tests, 100% pasan)

| Archivo | Tests | Tipo |
|---------|-------|------|
| `test_validators.py` | 18 | Unitario |
| `test_security.py` | 7 | Unitario |
| `test_dates.py` | 15 | Unitario |
| `test_cuota_service.py` | 11 | Service |
| `test_estudiante_service.py` | 8 | Service |
| `test_pago_service.py` | 7 | Service |
| `test_login.py` | 6 | Integración |
| `test_matriculas.py` | 6 | Integración |
| **TOTAL** | **78** | |

### Bugs Corregidos

| Bug | Archivos | Descripción |
|-----|----------|-------------|
| #7 | services/*.py, controllers/*.py | `id_usuario=1` → parámetro dinámico desde sesión |
| #12 | estudiante_view.py, estudiante_repository.py | Filtro "Retirados" usa `estado=RETIRADO` en vez de `activo=0` |
| #18 | utils/security.py | SHA-256 → bcrypt (hash seguro) |
| #8-9 | pago_view.py, pago_controller.py | View ya no llama a repository directamente |
| #10 | estudiante_view.py, estudiante_controller.py | View ya no llama a repository directamente |
| #16 | dashboard_service.py | Service ya no usa SQL directo, usa configuracion_repository |
| #19 | database/academia.db | DB estaba en `database/academia.db` (no raíz). `__pycache__` tenía `.pyc` viejo con SHA-256, causaba hash inválido |
| #20 | views/login/login_view.py, main.py | Login aparecía detrás de la ventana principal. Se agregó `lift()`/`focus_force()`/`topmost` + `withdraw()` en principal |

---

### Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `utils/security.py` | Migrado a bcrypt |
| `database/connection.py` | Manejo de `:memory:` para tests |
| `tests/conftest.py` | Fixture DB en memoria con patch de DB_PATH |
| `repositories/estudiante_repository.py` | Filtro `estado` en `obtener_todos` |
| `services/estudiante_service.py` | `id_usuario` dinámico + filtro `estado` |
| `services/persona_service.py` | `id_usuario` dinámico |
| `services/apoderado_service.py` | `id_usuario` dinámico |
| `services/matricula_service.py` | `id_usuario` dinámico + código muerto eliminado |
| `services/dashboard_service.py` | Usa `configuracion_repository` |
| `controllers/estudiante_controller.py` | `_get_id_usuario()` + `obtener_apoderado_por_persona()` |
| `controllers/persona_controller.py` | `_get_id_usuario()` |
| `controllers/matricula_controller.py` | `_get_id_usuario()` |
| `controllers/pago_controller.py` | `listar_matriculas_activas()` |
| `views/estudiantes/estudiante_view.py` | Filtro retirados + sin imports de repository |
| `views/pagos/pago_view.py` | Sin imports de repository |
| `views/login/login_view.py` | Centrado + diseño mejorado + fix ventana al frente |
| `main.py` | Centrado + pantalla bienvenida + sidebar con emojis + fix withdraw durante login |
| `views/matriculas/matricula_view.py` | Auto-categoría por edad al seleccionar estudiante |
| `views/configuracion/configuracion_view.py` | Sección Categorías de Edad (admin CRUD) |
| `views/tarifas/tarifa_view.py` | Vista CRUD de tarifas con nuevos campos |
| `controllers/tarifa_controller.py` | Controller de tarifas |
| `controllers/categoria_controller.py` | Controller de categorías |
| `services/tarifa_service.py` | Tarifas con descripcion/observaciones |
| `services/categoria_service.py` | Service CRUD categorías |
| `repositories/tarifa_repository.py` | INSERT/UPDATE con nuevos campos |
| `repositories/categoria_repository.py` | Repository CRUD categorías |
| `models/tarifa.py` | Campos descripcion/observaciones |
| `database/create_db.py` | Columnas tarifas + schema categorías |
| `tests/*.py` | 8 archivos de tests |

---

## Base de Datos en Tests vs Producción

Los tests usan SQLite `:memory:` (en memoria) para:
- Ser rápidos (no tocan disco)
- No contaminar la DB real
- Resetearse automáticamente entre tests

**La app de producción SIEMPRE usa `academia.db`** (archivo en disco). Al ejecutar `python main.py`:
1. Se crea `academia.db` si no existe
2. Se ejecuta `create_tables()` + `seed_database()`
3. Los datos persisten entre sesiones

**Nota:** Con el cambio a bcrypt (Bug #18), si ya tenías una `academia.db` antigua, debes eliminarla y volver a ejecutar `python main.py` para que se regenere con hashes bcrypt.

---

## Resumen de Cambios — Sprint 10 (hasta ahora)

### Tests (78 tests, 100% pasan)

| Archivo | Tests | Tipo |
|---------|-------|------|
| `test_validators.py` | 18 | Unitario |
| `test_security.py` | 7 | Unitario |
| `test_dates.py` | 15 | Unitario |
| `test_cuota_service.py` | 11 | Service |
| `test_estudiante_service.py` | 8 | Service |
| `test_pago_service.py` | 7 | Service |
| `test_login.py` | 6 | Integración |
| `test_matriculas.py` | 6 | Integración |
| **TOTAL** | **78** | |

### Bugs Corregidos

| Bug | Archivos | Descripción |
|-----|----------|-------------|
| #7 | services/*.py, controllers/*.py | `id_usuario=1` → parámetro dinámico desde sesión |
| #12 | estudiante_view.py, estudiante_repository.py | Filtro "Retirados" usa `estado=RETIRADO` en vez de `activo=0` |
| #18 | utils/security.py | SHA-256 → bcrypt (hash seguro) |
| #8-9 | pago_view.py, pago_controller.py | View ya no llama a repository directamente |
| #10 | estudiante_view.py, estudiante_controller.py | View ya no llama a repository directamente |
| #16 | dashboard_service.py | Service ya no usa SQL directo, usa configuracion_repository |
| #19 | database/academia.db | DB estaba en `database/academia.db` (no raíz). `__pycache__` tenía `.pyc` viejo con SHA-256, causaba hash inválido al regenerar DB |
| #20 | views/login/login_view.py, main.py | Login aparecía detrás de la ventana principal. Fix: `lift()`/`focus_force()`/`topmost` temporal + `withdraw()` en principal durante login |

---

## Bugs #19 y #20 — Post-Sprint 10

### Bug #19: Hash SHA-256 en DB a pesar de migrar a bcrypt

**Fecha:** 2026-08-02
**Causa raíz:** La `academia.db` está en `database/academia.db`, NO en la raíz del proyecto. Al intentar regenerar la DB eliminando `academia.db` (raíz), se creaba una nueva pero el `__pycache__/security.cpython-313.pyc` tenía el código viejo compilado (SHA-256), así que el seed guardaba hashes inválidos.

**Síntoma:** Login mostraba "Credenciales incorrectas o usuario desactivado" con usuario `admin` / `admin123`.

**Solución:**
1. Limpiar todos los `__pycache__/` del proyecto (no del .venv)
2. Eliminar `database/academia.db` (ruta correcta)
3. Regenerar DB con `create_tables()` + `seed_database()` (ahora usa bcrypt correctamente)

**Lección aprendida:** Después de cambiar algoritmos de hash, SIEMPRE limpiar `__pycache__` y regenerar la DB.

---

### Bug #20: Login aparecía detrás de la ventana principal

**Fecha:** 2026-08-02
**Causa raíz:** `LoginView` es un `CTkToplevel` que se creaba sin `lift()` ni `focus_force()`. La ventana principal (`App`) quedaba visible detrás.

**Síntoma:** La pantalla de login se mostraba detrás de la ventana de bienvenida.

**Solución en `views/login/login_view.py`:**
```python
def _elevar_ventana(self):
    self.lift()
    self.focus_force()
    self.attributes("-topmost", True)
    self.after(200, lambda: self.attributes("-topmost", False))
```

**Solución en `main.py`:**
```python
def _abrir_login(self):
    self.withdraw()  # Ocultar ventana principal
    LoginView(self, on_login_success=self._on_login_success)

def _on_login_success(self, usuario):
    self.deiconify()  # Restaurar ventana principal
    self.lift()
    self.focus_force()
```

---

## Ideas Futuras — Tarifas y Categorías ✅ IMPLEMENTADAS

### 1. Auto-asignación de categoría por edad (en Matrícula) ✅

**Dónde:** `views/matriculas/matricula_view.py` + `controllers/matricula_controller.py`

**Implementación:** Al seleccionar estudiante en el combo, se calcula edad con `calculate_age(fecha_nacimiento)`, se busca categoría con `edad_min <= edad <= edad_max`, y se auto-selecciona la tarifa correspondiente.

**Archivos:**
- `controllers/matricula_controller.py` — `obtener_tarifa_sugerida_por_edad()`
- `views/matriculas/matricula_view.py` — callback `_on_estudiante_changed()`

---

### 2. Tarifas más configurables ✅

**Campos agregados a tabla `tarifa`:**
- `descripcion TEXT` — descripción de la tarifa
- `observaciones TEXT` — notas internas

**Archivos modificados:**
- `database/create_db.py` — columnas `descripcion`, `observaciones`
- `models/tarifa.py` — campos `descripcion`, `observaciones`
- `repositories/tarifa_repository.py` — INSERT/UPDATE con nuevos campos
- `services/tarifa_service.py` — crear/editar con nuevos campos
- `views/tarifas/tarifa_view.py` — formulario completo con nuevos campos
- `controllers/tarifa_controller.py` — controller nuevo

---

### 3. Gestionar Categorías y Tarifas desde Configuración (Admin) ✅

**Dónde:** `views/configuracion/configuracion_view.py`

**Sección implementada:** "Categorías de Edad" (solo visible para ADMIN)

**Funcionalidades:**
- Ver lista de categorías activas
- Crear/editar/desactivar categorías (nombre, edad_min, edad_max)
- Botones de acción en cada categoría

**Archivos creados:**
- `controllers/categoria_controller.py` — CRUD de categorías
- `services/categoria_service.py` — lógica de negocio
- `repositories/categoria_repository.py` — acceso a datos

---

## Prioridad 11 — Extras (Opcional)

| # | Item | Descripción |
|---|------|-------------|
| 1 | Mejorar error handling en `main.py` | Usar `messagebox.showerror()` en vez de `print()` para errores críticos |
| 2 | Logging en backup/restore | Registrar operaciones de backup/restore en tabla `log` |
| 3 | Validación en restore | Verificar integridad del archivo SQLite antes de restaurar |

