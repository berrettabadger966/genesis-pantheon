"""OpenAI oracle adapter for GenesisPantheon."""

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


def _count_tokens(text: str, model: str = "gpt-4-turbo") -> int:
    """Count tokens for the given text using tiktoken.

    Falls back to a rough word-based estimate if tiktoken is
    unavailable or the encoding is not found.

    Args:
        text: Text to count tokens for.
        model: Model name to select the encoding.

    Returns:
        Estimated token count.
    """
    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return max(1, len(text.split()))


@register_oracle(OracleApiType.OPENAI)
class OpenAIOracle(BaseOracle):
    """OpenAI API adapter using ``openai.AsyncOpenAI``."""

    def __init__(
        self,
        config: OracleConfig,
        system_prompt: str = "",
        budget: Any = None,
    ) -> None:
        super().__init__(config, system_prompt, budget)
        self._client = self._build_client()

    def _build_client(self) -> Any:
        """Create and return the AsyncOpenAI client.

        Returns:
            AsyncOpenAI client instance.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required for OpenAIOracle. "
                "Install it with: pip install openai"
            ) from exc
        kwargs: dict = {
            "api_key": self.config.api_key or "sk-placeholder",
            "timeout": self.config.timeout,
            "max_retries": 0,  # tenacity handles retries
        }
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        if self.config.proxy:
            import httpx

            kwargs["http_client"] = httpx.AsyncClient(
                proxies=self.config.proxy
            )
        return AsyncOpenAI(**kwargs)

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
        """Send a prompt to the OpenAI API.

        Args:
            prompt: User prompt text.
            system_msgs: Additional system context strings.
            images: Optional image payloads (base64 or URL).
            stream: Whether to stream the response.

        Returns:
            Model response as a string.
        """
        messages = self._build_messages(prompt, system_msgs)

        if images:
            # Add images to the user message for vision models
            user_msg = messages[-1]
            content_parts: list[Any] = [
                {"type": "text", "text": user_msg["content"]}
            ]
            for img in images:
                if isinstance(img, str) and img.startswith("http"):
                    content_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": img},
                        }
                    )
                else:
                    content_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img}"
                            },
                        }
                    )
            messages[-1] = {
                "role": "user",
                "content": content_parts,
            }

        use_stream = stream and self.config.stream
        response_text = ""
        prompt_tokens = _count_tokens(prompt, self.config.model)
        completion_tokens = 0

        if use_stream:
            stream_resp = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **self.config.extra_kwargs,
            )
            async for chunk in stream_resp:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    response_text += delta.content
            completion_tokens = _count_tokens(
                response_text, self.config.model
            )
        else:
            resp = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=False,
                **self.config.extra_kwargs,
            )
            choice = resp.choices[0]
            response_text = choice.message.content or ""
            if resp.usage:
                prompt_tokens = resp.usage.prompt_tokens
                completion_tokens = resp.usage.completion_tokens

        self._track_usage(prompt_tokens, completion_tokens)
        logger.debug(
            f"[OpenAIOracle] model={self.config.model} "
            f"response_len={len(response_text)}"
        )
        return response_text

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        """Run multiple prompts sequentially and concatenate results.

        Args:
            prompts: List of prompt strings.
            system_msgs: Shared system messages.

        Returns:
            Concatenated responses separated by newlines.
        """
        responses: list[str] = []
        for p in prompts:
            r = await self.ask(p, system_msgs=system_msgs, stream=False)
            responses.append(r)
        return "\n".join(responses)


__all__ = ["OpenAIOracle"]
