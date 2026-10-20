"""Pruebas de la API con el contenedor real pero motores falsos."""

import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from reels_studio.application.use_cases.avatars import CreateAvatar, DeleteAvatar, ListAvatars
from reels_studio.application.use_cases.generate_script import GenerateScript
from reels_studio.application.use_cases.search_backgrounds import SearchBackgrounds
from reels_studio.application.use_cases.submit_render import SubmitRender
from reels_studio.bootstrap import Container
from reels_studio.config import Settings
from reels_studio.infrastructure.persistence.sqlite_avatar_repository import SqliteAvatarRepository
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase
from reels_studio.infrastructure.persistence.sqlite_job_repository import SqliteJobRepository
from reels_studio.infrastructure.storage.local_file_store import LocalFileStore
from reels_studio.interfaces.http.app import create_app
from tests.fakes import FakeRemover, FakeStock, FakeWriter


class _IdleWorker:
    def start(self) -> None: ...

    def stop(self) -> None: ...


class _NoLlama:
    def stop(self) -> None: ...


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(data_dir=tmp_path)
    files = LocalFileStore(tmp_path)
    database = SqliteDatabase(tmp_path / "db.sqlite3")
    jobs, avatars = SqliteJobRepository(database), SqliteAvatarRepository(database)
    container = Container(
        settings=settings,
        files=files,
        jobs=jobs,
        generate_script=GenerateScript(FakeWriter(), 1500),
        search_backgrounds=SearchBackgrounds(FakeStock()),
        submit_render=SubmitRender(jobs, files, avatars),
        create_avatar=CreateAvatar(files, FakeRemover(), avatars),
        list_avatars=ListAvatars(avatars),
        delete_avatar=DeleteAvatar(files, avatars),
        worker=_IdleWorker(),  # type: ignore[arg-type]
        llama=_NoLlama(),  # type: ignore[arg-type]
    )
    with TestClient(create_app(settings, container)) as test_client:
        yield test_client


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (400, 400), "blue").save(buffer, format="PNG")
    return buffer.getvalue()


def _create_avatar(client: TestClient) -> dict[str, str]:
    upload = client.post("/api/uploads", files={"file": ("me.png", _png(), "image/png")})
    assert upload.status_code == 201
    avatar = client.post("/api/avatars", json={"photo_file_id": upload.json()["file_id"], "name": "Yo"})
    assert avatar.status_code == 201
    return avatar.json()


def test_avatar_library_create_list_delete(client: TestClient) -> None:
    avatar = _create_avatar(client)

    assert [a["id"] for a in client.get("/api/avatars").json()] == [avatar["id"]]
    assert client.get(f"/api/files/{avatar['cutout_file_id']}").status_code == 200
    assert client.delete(f"/api/avatars/{avatar['id']}").status_code == 204
    assert client.get("/api/avatars").json() == []
    assert client.get(f"/api/files/{avatar['cutout_file_id']}").status_code == 404


def test_render_with_unknown_avatar_is_rejected(client: TestClient) -> None:
    script = client.post("/api/scripts", json={"context": "agenda"}).json()
    background = client.get("/api/backgrounds", params={"query": "office"}).json()[0]

    response = client.post(
        "/api/renders", json={"avatar_id": str(uuid.uuid4()), "script": script, "background": background}
    )

    assert response.status_code == 404


def test_upload_then_render_flow(client: TestClient) -> None:
    avatar = _create_avatar(client)
    script = client.post(
        "/api/scripts", json={"context": "agenda de citas", "handle": "@juvisy.cloud"}
    ).json()
    background = client.get("/api/backgrounds", params={"query": "office"}).json()[0]

    render = client.post(
        "/api/renders",
        json={"avatar_id": avatar["id"], "script": script, "background": background},
    )

    assert render.status_code == 202
    assert render.json()["status"] == "queued"
    assert client.get(f"/api/renders/{render.json()['id']}").status_code == 200


def test_upload_rejects_non_image(client: TestClient) -> None:
    response = client.post("/api/uploads", files={"file": ("x.png", b"<svg/>", "image/png")})

    assert response.status_code == 422


def test_files_endpoint_rejects_traversal(client: TestClient) -> None:
    assert client.get("/api/files/..%2F..%2Fetc%2Fpasswd").status_code in {404, 422}
    assert client.get(f"/api/files/{uuid.uuid4()}").status_code == 404


def test_render_rejects_unknown_fields_and_bad_handle(client: TestClient) -> None:
    response = client.post("/api/scripts", json={"context": "x", "handle": "@bad handle;rm", "admin": True})

    assert response.status_code == 422


def test_security_headers_present(client: TestClient) -> None:
    headers = client.get("/api/voices").headers

    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
