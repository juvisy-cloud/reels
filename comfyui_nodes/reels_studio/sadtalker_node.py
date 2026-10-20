"""Nodo ComfyUI que anima un retrato con audio usando SadTalker.

SadTalker fija dependencias antiguas (numpy 1.23, basicsr) incompatibles con el
entorno de ComfyUI, por eso corre en su propio venv como subproceso.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 - argumentos en lista, sin shell
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

import folder_paths

SADTALKER_HOME = Path(os.environ.get("SADTALKER_HOME", Path.home() / "ai-engines" / "SadTalker"))
MAX_SOURCE_SIDE = 1280
TIMEOUT_SECONDS = int(os.environ.get("SADTALKER_TIMEOUT", "3600"))
# SadTalker invoca `ffmpeg` por nombre; se antepone el binario estático empaquetado.
FFMPEG_BIN_DIR = Path(os.environ.get("REELS_FFMPEG_BIN_DIR", Path.home() / "ai-engines" / "bin"))


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{FFMPEG_BIN_DIR}{os.pathsep}{env.get('PATH', '')}"
    return env


def _resolve_input_file(relative_name: str) -> Path:
    base = Path(folder_paths.get_input_directory()).resolve()
    candidate = (base / relative_name).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_file():
        raise ValueError("audio_file debe ser un archivo dentro del directorio input de ComfyUI")
    return candidate


def _save_first_frame(image_tensor: object, target: Path) -> None:
    array = np.clip(image_tensor[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)  # type: ignore[index]
    image = Image.fromarray(array).convert("RGB")
    # El rostro se renderiza a 256 px; una foto enorme solo encarece el pegado (seamlessClone).
    image.thumbnail((MAX_SOURCE_SIDE, MAX_SOURCE_SIDE))
    image.save(target)


def _build_command(image: Path, audio: Path, result_dir: Path, options: dict[str, object]) -> list[str]:
    command = [
        str(SADTALKER_HOME / ".venv" / "bin" / "python"),
        str(SADTALKER_HOME / "inference.py"),
        "--driven_audio", str(audio),
        "--source_image", str(image),
        "--result_dir", str(result_dir),
        "--checkpoint_dir", str(SADTALKER_HOME / "checkpoints"),
        "--preprocess", str(options["preprocess"]),
        "--size", "256",
        "--expression_scale", str(options["expression_scale"]),
        "--pose_style", str(options["pose_style"]),
        "--batch_size", "1",
        "--cpu",
    ]
    if options["still"]:
        command.append("--still")
    return command


class ReelsSadTalker:
    CATEGORY = "reels_studio"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "animate"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, tuple[object, ...]]]:  # noqa: N802 - contrato ComfyUI
        return {
            "required": {
                "image": ("IMAGE",),
                "audio_file": ("STRING", {"default": ""}),
                "preprocess": (["full", "extfull", "crop", "resize"], {"default": "full"}),
                "still": ("BOOLEAN", {"default": True}),
                "expression_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
                "pose_style": ("INT", {"default": 0, "min": 0, "max": 45}),
            }
        }

    def animate(self, image: object, audio_file: str, **options: object) -> dict[str, object]:
        audio = _resolve_input_file(audio_file)
        work_dir = Path(folder_paths.get_temp_directory()) / f"sadtalker-{uuid.uuid4().hex}"
        work_dir.mkdir(parents=True)
        try:
            source = work_dir / "source.png"
            _save_first_frame(image, source)
            subprocess.run(  # noqa: S603 - binario y argumentos controlados
                _build_command(source, audio, work_dir / "out", options),
                cwd=SADTALKER_HOME, env=_subprocess_env(), check=True, timeout=TIMEOUT_SECONDS,
            )
            produced = sorted((work_dir / "out").glob("*.mp4"))
            if not produced:
                raise RuntimeError("SadTalker no produjo ningún video")
            filename = f"reels_avatar_{uuid.uuid4().hex}.mp4"
            final = Path(folder_paths.get_output_directory()) / filename
            shutil.move(produced[-1], final)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        return {
            "ui": {"reels_video": [{"filename": filename, "subfolder": "", "type": "output"}]},
            "result": (str(final),),
        }
