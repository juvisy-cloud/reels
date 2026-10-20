"""DTOs de la API. Validan forma y límites antes de llegar a los casos de uso."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from reels_studio.domain.models import (
    Avatar,
    BackgroundAsset,
    BrandKit,
    Job,
    MediaKind,
    ReelRequest,
    Scene,
    Script,
)

_HANDLE_PATTERN = r"^@?[A-Za-z0-9._]{0,30}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ScriptBriefIn(_Strict):
    context: str = Field(min_length=1, max_length=1500)
    tone: str = Field(default="", max_length=60)
    target_seconds: int = Field(default=15, ge=10, le=45)
    handle: str = Field(default="", pattern=_HANDLE_PATTERN)


class SceneDTO(_Strict):
    narration: str = Field(min_length=1, max_length=400)
    on_screen_text: str = Field(default="", max_length=60)
    seconds: float = Field(ge=1, le=20)


class ScriptDTO(_Strict):
    hook: str = Field(default="", max_length=80)
    scenes: list[SceneDTO] = Field(min_length=1, max_length=4)
    cta: str = Field(default="", max_length=120)
    pexels_queries: list[str] = Field(default_factory=list, max_length=3)

    @classmethod
    def from_domain(cls, script: Script) -> ScriptDTO:
        return cls(
            hook=script.hook,
            scenes=[
                SceneDTO(narration=s.narration, on_screen_text=s.on_screen_text, seconds=s.seconds)
                for s in script.scenes
            ],
            cta=script.cta,
            pexels_queries=list(script.pexels_queries),
        )

    def to_domain(self) -> Script:
        return Script(
            hook=self.hook,
            scenes=tuple(Scene(s.narration, s.on_screen_text, s.seconds) for s in self.scenes),
            cta=self.cta,
            pexels_queries=tuple(self.pexels_queries),
        )


class BackgroundDTO(_Strict):
    provider_id: int
    kind: MediaKind
    preview_url: HttpUrl
    download_url: HttpUrl
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    author: str = Field(max_length=120)
    author_url: HttpUrl
    duration_seconds: float | None = None

    @classmethod
    def from_domain(cls, asset: BackgroundAsset) -> BackgroundDTO:
        return cls.model_validate(asdict(asset))

    def to_domain(self) -> BackgroundAsset:
        return BackgroundAsset(
            provider_id=self.provider_id,
            kind=self.kind,
            preview_url=str(self.preview_url),
            download_url=str(self.download_url),
            width=self.width,
            height=self.height,
            author=self.author,
            author_url=str(self.author_url),
            duration_seconds=self.duration_seconds,
        )


class RenderIn(_Strict):
    avatar_id: UUID
    script: ScriptDTO
    background: BackgroundDTO
    voice: str = Field(default="em_alex", max_length=20)
    handle: str = Field(default="", pattern=_HANDLE_PATTERN)
    logo_file_id: UUID | None = None
    overlay_file_id: UUID | None = None

    def to_domain(self) -> ReelRequest:
        return ReelRequest(
            avatar_id=self.avatar_id,
            script=self.script.to_domain(),
            background=self.background.to_domain(),
            brand=BrandKit(handle=self.handle, logo_file_id=self.logo_file_id),
            voice=self.voice,
            overlay_file_id=self.overlay_file_id,
        )


class JobOut(BaseModel):
    id: UUID
    status: str
    stage: str | None
    progress: float
    error: str | None
    output_file_id: UUID | None

    @classmethod
    def from_domain(cls, job: Job) -> JobOut:
        return cls(
            id=job.id,
            status=job.status,
            stage=job.stage,
            progress=round(job.progress, 3),
            error=job.error,
            output_file_id=job.output_file_id,
        )


class UploadOut(BaseModel):
    file_id: UUID


class VoiceOut(BaseModel):
    id: str
    label: str


class AvatarIn(_Strict):
    photo_file_id: UUID
    name: str = Field(min_length=1, max_length=40)


class AvatarOut(BaseModel):
    id: UUID
    name: str
    cutout_file_id: UUID
    created_at: str

    @classmethod
    def from_domain(cls, avatar: Avatar) -> AvatarOut:
        return cls(
            id=avatar.id,
            name=avatar.name,
            cutout_file_id=avatar.cutout_file_id,
            created_at=avatar.created_at.isoformat(),
        )
