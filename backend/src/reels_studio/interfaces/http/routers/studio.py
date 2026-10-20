"""Endpoints del editor: guion, fondos de Pexels y voces."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from reels_studio.application.ports import ScriptBrief
from reels_studio.bootstrap import Container
from reels_studio.domain.models import MediaKind
from reels_studio.infrastructure.tts.kokoro_speech import SPANISH_VOICES
from reels_studio.interfaces.http.dependencies import get_container
from reels_studio.interfaces.http.schemas import BackgroundDTO, ScriptBriefIn, ScriptDTO, VoiceOut
from reels_studio.interfaces.http.security import SlidingWindowLimiter

router = APIRouter(prefix="/api", tags=["studio"])
ContainerDep = Annotated[Container, Depends(get_container)]
_script_limit = SlidingWindowLimiter(limit=10, window_seconds=60)
_search_limit = SlidingWindowLimiter(limit=30, window_seconds=60)


@router.post("/scripts", response_model=ScriptDTO, dependencies=[Depends(_script_limit)])
async def generate_script(body: ScriptBriefIn, container: ContainerDep) -> ScriptDTO:
    brief = ScriptBrief(
        context=body.context, tone=body.tone, target_seconds=body.target_seconds, handle=body.handle
    )
    script = await run_in_threadpool(container.generate_script.execute, brief)
    return ScriptDTO.from_domain(script)


@router.get("/backgrounds", response_model=list[BackgroundDTO], dependencies=[Depends(_search_limit)])
async def search_backgrounds(
    container: ContainerDep,
    query: Annotated[str, Query(min_length=1, max_length=80)],
    kind: Annotated[MediaKind, Query()] = MediaKind.VIDEO,
) -> list[BackgroundDTO]:
    assets = await run_in_threadpool(container.search_backgrounds.execute, query, kind)
    return [BackgroundDTO.from_domain(asset) for asset in assets]


@router.get("/voices", response_model=list[VoiceOut])
def list_voices() -> list[VoiceOut]:
    return [VoiceOut(id=voice_id, label=label) for voice_id, label in SPANISH_VOICES.items()]
