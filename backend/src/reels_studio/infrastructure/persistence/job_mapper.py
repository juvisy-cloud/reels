"""Serializa jobs del dominio a JSON y de vuelta (sin acoplar el dominio a la BD)."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from reels_studio.domain.models import (
    BackgroundAsset,
    BrandKit,
    Job,
    JobStatus,
    MediaKind,
    ReelRequest,
    RenderStage,
    Scene,
    Script,
)


def _uuid_or_none(value: object) -> UUID | None:
    return None if value is None else UUID(str(value))


def request_to_dict(request: ReelRequest) -> dict[str, Any]:
    data = asdict(request)
    data["avatar_id"] = str(request.avatar_id)
    data["overlay_file_id"] = None if request.overlay_file_id is None else str(request.overlay_file_id)
    logo = request.brand.logo_file_id
    data["brand"]["logo_file_id"] = None if logo is None else str(logo)
    return data


def request_from_dict(data: dict[str, Any]) -> ReelRequest:
    script = data["script"]
    return ReelRequest(
        avatar_id=UUID(data["avatar_id"]),
        script=Script(
            hook=script["hook"],
            scenes=tuple(Scene(**scene) for scene in script["scenes"]),
            cta=script["cta"],
            pexels_queries=tuple(script["pexels_queries"]),
        ),
        background=BackgroundAsset(**{**data["background"], "kind": MediaKind(data["background"]["kind"])}),
        brand=BrandKit(
            handle=data["brand"]["handle"], logo_file_id=_uuid_or_none(data["brand"]["logo_file_id"])
        ),
        voice=data["voice"],
        overlay_file_id=_uuid_or_none(data["overlay_file_id"]),
    )


def job_from_row(row: dict[str, Any], request: ReelRequest) -> Job:
    return Job(
        request=request,
        id=UUID(row["id"]),
        status=JobStatus(row["status"]),
        stage=None if row["stage"] is None else RenderStage(row["stage"]),
        progress=float(row["progress"]),
        error=row["error"],
        output_file_id=_uuid_or_none(row["output_file_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )
