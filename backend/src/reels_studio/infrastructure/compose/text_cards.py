"""Tarjetas gráficas renderizadas con Pillow (el ffmpeg estático no trae drawtext).

Renderizar el texto como imagen también evita escapar texto del usuario dentro
del filtergraph de ffmpeg (OWASP A03 inyección).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REEL_SIZE = (1080, 1920)
_ACCENT = (108, 76, 255, 255)
_OUTRO_BG = (238, 241, 248, 255)
_TEXT_DARK = (30, 30, 46, 255)


class CardRenderer:
    def __init__(self, font_path: Path) -> None:
        self._font_path = font_path

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(self._font_path), size)

    def caption(self, text: str, target: Path, font_size: int = 64, width_chars: int = 22) -> Path:
        font = self._font(font_size)
        lines = textwrap.wrap(text, width=width_chars) or [" "]
        line_height = int(font_size * 1.25)
        pad = 36
        width = max(int(font.getlength(line)) for line in lines) + pad * 2
        height = line_height * len(lines) + pad * 2
        card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle((0, 0, width, height), radius=32, fill=(255, 255, 255, 235))
        for index, line in enumerate(lines):
            line_width = font.getlength(line)
            draw.text(((width - line_width) / 2, pad + index * line_height), line, font=font, fill=_TEXT_DARK)
        card.save(target)
        return target

    def phone_frame(self, screenshot: Path, target: Path, width: int = 560) -> Path:
        image = ImageOps.contain(Image.open(screenshot).convert("RGBA"), (width, int(width * 2.1)))
        border = 14
        frame = Image.new("RGBA", (image.width + border * 2, image.height + border * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((0, 0, frame.width, frame.height), radius=48, fill=_ACCENT)
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, *image.size), radius=36, fill=255)
        frame.paste(image, (border, border), mask)
        frame.save(target)
        return target

    def outro(self, handle: str, cta: str, logo: Path | None, target: Path) -> Path:
        card = Image.new("RGBA", REEL_SIZE, _OUTRO_BG)
        draw = ImageDraw.Draw(card)
        y = 620
        if logo is not None:
            mark = ImageOps.contain(Image.open(logo).convert("RGBA"), (640, 520))
            card.alpha_composite(mark, ((REEL_SIZE[0] - mark.width) // 2, y - mark.height // 2))
            y += mark.height // 2 + 80
        for text, size in ((cta, 58), (f"Instagram: {handle}" if handle else "", 54)):
            if not text:
                continue
            font = self._font(size)
            for line in textwrap.wrap(text, width=26):
                draw.text(((REEL_SIZE[0] - font.getlength(line)) / 2, y), line, font=font, fill=_TEXT_DARK)
                y += int(size * 1.3)
            y += 40
        card.convert("RGB").save(target)
        return target
