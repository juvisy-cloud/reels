from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from reels_studio.bootstrap import Container, build_container
from reels_studio.config import Settings, get_settings
from reels_studio.domain.errors import (
    DomainError,
    EngineError,
    ForbiddenUrlError,
    InvalidScriptError,
    InvalidUploadError,
    NotFoundError,
)
from reels_studio.interfaces.http.routers import avatars, renders, studio, uploads
from reels_studio.interfaces.http.security import security_headers

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    InvalidScriptError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidUploadError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ForbiddenUrlError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    EngineError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


async def _domain_error_handler(_: Request, error: Exception) -> JSONResponse:
    code = next((c for kind, c in _STATUS_BY_ERROR.items() if isinstance(error, kind)), 400)
    return JSONResponse({"detail": str(error)}, status_code=code)


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    resolved = settings or get_settings()
    built = container or build_container(resolved)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = built
        built.worker.start()
        yield
        built.worker.stop()
        built.llama.stop()

    app = FastAPI(
        title="Reels Studio", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved.frontend_origin],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.middleware("http")(security_headers)
    app.add_exception_handler(DomainError, _domain_error_handler)
    for module in (uploads, avatars, studio, renders):
        app.include_router(module.router)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Solo localhost: el estudio no debe quedar expuesto en la red (OWASP A05).
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
