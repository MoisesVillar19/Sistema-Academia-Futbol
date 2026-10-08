from database.connection import get_connection, fetch_one
from models.configuracion import Configuracion
from utils.dates import get_now


def obtener_configuracion() -> dict | None:
    return fetch_one("SELECT * FROM configuracion WHERE id_configuracion = 1")


def actualizar(config: Configuracion) -> None:
    conn = get_connection()
    now = get_now()
    conn.execute(
        """UPDATE configuracion SET
           nombre_academia = ?, direccion = ?, telefono = ?, correo = ?,
           mora_habilitada = ?, tipo_mora = ?, porcentaje_mora = ?, monto_mora = ?,
           dias_por_vencer = ?, permitir_multiples_becas = ?,
           backup_automatico = ?, frecuencia_backup = ?,
           ruta_backup = ?, correo_onedrive = ?,
           pin_emergencia = ?, precio_inscripcion = ?, precio_mensualidad = ?, precio_uniforme = ?,
            precio_reingreso = ?, tasa_campeonato = ?, arbitraje_por_equipo = ?, pago_profesor = ?,
            frecuencia_profesores = ?, frecuencia_profesores_dias = ?,
            fecha_actualizacion = ?
            WHERE id_configuracion = ?""",
        (
            config.nombre_academia,
            config.direccion,
            config.telefono,
            config.correo,
            config.mora_habilitada,
            config.tipo_mora,
            config.porcentaje_mora,
            config.monto_mora,
            config.dias_por_vencer,
            config.permitir_multiples_becas,
            config.backup_automatico,
            config.frecuencia_backup,
            config.ruta_backup,
            config.correo_onedrive,
            config.pin_emergencia,
            config.precio_inscripcion,
            config.precio_mensualidad,
            config.precio_uniforme,
            config.precio_reingreso,
            config.tasa_campeonato,
            config.arbitraje_por_equipo,
            config.pago_profesor,
            config.frecuencia_profesores,
            config.frecuencia_profesores_dias,
            now,
            config.id_configuracion,
        ),
    )
    conn.commit()
