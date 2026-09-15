# Despliegue en Red LAN — 4 PCs, BD única (Modelo A+C)

> Evaluación honesta de la arquitectura (bitácora de incidentes, riesgos
> inherentes y punto de quiebre a cliente-servidor):
> `../desarrollo/red_lan_evaluacion.md`. Leer antes de culpar a la red.

> Topología decidida: una PC hace de servidor con carpeta compartida;
> las 4 PCs abren el **mismo** `academia.db` por UNC. Sin copias, sin merges.

## 1. Topología y requisitos

```text
PC1 (servidor, encendida en horario) ── \\PC1\Academia\
│   ├─ academia.db · fotos\ · comprobantes\ · BackupsAcademia\
├── PC2 ──┐
├── PC3 ──├── mismo archivo (sin semillas duplicadas: el seed es idempotente)
└── PC4 ──┘   (otro router: ver §5)
```

- SQLite multi-proceso con file locking soporta 3–4 usuarios de bajo volumen.
  Cobros simultáneos: el segundo **espera** (`busy_timeout` 20s), no falla.
- **Prohibido WAL en red**: la app fija `journal_mode=DELETE` sola si la ruta
  es UNC/red (`database/connection.py:es_ruta_red`). No tocar.
- Fotos/comprobantes/backups también centrales (mismos archivos para todos).

## 2. Instalación por PC (orden)

**PC1 (servidor):**
1. Crear carpeta `C:\Academia` → clic derecho → Compartir → permiso **total**
   para los usuarios de las demás PCs. Anotar `\\PC1\Academia`
   (mejor IP fija, ej. `\\192.168.1.50\Academia`).
2. Firewall: permitir **SMB TCP/445** entrante (red privada).
3. Instalar app (Setup o ZIP) + `setup_red "\\PC1\Academia"` → verifica
   lectura/escritura y escribe `config.ini`.
4. Abrir la app una vez: crea y siembra la BD **una sola vez**.

**PC2–PC4:** instalar app → copiar el `config.ini` de PC1 (misma carpeta
que el `.exe`) **o** correr `setup_red "\\PC1\Academia"` → abrir y verificar
con **Probar conexión** (Configuración → Respaldo).

**Jamás**: copiar `academia.db` entre PCs, ni apuntar cada PC a su propio
archivo (eso crea 4 BDs divergentes). El guardián anti-huérfana impide
sembrar datos locales si el share no responde.

## 3. Plan de acción ante apagado del servidor (contingencia)

**Recomendado (normal):** encender PC1 → en cada PC, Configuración →
Probar conexión (OK) → seguir operando. Nada se perdió: los datos viven
en el share.

**Si hay que atender sin servidor (contingencia, honesta):**
1. La app avisa "Base de datos no disponible" y **no** crea datos locales
   silenciosos (evita divergencias imposibles de fusionar).
2. Atender con registro manual (papel/Excel temporal).
3. Al volver el servidor: re-digitar cobros/ventas del período en el sistema
   (usar folios del registro manual para no duplicar).
4. **No existe auto-merge** a propósito: fusionar SQLite genera colisiones
   de IDs y pérdida silenciosa. No se implementará.

**Cada PC** conserva backups automáticos locales del share (última copia
útil como referencia de lectura ante apagado prolongado): si el destino
central falla, el sistema guarda en la carpeta local y avisa
("copia LOCAL: destino central inaccesible").

## 4. Operativa diaria

- Cierre con X hace apagado limpio (checkpoint + `sys.exit`): no quedan
  procesos zombi reteniendo el `.db`. Si una PC no reabre, revisar
  Administrador de tareas por `AcademiaFutbol.exe` colgado y terminarlo.
- Recibos correlativos únicos incluso con cobros simultáneos (reintento).
- Restaurar backup: solo ADMIN + PIN (cierra a todos antes: el archivo
  no debe estar abierto en otra PC durante la restauración).

## 5. Checklist 4ª PC en otro router

1. IP fija (o reserva DHCP) en PC1; usar `\\IP\Academia`.
2. Regla firewall SMB/445 en PC1.
3. Misma credencial o usuario dedicado con permiso total al recurso.
4. Desde PC4: `dir \\IP\Academia` + crear/borrar archivo de prueba.
5. Opcional: `net use Z: \\IP\Academia /persistent:yes`.
6. Si el router aísla clientes (AP isolation): desactivar o cablear.
7. Probar conexión desde la app antes de operar.

## 6. Matriz de pruebas red (antes de cada release con cambios de BD/red)

- [ ] 2 PCs cobran a la vez (pagos + ventas) sin errores ni duplicados.
- [ ] Servidor apagado → mensaje claro, sin BD huérfana, sin cuelgue.
- [ ] Corte de red a media venta → rollback limpio; reintento OK al volver.
- [ ] Cerrar con X → sin proceso residual → reabre OK.
- [ ] Restaurar con PIN (avisar a las demás PCs que cierren).
- [ ] ZIP en PC bloqueada: `setup_red.bat` sin admin + arranque.
