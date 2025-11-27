"""Anthropic Claude oracle adapter for GenesisPantheon."""

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


@register_oracle(OracleApiType.ANTHROPIC)
class AnthropicOracle(BaseOracle):
    """Anthropic Claude API adapter."""

    def __init__(
        self,
        config: OracleConfig,
        system_prompt: str = "",
        budget: Any = None,
    ) -> None:
        super().__init__(config, system_prompt, budget)
        self._client = self._build_client()

    def _build_client(self) -> Any:
        """Create and return the AsyncAnthropic client.

        Returns:
            AsyncAnthropic client instance.
        """
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic package is required. "
                "Install it with: pip install anthropic"
            ) from exc
        kwargs: dict = {
            "api_key": self.config.api_key or "placeholder",
            "timeout": float(self.config.timeout),
            "max_retries": 0,
        }
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        return anthropic.AsyncAnthropic(**kwargs)

    def _build_anthropic_messages(
        self,
        prompt: str,
    ) -> tuple:
        """Separate system content from user messages.

        Args:
            prompt: User prompt string.

        Returns:
            Tuple of (system_str, messages_list).
        """
        system_parts = []
        if self.system_prompt:
            system_parts.append(self.system_prompt)
        messages = [{"role": "user", "content": prompt}]
        return "\n".join(system_parts), messages

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
        """Send a prompt to the Anthropic API.

        Args:
            prompt: User prompt.
            system_msgs: Additional system context.
            images: Optional image payloads (not yet supported).
            stream: Whether to stream the response.

        Returns:
            Model response as a string.
        """
        system_parts = []
        if self.system_prompt:
            system_parts.append(self.system_prompt)
        if system_msgs:
            system_parts.extend(system_msgs)
        system_str = "\n".join(system_parts)

        messages = [{"role": "user", "content": prompt}]

        kwargs: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": messages,
        }
        if system_str:
            kwargs["system"] = system_str

        response_text = ""
        if stream and self.config.stream:
            async with self._client.messages.stream(
                **kwargs
            ) as stream_ctx:
                async for text in stream_ctx.text_stream:
                    response_text += text
            final = await stream_ctx.get_final_message()
            prompt_tokens = final.usage.input_tokens
            completion_tokens = final.usage.output_tokens
        else:
            resp = await self._client.messages.create(**kwargs)
            response_text = resp.content[0].text
            prompt_tokens = resp.usage.input_tokens
            completion_tokens = resp.usage.output_tokens

        self._track_usage(prompt_tokens, completion_tokens)
        logger.debug(
            f"[AnthropicOracle] model={self.config.model} "
            f"response_len={len(response_text)}"
        )
        return response_text

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        """Send multiple prompts and concatenate results.

        Args:
            prompts: List of user prompts.
            system_msgs: Shared system messages.

        Returns:
            Concatenated responses.
        """
        responses: list[str] = []
        for p in prompts:
            r = await self.ask(p, system_msgs=system_msgs, stream=False)
            responses.append(r)
        return "\n".join(responses)


__all__ = ["AnthropicOracle"]
