"""Entidades del dominio. Inmutables y sin dependencias de infraestructura."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from reels_studio.domain.errors import InvalidScriptError

MIN_TOTAL_SECONDS = 5.0
MAX_TOTAL_SECONDS = 60.0
MAX_SCENES = 4


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class RenderStage(StrEnum):
    VOICE = "voice"
    AVATAR = "avatar"
    BACKGROUND = "background"
    COMPOSE = "compose"
    VERIFY = "verify"


@dataclass(frozen=True, slots=True)
class Scene:
    narration: str
    on_screen_text: str
    seconds: float


@dataclass(frozen=True, slots=True)
class Script:
    hook: str
    scenes: tuple[Scene, ...]
    cta: str
    pexels_queries: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.scenes) <= MAX_SCENES:
            raise InvalidScriptError(f"el guion debe tener entre 1 y {MAX_SCENES} escenas")
        if not MIN_TOTAL_SECONDS <= self.total_seconds <= MAX_TOTAL_SECONDS:
            raise InvalidScriptError("la duración total está fuera de rango")

    @property
    def total_seconds(self) -> float:
        return sum(scene.seconds for scene in self.scenes)

    @property
    def narration(self) -> str:
        return " ".join(scene.narration for scene in self.scenes)


@dataclass(frozen=True, slots=True)
class BackgroundAsset:
    provider_id: int
    kind: MediaKind
    preview_url: str
    download_url: str
    width: int
    height: int
    author: str
    author_url: str
    duration_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class BrandKit:
    handle: str
    logo_file_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Avatar:
    """Retrato ya recortado (PNG con transparencia), reutilizable en muchos reels."""

    name: str
    cutout_file_id: UUID
    source_file_id: UUID
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class ReelRequest:
    avatar_id: UUID
    script: Script
    background: BackgroundAsset
    brand: BrandKit
    voice: str
    overlay_file_id: UUID | None = None


@dataclass(slots=True)
class Job:
    request: ReelRequest
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.QUEUED
    stage: RenderStage | None = None
    progress: float = 0.0
    error: str | None = None
    output_file_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def advance(self, stage: RenderStage, progress: float) -> None:
        self.status = JobStatus.RUNNING
        self.stage = stage
        self.progress = max(0.0, min(progress, 1.0))

    def complete(self, output_file_id: UUID) -> None:
        self.status = JobStatus.DONE
        self.progress = 1.0
        self.output_file_id = output_file_id

    def fail(self, reason: str) -> None:
        self.status = JobStatus.FAILED
        self.error = reason
