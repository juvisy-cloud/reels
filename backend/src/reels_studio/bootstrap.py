"""Composition root: el único lugar que conoce las implementaciones concretas."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

from reels_studio.application.use_cases.avatars import CreateAvatar, DeleteAvatar, ListAvatars
from reels_studio.application.use_cases.generate_script import GenerateScript
from reels_studio.application.use_cases.render_reel import RenderEngines, RenderReel
from reels_studio.application.use_cases.search_backgrounds import SearchBackgrounds
from reels_studio.application.use_cases.submit_render import SubmitRender
from reels_studio.config import Settings
from reels_studio.infrastructure.comfyui.client import ComfyUIClient
from reels_studio.infrastructure.comfyui.comfy_avatar_animator import ComfyAvatarAnimator
from reels_studio.infrastructure.comfyui.comfy_background_remover import ComfyBackgroundRemover
from reels_studio.infrastructure.comfyui.workflow_runner import ComfyWorkflowRunner
from reels_studio.infrastructure.comfyui.workflow_template import WorkflowTemplate
from reels_studio.infrastructure.compose.ffmpeg_composer import FfmpegComposer
from reels_studio.infrastructure.compose.media_prober import PyAvProber
from reels_studio.infrastructure.compose.text_cards import CardRenderer
from reels_studio.infrastructure.llm.llama_script_writer import LlamaScriptWriter
from reels_studio.infrastructure.llm.llama_supervisor import LlamaServerSupervisor
from reels_studio.infrastructure.persistence.sqlite_avatar_repository import SqliteAvatarRepository
from reels_studio.infrastructure.persistence.sqlite_database import SqliteDatabase
from reels_studio.infrastructure.persistence.sqlite_job_repository import SqliteJobRepository
from reels_studio.infrastructure.stock.pexels_stock import PexelsStock
from reels_studio.infrastructure.stock.safe_downloader import SafeDownloader
from reels_studio.infrastructure.storage.local_file_store import LocalFileStore
from reels_studio.infrastructure.tts.kokoro_speech import KokoroSpeech
from reels_studio.workers.render_worker import RenderWorker

_PEXELS_HOSTS = ("pexels.com",)
_MAX_BACKGROUND_BYTES = 250 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    files: LocalFileStore
    jobs: SqliteJobRepository
    generate_script: GenerateScript
    search_backgrounds: SearchBackgrounds
    submit_render: SubmitRender
    create_avatar: CreateAvatar
    list_avatars: ListAvatars
    delete_avatar: DeleteAvatar
    worker: RenderWorker
    llama: LlamaServerSupervisor


def _llama_binary() -> Path:
    found = shutil.which("llama-server")
    return Path(found) if found else Path.home() / ".local" / "bin" / "llama-server"


def _workflow(settings: Settings, name: str) -> WorkflowTemplate:
    return WorkflowTemplate(settings.workflows_dir / name)


def _build_engines(settings: Settings, runner: ComfyWorkflowRunner, stock: PexelsStock) -> RenderEngines:
    return RenderEngines(
        speech=KokoroSpeech(settings.kokoro_model_path, settings.kokoro_voices_path),
        animator=ComfyAvatarAnimator(
            runner, _workflow(settings, "avatar_talking_head.json"), settings.avatar_timeout_seconds
        ),
        stock=stock,
        composer=FfmpegComposer(imageio_ffmpeg.get_ffmpeg_exe(), CardRenderer(settings.font_path)),
        prober=PyAvProber(),
    )


def build_container(settings: Settings) -> Container:
    files = LocalFileStore(settings.data_dir)
    database = SqliteDatabase(settings.data_dir / "reels.sqlite3")
    jobs, avatars = SqliteJobRepository(database), SqliteAvatarRepository(database)
    llama = LlamaServerSupervisor(_llama_binary(), settings.llm_model_path, settings.llama_server_url)
    stock = PexelsStock(
        settings.pexels_api_key,
        settings.pexels_base_url,
        SafeDownloader(_PEXELS_HOSTS, _MAX_BACKGROUND_BYTES),
    )
    runner = ComfyWorkflowRunner(ComfyUIClient(settings.comfyui_url), settings.comfyui_input_dir)
    remover = ComfyBackgroundRemover(runner, _workflow(settings, "remove_background.json"))
    render = RenderReel(_build_engines(settings, runner, stock), files, jobs, avatars)
    return Container(
        settings=settings,
        files=files,
        jobs=jobs,
        generate_script=GenerateScript(
            LlamaScriptWriter(llama, settings.llm_timeout_seconds), settings.max_context_chars
        ),
        search_backgrounds=SearchBackgrounds(stock),
        submit_render=SubmitRender(jobs, files, avatars),
        create_avatar=CreateAvatar(files, remover, avatars),
        list_avatars=ListAvatars(avatars),
        delete_avatar=DeleteAvatar(files, avatars),
        worker=RenderWorker(jobs, render, before_render=llama.stop),
        llama=llama,
    )
