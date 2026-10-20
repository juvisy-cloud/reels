"""Validación y re-codificación de imágenes subidas (OWASP A04/A08).

Se valida por *magic bytes* (no por extensión ni Content-Type), se limita el
tamaño en píxeles (bombas de descompresión) y se re-codifica a PNG, lo que
elimina EXIF/GPS y cualquier carga añadida al final del archivo.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from reels_studio.domain.errors import InvalidUploadError

_SIGNATURES: tuple[tuple[bytes, int], ...] = ((b"\x89PNG\r\n\x1a\n", 0), (b"\xff\xd8\xff", 0), (b"WEBP", 8))
_ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}
MAX_PIXELS = 40_000_000
MIN_SIDE = 256


def _has_allowed_signature(data: bytes) -> bool:
    return any(data[offset : offset + len(magic)] == magic for magic, offset in _SIGNATURES)


def sanitize_image(data: bytes, max_bytes: int) -> bytes:
    if not data or len(data) > max_bytes:
        raise InvalidUploadError(f"la imagen debe pesar menos de {max_bytes // (1024 * 1024)} MB")
    if not _has_allowed_signature(data):
        raise InvalidUploadError("solo se aceptan imágenes PNG, JPEG o WebP")
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in _ALLOWED_FORMATS:
                raise InvalidUploadError("formato de imagen no permitido")
            probe.verify()
        with Image.open(io.BytesIO(data)) as image:
            upright = ImageOps.exif_transpose(image)
            if min(upright.size) < MIN_SIDE:
                raise InvalidUploadError(f"la imagen debe medir al menos {MIN_SIDE}px por lado")
            converted = upright.convert("RGBA" if "A" in upright.getbands() else "RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as error:
        raise InvalidUploadError("la imagen está dañada o no es válida") from error
    output = io.BytesIO()
    converted.save(output, format="PNG", optimize=True)
    return output.getvalue()
