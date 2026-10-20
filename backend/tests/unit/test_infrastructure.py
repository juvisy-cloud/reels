import json
import uuid
from pathlib import Path

import httpx
import pytest
import respx

from reels_studio.application.ports import ScriptBrief
from reels_studio.domain.errors import EngineError, InvalidScriptError
from reels_studio.domain.models import Job, JobStatus
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate
from reels_studio.infrastructure.compose.filtergraph import FilterGraphBuilder
from reels_studio.infrastructure.compose.timeline import overlay_window, scene_windows
from reels_studio.infrastructure.llm.llama_script_writer import LlamaScriptWriter
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase
from reels_studio.infrastructure.persistence.sqlite_job_repository import SqliteJobRepository
from tests.fakes import make_request, make_script


class _AlwaysUp:
    def ensure_running(self) -> str:
        return "http://llm.test"


def _llm_reply(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


VALID_SCRIPT = {
    "hook": "Agenda\x07 sin llamadas 🤖",
    "scenes": [
        {"narration": "Hola.", "on_screen_text": "Hola", "seconds": 5},
        {"narration": "Agenda.", "on_screen_text": "Agenda", "seconds": 5},
    ],
    "cta": "Síguenos",
    "pexels_queries": ["office"],
}


@respx.mock
def test_script_writer_validates_and_cleans_llm_output() -> None:
    respx.post("http://llm.test/v1/chat/completions").mock(return_value=_llm_reply(json.dumps(VALID_SCRIPT)))

    script = LlamaScriptWriter(_AlwaysUp(), 5).write(ScriptBrief("tema", "", 10, "@x"))  # type: ignore[arg-type]

    assert script.hook == "Agenda sin llamadas"
    assert len(script.scenes) == 2


@respx.mock
def test_script_writer_rejects_malformed_json() -> None:
    respx.post("http://llm.test/v1/chat/completions").mock(return_value=_llm_reply("{not json"))

    with pytest.raises(InvalidScriptError):
        LlamaScriptWriter(_AlwaysUp(), 5).write(ScriptBrief("tema", "", 10, ""))  # type: ignore[arg-type]


@respx.mock
def test_script_writer_maps_connection_errors() -> None:
    respx.post("http://llm.test/v1/chat/completions").mock(side_effect=httpx.ConnectError("down"))

    with pytest.raises(EngineError):
        LlamaScriptWriter(_AlwaysUp(), 5).write(ScriptBrief("tema", "", 10, ""))  # type: ignore[arg-type]


def test_workflow_template_replaces_only_exact_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "wf.json"
    path.write_text(json.dumps({"1": {"inputs": {"image": "{{PHOTO}}", "note": "x {{PHOTO}}"}}}))

    rendered = WorkflowTemplate(path).render({"PHOTO": "a.png"})

    assert rendered["1"]["inputs"] == {"image": "a.png", "note": "x {{PHOTO}}"}


def test_workflow_template_detects_unused_values(tmp_path: Path) -> None:
    path = tmp_path / "wf.json"
    path.write_text(json.dumps({"1": {"inputs": {"image": "{{PHOTO}}"}}}))

    with pytest.raises(EngineError):
        WorkflowTemplate(path).render({"PHOTO": "a.png", "AUDIO": "b.wav"})


def test_scene_windows_scale_to_real_voice_duration() -> None:
    windows = scene_windows(make_script(), voice_seconds=12.0)

    assert [(w.start, w.end) for w in windows] == [(0.0, 6.0), (6.0, 12.0)]
    assert overlay_window(windows) == windows[1]


def test_filtergraph_builds_argument_list_without_shell() -> None:
    graph = FilterGraphBuilder("ffmpeg")
    index = graph.add_input(Path("bg.jpg"), loop_image_seconds=3)
    label = graph.chain([f"{index}:v"], "scale=1080:1920")
    command = graph.build(label, f"{index}:a", Path("out.mp4"), 3)

    assert command[:2] == ["ffmpeg", "-y"]
    assert "-filter_complex" in command
    assert "[0:v]scale=1080:1920[l1]" in command


def test_sqlite_repository_roundtrip_and_orphan_recovery(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite3"
    repo = SqliteJobRepository(SqliteDatabase(database))
    job = Job(request=make_request(uuid.uuid4()))
    repo.save(job)
    assert repo.next_queued() is not None
    job.status = JobStatus.RUNNING
    repo.save(job)

    restored = SqliteJobRepository(SqliteDatabase(database)).get(job.id)

    assert restored.status is JobStatus.FAILED
    assert restored.request == job.request
