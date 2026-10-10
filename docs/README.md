# Documentación — Academia Deportiva

> **Índice** organizado por dominio. Prioridad: `AGENTS.md > sistema/reglas_negocio.md > sistema/arquitectura_bd.md > sistema/diccionario_datos.md > sistema/arquitectura_software.md > sistema/convenciones_codigo.md` (ver `AGENTS.md`).

### Estructura

```
docs/
├── sistema/              # Reglas y diseño del sistema (fuente de verdad)
│   ├── reglas_negocio.md              # RN-001..050 (inscripción, mensualidad, ventas, OneDrive)
│   ├── arquitectura_software.md       # Capas View→Controller→Service→Repository→SQLite
│   ├── arquitectura_bd.md             # Tablas, relaciones, índices (antes AcademiaFutbol_Arquitectura_BD.md)
│   ├── diccionario_datos.md           # Campos, tipos, checks, índices
│   ├── casos_uso.md                   # Actores y flujos (estudiante, apoderado, pago, venta)
│   └── convenciones_codigo.md         # snake_case, PascalCase, dataclass, logging
│
├── desarrollo/           # Evolución por línea de tiempo (ver TIMELINE.md)
│   ├── TIMELINE.md                    # Índice cronológico (árbol de cambios por fecha)
│   ├── linea-tiempo/                  # Un resumen por hito (YYYY-MM-DD_slug.md)
│   ├── archivo/                       # Históricos superados/ejecutados (solo lectura)
│   ├── roadmap.md                     # Hacia dónde va el producto (vigente)
│   ├── plan_sprints.md                # Cómo se trabaja por sprints (vigente)
│   ├── changelog.md                   # Qué trae cada release (canónico)
│   ├── cambios_RN_v2.md               # Delta v2 flexible (precios, uniformes, OneDrive)
│   ├── plan_dayanna_v2.1.md           # v2.1: es_nuevo, conceptos, permisos secretaria
│   ├── plan_accion_cierre.md          # Backlog v1.3→v1.5 (diseño)
│   ├── plan_deuda_tecnica.md          # Deuda crítica/media/baja y sprints
│   ├── plan_inventario_escalable.md   # Diseño futuro inventario (tallas/lotes/sedes)
│   └── plan_red_lan.md + red_lan_evaluacion.md  # Red LAN: diseño + evaluación
│
├── changelog.md            # Redirect → desarrollo/changelog.md (canónico)
│
├── testing/              # Calidad
│   └── tests_registro.md              # Cobertura, fixtures, markers
│
├── despliegue/           # Instalación y operación
│   ├── instalacion.md                 # Wizard Inno Setup
│   ├── despliegue_produccion.md       # OneDrive central BD no se mueve
│   ├── actualizacion.md
│   └── publicacion_release.md         # VERSION → tag → Release ZIP
│
└── manuales/             # Uso (md + pdf listos para imprimir/entregar)
    ├── manual_sistema.md/.pdf         # Uso diario ADMIN/SECRETARIA
    └── manual_flujos.md/.pdf          # Paso a paso + casuísticas + matriz de pruebas por release
```

### Cómo navegar

- **¿Nueva regla?** → `sistema/reglas_negocio.md` (RN) → `sistema/arquitectura_bd.md` (DDL) → `sistema/diccionario_datos.md`.
- **¿Qué cambió y cuándo?** → `desarrollo/TIMELINE.md` (línea de tiempo por fecha) → `desarrollo/linea-tiempo/` (resumen) → `desarrollo/archivo/` (detalle histórico).
- **¿Nuevo feature?** → `desarrollo/roadmap.md` → `desarrollo/plan_sprints.md` → `desarrollo/plan_dayanna_v2.1.md` (v2.1 documentado: es_nuevo, conceptos sin redundancia, permisos secretaria).
- **¿Deploy?** → `despliegue/despliegue_produccion.md` + `setup_onedrive.bat` (raíz).
- **¿Uso?** → `manuales/manual_sistema.md`.
- **¿Probar un flujo / release?** → `manuales/manual_flujos.md`.
- **¿Instalar en una PC?** → `despliegue/guia_instalacion.md` (Setup + ZIP + red + bloqueos, lenguaje simple).

> **Nota migración:** `docs/` antes plano; ahora agrupado. Rutas antiguas redirigen aquí. Artefactos en raíz: `setup_onedrive.bat`, `config.ini` (generado), `VERSION`.
