"""Search engine configuration."""

from enum import Enum

from pydantic import BaseModel, Field


class SearchEngine(str, Enum):
    """Supported search engine backends."""

    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"
    BING = "bing"


class SearchConfig(BaseModel):
    """Configuration for web search capabilities.

    API keys must be supplied through environment variables or
    the blueprint.yaml configuration file.
    """

    engine: SearchEngine = SearchEngine.DUCKDUCKGO
    api_key: str = ""
    cse_id: str = ""  # Google Custom Search Engine ID
    max_results: int = Field(default=8, ge=1, le=50)
    safe_search: bool = True
    language: str = "en"
    country: str = "us"

    def is_configured(self) -> bool:
        """Return True if the search engine has the required credentials."""
        if self.engine == SearchEngine.DUCKDUCKGO:
            return True
        return bool(self.api_key)


__all__ = ["SearchEngine", "SearchConfig"]
