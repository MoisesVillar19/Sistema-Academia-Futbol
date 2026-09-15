# Red LAN: evaluación honesta (una PC → 4 PCs en red privada)

> El sistema nació monousuario local. La red de 4 PCs llegó en despliegue
> y desde entonces se parchó incidente tras incidente. Este documento pone
> cada cosa en su sitio: qué era bug de app, qué es entorno y qué es
> límite real de la arquitectura. Sin maquillaje.

## 1. Bitácora: cada "algo diferente" y su causa real

| # | Síntoma en campo | Causa real | Tipo | Estado |
|---|---|---|---|---|
| 1 | Vistas no abrían (`debounce`/`event_bus`/`pagination`) | Módulos nuevos sin commitear | Bug app (empaquetado dev) | Fix + tests |
| 2 | Dashboard roto (`estudiante_repository` local) | Re-import dentro de función (UnboundLocalError) | Bug app | Fix + tests |
| 3 | Detalle dashboard vacío, 11 widgets invisibles | Viewport `CTkScrollableFrame` en 1x1 + frames que no encogen (quirks CTk 6.0) | Bug app (UI toolkit) | Fix + probes de píxeles |
| 4 | Cards solo clickeables en el borde | `CTkButton` 6.0 es compuesto y traga clics | Bug app (UI toolkit) | Fix (frames + clic propagado) |
| 5 | Sin gráficos/tablas | matplotlib ausente en Python del sistema (solo dev) | Entorno dev | Instalado + tests |
| 6 | Parpadeo al mover el mouse | Hovers reconfigurando colores + canvas matplotlib pesados | Bug app (rendimiento) | Fix (solo cursor + charts compactos) |
| 7 | App no reabre tras cerrar | Sin `sys.exit` + timers vivos (proceso zombi con el `.db`) | Bug app | Fix (apagado limpio) |
| 8 | Muerte muda al arrancar (cero log, cero ventana) | `except` con solo `print` en exe sin consola | Bug app (diagnóstico) | Fix (`crashlog.py`, diálogo fatal, fases) |
| 9 | `UNIQUE persona.dni` + `database is locked` al arrancar varias | Seed check-then-insert no atómico (carrera real) | **Bug app expuesto por red** | Fix (seed atómico + reintento) |
| 10 | App abría en OneDrive en vez del share | Doble generador de `config.ini` (installer vs `setup_red`) + fallback OneDrive | **Deuda de modelo** (época OneDrive) | Fix (OneDrive eliminado, setup_red manda) |
| 11 | Credenciales/1219/sesiones, share "invisible", servidor dormido | SMB + UAC split + energía + routers | **Entorno, no código** | Checklist + Credential Manager + guía |
| 12 | Antivirus bloquea exe en una PC | Heurística PyInstaller (falso positivo) | Entorno | Mitigado (version info, upx off, exclusión doc) |

Lectura: de 12 incidentes, **8 eran bugs de app que la red solo hizo visibles**
(en local pasaban piola), 3 son entorno puro y **1 solo** (nº 9) es conflicto
genuino de arquitectura compartida. No es que "la red rompa todo": es que
sin diagnóstico (`error_log.txt` no existía) cada síntoma parecía misterio
distinto.

## 2. Riesgos inherentes que QUEDAN (aunque el código esté perfecto)

Estos no se parchan: son física de archivo-compartido-SMB.

1. **Escrituras concurrentes se serializan.** Con 3–4 cobradores el `busy_timeout`
   lo absorbe (milisegundos–segundos). Con 10+ sería cola visible.
2. **SMB no es un servidor de BD.** Microcortes, `oplocks`, antivirus
   escaneando el `.db` abierto o dormir la PC pueden dar `OperationalError`
   esporádicos. La app reintenta arranque y opera atómica (rollback), pero
   un corte a media transacción se siente como error puntual.
3. **Punto único de falla:** PC1 apagada = nadie escribe (diseñado así + contingencia).
4. **Restaurar exige coordinación humana** (lock file ayuda, no lo automatiza todo).
5. **La 4ª PC en otro router** vive de la red externa: latencia y reglas fuera
   de nuestro control.

## 3. Veredicto: ¿sigue siendo viable el archivo compartido?

**Sí, para ESTE caso (4 PCs, bajo volumen, misma LAN, servidor normalmente
encendido), con todo lo endurecido.** Cada riesgo de §2 tiene mitigación
implementada y testeada (332 tests, varios de concurrencia real). El sistema
ya no está "parchado a ciegas": cada incidente dejó test de regresión +
diagnóstico que convierte el próximo misterio en 5 minutos de log.

## 4. Punto de quiebre: cuándo migrar de arquitectura (Plan B)

Si ocurre **cualquiera** de estos, el archivo compartido deja de bastar y se
migra a **cliente-servidor** (abajo). No antes: sería sobreingeniería hoy.

- Más de **2 incidentes de acceso a datos sin causa clara en 30 días**
  teniendo `error_log.txt` activo.
- Crecer a **6+ PCs** o necesitar acceso **fuera de la LAN** (internet).
- Necesidad de escritura intensiva real (colas visibles, esperas >5s).

### Plan B (diseño previo, sin picar aún)

PC1 corre un **mini-servidor HTTP** (stdlib o FastAPI) dueño **exclusivo**
del `.sqlite` en local (WAL permitido, un solo escritor → se evaporan los
riesgos §2.1–2.2). Los clientes cambian solo la capa `repositories/` por un
cliente HTTP con **las mismas firmas** (vistas y servicios intactos).
Sin cambio de schema ni de UI. Esfuerzo estimado: medio (shim de repositorios
+ servidor + auth por token + instalador del servicio). Alternativa
descartada por ahora: Postgres en PC1 (instalación y drivers pesados para
este despliegue).

## 5. Reglas para no reabrir la caja de Pandora

1. Un solo `config.ini` por PC, junto al exe, apuntando a la misma UNC.
2. Jamás copiar `academia.db`, jamás borrar `-wal/-shm` a ciegas.
3. Arrancar escalonado solo si el fix de seed no estuviera (ya lo está).
4. Ante síntoma nuevo: `error_log.txt` + hora + estado del servidor, antes de tocar nada.
