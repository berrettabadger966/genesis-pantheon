"""Abstract base class for LLM oracle adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from genesis_pantheon.configs.oracle_config import OracleConfig
from genesis_pantheon.ledger import BudgetLedger
from genesis_pantheon.logger import logger


class BaseOracle(ABC):
    """Abstract adapter between the framework and an LLM provider.

    Subclasses implement provider-specific API calls. All I/O is
    async to avoid blocking the event loop.
    """

    def __init__(
        self,
        config: OracleConfig,
        system_prompt: str = "",
        budget: BudgetLedger | None = None,
    ) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.budget = budget

    # ----------------------------------------------------------------
    # Abstract interface
    # ----------------------------------------------------------------

    @abstractmethod
    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        """Send a prompt to the LLM and return the response.

        Args:
            prompt: User-facing prompt string.
            system_msgs: Additional system context messages.
            images: Optional image payloads for vision models.
            stream: Whether to stream the response.

        Returns:
            LLM response as a string.
        """

    @abstractmethod
    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        """Send multiple prompts and return a combined response.

        Args:
            prompts: List of prompt strings to send sequentially.
            system_msgs: Shared system messages.

        Returns:
            Combined LLM response.
        """

    # ----------------------------------------------------------------
    # Concrete helpers
    # ----------------------------------------------------------------

    async def ask_code(self, prompts: list[str]) -> str:
        """Ask the oracle for code, joining multiple prompts.

        Args:
            prompts: Prompt strings to send.

        Returns:
            LLM response (expected to contain a code block).
        """
        combined = "\n\n".join(prompts)
        return await self.ask(combined, stream=False)

    def _build_messages(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Construct the messages list for the API call.

        Args:
            prompt: User prompt.
            system_msgs: Optional extra system messages.

        Returns:
            List of role/content message dicts.
        """
        messages: list[dict[str, str]] = []
        sys_content_parts = []
        if self.system_prompt:
            sys_content_parts.append(self.system_prompt)
        if system_msgs:
            sys_content_parts.extend(system_msgs)
        if sys_content_parts:
            messages.append(
                {
                    "role": "system",
                    "content": "\n".join(sys_content_parts),
                }
            )
        messages.append({"role": "user", "content": prompt})
        return messages

    def _track_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Record token usage in the attached BudgetLedger.

        Args:
            prompt_tokens: Number of prompt tokens used.
            completion_tokens: Number of completion tokens produced.
        """
        if self.budget is not None:
            self.budget.record_usage(
                self.config.model,
                prompt_tokens,
                completion_tokens,
            )
        logger.debug(
            f"[{self.__class__.__name__}] "
            f"prompt={prompt_tokens} "
            f"completion={completion_tokens}"
        )


__all__ = ["BaseOracle"]
