"""Cliente mínimo de la API HTTP de ComfyUI (/prompt, /history, /view)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from reels_studio.domain.errors import EngineError

_POLL_SECONDS = 2.0


class ComfyUIClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client_id = uuid.uuid4().hex

    def queue(self, workflow: dict[str, Any]) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/prompt",
                json={"prompt": workflow, "client_id": self._client_id},
                timeout=30.0,
            )
        except httpx.HTTPError as error:
            raise EngineError("ComfyUI no está corriendo (ejecuta make comfy)") from error
        if response.status_code != httpx.codes.OK:
            raise EngineError(f"ComfyUI rechazó el workflow: {response.text[:300]}")
        return str(response.json()["prompt_id"])

    def wait(self, prompt_id: str, timeout_seconds: float, on_tick: Any = None) -> dict[str, Any]:  # noqa: ANN401
        started = time.monotonic()
        while (elapsed := time.monotonic() - started) < timeout_seconds:
            entry = self._history(prompt_id)
            if entry is not None:
                return self._ensure_success(entry)
            if on_tick is not None:
                on_tick(elapsed)
            time.sleep(_POLL_SECONDS)
        raise EngineError("ComfyUI tardó demasiado en animar el avatar")

    def download_output(self, file_info: dict[str, str], target: Path) -> Path:
        params = {k: file_info[k] for k in ("filename", "subfolder", "type")}
        with httpx.stream("GET", f"{self._base_url}/view", params=params, timeout=120.0) as response:
            response.raise_for_status()
            with target.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
        return target

    def _history(self, prompt_id: str) -> dict[str, Any] | None:
        try:
            response = httpx.get(f"{self._base_url}/history/{prompt_id}", timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EngineError("se perdió la conexión con ComfyUI") from error
        entry: dict[str, Any] | None = response.json().get(prompt_id)
        return entry

    @staticmethod
    def _ensure_success(entry: dict[str, Any]) -> dict[str, Any]:
        status = entry.get("status", {})
        if status.get("status_str") != "success":
            raise EngineError("ComfyUI falló al animar el avatar (revisa la consola de ComfyUI)")
        outputs: dict[str, Any] = entry.get("outputs", {})
        return outputs
