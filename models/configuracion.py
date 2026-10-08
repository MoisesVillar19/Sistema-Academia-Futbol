from dataclasses import dataclass


@dataclass
class Configuracion:
    id_configuracion: int | None = None
    nombre_academia: str = ""
    direccion: str = ""
    telefono: str = ""
    correo: str = ""
    mora_habilitada: int = 0
    tipo_mora: str = "PORCENTAJE"
    porcentaje_mora: float = 0.0
    monto_mora: float = 0.0
    dias_por_vencer: int = 3
    permitir_multiples_becas: int = 1
    backup_automatico: int = 1
    frecuencia_backup: int = 7
    ruta_backup: str = "backups/"
    correo_onedrive: str = ""
    pin_emergencia: str = ""
    precio_inscripcion: float = 100.0
    precio_mensualidad: float = 100.0
    precio_uniforme: float = 20.0
    precio_reingreso: float = 100.0
    tasa_campeonato: float = 15.0
    arbitraje_por_equipo: float = 15.0
    pago_profesor: float = 200.0
    frecuencia_profesores: str = "MENSUAL"
    frecuencia_profesores_dias: int = 30
    fecha_actualizacion: str = ""
