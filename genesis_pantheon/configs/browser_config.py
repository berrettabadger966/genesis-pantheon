"""Browser automation configuration."""

from enum import Enum

from pydantic import BaseModel, Field


class BrowserDriver(str, Enum):
    """Supported browser automation backends."""

    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"


class BrowserConfig(BaseModel):
    """Configuration for browser automation tools."""

    driver: BrowserDriver = BrowserDriver.PLAYWRIGHT
    headless: bool = True
    timeout: int = Field(default=30, ge=1)
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    proxy: str = ""
    screenshot_on_error: bool = False

    def is_configured(self) -> bool:
        """Return True if browser driver is available."""
        try:
            if self.driver == BrowserDriver.PLAYWRIGHT:
                import playwright  # noqa: F401

                return True
            else:
                import selenium  # noqa: F401

                return True
        except ImportError:
            return False


__all__ = ["BrowserDriver", "BrowserConfig"]
