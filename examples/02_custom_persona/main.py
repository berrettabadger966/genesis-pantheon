"""Custom Persona — define a Directive and Persona from scratch.

Demonstrates:
- Subclassing Directive with custom run() logic
- Subclassing Persona and wiring directives in __init__
- Running the persona on a long text signal

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
# Mock oracle
# ---------------------------------------------------------------------------

LONG_TEXT = (
    "Artificial intelligence (AI) is intelligence demonstrated by "
    "machines, as opposed to natural intelligence displayed by "
    "animals including humans. AI research has been defined as the "
    "field of study of intelligent agents, which refers to any "
    "system that perceives its environment and takes actions that "
    "maximise its chance of achieving its goals. The term "
    "artificial intelligence had previously been used to describe "
    "machines that mimic and display human cognitive skills "
    "associated with the human mind."
)


class MockOracle(BaseOracle):
    """Returns a canned three-bullet summary."""

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        return (
            "• AI refers to intelligence demonstrated by machines.\n"
            "• The field studies intelligent agents that maximise "
            "goal-achievement.\n"
            "• Historically the term covered machines mimicking "
            "human cognitive skills."
        )

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        return await self.ask(prompts[0] if prompts else "")


# ---------------------------------------------------------------------------
# Custom directive
# ---------------------------------------------------------------------------


class SummariserDirective(Directive):
    """Summarise incoming text into three bullet points."""

    name: str = "SummariserDirective"
    desc: str = "Condense any text to exactly three bullet points"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        text = str(context) if context else ""
        prompt = (
            "Summarise the following text into exactly 3 bullet "
            f"points. Be concise.\n\nText:\n{text}"
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


# ---------------------------------------------------------------------------
# Custom persona
# ---------------------------------------------------------------------------


class SummariserPersona(Persona):
    """A persona specialised in text summarisation."""

    name: str = "Summariser"
    profile: str = "Text Summarisation Expert"
    goal: str = "Produce concise three-bullet summaries of any text"
    constraints: str = (
        "Always produce exactly 3 bullet points; "
        "each bullet must be one sentence"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives([SummariserDirective])
        self._subscribe_to([UserDirective])
        self.ctx.react_mode = PersonaReactMode.BY_ORDER


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    nexus = Nexus()
    nexus._oracle = MockOracle(config=OracleConfig(api_key="fake"))

    summariser = SummariserPersona()
    summariser.nexus = nexus
    # Propagate nexus to directives created before nexus was assigned
    for directive in summariser.directives:
        directive.nexus = nexus

    signal = Signal(content=LONG_TEXT, cause_by="UserDirective")
    result = await summariser.run(signal)

    print("=== Summary ===")
    if result:
        print(result.content)
    else:
        print("No output produced.")


if __name__ == "__main__":
    asyncio.run(main())
