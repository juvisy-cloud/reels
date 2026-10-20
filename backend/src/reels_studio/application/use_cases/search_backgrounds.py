from reels_studio.application.ports import StockMediaPort
from reels_studio.domain.errors import InvalidScriptError
from reels_studio.domain.models import BackgroundAsset, MediaKind

MAX_QUERY_CHARS = 80
PER_PAGE = 15


class SearchBackgrounds:
    def __init__(self, stock: StockMediaPort) -> None:
        self._stock = stock

    def execute(self, query: str, kind: MediaKind) -> list[BackgroundAsset]:
        cleaned = " ".join(query.split())
        if not cleaned or len(cleaned) > MAX_QUERY_CHARS:
            raise InvalidScriptError(f"la búsqueda debe tener entre 1 y {MAX_QUERY_CHARS} caracteres")
        return self._stock.search(cleaned, kind, PER_PAGE)
