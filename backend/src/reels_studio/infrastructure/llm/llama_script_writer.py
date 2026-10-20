from __future__ import annotations

import json
import re

import httpx
from pydantic import BaseModel, Field, ValidationError

from reels_studio.application.ports import ScriptBrief
from reels_studio.domain.errors import EngineError, InvalidScriptError
from reels_studio.domain.models import Scene, Script
from reels_studio.infrastructure.llm.llama_supervisor import LlamaServerSupervisor
from reels_studio.infrastructure.llm.prompts import SCRIPT_JSON_SCHEMA, SYSTEM_PROMPT, USER_TEMPLATE

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
# Emojis y símbolos: la fuente de los textos no los dibuja y la voz los leería mal.
_EMOJI = re.compile("[\u2190-\u2bff\u2e00-\u2e7f\U0001f000-\U0001faff\ufe0f\u200d]")


class _SceneDTO(BaseModel):
    narration: str = Field(min_length=1, max_length=400)
    on_screen_text: str = Field(max_length=60)
    seconds: float = Field(ge=2, le=20)


class _ScriptDTO(BaseModel):
    hook: str = Field(max_length=80)
    scenes: list[_SceneDTO] = Field(min_length=1, max_length=4)
    cta: str = Field(max_length=120)
    pexels_queries: list[str] = Field(min_length=1, max_length=3)


def _clean(text: str) -> str:
    return " ".join(_EMOJI.sub("", _CONTROL_CHARS.sub("", text)).split())


def _to_domain(dto: _ScriptDTO) -> Script:
    return Script(
        hook=_clean(dto.hook),
        scenes=tuple(
            Scene(narration=_clean(s.narration), on_screen_text=_clean(s.on_screen_text), seconds=s.seconds)
            for s in dto.scenes
        ),
        cta=_clean(dto.cta),
        pexels_queries=tuple(_clean(q)[:40] for q in dto.pexels_queries if q.strip()),
    )


class LlamaScriptWriter:
    """Usa el LLM solo para redactar/extraer JSON; la validación es determinista."""

    def __init__(self, supervisor: LlamaServerSupervisor, timeout_seconds: float) -> None:
        self._supervisor = supervisor
        self._timeout = timeout_seconds

    def write(self, brief: ScriptBrief) -> Script:
        base_url = self._supervisor.ensure_running()
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._user_message(brief)},
            ],
            "temperature": 0.7,
            "max_tokens": 900,
            # Gemma 4 "piensa" por defecto y en CPU eso consume minutos y el presupuesto de tokens.
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_schema", "json_schema": {"schema": SCRIPT_JSON_SCHEMA}},
        }
        try:
            response = httpx.post(f"{base_url}/v1/chat/completions", json=payload, timeout=self._timeout)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _to_domain(_ScriptDTO.model_validate(json.loads(content)))
        except (httpx.HTTPError, KeyError, IndexError) as error:
            raise EngineError("el modelo de lenguaje no respondió; intenta de nuevo") from error
        except (json.JSONDecodeError, ValidationError) as error:
            raise InvalidScriptError("el guion generado no es válido; vuelve a generarlo") from error

    @staticmethod
    def _user_message(brief: ScriptBrief) -> str:
        context = brief.context.replace("</contexto_usuario>", "")
        return USER_TEMPLATE.format(
            seconds=brief.target_seconds,
            tone=brief.tone or "cercano y profesional",
            handle=brief.handle or "(sin usuario)",
            context=context,
        )
