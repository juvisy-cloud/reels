"""Carga un workflow API de ComfyUI y sustituye marcadores `{{NOMBRE}}`.

La sustitución recorre el árbol JSON y solo reemplaza valores que son
exactamente el marcador: nunca se concatena texto en el JSON.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from reels_studio.domain.errors import EngineError


class WorkflowTemplate:
    def __init__(self, path: Path) -> None:
        self._template: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    def render(self, values: dict[str, str]) -> dict[str, Any]:
        rendered = copy.deepcopy(self._template)
        missing = set(values)
        for node in rendered.values():
            for key, value in node.get("inputs", {}).items():
                name = self._placeholder(value)
                if name is None:
                    continue
                if name not in values:
                    raise EngineError(f"falta el valor para el marcador {name}")
                node["inputs"][key] = values[name]
                missing.discard(name)
        if missing:
            raise EngineError(f"el workflow no usa los marcadores {sorted(missing)}")
        return rendered

    @staticmethod
    def _placeholder(value: object) -> str | None:
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            return value[2:-2]
        return None
