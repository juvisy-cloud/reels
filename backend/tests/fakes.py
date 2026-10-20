"""Dobles de prueba de los puertos: permiten probar casos de uso sin modelos ni red."""

from __future__ import annotations

import uuid
from pathlib import Path
from uuid import UUID

from reels_studio.application.ports import (
    CompositionSpec,
    MediaProbe,
    ProgressCallback,
    ScriptBrief,
    SpeechResult,
)
from reels_studio.domain.errors import NotFoundError
from reels_studio.domain.models import (
    Avatar,
    BackgroundAsset,
    BrandKit,
    Job,
    JobStatus,
    MediaKind,
    ReelRequest,
    Scene,
    Script,
)


def make_script() -> Script:
    return Script(
        hook="Agenda sin llamadas",
        scenes=(
            Scene("Hola, te cuento cómo agendar citas.", "Citas por chat", 4.0),
            Scene("Tu cliente escribe y el bot agenda.", "Agenda automática", 4.0),
        ),
        cta="Síguenos en @juvisy.cloud",
        pexels_queries=("office",),
    )


def make_background() -> BackgroundAsset:
    return BackgroundAsset(
        provider_id=1,
        kind=MediaKind.VIDEO,
        preview_url="https://images.pexels.com/p.jpg",
        download_url="https://videos.pexels.com/v.mp4",
        width=1080,
        height=1920,
        author="Ana",
        author_url="https://www.pexels.com/@ana",
        duration_seconds=12.0,
    )


def make_request(avatar_id: UUID) -> ReelRequest:
    return ReelRequest(
        avatar_id=avatar_id,
        script=make_script(),
        background=make_background(),
        brand=BrandKit(handle="@juvisy.cloud"),
        voice="em_alex",
    )


class FakeFiles:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.known: dict[UUID, Path] = {}

    def save_bytes(self, data: bytes, suffix: str) -> UUID:
        file_id, path = self.new_path(suffix)
        path.write_bytes(data)
        return file_id

    def new_path(self, suffix: str) -> tuple[UUID, Path]:
        file_id = uuid.uuid4()
        path = self.root / f"{file_id}{suffix}"
        self.known[file_id] = path
        return file_id, path

    def path_for(self, file_id: UUID) -> Path:
        if file_id not in self.known:
            raise NotFoundError("archivo no encontrado")
        return self.known[file_id]

    def delete(self, file_id: UUID) -> None:
        path = self.known.pop(file_id, None)
        if path is not None:
            path.unlink(missing_ok=True)

    def work_dir(self, job_id: UUID) -> Path:
        path = self.root / str(job_id)
        path.mkdir(exist_ok=True)
        return path


class FakeJobs:
    def __init__(self) -> None:
        self.jobs: dict[UUID, Job] = {}
        self.history: list[tuple[JobStatus, str | None]] = []

    def save(self, job: Job) -> None:
        self.jobs[job.id] = job
        self.history.append((job.status, job.stage))

    def get(self, job_id: UUID) -> Job:
        return self.jobs[job_id]

    def next_queued(self) -> Job | None:
        return next((j for j in self.jobs.values() if j.status is JobStatus.QUEUED), None)


class FakeWriter:
    def __init__(self) -> None:
        self.briefs: list[ScriptBrief] = []

    def write(self, brief: ScriptBrief) -> Script:
        self.briefs.append(brief)
        return make_script()


class FakeStock:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, kind: MediaKind, per_page: int) -> list[BackgroundAsset]:
        self.queries.append(query)
        return [make_background()]

    def download(self, asset: BackgroundAsset, target_dir: Path) -> Path:
        path = target_dir / "bg.mp4"
        path.write_bytes(b"bg")
        return path


class FakeSpeech:
    def synthesize(self, text: str, voice: str, target: Path) -> SpeechResult:
        target.write_bytes(b"wav")
        return SpeechResult(audio_path=target, duration_seconds=8.0)


class FakeAnimator:
    def __init__(self, fail: Exception | None = None) -> None:
        self.fail = fail

    def animate(self, photo: Path, audio: Path, target: Path, on_progress: ProgressCallback) -> Path:
        if self.fail is not None:
            raise self.fail
        on_progress(0.5)
        target.write_bytes(b"avatar")
        return target


class FakeComposer:
    def __init__(self) -> None:
        self.specs: list[CompositionSpec] = []

    def compose(self, spec: CompositionSpec) -> Path:
        self.specs.append(spec)
        spec.output_path.write_bytes(b"mp4")
        return spec.output_path


class FakeProber:
    def __init__(self, video: MediaProbe, audio_seconds: float = 8.0) -> None:
        self.video = video
        self.audio_seconds = audio_seconds

    def probe(self, path: Path) -> MediaProbe:
        if path.suffix == ".wav":
            return MediaProbe(0, 0, self.audio_seconds, True)
        return self.video


class FakeAvatars:
    def __init__(self) -> None:
        self.avatars: dict[UUID, Avatar] = {}

    def save(self, avatar: Avatar) -> None:
        self.avatars[avatar.id] = avatar

    def get(self, avatar_id: UUID) -> Avatar:
        if avatar_id not in self.avatars:
            raise NotFoundError("avatar no encontrado")
        return self.avatars[avatar_id]

    def list(self) -> list[Avatar]:
        return list(self.avatars.values())

    def delete(self, avatar_id: UUID) -> None:
        self.avatars.pop(avatar_id, None)


class FakeRemover:
    def __init__(self, fail: Exception | None = None) -> None:
        self.fail = fail

    def remove(self, photo: Path, target: Path) -> Path:
        if self.fail is not None:
            target.write_bytes(b"partial")
            raise self.fail
        target.write_bytes(b"cutout")
        return target


def make_avatar(files: FakeFiles, avatars: FakeAvatars) -> Avatar:
    source_id, source = files.new_path(".png")
    source.write_bytes(b"png")
    cutout_id, cutout = files.new_path(".png")
    cutout.write_bytes(b"cutout")
    avatar = Avatar(name="Yo", cutout_file_id=cutout_id, source_file_id=source_id)
    avatars.save(avatar)
    return avatar
