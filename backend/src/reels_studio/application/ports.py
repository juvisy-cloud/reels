"""Puertos (interfaces) que la capa de aplicación necesita del mundo exterior."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from reels_studio.domain.models import Avatar, BackgroundAsset, Job, MediaKind, Script

ProgressCallback = Callable[[float], None]


@dataclass(frozen=True, slots=True)
class ScriptBrief:
    context: str
    tone: str
    target_seconds: int
    handle: str


@dataclass(frozen=True, slots=True)
class SpeechResult:
    audio_path: Path
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class CompositionSpec:
    background_path: Path
    background_kind: MediaKind
    avatar_video_path: Path
    audio_path: Path
    script: Script
    handle: str
    logo_path: Path | None
    overlay_path: Path | None
    output_path: Path


@dataclass(frozen=True, slots=True)
class MediaProbe:
    width: int
    height: int
    duration_seconds: float
    has_audio: bool


class ScriptWriterPort(Protocol):
    def write(self, brief: ScriptBrief) -> Script: ...


class StockMediaPort(Protocol):
    def search(self, query: str, kind: MediaKind, per_page: int) -> list[BackgroundAsset]: ...

    def download(self, asset: BackgroundAsset, target_dir: Path) -> Path: ...


class SpeechSynthesizerPort(Protocol):
    def synthesize(self, text: str, voice: str, target: Path) -> SpeechResult: ...


class BackgroundRemoverPort(Protocol):
    def remove(self, photo: Path, target: Path) -> Path: ...


class AvatarAnimatorPort(Protocol):
    def animate(self, photo: Path, audio: Path, target: Path, on_progress: ProgressCallback) -> Path: ...


class VideoComposerPort(Protocol):
    def compose(self, spec: CompositionSpec) -> Path: ...


class MediaProberPort(Protocol):
    def probe(self, path: Path) -> MediaProbe: ...


class FileStorePort(Protocol):
    def save_bytes(self, data: bytes, suffix: str) -> UUID: ...

    def path_for(self, file_id: UUID) -> Path: ...

    def new_path(self, suffix: str) -> tuple[UUID, Path]: ...

    def work_dir(self, job_id: UUID) -> Path: ...

    def delete(self, file_id: UUID) -> None: ...


class JobRepositoryPort(Protocol):
    def save(self, job: Job) -> None: ...

    def get(self, job_id: UUID) -> Job: ...

    def next_queued(self) -> Job | None: ...


class AvatarRepositoryPort(Protocol):
    def save(self, avatar: Avatar) -> None: ...

    def get(self, avatar_id: UUID) -> Avatar: ...

    def list(self) -> list[Avatar]: ...

    def delete(self, avatar_id: UUID) -> None: ...
