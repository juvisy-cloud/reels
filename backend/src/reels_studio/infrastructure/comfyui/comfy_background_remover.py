"""Quita el fondo de la foto con RMBG-2.0 (workflow `remove_background.json`) → PNG transparente."""

from __future__ import annotations

from pathlib import Path

from reels_studio.infrastructure.comfyui.workflow_runner import ComfyWorkflowRunner, WorkflowOutput
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate

_OUTPUT = WorkflowOutput(node_id="3", key="images")
# La primera vez descarga el modelo (~900 MB); después tarda menos de un minuto en CPU.
_TIMEOUT_SECONDS = 1800.0


class ComfyBackgroundRemover:
    def __init__(self, runner: ComfyWorkflowRunner, template: WorkflowTemplate) -> None:
        self._runner = runner
        self._template = template

    def remove(self, photo: Path, target: Path) -> Path:
        return self._runner.run(
            self._template, {"PHOTO": photo}, _OUTPUT, target, timeout_seconds=_TIMEOUT_SECONDS
        )
