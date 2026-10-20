from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_HOME = Path.home()
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_PROJECT_ROOT / ".env", env_prefix="REELS_", extra="ignore")

    data_dir: Path = _PROJECT_ROOT / "data"
    workflows_dir: Path = _PROJECT_ROOT / "workflows"
    frontend_origin: str = "http://localhost:5173"

    pexels_api_key: SecretStr = SecretStr("")
    pexels_base_url: str = "https://api.pexels.com"

    llama_server_url: str = "http://127.0.0.1:8090"
    llm_model_path: Path = _HOME / "modelos" / "gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
    font_path: Path = Path("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf")
    llm_timeout_seconds: float = 180.0

    comfyui_url: str = "http://127.0.0.1:8188"
    comfyui_input_dir: Path = _HOME / "ComfyUI" / "input"
    avatar_timeout_seconds: float = 3600.0

    kokoro_model_path: Path = _HOME / "ai-engines" / "kokoro" / "kokoro-v1.0.onnx"
    kokoro_voices_path: Path = _HOME / "ai-engines" / "kokoro" / "voices-v1.0.bin"
    default_voice: str = "em_alex"

    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_context_chars: int = Field(default=1500, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
