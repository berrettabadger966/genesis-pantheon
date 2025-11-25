"""Human-in-the-loop oracle adapter for GenesisPantheon."""

from __future__ import annotations

import asyncio
from typing import Any

from genesis_pantheon.configs.oracle_config import (
    OracleApiType,
)
from genesis_pantheon.logger import logger
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.oracles.registry import register_oracle


@register_oracle(OracleApiType.HUMAN)
class HumanOracle(BaseOracle):
    """Oracle that reads responses from standard input.

    Useful for testing and human-assisted scenarios where a real
    LLM is not available.
    """

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = False,
    ) -> str:
        """Print prompt to stdout and read a response from stdin.

        Args:
            prompt: Prompt to display to the human operator.
            system_msgs: Additional context (printed before prompt).
            images: Ignored for human oracle.
            stream: Ignored for human oracle.

        Returns:
            Text entered by the human operator.
        """
        if system_msgs:
            for msg in system_msgs:
                print(f"[SYSTEM] {msg}")
        print(f"\n[PROMPT]\n{prompt}\n")
        print("[Your response] >>> ", end="", flush=True)
        # Run blocking input in executor to keep async compat
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, input)
        logger.debug(
            f"[HumanOracle] received {len(response)} chars"
        )
        # No token cost for human responses
        return response

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        """Ask the human operator each prompt in sequence.

        Args:
            prompts: List of prompts to present.
            system_msgs: Shared system messages.

        Returns:
            Concatenated responses.
        """
        responses: list[str] = []
        for p in prompts:
            r = await self.ask(p, system_msgs=system_msgs)
            responses.append(r)
        return "\n".join(responses)


__all__ = ["HumanOracle"]
