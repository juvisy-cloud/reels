"""Anima el avatar recortado con SadTalker (workflow `avatar_talking_head.json`)."""

from __future__ import annotations

from pathlib import Path

import soundfile

from reels_studio.application.ports import ProgressCallback
from reels_studio.infrastructure.comfyui.green_screen import flatten_on_green
from reels_studio.infrastructure.comfyui.workflow_runner import ComfyWorkflowRunner, WorkflowOutput
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate

_OUTPUT = WorkflowOutput(node_id="3", key="reels_video")
# Medido en este equipo (i5 Skylake, 4 núcleos, CPU): 20 min para 5 s de audio.
ESTIMATED_SECONDS_PER_AUDIO_SECOND = 240.0
MAX_ESTIMATED_PROGRESS = 0.95


class ComfyAvatarAnimator:
    def __init__(
        self, runner: ComfyWorkflowRunner, template: WorkflowTemplate, timeout_seconds: float
    ) -> None:
        self._runner = runner
        self._template = template
        self._timeout = timeout_seconds

    def animate(self, photo: Path, audio: Path, target: Path, on_progress: ProgressCallback) -> Path:
        green = flatten_on_green(photo, target.with_name(f"{target.stem}-green.png"))
        expected = self._expected_seconds(audio)
        return self._runner.run(
            self._template,
            {"PHOTO": green, "AUDIO": audio},
            _OUTPUT,
            target,
            timeout_seconds=self._timeout,
            on_tick=lambda elapsed: on_progress(min(elapsed / expected, MAX_ESTIMATED_PROGRESS)),
        )

    @staticmethod
    def _expected_seconds(audio: Path) -> float:
        duration = float(soundfile.info(str(audio)).duration)
        return max(duration * ESTIMATED_SECONDS_PER_AUDIO_SECOND, 30.0)
