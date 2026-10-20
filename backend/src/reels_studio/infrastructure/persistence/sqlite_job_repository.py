from __future__ import annotations

import json
import sqlite3
from uuid import UUID

from reels_studio.domain.errors import NotFoundError
from reels_studio.domain.models import Job, JobStatus
from reels_studio.infrastructure.persistence.job_mapper import (
    job_from_row,
    request_from_dict,
    request_to_dict,
)
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    stage TEXT,
    progress REAL NOT NULL,
    error TEXT,
    output_file_id TEXT,
    request_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_status_created ON jobs(status, created_at);
"""

_UPSERT = """
INSERT INTO jobs (id, status, stage, progress, error, output_file_id, request_json, created_at)
VALUES (:id, :status, :stage, :progress, :error, :output_file_id, :request_json, :created_at)
ON CONFLICT(id) DO UPDATE SET status=excluded.status, stage=excluded.stage, progress=excluded.progress,
    error=excluded.error, output_file_id=excluded.output_file_id
"""


class SqliteJobRepository:
    def __init__(self, database: SqliteDatabase) -> None:
        self._db = database
        with self._db.transaction() as connection:
            connection.executescript(_SCHEMA)
            # Un job RUNNING tras reiniciar quedó huérfano: se marca como fallido.
            connection.execute(
                "UPDATE jobs SET status=?, error=? WHERE status=?",
                (JobStatus.FAILED, "el servidor se reinició durante el render", JobStatus.RUNNING),
            )

    def save(self, job: Job) -> None:
        with self._db.transaction() as connection:
            connection.execute(
                _UPSERT,
                {
                    "id": str(job.id),
                    "status": job.status,
                    "stage": job.stage,
                    "progress": job.progress,
                    "error": job.error,
                    "output_file_id": None if job.output_file_id is None else str(job.output_file_id),
                    "request_json": json.dumps(request_to_dict(job.request), ensure_ascii=False),
                    "created_at": job.created_at.isoformat(),
                },
            )

    def get(self, job_id: UUID) -> Job:
        with self._db.transaction() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id=?", (str(job_id),)).fetchone()
        if row is None:
            raise NotFoundError("render no encontrado")
        return self._to_job(row)

    def next_queued(self) -> Job | None:
        with self._db.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE status=? ORDER BY created_at LIMIT 1", (JobStatus.QUEUED,)
            ).fetchone()
        return None if row is None else self._to_job(row)

    @staticmethod
    def _to_job(row: sqlite3.Row) -> Job:
        data = dict(row)
        return job_from_row(data, request_from_dict(json.loads(data["request_json"])))
