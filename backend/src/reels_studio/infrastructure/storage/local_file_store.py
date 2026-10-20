"""Almacén de archivos por UUID. Nunca se usa un nombre provisto por el usuario (OWASP A01)."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from uuid import UUID

from reels_studio.domain.errors import NotFoundError

_SAFE_SUFFIX = re.compile(r"^\.[a-z0-9]{1,5}$")


class LocalFileStore:
    def __init__(self, root: Path) -> None:
        self._files = (root / "files").resolve()
        self._work = (root / "work").resolve()
        self._files.mkdir(parents=True, exist_ok=True)
        self._work.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, data: bytes, suffix: str) -> UUID:
        file_id, path = self.new_path(suffix)
        path.write_bytes(data)
        return file_id

    def new_path(self, suffix: str) -> tuple[UUID, Path]:
        if not _SAFE_SUFFIX.match(suffix):
            raise ValueError("extensión no permitida")
        file_id = uuid.uuid4()
        return file_id, self._files / f"{file_id}{suffix}"

    def path_for(self, file_id: UUID) -> Path:
        matches = [
            p for p in self._files.glob(f"{UUID(str(file_id))}.*") if p.resolve().parent == self._files
        ]
        if len(matches) != 1:
            raise NotFoundError("archivo no encontrado")
        return matches[0]

    def work_dir(self, job_id: UUID) -> Path:
        path = self._work / str(UUID(str(job_id)))
        path.mkdir(parents=True, exist_ok=True)
        return path

    def delete(self, file_id: UUID) -> None:
        try:
            self.path_for(file_id).unlink(missing_ok=True)
        except NotFoundError:
            return
