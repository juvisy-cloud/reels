"""Biblioteca de avatares: el fondo se quita una sola vez y el recorte se reutiliza."""

from __future__ import annotations

from uuid import UUID

from reels_studio.application.ports import AvatarRepositoryPort, BackgroundRemoverPort, FileStorePort
from reels_studio.domain.errors import InvalidUploadError
from reels_studio.domain.models import Avatar

MAX_NAME_CHARS = 40


class CreateAvatar:
    def __init__(
        self, files: FileStorePort, remover: BackgroundRemoverPort, avatars: AvatarRepositoryPort
    ) -> None:
        self._files = files
        self._remover = remover
        self._avatars = avatars

    def execute(self, photo_file_id: UUID, name: str) -> Avatar:
        clean_name = " ".join(name.split())[:MAX_NAME_CHARS]
        if not clean_name:
            raise InvalidUploadError("ponle un nombre al avatar")
        photo = self._files.path_for(photo_file_id)
        cutout_id, cutout_path = self._files.new_path(".png")
        try:
            self._remover.remove(photo, cutout_path)
        except Exception:
            cutout_path.unlink(missing_ok=True)
            raise
        avatar = Avatar(name=clean_name, cutout_file_id=cutout_id, source_file_id=photo_file_id)
        self._avatars.save(avatar)
        return avatar


class ListAvatars:
    def __init__(self, avatars: AvatarRepositoryPort) -> None:
        self._avatars = avatars

    def execute(self) -> list[Avatar]:
        return self._avatars.list()


class DeleteAvatar:
    def __init__(self, files: FileStorePort, avatars: AvatarRepositoryPort) -> None:
        self._files = files
        self._avatars = avatars

    def execute(self, avatar_id: UUID) -> None:
        avatar = self._avatars.get(avatar_id)
        self._avatars.delete(avatar_id)
        for file_id in (avatar.cutout_file_id, avatar.source_file_id):
            self._files.delete(file_id)
