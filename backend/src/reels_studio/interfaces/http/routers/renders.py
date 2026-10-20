from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from reels_studio.bootstrap import Container
from reels_studio.domain.models import JobStatus
from reels_studio.interfaces.http.dependencies import get_container
from reels_studio.interfaces.http.schemas import JobOut, RenderIn
from reels_studio.interfaces.http.security import SlidingWindowLimiter

router = APIRouter(prefix="/api/renders", tags=["renders"])
ContainerDep = Annotated[Container, Depends(get_container)]
_render_limit = SlidingWindowLimiter(limit=5, window_seconds=300)
_TERMINAL = {JobStatus.DONE, JobStatus.FAILED}
_POLL_SECONDS = 1.5


@router.post("", response_model=JobOut, status_code=202, dependencies=[Depends(_render_limit)])
async def submit_render(body: RenderIn, container: ContainerDep) -> JobOut:
    job = await run_in_threadpool(container.submit_render.execute, body.to_domain())
    return JobOut.from_domain(job)


@router.get("/{job_id}", response_model=JobOut)
def get_render(job_id: UUID, container: ContainerDep) -> JobOut:
    return JobOut.from_domain(container.jobs.get(job_id))


@router.get("/{job_id}/events")
async def render_events(job_id: UUID, container: ContainerDep) -> StreamingResponse:
    container.jobs.get(job_id)

    async def stream() -> AsyncIterator[str]:
        last = ""
        while True:
            job = await run_in_threadpool(container.jobs.get, job_id)
            payload = JobOut.from_domain(job).model_dump_json()
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            if job.status in _TERMINAL:
                return
            await asyncio.sleep(_POLL_SECONDS)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
