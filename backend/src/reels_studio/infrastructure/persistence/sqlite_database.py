"""Conexión SQLite compartida por los repositorios: una transacción por operación."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class SqliteDatabase:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._lock = threading.Lock()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit al salir sin error; rollback automático si algo falla."""
        with self._lock:
            connection = sqlite3.connect(self._path)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    yield connection
            finally:
                connection.close()
