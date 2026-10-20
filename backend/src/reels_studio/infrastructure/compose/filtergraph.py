"""Builder de comandos ffmpeg: entradas numeradas + cadenas de filtros con etiquetas."""

from __future__ import annotations

from pathlib import Path


class FilterGraphBuilder:
    def __init__(self, ffmpeg_binary: str) -> None:
        self._binary = ffmpeg_binary
        self._inputs: list[list[str]] = []
        self._chains: list[str] = []
        self._label_counter = 0

    def add_input(
        self, path: Path, *, loop_image_seconds: float | None = None, loop_video: bool = False
    ) -> int:
        args: list[str] = []
        if loop_image_seconds is not None:
            args += ["-loop", "1", "-t", f"{loop_image_seconds:.3f}"]
        if loop_video:
            args += ["-stream_loop", "-1"]
        self._inputs.append([*args, "-i", str(path)])
        return len(self._inputs) - 1

    def label(self) -> str:
        self._label_counter += 1
        return f"l{self._label_counter}"

    def chain(self, sources: list[str], filters: str) -> str:
        output = self.label()
        self._chains.append(f"{''.join(f'[{s}]' for s in sources)}{filters}[{output}]")
        return output

    def overlay_timed(self, base: str, layer: str, x: str, y: str, *, start: float, end: float) -> str:
        return self.chain([base, layer], f"overlay={x}:{y}:enable='between(t,{start:.3f},{end:.3f})'")

    def build(self, video_label: str, audio_label: str, output: Path, duration: float) -> list[str]:
        command = [self._binary, "-y", "-hide_banner", "-loglevel", "error"]
        for args in self._inputs:
            command += args
        command += [
            "-filter_complex",
            ";".join(self._chains),
            "-map",
            f"[{video_label}]",
            "-map",
            f"[{audio_label}]",
            "-t",
            f"{duration:.3f}",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ]
        return command
