"""Arranca y detiene llama-server bajo demanda.

Con 15 GB de RAM y sin GPU no caben el LLM y SadTalker a la vez con holgura:
el worker detiene el servidor antes de cada render.
"""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

import httpx

from reels_studio.domain.errors import EngineError

_STARTUP_TIMEOUT_SECONDS = 120.0


class LlamaServerSupervisor:
    def __init__(self, binary: Path, model: Path, url: str, threads: int = 4) -> None:
        self._binary = binary
        self._model = model
        self._url = url.rstrip("/")
        self._threads = threads
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    def ensure_running(self) -> str:
        with self._lock:
            if self._healthy():
                return self._url
            if self._process is None or self._process.poll() is not None:
                self._process = self._spawn()
            self._wait_until_healthy()
            return self._url

    def stop(self) -> None:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            self._process = None

    def _spawn(self) -> subprocess.Popen[bytes]:
        if not self._model.is_file():
            raise EngineError(f"no se encontró el modelo de lenguaje en {self._model}")
        port = self._url.rsplit(":", 1)[-1]
        command = [
            str(self._binary),
            "-m",
            str(self._model),
            "--host",
            "127.0.0.1",
            "--port",
            port,
            "-c",
            "4096",
            "-t",
            str(self._threads),
            "--jinja",
        ]
        return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603

    def _healthy(self) -> bool:
        try:
            return httpx.get(f"{self._url}/health", timeout=2.0).status_code == httpx.codes.OK
        except httpx.HTTPError:
            return False

    def _wait_until_healthy(self) -> None:
        deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._healthy():
                return
            time.sleep(1.0)
        raise EngineError("el modelo de lenguaje tardó demasiado en arrancar")
