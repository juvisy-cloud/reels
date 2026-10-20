"""Descarga con lista blanca de hosts (OWASP A10 SSRF) y límite de tamaño."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from reels_studio.domain.errors import EngineError, ForbiddenUrlError

_MAX_REDIRECTS = 3
_CHUNK = 1024 * 256


class SafeDownloader:
    def __init__(self, allowed_host_suffixes: tuple[str, ...], max_bytes: int) -> None:
        self._suffixes = allowed_host_suffixes
        self._max_bytes = max_bytes

    def assert_allowed(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(host == s or host.endswith(f".{s}") for s in self._suffixes):
            raise ForbiddenUrlError("solo se permiten descargas desde Pexels por https")

    def download(self, url: str, target: Path) -> Path:
        current = url
        with httpx.Client(follow_redirects=False, timeout=60.0) as client:
            for _ in range(_MAX_REDIRECTS + 1):
                self.assert_allowed(current)
                with client.stream("GET", current) as response:
                    if response.is_redirect:
                        current = urljoin(current, response.headers["location"])
                        continue
                    response.raise_for_status()
                    return self._write(response, target)
        raise EngineError("demasiadas redirecciones al descargar el fondo")

    def _write(self, response: httpx.Response, target: Path) -> Path:
        partial = target.with_suffix(target.suffix + ".part")
        written = 0
        with partial.open("wb") as handle:
            for chunk in response.iter_bytes(_CHUNK):
                written += len(chunk)
                if written > self._max_bytes:
                    partial.unlink(missing_ok=True)
                    raise EngineError("el archivo de fondo es demasiado grande")
                handle.write(chunk)
        partial.replace(target)
        return target
