"""Hello World — minimal GenesisPantheon example.

Demonstrates:
- Creating a Nexus and injecting a mock oracle
- Defining a single Persona with a custom directive
- Running the persona with a Signal and printing the result

Run with: python main.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from genesis_pantheon.configs.oracle_config import OracleConfig
from genesis_pantheon.directives.base import Directive
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.personas.persona import Persona, PersonaReactMode
from genesis_pantheon.schema import DirectiveOutput, Signal

# ---------------------------------------------------------------------------
# Minimal echo oracle — no API key required
# ---------------------------------------------------------------------------


class EchoOracle(BaseOracle):
    """Returns the last user message with an 'Echo:' prefix."""

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        return f"Echo: {prompt}"

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        return "\n".join(f"Echo: {p}" for p in prompts)


# ---------------------------------------------------------------------------
# Custom directive
# ---------------------------------------------------------------------------


class GreetDirective(Directive):
    """Greets whoever is named in the incoming signal."""

    name: str = "GreetDirective"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        reply = await self._ask(f"Say a warm greeting to: {context}")
        return DirectiveOutput(content=reply)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    # 1. Create a Nexus and inject the mock oracle
    nexus = Nexus()
    nexus._oracle = EchoOracle(config=OracleConfig(api_key="fake"))

    # 2. Create and configure the persona
    agent = Persona(
        name="Greeter",
        profile="Friendly greeter",
        goal="Welcome every user warmly",
        constraints="Be concise and positive",
    )
    agent.nexus = nexus
    agent._assign_directives([GreetDirective])
    agent._subscribe_to([UserDirective])
    agent.ctx.react_mode = PersonaReactMode.BY_ORDER

    # 3. Create a signal and run
    signal = Signal(
        content="Hello, GenesisPantheon!",
        cause_by="UserDirective",
    )
    result = await agent.run(signal)

    if result:
        print(f"Agent response: {result.content}")
    else:
        print("No response produced.")


if __name__ == "__main__":
    asyncio.run(main())
