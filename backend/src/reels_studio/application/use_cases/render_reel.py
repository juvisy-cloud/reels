"""Pipeline de render: voz → avatar → fondo → composición → verificación.

El orden es fijo (Template Method en `execute`); cada etapa es un método corto
que solo conoce puertos. El job solo pasa a DONE si la verificación pasa.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from reels_studio.application.ports import (
    AvatarAnimatorPort,
    AvatarRepositoryPort,
    CompositionSpec,
    FileStorePort,
    JobRepositoryPort,
    MediaProberPort,
    SpeechSynthesizerPort,
    StockMediaPort,
    VideoComposerPort,
)
from reels_studio.domain.errors import DomainError, VerificationError
from reels_studio.domain.models import Job, RenderStage

REEL_WIDTH = 1080
REEL_HEIGHT = 1920
OUTRO_SECONDS = 2.5
DURATION_TOLERANCE = 1.0

_STAGE_WEIGHTS: dict[RenderStage, tuple[float, float]] = {
    RenderStage.VOICE: (0.0, 0.05),
    RenderStage.AVATAR: (0.05, 0.80),
    RenderStage.BACKGROUND: (0.80, 0.85),
    RenderStage.COMPOSE: (0.85, 0.97),
    RenderStage.VERIFY: (0.97, 1.0),
}


@dataclass(frozen=True, slots=True)
class RenderEngines:
    speech: SpeechSynthesizerPort
    animator: AvatarAnimatorPort
    stock: StockMediaPort
    composer: VideoComposerPort
    prober: MediaProberPort


class RenderReel:
    def __init__(
        self,
        engines: RenderEngines,
        files: FileStorePort,
        jobs: JobRepositoryPort,
        avatars: AvatarRepositoryPort,
    ) -> None:
        self._engines = engines
        self._files = files
        self._jobs = jobs
        self._avatars = avatars

    def execute(self, job: Job) -> Job:
        try:
            work = self._files.work_dir(job.id)
            audio = self._voice(job, work)
            avatar = self._avatar(job, audio, work)
            background = self._background(job, work)
            output_id, output = self._compose(job, audio, avatar, background)
            self._verify(job, output_id, output, audio)
        except DomainError as error:
            job.fail(str(error))
        except Exception:
            job.fail("error interno al generar el reel; revisa los logs del servidor")
        self._jobs.save(job)
        return job

    def _report(self, job: Job, stage: RenderStage, fraction: float = 0.0) -> None:
        start, end = _STAGE_WEIGHTS[stage]
        job.advance(stage, start + (end - start) * fraction)
        self._jobs.save(job)

    def _voice(self, job: Job, work: Path) -> Path:
        self._report(job, RenderStage.VOICE)
        script = job.request.script
        return self._engines.speech.synthesize(
            script.narration, job.request.voice, work / "voice.wav"
        ).audio_path

    def _avatar(self, job: Job, audio: Path, work: Path) -> Path:
        self._report(job, RenderStage.AVATAR)
        avatar = self._avatars.get(job.request.avatar_id)
        photo = self._files.path_for(avatar.cutout_file_id)
        return self._engines.animator.animate(
            photo, audio, work / "avatar.mp4", lambda f: self._report(job, RenderStage.AVATAR, f)
        )

    def _background(self, job: Job, work: Path) -> Path:
        self._report(job, RenderStage.BACKGROUND)
        return self._engines.stock.download(job.request.background, work)

    def _compose(self, job: Job, audio: Path, avatar: Path, background: Path) -> tuple[UUID, Path]:
        self._report(job, RenderStage.COMPOSE)
        request = job.request
        output_id, output_path = self._files.new_path(".mp4")
        self._engines.composer.compose(
            CompositionSpec(
                background_path=background,
                background_kind=request.background.kind,
                avatar_video_path=avatar,
                audio_path=audio,
                script=request.script,
                handle=request.brand.handle,
                logo_path=self._optional_path(request.brand.logo_file_id),
                overlay_path=self._optional_path(request.overlay_file_id),
                output_path=output_path,
            )
        )
        return output_id, output_path

    def _verify(self, job: Job, output_id: UUID, output: Path, audio: Path) -> None:
        self._report(job, RenderStage.VERIFY)
        result = self._engines.prober.probe(output)
        voice = self._engines.prober.probe(audio)
        expected = voice.duration_seconds + OUTRO_SECONDS
        if (result.width, result.height) != (REEL_WIDTH, REEL_HEIGHT):
            raise VerificationError(f"resolución inesperada {result.width}x{result.height}")
        if not result.has_audio:
            raise VerificationError("el video final no tiene audio")
        if abs(result.duration_seconds - expected) > DURATION_TOLERANCE:
            raise VerificationError("la duración del video no coincide con la narración")
        job.complete(output_id)

    def _optional_path(self, file_id: UUID | None) -> Path | None:
        return None if file_id is None else self._files.path_for(file_id)
