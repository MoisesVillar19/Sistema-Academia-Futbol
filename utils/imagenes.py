"""Fase 3: validación visible de imágenes/comprobantes al seleccionar.

Antes solo se validaba tamaño (y en ventas/matrícula ni eso); un formato
inválido pasaba con ✅ silencioso y fallaba al guardar. Ahora se valida
extensión + contenido real (PIL) y se responde (ok, mensaje) para mostrar
messagebox inmediato.
"""

import os

EXT_IMAGEN = (".jpg", ".jpeg", ".png")
EXT_PDF = (".pdf",)


def validar_imagen(path: str, max_mb: float = 5,
                   permitir_pdf: bool = False) -> tuple[bool, str]:
    """Valida existencia, tamaño, extensión y contenido legible."""
    if not path or not os.path.isfile(path):
        return False, "Archivo no encontrado"
    try:
        tam = os.path.getsize(path)
    except OSError as e:
        return False, f"No se pudo leer el archivo: {e}"
    if tam <= 0:
        return False, "El archivo está vacío"
    if tam > max_mb * 1024 * 1024:
        return False, f"El archivo debe ser ≤{max_mb:g}MB (pesa {tam/1048576:.1f}MB)"
    ext = os.path.splitext(path)[1].lower()
    validas = EXT_IMAGEN + (EXT_PDF if permitir_pdf else ())
    if ext not in validas:
        espera = "JPG, PNG" + (" o PDF" if permitir_pdf else "")
        return False, f"Formato no admitido ({ext or 'sin extensión'}). Use: {espera}"
    if ext in EXT_PDF:
        return True, "OK"
    try:
        from PIL import Image
    except ImportError:
        return True, "OK (sin verificación de contenido)"
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            img.load()
    except Exception:
        return False, "El archivo no es una imagen válida (está corrupto o no es JPG/PNG real)"
    return True, "OK"


def extension_real(path: str, defecto: str = ".jpg") -> str:
    ext = os.path.splitext(path or "")[1].lower()
    if ext in EXT_IMAGEN + EXT_PDF:
        return ext
    return defecto
