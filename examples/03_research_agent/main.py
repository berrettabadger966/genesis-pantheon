"""Research Agent — two-persona pipeline using the Arena.

Demonstrates:
- InsightHunter persona publishing a research signal
- A custom Synthesiser persona subscribing to that signal
- Arena-based signal routing between personas
- Mock oracle for offline testing

Run with: python main.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from genesis_pantheon.arena.base import Arena
from genesis_pantheon.configs.oracle_config import OracleConfig
from genesis_pantheon.directives.base import Directive
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.personas.insight_hunter import (
    InsightHunter,
    ResearchDirective,
)
from genesis_pantheon.personas.persona import Persona, PersonaReactMode
from genesis_pantheon.schema import DirectiveOutput, Signal

# ---------------------------------------------------------------------------
# Mock oracle
# ---------------------------------------------------------------------------


class MockOracle(BaseOracle):
    """Deterministic responses for offline demos."""

    _call_count: int = 0

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        self._call_count += 1
        if "research" in prompt.lower() or "findings" in prompt.lower():
            return (
                "## Research Report: Python Async\n\n"
                "**Summary:** asyncio is Python's built-in async "
                "framework.\n\n"
                "**Key Findings:**\n"
                "1. async/await syntax introduced in Python 3.5\n"
                "2. Event loop drives coroutine execution\n"
                "3. aiohttp and httpx for async HTTP\n\n"
                "**Conclusion:** Async Python is production-ready."
            )
        return (
            "**Executive Synthesis:**\n"
            "Python's asyncio enables high-throughput I/O-bound "
            "applications. Adoption is growing rapidly across the "
            "web services ecosystem.\n\n"
            "**Recommendation:** Adopt async patterns for all new "
            "network-facing services."
        )

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        return await self.ask(prompts[0] if prompts else "")


# ---------------------------------------------------------------------------
# Synthesiser directive and persona
# ---------------------------------------------------------------------------


class SynthesiseDirective(Directive):
    """Turn a research report into an executive synthesis."""

    name: str = "SynthesiseDirective"
    desc: str = "Synthesise research findings into an executive summary"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        prompt = (
            "You are an executive analyst. Given the following research "
            "findings, produce a concise executive synthesis with a clear "
            "recommendation.\n\n"
            f"Research:\n{context}"
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


class Synthesiser(Persona):
    """Synthesises research reports into executive summaries."""

    name: str = "Synthesiser"
    profile: str = "Executive Analyst"
    goal: str = "Distil research into clear executive summaries"
    constraints: str = (
        "Be concise; always end with a concrete recommendation"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives([SynthesiseDirective])
        # Subscribe to signals produced by InsightHunter
        self._subscribe_to([ResearchDirective])
        self.ctx.react_mode = PersonaReactMode.BY_ORDER


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    # Shared nexus with mock oracle
    nexus = Nexus()
    nexus._oracle = MockOracle(config=OracleConfig(api_key="fake"))

    # Build personas
    hunter = InsightHunter()
    synthesiser = Synthesiser()

    # Wire into an Arena
    arena = Arena(context=nexus)
    arena.add_personas([hunter, synthesiser])

    # Kick off with a UserDirective signal
    start_signal = Signal(
        content="Research Python async patterns and best practices",
        cause_by="UserDirective",
    )
    arena.publish_signal(start_signal)

    print("=== Round 1: InsightHunter researches ===")
    round1 = await arena.run()
    for s in round1:
        print(f"[{s.sent_from}] {s.content[:200]}\n")

    print("=== Round 2: Synthesiser synthesises ===")
    round2 = await arena.run()
    for s in round2:
        print(f"[{s.sent_from}] {s.content[:200]}\n")

    print(f"Total signals in chronicle: {len(arena.history)}")


if __name__ == "__main__":
    asyncio.run(main())
