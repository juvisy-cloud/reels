"""Aplana el recorte transparente sobre verde puro para el chroma key del compositor."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

CHROMA_GREEN = (0, 255, 0)


def flatten_on_green(cutout: Path, target: Path) -> Path:
    with Image.open(cutout) as image:
        rgba = image.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, CHROMA_GREEN)
        canvas.paste(rgba, mask=rgba.getchannel("A"))
        canvas.save(target)
    return target
