"""Cabeceras de seguridad y límite de peticiones (OWASP A05)."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
}


async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    return response


class SlidingWindowLimiter:
    """Dependencia FastAPI: máximo `limit` llamadas por ventana, por cliente."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def __call__(self, request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(client, deque())
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS, "demasiadas solicitudes, espera un momento"
                )
            hits.append(now)
