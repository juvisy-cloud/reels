"""Ejecuta un workflow de ComfyUI con archivos locales y descarga una salida.

ComfyUI corre en la misma máquina: las entradas se copian a `input/reels/<id>`,
se sustituyen los marcadores del template y el resultado se baja por /view.
"""

from __future__ import annotations

import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from reels_studio.domain.errors import EngineError
from reels_studio.infrastructure.comfyui.client import ComfyUIClient
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate


@dataclass(frozen=True, slots=True)
class WorkflowOutput:
    node_id: str
    key: str


class ComfyWorkflowRunner:
    def __init__(self, client: ComfyUIClient, comfy_input_dir: Path) -> None:
        self._client = client
        self._input_dir = comfy_input_dir

    def run(
        self,
        template: WorkflowTemplate,
        inputs: dict[str, Path],
        output: WorkflowOutput,
        target: Path,
        *,
        timeout_seconds: float,
        on_tick: Callable[[float], None] | None = None,
    ) -> Path:
        staging = self._input_dir / "reels" / uuid.uuid4().hex
        staging.mkdir(parents=True)
        try:
            values = {name: self._stage(staging, name, path) for name, path in inputs.items()}
            prompt_id = self._client.queue(template.render(values))
            outputs = self._client.wait(prompt_id, timeout_seconds, on_tick=on_tick)
            return self._client.download_output(self._file_info(outputs, output), target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _stage(self, staging: Path, name: str, source: Path) -> str:
        staged = staging / f"{name.lower()}{source.suffix}"
        shutil.copyfile(source, staged)
        return str(staged.relative_to(self._input_dir))

    @staticmethod
    def _file_info(outputs: dict[str, object], output: WorkflowOutput) -> dict[str, str]:
        node = outputs.get(output.node_id)
        if not isinstance(node, dict) or not node.get(output.key):
            raise EngineError("ComfyUI terminó sin devolver el archivo esperado")
        info: dict[str, str] = node[output.key][0]
        return info
