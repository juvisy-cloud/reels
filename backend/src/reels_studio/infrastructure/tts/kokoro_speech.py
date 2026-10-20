from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import soundfile

from reels_studio.application.ports import SpeechResult
from reels_studio.domain.errors import EngineError

SPANISH_VOICES: dict[str, str] = {
    "em_alex": "Alex (hombre)",
    "em_santa": "Santa (hombre, grave)",
    "ef_dora": "Dora (mujer)",
}


class KokoroSpeech:
    """Kokoro-82M en ONNX: rápido en CPU. El modelo se carga perezosamente una sola vez."""

    def __init__(self, model_path: Path, voices_path: Path, speed: float = 1.05) -> None:
        self._model_path = model_path
        self._voices_path = voices_path
        self._speed = speed
        self._engine: Any = None
        self._lock = threading.Lock()

    def synthesize(self, text: str, voice: str, target: Path) -> SpeechResult:
        if voice not in SPANISH_VOICES:
            raise EngineError("voz no disponible")
        samples, sample_rate = self._load().create(text, voice=voice, speed=self._speed, lang="es")
        soundfile.write(target, samples, sample_rate)
        return SpeechResult(audio_path=target, duration_seconds=len(samples) / sample_rate)

    def _load(self) -> Any:  # noqa: ANN401 - kokoro_onnx no publica tipos
        with self._lock:
            if self._engine is None:
                if not self._model_path.is_file() or not self._voices_path.is_file():
                    raise EngineError("faltan los archivos del modelo de voz Kokoro (ejecuta make models)")
                from kokoro_onnx import Kokoro  # noqa: PLC0415 - carga pesada, solo al primer uso

                self._engine = Kokoro(str(self._model_path), str(self._voices_path))
            return self._engine
