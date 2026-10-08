# AcademiaFutbol — Sistema de Gestión v1.2.0

> **Academia Deportiva Roncalli.** Matrículas, mensualidades, cobros
> (cuotas/inscripción/campeonatos), tienda, uniformes por talla, egresos,
> inventario, dashboard Pro (tablas + gráficos + comparativa MoM), reportes,
> auditoría con usuario, backups con fallback local. **BD única en red LAN**
> (`\\SERVIDOR\Academia\academia.db`) + **precios en Tarifas**.

[![Versión](https://img.shields.io/badge/versión-1.2.0-blue)]() `VERSION`

### Inicio rápido

1. **Red:** en cada PC ejecuta **`setup_red.bat "\\SERVIDOR\Academia"`**
   (verifica lectura/escritura y escribe `config.ini`).Detalle en
   `docs/despliegue/guia_instalacion.md`.
2. **App:** `py main.py` (dev) o instala `AcademiaFutbol-Setup-1.2.0.exe`
   o extrae `AcademiaFutbol-v1.2.0.zip` (portable, sin admin).
3. **Login:** `admin / admin123` → cambia la clave → crea usuarios
   SECRETARIA → verifica Tarifas y Probar conexión.

> Sin red: fallback a BD local. Nunca copies `academia.db` entre PCs.

### Estructura del proyecto

```
AcademiaFutbol/
├── main.py + VERSION + config.ini (generado)
├── setup_red.bat              # Apunta cada PC al recurso compartido
├── database/  connection.py (journal adaptativo red/local, timeout, cierre limpio),
│              create_db.py (migraciones), seed.py (idempotente), backup.py, restore.py
├── models/  dataclass (@dataclass)
├── repositories/  solo INSERT/UPDATE/SELECT, soft delete activo=0
├── services/  matricula, pago, venta (campeonato por tarifa), uniforme_service
│              (asegurado único + tallas), egreso, cuota (mora + edición),
│              dashboard (comparativa MoM), backup (fallback local)
├── controllers/  login, estudiante, matricula, pago, venta, egreso, beca,
│                 inventario, categoria, tarifa, reporte, auditoria, importar,
│                 usuario (roles + matriz de permisos), configuracion
├── views/  dashboard Pro, estudiantes, matriculas, mensualidades (por
│           estudiante + general, edición), cobros (historial/registro/
│           mensualidades/campeonatos/morosos), tiendita (ganancias por
│           venta y por producto), uniformes (productos + tallas + ventas),
│           egresos (por grupos + frecuencia profesores), inventario,
│           tarifas+becas, usuarios+permisos, reportes, auditoria,
│           configuracion, importar, login
├── utils/  constants (rutas red/local, topes anti-instancias), validators,
│           security (bcrypt), ui_helpers (secciones, cards, toggle),
│           dates, logger
├── widgets/  date_picker.py, periodo_filter.py (año + trimestre/meses + orden),
│              loading_dialog.py, debounce, pagination
├── installer/  setup.iss (Inno Setup), build_installer.bat, README_BLOQUEO.txt
├── updater/  automático (descarga → aplica al salir → relanza), dual
│             Setup/ZIP con barra de progreso (%, MB/s, ETA), anti-downgrade
├── docs/  sistema/ + desarrollo/ (incl. plan_red_lan.md) + despliegue/
│          (guia_instalacion.md/.pdf, despliegue_red.md) + manuales/ (.md + .pdf)
└── tools/md_to_pdf.py  # genera los PDF de la documentación
```

### Documentación

- Uso: `docs/manuales/manual_sistema.md(.pdf)` · Flujos y casos:
  `docs/manuales/manual_flujos.md(.pdf)` · Instalación:
  `docs/despliegue/guia_instalacion.md(.pdf)` · Red:
  `docs/despliegue/despliegue_red.md` · Decisiones: `docs/desarrollo/plan_red_lan.md`
- Índice: `docs/README.md`. Prioridad:
  `AGENTS.md > sistema/reglas_negocio > arquitectura_bd > diccionario > arquitectura_software`

### Flujos clave

- **Nuevo:** Estudiante 🆕 → Matrícula (tarifa/monto) + ☑ uniforme con talla (venta inmediata) → cuota PENDIENTE
- **Reingreso:** Retirar → Reingresante → matrícula **nueva** (no reactiva)
- **Mensualidad:** tarifa por edad/vigencia o monto pactado (0 = gratuito) + beca %/monto + diferir 2-3; editable con auditoría
- **Cobros:** parcial/total, comprobante opcional, PARCIAL→PAGADO automático; pestañas por concepto
- **Campeonato:** división (tarifa) → jala el monto al cobro; arbitraje vinculado = neto por división
- **Egresos:** por grupos (Profesores/Operativos/Campeonatos) + recordatorio mensual/quincenal/personalizado
- **Importación:** celda 150 = matrícula de nuevo (cuota 120 + uniforme 30); 70 solo = uniforme aparte; idempotente (adopta, nunca duplica)
- **Precios:** todo en Tarifas (ACADEMIA/CAMPEONATO/SERVICIO); egresos PROFESOR/ARBITRAJE con monto sugerido editable

### Roles

- **ADMIN:** todo (Usuarios, Tarifas+Becas, Auditoría, Configuración, Importar, Restaurar, Almacén).
- **SECRETARIA:** Dashboard, Estudiantes, Matrículas, Mensualidades, Cobros, Tienda, Uniformes, Egresos, Reportes, Respaldo manual. Matriz ajustable en Usuarios → Permisos por rol.

### Requisitos

- Windows 10/11, red LAN con carpeta compartida (servidor siempre encendido en horario)
- Dev: Python 3.13, `pip install -r requirements.txt`
- 4 GB RAM, 500 MB disco

### Troubleshooting

- `No se puede acceder a la base de datos` → encender servidor, revisar red/recurso
- App no reabre → terminar `AcademiaFutbol.exe` en Administrador de tareas
- Bloqueo SmartScreen/antivirus → `guia_instalacion.md` §7 (o usar ZIP)
- Dato borrado → restaurar backup con PIN (ADMIN, demás PCs cerradas)
- Dato mal pasado → editar desde Mensualidades o Ganancias (queda en auditoría)

### Licencia

Privado — Academia Deportiva Roncalli.
