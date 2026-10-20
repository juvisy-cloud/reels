from reels_studio.application.ports import ScriptBrief, ScriptWriterPort
from reels_studio.domain.errors import InvalidScriptError
from reels_studio.domain.models import Script

MIN_TARGET_SECONDS = 10
MAX_TARGET_SECONDS = 45


class GenerateScript:
    def __init__(self, writer: ScriptWriterPort, max_context_chars: int) -> None:
        self._writer = writer
        self._max_context_chars = max_context_chars

    def execute(self, brief: ScriptBrief) -> Script:
        context = brief.context.strip()
        if not context:
            raise InvalidScriptError("escribe de qué trata el reel")
        if len(context) > self._max_context_chars:
            raise InvalidScriptError(f"el contexto no puede superar {self._max_context_chars} caracteres")
        seconds = min(max(brief.target_seconds, MIN_TARGET_SECONDS), MAX_TARGET_SECONDS)
        return self._writer.write(
            ScriptBrief(context=context, tone=brief.tone.strip(), target_seconds=seconds, handle=brief.handle)
        )
