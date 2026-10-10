> **ARCHIVADO — documento histórico.** No usar como guía vigente. Resumen vigente en `../linea-tiempo/2026-08-01_sprints-7-10-estabilizacion.md` · Índice: `../TIMELINE.md`.

# Estado del Proyecto — AcademiaFutbol

**Fecha:** 2026-08-01
**Último sprint completado:** 9 (Configuración)
**Próximo sprint:** 10 (Estabilización)

---

## 1. Sprints Completados

| Sprint | Estado | Descripción |
|---|---|---|
| 1 (Database) | ✅ | Base de datos, modelos, seed, backup/restore |
| 2 (Security) | ✅ | Auth, usuarios, auditoría, login |
| 3 (Académica) | ✅ | Personas, apoderados, estudiantes |
| 4 (Matrículas) | ✅ | Tarifas, becas, matrículas, cuotas |
| 5 (Pagos) | ✅ | Pagos, detalle pagos |
| 6 (Inventario) | ✅ | Categorías, productos, movimientos |
| 7 (Dashboard) | ✅ | Dashboard interactivo con gráficos |
| 8 (Reportes) | ✅ | Exportación a Excel con selector de período |
| 9 (Configuración) | ✅ | Panel de configuración del sistema |

---

## 2. Bugs Corregidos en Sesión

| # | Bug | Archivo | Corrección |
|---|---|---|---|
| 5 | `obtener_pendientes_por_matricula(0)` retornaba vacío | `cuota_service.py` | Creada `obtener_todas_pendientes()` |
| 6 | `requiere_cambio_password()` retornaba False | `auth_service.py` | Cambiado a `verify_password()` |
| 1 | Import de `apoderado_controller` inexistente | `estudiante_view.py` | Eliminado import |
| 2-3 | `valor_nuevos` (singular) en `registrar_update()` | `estudiante_service.py` | Corregido a `valores_nuevos` |
| 4 | `valor_anteriores`/`valor_nuevos` en `registrar_log()` | `usuario_service.py` | Corregido a singular |

---

## 3. Bugs Pendientes (Sprint 10)

### CRÍTICOS

| # | Bug | Severidad | Archivos | Descripción |
|---|-----|-----------|----------|-------------|
| 7 | `id_usuario=1` hardcodeado | ALTA | 17 ocurrencias en services | Auditoría no registra usuario real |
| 18 | SHA-256 débil | ALTA | `utils/security.py` | Usar bcrypt (ya en requirements.txt) |
| 19 | Credenciales hardcodeadas | BAJA | `utils/constants.py` | admin/admin123 en código fuente |

### MEDIOS

| # | Bug | Severidad | Archivos | Descripción |
|---|-----|-----------|----------|-------------|
| 8 | View → Repository | MEDIA | `pago_view.py:192` | `matricula_repository` importado directamente |
| 9 | View → Service | MEDIA | `pago_view.py:203` | `cuota_service` importado directamente |
| 10 | View → Repository | MEDIA | `estudiante_view.py:379` | `apoderado_repository` importado directamente |
| 12 | Filtro "Retirados" erróneo | MEDIA | `estudiante_view.py:284-285` | Filtra `activo=0` en vez de `estado='RETIRADO'` |
| 16 | Service → Database | MEDIA | `dashboard_service.py:115` | `database.connection.fetch_one` directo |

### BAJOS

| # | Bug | Severidad | Archivos | Descripción |
|---|-----|-----------|----------|-------------|
| 14 | Código muerto | BAJA | `matricula_service.py:39` | Variable `tarifa` sin usar |
| 15 | Import redundante | BAJA | `matricula_service.py:69` | Re-importa `estudiante_repository` |
| 17 | Código muerto | BAJA | `database/connection.py:27-32` | Función `execute_query()` sin usar |
| 20 | Import muerto | BAJA | `repositories/estudiante_apoderado_repository.py:2` | `get_now` sin usar |
| 21 | Sin feedback | BAJA | `views/usuarios/usuario_view.py:152-160` | Error silencioso al activar/desactivar |
| 22 | Ambigüedad | BAJA | `services/inventario_service.py:167` | AJUSTE usa `cantidad` como absoluto |
| 24 | Fallback silencioso | BAJA | `services/dashboard_service.py:52-62` | `_ultimo_dia_mes` retorna 30 en error |
| 25 | Error handling básico | BAJA | `main.py` | `print()` en vez de `messagebox` para errores críticos |
| 26 | Sin logging backup | BAJA | `database/backup.py` | No registra operaciones en auditoría |
| 27 | Sin validación restore | BAJA | `database/restore.py` | No verifica integridad después de restaurar |

---

## 4. Violaciones de Arquitectura Pendientes

| Ubicación | Violación | Corrección |
|-----------|-----------|------------|
| `pago_view.py:192` | View → Repository | Crear función en `pago_controller` |
| `pago_view.py:203` | View → Service | Crear función en `pago_controller` |
| `estudiante_view.py:379` | View → Repository | Usar `estudiante_controller` |
| `dashboard_service.py:115` | Service → Database | Usar `configuracion_repository` |

---

## 5. Cursos Pendientes

| Curso | Archivos | Estado |
|-------|----------|--------|
| Validators | `utils/validators.py` | Sin tests |
| Security | `utils/security.py` | Sin tests |
| Dates | `utils/dates.py` | Sin tests |
| Cuota Service | `services/cuota_service.py` | Sin tests |
| Pago Service | `services/pago_service.py` | Sin tests |
| Estudiante Service | `services/estudiante_service.py` | Sin tests |
| Login Flow | `controllers/login_controller.py` | Sin tests |
| Matrícula Flow | `controllers/matricula_controller.py` | Sin tests |

---

## 6. Archivos Faltantes

| Archivo | Descripción |
|---------|-------------|
| `tests/conftest.py` | Configuración de pytest |
| `tests/test_validators.py` | Tests de validadores |
| `tests/test_security.py` | Tests de seguridad |
| `tests/test_cuota_service.py` | Tests de servicio de cuotas |
| `tests/test_pago_service.py` | Tests de servicio de pagos |
| `tests/test_estudiante_service.py` | Tests de servicio de estudiantes |
| `tests/test_login.py` | Tests de login (vacío) |
| `tests/test_matriculas.py` | Tests de matrículas |
| `.env` | Variables de entorno (vacío) |
| `.env.example` | Ejemplo de variables (vacío) |

---

## 7. Dependencias No Usadas

| Paquete | Estado |
|---------|--------|
| `bcrypt` | Instalado pero no usado (debería reemplazar SHA-256) |
| `pandas` | Instalado pero no usado |
| `reportlab` | Instalado pero no hay funcionalidad PDF |
| `tkcalendar` | Instalado pero no usado |
| `python-dotenv` | Instalado pero nunca importado |
| `pytest` | NO instalado (necesario para tests) |

---

## 8. Estado del Git

- ✅ Commit de Sprints 1-9 realizado
- ✅ Push a GitHub exitoso
- Repo: https://github.com/MoisesVillar19/AcademiaFutbol

---

## 9. Próximo: Sprint 10 — Estabilización

### Orden de ejecución

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

### Base de datos para tests

- Se usa `:memory:` (SQLite en memoria)
- No se toca `academia.db` (datos de cada usuario)
- Se crea automáticamente al ejecutar `python main.py`

Ver archivo: `docs/sprint10_plan.md`

