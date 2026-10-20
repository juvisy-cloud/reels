from pathlib import Path

import pytest

from reels_studio.application.ports import MediaProbe
from reels_studio.application.use_cases.render_reel import RenderEngines, RenderReel
from reels_studio.domain.errors import EngineError
from reels_studio.domain.models import Job, JobStatus, RenderStage
from tests.fakes import (
    FakeAnimator,
    FakeAvatars,
    FakeComposer,
    FakeFiles,
    FakeJobs,
    FakeProber,
    FakeSpeech,
    FakeStock,
    make_avatar,
    make_request,
)

GOOD_VIDEO = MediaProbe(width=1080, height=1920, duration_seconds=10.5, has_audio=True)


def _pipeline(tmp_path: Path, prober: FakeProber, animator: FakeAnimator | None = None):
    files, jobs, composer, avatars = FakeFiles(tmp_path), FakeJobs(), FakeComposer(), FakeAvatars()
    engines = RenderEngines(FakeSpeech(), animator or FakeAnimator(), FakeStock(), composer, prober)
    avatar = make_avatar(files, avatars)
    render = RenderReel(engines, files, jobs, avatars)
    return render, Job(request=make_request(avatar.id)), jobs, composer


def test_successful_render_marks_job_done_after_verification(tmp_path: Path) -> None:
    render, job, jobs, composer = _pipeline(tmp_path, FakeProber(GOOD_VIDEO))

    result = render.execute(job)

    assert result.status is JobStatus.DONE
    assert result.output_file_id is not None
    assert composer.specs[0].handle == "@juvisy.cloud"
    stages = [stage for _, stage in jobs.history if stage]
    assert (
        stages.index(RenderStage.AVATAR)
        < stages.index(RenderStage.COMPOSE)
        < stages.index(RenderStage.VERIFY)
    )


@pytest.mark.parametrize(
    ("probe", "reason"),
    [
        (MediaProbe(720, 1280, 10.5, True), "resolución"),
        (MediaProbe(1080, 1920, 10.5, False), "audio"),
        (MediaProbe(1080, 1920, 3.0, True), "duración"),
    ],
)
def test_failed_verification_never_reports_done(tmp_path: Path, probe: MediaProbe, reason: str) -> None:
    render, job, _, _ = _pipeline(tmp_path, FakeProber(probe))

    result = render.execute(job)

    assert result.status is JobStatus.FAILED
    assert reason in (result.error or "")


def test_engine_error_is_reported_with_user_message(tmp_path: Path) -> None:
    animator = FakeAnimator(fail=EngineError("ComfyUI no está corriendo"))
    render, job, _, _ = _pipeline(tmp_path, FakeProber(GOOD_VIDEO), animator)

    assert render.execute(job).error == "ComfyUI no está corriendo"


def test_unexpected_error_does_not_leak_internals(tmp_path: Path) -> None:
    animator = FakeAnimator(fail=RuntimeError("/home/secret/path traceback"))
    render, job, _, _ = _pipeline(tmp_path, FakeProber(GOOD_VIDEO), animator)

    result = render.execute(job)

    assert result.status is JobStatus.FAILED
    assert "/home" not in (result.error or "")
