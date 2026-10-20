class DomainError(Exception):
    """Error de negocio con mensaje apto para mostrar al usuario."""


class InvalidScriptError(DomainError):
    pass


class InvalidUploadError(DomainError):
    pass


class ForbiddenUrlError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class EngineError(DomainError):
    """Falla de un motor externo (LLM, ComfyUI, TTS, ffmpeg)."""


class VerificationError(DomainError):
    pass
