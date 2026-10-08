from repositories import categoria_repository
from services import auditoria_service
from utils.logger import logger


TIPOS_CATEGORIA = ("ACADEMIA", "CAMPEONATO", "SERVICIO")


def _validar_edades(tipo: str, edad_min, edad_max) -> tuple[bool, str, int | None, int | None]:
    """Edad obligatoria solo en ACADEMIA; en CAMPEONATO/SERVICIO es opcional."""
    if tipo != "ACADEMIA" and (edad_min in (None, "") and edad_max in (None, "")):
        return True, "", None, None
    try:
        edad_min = int(edad_min)
        edad_max = int(edad_max)
    except (ValueError, TypeError):
        return False, "Las edades deben ser números", None, None
    if edad_min < 0 or edad_max < 0:
        return False, "Las edades no pueden ser negativas", None, None
    if edad_min > edad_max:
        return False, "La edad mínima no puede ser mayor que la máxima", None, None
    return True, "", edad_min, edad_max


def crear_categoria(data: dict) -> tuple[bool, str, int | None]:
    nombre = data.get("nombre", "").strip()
    tipo = (data.get("tipo") or "ACADEMIA").strip().upper()

    if not nombre:
        return False, "El nombre es obligatorio", None
    if tipo not in TIPOS_CATEGORIA:
        return False, f"Tipo no válido. Use: {', '.join(TIPOS_CATEGORIA)}", None
    ok, msg, edad_min, edad_max = _validar_edades(tipo, data.get("edad_min"), data.get("edad_max"))
    if not ok:
        return False, msg, None

    if categoria_repository.existe_nombre(nombre):
        return False, "Ya existe una categoría con ese nombre", None

    id_categoria = categoria_repository.insertar(nombre, edad_min, edad_max, tipo)

    auditoria_service.registrar_insert(
        id_usuario=1,
        tabla="categoria",
        id_registro=id_categoria,
        valores_nuevos=f"nombre={nombre}, tipo={tipo}, edad_min={edad_min}, edad_max={edad_max}",
    )

    logger.info(f"Categoría creada: {nombre} [{tipo}] ({edad_min}-{edad_max})")
    return True, "Categoría creada correctamente", id_categoria


def editar_categoria(id_categoria: int, data: dict) -> tuple[bool, str]:
    cat = categoria_repository.obtener_por_id(id_categoria)
    if not cat:
        return False, "Categoría no encontrada"

    nombre = data.get("nombre", cat["nombre"]).strip()
    tipo = (data.get("tipo", cat.get("tipo", "ACADEMIA")) or "ACADEMIA").strip().upper()
    if tipo not in TIPOS_CATEGORIA:
        return False, f"Tipo no válido. Use: {', '.join(TIPOS_CATEGORIA)}"

    ok, msg, edad_min, edad_max = _validar_edades(tipo, data.get("edad_min", cat["edad_min"]), data.get("edad_max", cat["edad_max"]))
    if not ok:
        return False, msg

    if categoria_repository.existe_nombre(nombre, exclude_id=id_categoria):
        return False, "Ya existe otra categoría con ese nombre"

    categoria_repository.actualizar(id_categoria, nombre, edad_min, edad_max, tipo)
    auditoria_service.registrar_update(
        auditoria_service.id_usuario_sesion(), "categoria", id_categoria,
        f"nombre={cat['nombre']}",
        f"nombre={nombre}, edad={edad_min}-{edad_max}, tipo={tipo}")
    return True, "Categoría actualizada correctamente"


def desactivar_categoria(id_categoria: int) -> tuple[bool, str]:
    cat = categoria_repository.obtener_por_id(id_categoria)
    if not cat:
        return False, "Categoría no encontrada"
    if cat["activo"] == 0:
        return False, "La categoría ya está desactivada"

    categoria_repository.soft_delete(id_categoria)

    auditoria_service.registrar_desactivacion(
        id_usuario=auditoria_service.id_usuario_sesion(),
        tabla="categoria",
        id_registro=id_categoria,
        valores_anteriores=f"nombre={cat['nombre']}, activo=1",
        valores_nuevos="activo=0",
    )

    logger.info(f"Categoría desactivada: {cat['nombre']} (id={id_categoria})")
    return True, "Categoría desactivada correctamente"


def listar_categorias() -> list[dict]:
    return categoria_repository.obtener_activas()


def listar_categorias_por_tipo(tipo: str) -> list[dict]:
    return categoria_repository.obtener_por_tipo(tipo)


def listar_todas_las_categorias() -> list[dict]:
    return categoria_repository.obtener_todas()


def obtener_categoria(id_categoria: int) -> dict | None:
    return categoria_repository.obtener_por_id(id_categoria)


def obtener_categoria_por_edad(edad: int) -> dict | None:
    return categoria_repository.obtener_por_edad(edad)
