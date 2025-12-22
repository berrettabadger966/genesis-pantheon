"""CodeCrafter persona: software implementation agent."""

from __future__ import annotations

from typing import Any

from genesis_pantheon.directives.allocate_tasks import AllocateTasks
from genesis_pantheon.directives.condense_code import CondenseCode
from genesis_pantheon.directives.craft_code import CraftCode
from genesis_pantheon.directives.design_system import DesignSystem
from genesis_pantheon.directives.review_code import ReviewCode
from genesis_pantheon.logger import logger
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.schema import Signal


class CodeCrafter(Persona):
    """Code Crafter (software engineer) persona.

    Subscribes to AllocateTasks signals and generates Python code
    files using CraftCode.  Optionally performs self-review via
    ReviewCode.

    Attributes:
        n_crafters: Number of parallel coding tasks (currently
            sequential; kept for API compatibility).
        code_review: Whether to self-review generated code.
        use_code_review: Alias for code_review.
    """

    name: str = "Charlie"
    profile: str = "Code Crafter"
    goal: str = (
        "Write clean, efficient, and well-tested Python code "
        "that satisfies the design requirements"
    )
    constraints: str = (
        "Follow PEP 8; write complete implementations "
        "(no stubs or TODOs); include docstrings and type hints"
    )
    n_crafters: int = 1
    code_review: bool = False
    use_code_review: bool = False

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        directives = [CraftCode]
        if self.code_review or self.use_code_review:
            directives.append(ReviewCode)
        directives.append(CondenseCode)
        self._assign_directives(directives)
        self._subscribe_to([AllocateTasks, DesignSystem])

    async def run(
        self, signal: Signal | None = None
    ) -> Signal | None:
        """Run the code crafting cycle.

        Args:
            signal: Optional signal to start from.

        Returns:
            Result Signal or None.
        """
        result = await super().run(signal)
        if result:
            logger.info(
                f"[{self.name}] Generated code "
                f"({len(result.content)} chars)"
            )
        return result


__all__ = ["CodeCrafter"]
