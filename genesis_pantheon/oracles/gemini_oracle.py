"""Google Gemini oracle adapter for GenesisPantheon."""

from __future__ import annotations

from typing import Any

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


@register_oracle(OracleApiType.GEMINI)
class GeminiOracle(BaseOracle):
    """Google Gemini API adapter."""

    def __init__(
        self,
        config: OracleConfig,
        system_prompt: str = "",
        budget: Any = None,
    ) -> None:
        super().__init__(config, system_prompt, budget)
        self._model = self._build_model()

    def _build_model(self) -> Any:
        """Configure and return the Gemini GenerativeModel.

        Returns:
            Configured GenerativeModel instance.
        """
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for GeminiOracle. "
                "Install: pip install google-generativeai"
            ) from exc
        if self.config.api_key:
            genai.configure(api_key=self.config.api_key)
        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        return genai.GenerativeModel(
            model_name=self.config.model,
            generation_config=generation_config,
            system_instruction=self.system_prompt or None,
        )

    def _build_gemini_parts(self, prompt: str) -> list[dict]:
        """Convert a prompt string to Gemini content parts.

        Args:
            prompt: User prompt text.

        Returns:
            List of content part dicts.
        """
        return [{"role": "user", "parts": [prompt]}]

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        """Send a prompt to the Gemini API.

        Args:
            prompt: User prompt.
            system_msgs: Additional context prepended to prompt.
            images: Optional image payloads (not yet supported).
            stream: Ignored; Gemini always returns full responses
                in the async API.

        Returns:
            Model response as a string.
        """
        full_prompt = prompt
        if system_msgs:
            full_prompt = "\n".join(system_msgs) + "\n\n" + prompt

        response = await self._model.generate_content_async(
            full_prompt
        )
        response_text = response.text or ""

        # Estimate tokens since Gemini may not return usage
        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(
                usage, "prompt_token_count", len(full_prompt) // 4
            )
            completion_tokens = getattr(
                usage,
                "candidates_token_count",
                len(response_text) // 4,
            )
        else:
            prompt_tokens = max(1, len(full_prompt) // 4)
            completion_tokens = max(1, len(response_text) // 4)

        self._track_usage(prompt_tokens, completion_tokens)
        logger.debug(
            f"[GeminiOracle] model={self.config.model} "
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


__all__ = ["GeminiOracle"]
