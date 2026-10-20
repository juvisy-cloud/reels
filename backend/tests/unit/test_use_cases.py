import uuid
from pathlib import Path

import pytest

from reels_studio.application.ports import ScriptBrief
from reels_studio.application.use_cases.generate_script import GenerateScript
from reels_studio.application.use_cases.search_backgrounds import SearchBackgrounds
from reels_studio.application.use_cases.submit_render import SubmitRender
from reels_studio.domain.errors import InvalidScriptError, NotFoundError
from reels_studio.domain.models import JobStatus, MediaKind, Scene, Script
from tests.fakes import (
    FakeAvatars,
    FakeFiles,
    FakeJobs,
    FakeStock,
    FakeWriter,
    make_avatar,
    make_request,
)


def test_generate_script_clamps_duration_and_trims_context() -> None:
    writer = FakeWriter()

    GenerateScript(writer, max_context_chars=100).execute(ScriptBrief("  agenda  ", "", 300, "@x"))

    assert writer.briefs[0].context == "agenda"
    assert writer.briefs[0].target_seconds == 45


@pytest.mark.parametrize("context", ["", "   ", "x" * 101])
def test_generate_script_rejects_empty_or_huge_context(context: str) -> None:
    with pytest.raises(InvalidScriptError):
        GenerateScript(FakeWriter(), max_context_chars=100).execute(ScriptBrief(context, "", 15, ""))


def test_search_backgrounds_normalizes_query() -> None:
    stock = FakeStock()

    SearchBackgrounds(stock).execute("  modern   office ", MediaKind.VIDEO)

    assert stock.queries == ["modern office"]


def test_submit_render_requires_existing_avatar(tmp_path: Path) -> None:
    use_case = SubmitRender(FakeJobs(), FakeFiles(tmp_path), FakeAvatars())

    with pytest.raises(NotFoundError):
        use_case.execute(make_request(uuid.uuid4()))


def test_submit_render_queues_job(tmp_path: Path) -> None:
    files, jobs, avatars = FakeFiles(tmp_path), FakeJobs(), FakeAvatars()
    avatar = make_avatar(files, avatars)

    job = SubmitRender(jobs, files, avatars).execute(make_request(avatar.id))

    assert jobs.next_queued() is job
    assert job.status is JobStatus.QUEUED


def test_script_rejects_out_of_range_duration() -> None:
    with pytest.raises(InvalidScriptError):
        Script("h", (Scene("a", "b", 1.0),), "c", ())
