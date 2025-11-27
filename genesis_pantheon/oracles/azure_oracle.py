"""Azure OpenAI oracle adapter for GenesisPantheon."""

from __future__ import annotations

from typing import Any

from genesis_pantheon.configs.oracle_config import (
    OracleApiType,
)
from genesis_pantheon.oracles.openai_oracle import OpenAIOracle
from genesis_pantheon.oracles.registry import register_oracle


@register_oracle(OracleApiType.AZURE)
class AzureOracle(OpenAIOracle):
    """Azure OpenAI adapter.

    Inherits all logic from OpenAIOracle and only overrides the
    client construction to use ``AsyncAzureOpenAI``.
    """

    def _build_client(self) -> Any:
        """Create and return the AsyncAzureOpenAI client.

        Returns:
            AsyncAzureOpenAI client instance.
        """
        try:
            from openai import AsyncAzureOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required for AzureOracle. "
                "Install it with: pip install openai"
            ) from exc
        kwargs: dict = {
            "api_key": self.config.api_key or "placeholder",
            "azure_endpoint": self.config.base_url,
            "api_version": self.config.api_version or "2024-02-01",
            "timeout": self.config.timeout,
            "max_retries": 0,
        }
        return AsyncAzureOpenAI(**kwargs)


__all__ = ["AzureOracle"]
