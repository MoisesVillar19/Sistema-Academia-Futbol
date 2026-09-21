"""Normalización y coincidencia multi-campo para buscadores (plan inventario UX, Bloque A2).

Uso pensado junto a ``utils.debounce.Debouncer``: la vista filtra con
:func:`coincide` sobre los campos visibles de cada tarjeta.

El "carnet" no es una columna propia: vive en ``persona.dni`` con
``tipo_documento='CARNET'``; por eso basta con incluir el documento en los
campos buscados (ya cubre DNI de 8 y carnet de 9 dígitos).
"""

import unicodedata


def normalizar(texto) -> str:
    """Minúsculas, sin tildes, espacios colapsados."""
    if texto is None:
        return ""
    s = str(texto).strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(s.split())


def coincide(query, *campos) -> bool:
    """True si TODA palabra de la query aparece en ALGÚN campo (multi-campo).

    Ej: query "juan perez" coincide con campos ("Juan", "Pérez López").
    """
    q = normalizar(query)
    if not q:
        return True
    normalizados = [normalizar(c) for c in campos]
    return all(any(palabra in campo for campo in normalizados) for palabra in q.split())


def filtrar(filas: list, query: str, *getters) -> list:
    """Filtra lista de dicts aplicando :func:`coincide` con los getters dados."""
    if not normalizar(query):
        return list(filas)
    return [f for f in filas if coincide(query, *(g(f) for g in getters))]
