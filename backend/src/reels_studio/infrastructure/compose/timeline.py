"""Reparte la duración real de la voz entre las escenas, proporcional a lo estimado."""

from __future__ import annotations

from dataclasses import dataclass

from reels_studio.domain.models import Script

HOOK_MAX_SECONDS = 3.0


@dataclass(frozen=True, slots=True)
class Window:
    start: float
    end: float


def scene_windows(script: Script, voice_seconds: float) -> list[Window]:
    scale = voice_seconds / script.total_seconds
    windows: list[Window] = []
    cursor = 0.0
    for scene in script.scenes:
        end = cursor + scene.seconds * scale
        windows.append(Window(round(cursor, 3), round(end, 3)))
        cursor = end
    return windows


def hook_window(voice_seconds: float) -> Window:
    return Window(0.0, min(HOOK_MAX_SECONDS, voice_seconds))


def overlay_window(windows: list[Window]) -> Window:
    """El mockup aparece en la segunda escena (como en el reel de referencia)."""
    return windows[1] if len(windows) > 1 else windows[0]
