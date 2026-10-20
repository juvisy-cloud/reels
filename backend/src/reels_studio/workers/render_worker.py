"""Worker de un solo hilo: el render es CPU-bound, ejecutar dos a la vez solo lo hace más lento."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from reels_studio.application.ports import JobRepositoryPort
from reels_studio.application.use_cases.render_reel import RenderReel

logger = logging.getLogger(__name__)
_IDLE_SECONDS = 1.5


class RenderWorker:
    def __init__(
        self, jobs: JobRepositoryPort, render: RenderReel, before_render: Callable[[], None]
    ) -> None:
        self._jobs = jobs
        self._render = render
        self._before_render = before_render
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="render-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            job = self._jobs.next_queued()
            if job is None:
                self._stop.wait(_IDLE_SECONDS)
                continue
            logger.info("render %s iniciado", job.id)
            self._before_render()
            finished = self._render.execute(job)
            logger.info("render %s terminó con estado %s", job.id, finished.status)
