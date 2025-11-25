"""Ollama local LLM oracle adapter for GenesisPantheon."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from genesis_pantheon.configs.oracle_config import (
    OracleApiType,
    OracleConfig,
)
from genesis_pantheon.logger import logger
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.oracles.registry import register_oracle


@register_oracle(OracleApiType.OLLAMA)
class OllamaOracle(BaseOracle):
    """Ollama local LLM adapter using the /api/chat endpoint."""

    _DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        config: OracleConfig,
        system_prompt: str = "",
        budget: Any = None,
    ) -> None:
        super().__init__(config, system_prompt, budget)
        base = self.config.base_url or self._DEFAULT_BASE_URL
        self._base_url = base.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout
        )

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = False,
    ) -> str:
        """Send a prompt to the local Ollama instance.

        Args:
            prompt: User prompt.
            system_msgs: Additional system context.
            images: Optional image paths (not yet supported).
            stream: Ignored; always returns full response.

        Returns:
            Model response as a string.
        """
        messages = self._build_messages(prompt, system_msgs)
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        url = f"{self._base_url}/api/chat"
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        response_text = (
            data.get("message", {}).get("content", "")
        )
        # Ollama may return token counts in eval_count fields
        prompt_tokens = data.get(
            "prompt_eval_count", max(1, len(prompt) // 4)
        )
        completion_tokens = data.get(
            "eval_count", max(1, len(response_text) // 4)
        )
        self._track_usage(prompt_tokens, completion_tokens)
        logger.debug(
            f"[OllamaOracle] model={self.config.model} "
            f"response_len={len(response_text)}"
        )
        return response_text

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        """Send multiple prompts sequentially.

        Args:
            prompts: List of user prompts.
            system_msgs: Shared system messages.

        Returns:
            Concatenated responses.
        """
        responses: list[str] = []
        for p in prompts:
            r = await self.ask(p, system_msgs=system_msgs)
            responses.append(r)
        return "\n".join(responses)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


__all__ = ["OllamaOracle"]
