import json
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from reels_studio.application.use_cases.avatars import CreateAvatar, DeleteAvatar, ListAvatars
from reels_studio.domain.errors import EngineError, InvalidUploadError, NotFoundError
from reels_studio.domain.models import Avatar
from reels_studio.infrastructure.comfyui.green_screen import CHROMA_GREEN, flatten_on_green
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate
from reels_studio.infrastructure.persistence.sqlite_avatar_repository import SqliteAvatarRepository
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase
from tests.fakes import FakeAvatars, FakeFiles, FakeRemover, make_avatar

WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"


def _photo(files: FakeFiles):
    photo_id, photo = files.new_path(".png")
    photo.write_bytes(b"png")
    return photo_id


def test_create_avatar_removes_background_once_and_saves_it(tmp_path: Path) -> None:
    files, avatars = FakeFiles(tmp_path), FakeAvatars()
    photo_id = _photo(files)

    avatar = CreateAvatar(files, FakeRemover(), avatars).execute(photo_id, "  Julián   oficina ")

    assert avatar.name == "Julián oficina"
    assert files.path_for(avatar.cutout_file_id).read_bytes() == b"cutout"
    assert ListAvatars(avatars).execute() == [avatar]


def test_create_avatar_requires_name(tmp_path: Path) -> None:
    files = FakeFiles(tmp_path)

    with pytest.raises(InvalidUploadError):
        CreateAvatar(files, FakeRemover(), FakeAvatars()).execute(_photo(files), "   ")


def test_failed_background_removal_leaves_no_orphan_files(tmp_path: Path) -> None:
    files, avatars = FakeFiles(tmp_path), FakeAvatars()
    photo_id = _photo(files)
    remover = FakeRemover(fail=EngineError("ComfyUI no está corriendo"))

    with pytest.raises(EngineError):
        CreateAvatar(files, remover, avatars).execute(photo_id, "Yo")

    assert avatars.list() == []
    assert sorted(p.name for p in tmp_path.iterdir()) == [files.path_for(photo_id).name]


def test_delete_avatar_removes_row_and_files(tmp_path: Path) -> None:
    files, avatars = FakeFiles(tmp_path), FakeAvatars()
    avatar = make_avatar(files, avatars)

    DeleteAvatar(files, avatars).execute(avatar.id)

    assert avatars.list() == []
    with pytest.raises(NotFoundError):
        files.path_for(avatar.cutout_file_id)


def test_sqlite_avatar_repository_roundtrip(tmp_path: Path) -> None:
    repo = SqliteAvatarRepository(SqliteDatabase(tmp_path / "db.sqlite3"))
    avatar = Avatar(name="Yo", cutout_file_id=FakeFiles(tmp_path).new_path(".png")[0], source_file_id=uuid4())

    repo.save(avatar)

    assert repo.get(avatar.id) == avatar
    assert repo.list() == [avatar]
    repo.delete(avatar.id)
    with pytest.raises(NotFoundError):
        repo.get(avatar.id)


def test_flatten_on_green_fills_transparent_pixels(tmp_path: Path) -> None:
    cutout = tmp_path / "cutout.png"
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((0, 0), (200, 10, 10, 255))
    image.save(cutout)

    result = Image.open(flatten_on_green(cutout, tmp_path / "green.png"))

    assert result.getpixel((0, 0)) == (200, 10, 10)
    assert result.getpixel((3, 3)) == CHROMA_GREEN


@pytest.mark.parametrize(
    ("name", "values"),
    [
        ("remove_background.json", {"PHOTO": "a.png"}),
        ("avatar_talking_head.json", {"PHOTO": "a.png", "AUDIO": "b.wav"}),
    ],
)
def test_shipped_workflows_use_exactly_their_placeholders(name: str, values: dict[str, str]) -> None:
    rendered = WorkflowTemplate(WORKFLOWS / name).render(values)

    assert "{{" not in json.dumps(rendered)
