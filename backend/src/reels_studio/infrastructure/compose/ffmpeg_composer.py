"""Compone el reel final 1080x1920: fondo + avatar (chroma key) + textos + mockup + cierre."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import soundfile

from reels_studio.application.ports import CompositionSpec
from reels_studio.domain.errors import EngineError
from reels_studio.domain.models import MediaKind
from reels_studio.infrastructure.compose.filtergraph import FilterGraphBuilder
from reels_studio.infrastructure.compose.text_cards import CardRenderer
from reels_studio.infrastructure.compose.timeline import Window, hook_window, overlay_window, scene_windows

OUTRO_SECONDS = 2.5
_FADE = 0.35
_TIMEOUT_SECONDS = 900
_FIT_REEL = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30"
_KEY_AVATAR = (
    "chromakey=0x00FF00:0.16:0.06,despill=type=green,"
    "scale=1080:1450:force_original_aspect_ratio=decrease,fps=30"
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Placement:
    x: str
    y: str
    window: Window
    fade: bool = False


class FfmpegComposer:
    def __init__(self, ffmpeg_binary: str, cards: CardRenderer) -> None:
        self._ffmpeg = ffmpeg_binary
        self._cards = cards

    def compose(self, spec: CompositionSpec) -> Path:
        voice = float(soundfile.info(str(spec.audio_path)).duration)
        graph = FilterGraphBuilder(self._ffmpeg)
        base = self._base_layer(graph, spec, voice)
        base = self._text_layers(graph, spec, voice, base)
        base = self._overlay_layer(graph, spec, voice, base)
        video = self._append_outro(graph, spec, voice, base)
        audio = graph.chain(
            [f"{graph.add_input(spec.audio_path)}:a"],
            f"aresample=48000,apad=whole_dur={voice + OUTRO_SECONDS:.3f}",
        )
        self._run(graph.build(video, audio, spec.output_path, voice + OUTRO_SECONDS))
        return spec.output_path

    def _base_layer(self, graph: FilterGraphBuilder, spec: CompositionSpec, voice: float) -> str:
        is_photo = spec.background_kind is MediaKind.PHOTO
        bg_index = graph.add_input(
            spec.background_path, loop_image_seconds=voice if is_photo else None, loop_video=not is_photo
        )
        background = graph.chain(
            [f"{bg_index}:v"], f"{_FIT_REEL},trim=duration={voice:.3f},setpts=PTS-STARTPTS"
        )
        avatar = graph.chain([f"{graph.add_input(spec.avatar_video_path)}:v"], _KEY_AVATAR)
        return graph.chain([background, avatar], "overlay=(W-w)/2:H-h:eof_action=repeat")

    def _text_layers(self, graph: FilterGraphBuilder, spec: CompositionSpec, voice: float, base: str) -> str:
        work = spec.output_path.parent
        hook = self._cards.caption(spec.script.hook, work / f"{spec.output_path.stem}-hook.png", font_size=78)
        window = hook_window(voice)
        base = self._still(graph, base, hook, voice, Placement("(W-w)/2", "140", window))
        for index, (scene, scene_window) in enumerate(
            zip(spec.script.scenes, scene_windows(spec.script, voice), strict=True)
        ):
            if not scene.on_screen_text:
                continue
            card = self._cards.caption(
                scene.on_screen_text, work / f"{spec.output_path.stem}-scene{index}.png"
            )
            base = self._still(graph, base, card, voice, Placement("(W-w)/2", "360", scene_window))
        return base

    def _overlay_layer(
        self, graph: FilterGraphBuilder, spec: CompositionSpec, voice: float, base: str
    ) -> str:
        if spec.overlay_path is None:
            return base
        framed = self._cards.phone_frame(
            spec.overlay_path, spec.output_path.parent / f"{spec.output_path.stem}-phone.png"
        )
        window = overlay_window(scene_windows(spec.script, voice))
        return self._still(graph, base, framed, voice, Placement("60", "520", window, fade=True))

    def _append_outro(self, graph: FilterGraphBuilder, spec: CompositionSpec, voice: float, base: str) -> str:
        outro = self._cards.outro(
            spec.handle,
            spec.script.cta,
            spec.logo_path,
            spec.output_path.parent / f"{spec.output_path.stem}-outro.png",
        )
        main = graph.chain([base], f"trim=duration={voice:.3f},setpts=PTS-STARTPTS,format=yuv420p,setsar=1")
        tail = graph.chain(
            [f"{graph.add_input(outro, loop_image_seconds=OUTRO_SECONDS)}:v"],
            "scale=1080:1920,fps=30,format=yuv420p,setsar=1",
        )
        return graph.chain([main, tail], "concat=n=2:v=1:a=0")

    @staticmethod
    def _still(graph: FilterGraphBuilder, base: str, image: Path, voice: float, place: Placement) -> str:
        layer = f"{graph.add_input(image, loop_image_seconds=voice)}:v"
        window = place.window
        if place.fade:
            fade_out = max(window.end - _FADE, window.start)
            layer = graph.chain(
                [layer],
                f"format=rgba,fade=t=in:st={window.start:.3f}:d={_FADE}:alpha=1,"
                f"fade=t=out:st={fade_out:.3f}:d={_FADE}:alpha=1",
            )
        return graph.overlay_timed(base, layer, place.x, place.y, start=window.start, end=window.end)

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=_TIMEOUT_SECONDS)  # noqa: S603
        except subprocess.CalledProcessError as error:
            logger.error("ffmpeg falló: %s", error.stderr.decode(errors="replace")[-2000:])
            raise EngineError("no se pudo componer el video final") from error
        except subprocess.TimeoutExpired as error:
            raise EngineError("la composición del video tardó demasiado") from error
