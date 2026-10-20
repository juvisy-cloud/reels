from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from reels_studio.bootstrap import Container
from reels_studio.domain.errors import InvalidUploadError
from reels_studio.infrastructure.storage.image_sanitizer import sanitize_image
from reels_studio.interfaces.http.dependencies import get_container
from reels_studio.interfaces.http.schemas import UploadOut

router = APIRouter(prefix="/api", tags=["files"])
_MEDIA_TYPES = {".png": "image/png", ".mp4": "video/mp4"}
ContainerDep = Annotated[Container, Depends(get_container)]


@router.post("/uploads", response_model=UploadOut, status_code=201)
async def upload_image(file: UploadFile, container: ContainerDep) -> UploadOut:
    limit = container.settings.max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise InvalidUploadError("la imagen es demasiado grande")
    clean = await run_in_threadpool(sanitize_image, data, limit)
    return UploadOut(file_id=container.files.save_bytes(clean, ".png"))


@router.get("/files/{file_id}")
def get_file(
    file_id: UUID, container: ContainerDep, download: Annotated[bool, Query()] = False
) -> FileResponse:
    path = container.files.path_for(file_id)
    media_type = _MEDIA_TYPES.get(path.suffix, "application/octet-stream")
    filename = f"reel-{file_id}{path.suffix}" if download else None
    return FileResponse(path, media_type=media_type, filename=filename)
