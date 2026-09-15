"""Seed atómico ante arranques simultáneos (red LAN, 4 PCs)."""
import sqlite3
import threading


def _db_tmp(tmp_path):
    ruta = str(tmp_path / "race.db")
    conn = sqlite3.connect(ruta, timeout=20)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL)")
    conn.commit()
    return ruta


def test_asegurar_sin_duplicados_con_hilos(tmp_path):
    from database.seed import _asegurar
    ruta = _db_tmp(tmp_path)
    barrera = threading.Barrier(4)
    resultados, errores = [], []

    def _worker():
        try:
            c = sqlite3.connect(ruta, timeout=20)
            barrera.wait(timeout=10)
            for _ in range(5):
                r = _asegurar(
                    c,
                    "SELECT id FROM t WHERE nombre=?", ("x",),
                    "INSERT INTO t (nombre) VALUES (?)", ("x",),
                )
                resultados.append(r["id"] if r else None)
            c.commit()
            c.close()
        except Exception as e:  # noqa: BLE001
            errores.append(e)

    hilos = [threading.Thread(target=_worker) for _ in range(4)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=30)
    assert not errores
    assert resultados and all(r == resultados[0] for r in resultados)
    c = sqlite3.connect(ruta)
    assert c.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    c.close()


def test_doble_seed_secuencial_sin_error():
    from database.seed import seed_database
    from repositories import usuario_repository
    seed_database()
    seed_database()
    assert usuario_repository.obtener_por_username("admin") is not None


def test_initialize_reintenta_lock(monkeypatch):
    import main as app_main
    llamadas = {"n": 0}

    def _falla_una_vez():
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(app_main, "create_tables", _falla_una_vez)
    monkeypatch.setattr(app_main, "seed_database", lambda: None)
    app_main.initialize_system()  # no debe lanzar
    assert llamadas["n"] == 2


def test_initialize_lock_persistente_lanza(monkeypatch):
    import main as app_main

    def _siempre_lock():
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(app_main, "create_tables", _siempre_lock)
    monkeypatch.setattr(app_main, "seed_database", lambda: None)
    try:
        app_main.initialize_system()
    except sqlite3.OperationalError as e:
        assert "locked" in str(e).lower()
    else:
        raise AssertionError("debió lanzar")
