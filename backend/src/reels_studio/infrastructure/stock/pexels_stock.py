"""Adaptador de Pexels. La llave nunca sale del backend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from pydantic import SecretStr

from reels_studio.domain.errors import EngineError
from reels_studio.domain.models import BackgroundAsset, MediaKind
from reels_studio.infrastructure.stock.safe_downloader import SafeDownloader

_TARGET_HEIGHT = 1920


def _photo_to_asset(item: dict[str, Any]) -> BackgroundAsset:
    src = item["src"]
    return BackgroundAsset(
        provider_id=int(item["id"]),
        kind=MediaKind.PHOTO,
        preview_url=src["portrait"],
        download_url=src["large2x"],
        width=int(item["width"]),
        height=int(item["height"]),
        author=str(item["photographer"]),
        author_url=str(item["photographer_url"]),
    )


def _best_video_file(files: list[dict[str, Any]]) -> dict[str, Any]:
    portrait = [f for f in files if f.get("height") and f.get("width") and f["height"] > f["width"]]
    candidates = portrait or files
    return min(candidates, key=lambda f: abs(int(f.get("height") or 0) - _TARGET_HEIGHT))


def _video_to_asset(item: dict[str, Any]) -> BackgroundAsset:
    best = _best_video_file(item["video_files"])
    return BackgroundAsset(
        provider_id=int(item["id"]),
        kind=MediaKind.VIDEO,
        preview_url=str(item["image"]),
        download_url=str(best["link"]),
        width=int(best["width"]),
        height=int(best["height"]),
        author=str(item["user"]["name"]),
        author_url=str(item["user"]["url"]),
        duration_seconds=float(item["duration"]),
    )


class PexelsStock:
    def __init__(self, api_key: SecretStr, base_url: str, downloader: SafeDownloader) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._downloader = downloader

    def search(self, query: str, kind: MediaKind, per_page: int) -> list[BackgroundAsset]:
        if not self._api_key.get_secret_value():
            raise EngineError("falta configurar REELS_PEXELS_API_KEY en el archivo .env")
        path, key, mapper = (
            ("/v1/search", "photos", _photo_to_asset)
            if kind is MediaKind.PHOTO
            else ("/videos/search", "videos", _video_to_asset)
        )
        params: dict[str, str | int] = {"query": query, "orientation": "portrait", "per_page": per_page}
        try:
            response = httpx.get(
                f"{self._base_url}{path}",
                params=params,
                headers={"Authorization": self._api_key.get_secret_value()},
                timeout=20.0,
            )
            response.raise_for_status()
            return [mapper(item) for item in response.json().get(key, [])]
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise EngineError("no se pudo consultar Pexels en este momento") from error

    def download(self, asset: BackgroundAsset, target_dir: Path) -> Path:
        suffix = ".jpg" if asset.kind is MediaKind.PHOTO else ".mp4"
        target = target_dir / f"background-{asset.kind}-{asset.provider_id}{suffix}"
        if target.is_file():
            return target
        return self._downloader.download(asset.download_url, target)
