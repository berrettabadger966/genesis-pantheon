"""Code Review — CodeCrafter with code_review=True.

Demonstrates:
- Using the built-in CodeCrafter persona
- Enabling the self-review directive (code_review=True)
- Injecting a mock oracle that returns canned code and review feedback
- Processing an AllocateTasks signal (CodeCrafter's subscription)

Run with: python main.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from genesis_pantheon.configs.oracle_config import OracleConfig
from genesis_pantheon.directives.allocate_tasks import AllocateTasks
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.personas.code_crafter import CodeCrafter
from genesis_pantheon.schema import Signal

# ---------------------------------------------------------------------------
# Mock oracle with code-aware responses
# ---------------------------------------------------------------------------

CANNED_CODE = '''
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Return the difference of two integers."""
    return a - b
'''.strip()

CANNED_REVIEW = (
    "Code review passed.\n"
    "- Type hints present on all functions.\n"
    "- Docstrings are clear and concise.\n"
    "- No logic errors detected.\n"
    "- Suggestion: add edge-case handling for very large integers."
)

CANNED_CONDENSE = (
    "Module contains two arithmetic functions: `add` and `subtract`. "
    "Both are fully typed and documented."
)


class CodeReviewOracle(BaseOracle):
    """Returns deterministic code, review, and condense responses."""

    _call_count: int = 0

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        self._call_count += 1
        p = prompt.lower()
        if "review" in p or "improve" in p:
            return CANNED_REVIEW
        if "summarise" in p or "condense" in p or "summary" in p:
            return CANNED_CONDENSE
        # Default: return code
        return CANNED_CODE

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        return await self.ask(prompts[0] if prompts else "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    # Set up nexus with mock oracle
    nexus = Nexus()
    nexus._oracle = CodeReviewOracle(config=OracleConfig(api_key="fake"))

    # CodeCrafter with self-review enabled
    crafter = CodeCrafter(code_review=True)
    crafter.nexus = nexus
    # Propagate nexus to directives created before nexus was assigned
    for directive in crafter.directives:
        directive.nexus = nexus

    print(f"Directives: {[d.name for d in crafter.directives]}")
    print()

    # AllocateTasks signal (what CodeCrafter subscribes to)
    task_signal = Signal(
        content=(
            "Implement a Python module `arithmetic.py` with two "
            "functions: `add(a, b)` and `subtract(a, b)`. "
            "Both should be fully typed and documented."
        ),
        cause_by=AllocateTasks.__name__,
    )

    result = await crafter.run(task_signal)

    print("=== CodeCrafter Output ===")
    if result:
        print(result.content)
    else:
        print("No output produced.")


if __name__ == "__main__":
    asyncio.run(main())
