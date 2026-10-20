from __future__ import annotations

from pathlib import Path

import av

from reels_studio.application.ports import MediaProbe
from reels_studio.domain.errors import VerificationError


class PyAvProber:
    def probe(self, path: Path) -> MediaProbe:
        try:
            with av.open(str(path)) as container:
                video = next(iter(container.streams.video), None)
                duration = float(container.duration or 0) / 1_000_000
                return MediaProbe(
                    width=video.codec_context.width if video else 0,
                    height=video.codec_context.height if video else 0,
                    duration_seconds=duration,
                    has_audio=bool(container.streams.audio),
                )
        except (av.error.FFmpegError, OSError) as error:
            raise VerificationError("el archivo generado no se puede leer") from error
