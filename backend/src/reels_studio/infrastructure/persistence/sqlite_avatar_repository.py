from __future__ import annotations

import sqlite3
from datetime import datetime
from uuid import UUID

from reels_studio.domain.errors import NotFoundError
from reels_studio.domain.models import Avatar
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase

_SCHEMA = """
CREATE TABLE IF NOT EXISTS avatars (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cutout_file_id TEXT NOT NULL,
    source_file_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _to_avatar(row: sqlite3.Row) -> Avatar:
    return Avatar(
        id=UUID(row["id"]),
        name=row["name"],
        cutout_file_id=UUID(row["cutout_file_id"]),
        source_file_id=UUID(row["source_file_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class SqliteAvatarRepository:
    def __init__(self, database: SqliteDatabase) -> None:
        self._db = database
        with self._db.transaction() as connection:
            connection.executescript(_SCHEMA)

    def save(self, avatar: Avatar) -> None:
        with self._db.transaction() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO avatars VALUES (?, ?, ?, ?, ?)",
                (
                    str(avatar.id),
                    avatar.name,
                    str(avatar.cutout_file_id),
                    str(avatar.source_file_id),
                    avatar.created_at.isoformat(),
                ),
            )

    def get(self, avatar_id: UUID) -> Avatar:
        with self._db.transaction() as connection:
            row = connection.execute("SELECT * FROM avatars WHERE id=?", (str(avatar_id),)).fetchone()
        if row is None:
            raise NotFoundError("avatar no encontrado")
        return _to_avatar(row)

    def list(self) -> list[Avatar]:
        with self._db.transaction() as connection:
            rows = connection.execute("SELECT * FROM avatars ORDER BY created_at DESC").fetchall()
        return [_to_avatar(row) for row in rows]

    def delete(self, avatar_id: UUID) -> None:
        with self._db.transaction() as connection:
            connection.execute("DELETE FROM avatars WHERE id=?", (str(avatar_id),))
