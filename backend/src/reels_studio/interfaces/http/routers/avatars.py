"""Biblioteca de avatares: crear (quita el fondo una vez), listar y borrar."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from starlette.concurrency import run_in_threadpool

from reels_studio.bootstrap import Container
from reels_studio.interfaces.http.dependencies import get_container
from reels_studio.interfaces.http.schemas import AvatarIn, AvatarOut
from reels_studio.interfaces.http.security import SlidingWindowLimiter

router = APIRouter(prefix="/api/avatars", tags=["avatars"])
ContainerDep = Annotated[Container, Depends(get_container)]
_create_limit = SlidingWindowLimiter(limit=10, window_seconds=300)


@router.post("", response_model=AvatarOut, status_code=201, dependencies=[Depends(_create_limit)])
async def create_avatar(body: AvatarIn, container: ContainerDep) -> AvatarOut:
    avatar = await run_in_threadpool(container.create_avatar.execute, body.photo_file_id, body.name)
    return AvatarOut.from_domain(avatar)


@router.get("", response_model=list[AvatarOut])
def list_avatars(container: ContainerDep) -> list[AvatarOut]:
    return [AvatarOut.from_domain(avatar) for avatar in container.list_avatars.execute()]


@router.delete("/{avatar_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_avatar(avatar_id: UUID, container: ContainerDep) -> Response:
    container.delete_avatar.execute(avatar_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
