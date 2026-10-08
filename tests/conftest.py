import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services import matricula_service
from repositories import cuota_repository
from models.tarifa import Tarifa
from utils.dates import get_today


@pytest.fixture(autouse=True)
def test_db():
    """Base de datos en memoria para cada test."""
    import database.connection as conn_module
    import utils.constants as const_module

    original_db_name = const_module.DB_NAME
    original_db_path = const_module.DB_PATH
    original_conn_db_path = getattr(conn_module, 'DB_PATH', None)

    if conn_module._connection is not None:
        conn_module._connection.close()
        conn_module._connection = None
        conn_module._nivel_transaccion = 0

    const_module.DB_NAME = ":memory:"
    const_module.DB_PATH = ":memory:"
    conn_module.DB_PATH = ":memory:"

    from database.create_db import create_tables
    from database.seed import seed_database
    create_tables()
    seed_database()
    # Cachés en memoria fuera de la BD: resetear por test.
    try:
        from services import avisos_service
        avisos_service.invalidar_cache_avisos()
    except Exception:
        pass
    try:
        from services import dashboard_service
        dashboard_service._ULTIMA_MORA_TS = 0.0
    except Exception:
        pass

    yield

    from database.connection import close_connection
    close_connection()
    const_module.DB_NAME = original_db_name
    const_module.DB_PATH = original_db_path
    if original_conn_db_path is not None:
        conn_module.DB_PATH = original_conn_db_path


@pytest.fixture
def usuario_admin():
    """Sesion iniciada como administrador (usuario seed)."""
    from services import auth_service
    usuario = auth_service.login("admin", "admin123")
    assert usuario is not None
    yield usuario
    auth_service.logout()


@pytest.fixture
def usuario_secretaria(usuario_admin):
    """Crea un usuario SECRETARIA e inicia sesion con el."""
    from services import usuario_service, auth_service
    exito, temp_pass, _ = usuario_service.crear_usuario(
        {"dni": "55555555", "nombres": "Secretaria", "apellidos": "De Prueba"},
        "secretaria_test",
        "SECRETARIA",
    )
    assert exito, temp_pass
    auth_service.logout()
    usuario = auth_service.login("secretaria_test", temp_pass)
    assert usuario is not None
    yield usuario
    auth_service.logout()


# ── Factories de datos ──────────────────────────────────────────

@pytest.fixture
def crear_persona():
    """Factory: inserta una persona con DNI unico. Retorna id_persona."""
    contador = {"n": 0}

    def _factory(**overrides) -> int:
        contador["n"] += 1
        datos = {
            "dni": f"7{contador['n']:07d}",
            "nombres": "Persona",
            "apellidos": f"Test{contador['n']}",
            "fecha_nacimiento": "2015-04-10",
            "sexo": "M",
        }
        datos.update(overrides)
        from models.persona import Persona
        from repositories import persona_repository
        return persona_repository.insertar(Persona(**datos))

    return _factory


@pytest.fixture
def crear_estudiante(crear_persona):
    """Factory: crea persona + estudiante. Retorna id_estudiante."""
    def _factory(estado="ACTIVO", **persona_overrides) -> int:
        id_persona = crear_persona(**persona_overrides)
        from models.estudiante import Estudiante
        from repositories import estudiante_repository
        estudiante = Estudiante(
            id_persona=id_persona,
            estado=estado,
            fecha_ingreso=get_today(),
        )
        return estudiante_repository.insertar(estudiante)

    return _factory


@pytest.fixture
def obtener_tarifa():
    """Retorna (id_tarifa, monto) de la primera tarifa activa; la crea si no hay."""
    def _factory(monto: float | None = None) -> tuple[int, float]:
        from repositories import tarifa_repository
        from database.connection import fetch_one
        tarifas = tarifa_repository.obtener_activas()
        if tarifas and monto is None:
            return tarifas[0]["id_tarifa"], tarifas[0]["monto"]
        if monto is None:
            monto = 200.0
        cat = fetch_one("SELECT id_categoria FROM categoria WHERE activo = 1 LIMIT 1")
        assert cat is not None
        id_tarifa = tarifa_repository.insertar(Tarifa(
            id_categoria=cat["id_categoria"],
            nombre="Tarifa Test",
            monto=monto,
        ))
        return id_tarifa, monto

    return _factory


@pytest.fixture
def crear_matricula(crear_estudiante, obtener_tarifa):
    """Factory: estudiante + matricula activa con primera cuota automatica.

    Retorna dict con id_estudiante, id_matricula e id_cuota.
    """
    def _factory(id_estudiante=None, id_tarifa=None, monto_pactado=200.0,
                 dia_vencimiento=15, **extras) -> dict:
        if id_estudiante is None:
            id_estudiante = crear_estudiante()
        if id_tarifa is None:
            id_tarifa, _ = obtener_tarifa()
        data = {
            "id_estudiante": id_estudiante,
            "id_tarifa": id_tarifa,
            "monto_pactado": monto_pactado,
            "dia_vencimiento": dia_vencimiento,
        }
        data.update(extras)
        exito, msg, id_matricula = matricula_service.crear_matricula(data)
        assert exito, msg
        cuotas = cuota_repository.obtener_por_matricula(id_matricula)
        return {
            "id_estudiante": id_estudiante,
            "id_matricula": id_matricula,
            "id_cuota": cuotas[0]["id_cuota"] if cuotas else None,
        }

    return _factory


# ── Infraestructura UI (marker: ui) ─────────────────────────────

@pytest.fixture(scope="session")
def ctk_root():
    """Raiz CustomTkinter compartida para toda la sesion de tests UI."""
    try:
        import customtkinter as ctk
        root = ctk.CTk()
        root.geometry("1280x800+0+0")
        root.update_idletasks()
    except Exception as e:  # sin display / entorno headless
        pytest.skip(f"Display no disponible para pruebas UI: {e}")
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def crear_vista(ctk_root):
    """Factory que instancia vistas y garantiza su destruccion al terminar."""
    creadas = []

    def _factory(cls, *args, **kwargs):
        vista = cls(ctk_root, *args, **kwargs)
        creadas.append(vista)
        ctk_root.update_idletasks()
        return vista

    yield _factory

    for vista in creadas:
        try:
            if vista.winfo_exists():
                vista.destroy()
        except Exception:
            pass

    # Limpiar Toplevels residuales (ej. formulario oculto de TarifaView)
    import customtkinter as ctk
    for hijo in list(ctk_root.winfo_children()):
        try:
            hijo.destroy()
        except Exception:
            pass
    try:
        ctk_root.update()
    except Exception:
        pass
