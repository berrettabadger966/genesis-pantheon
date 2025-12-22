"""QualityGuardian persona: QA and testing agent."""

from __future__ import annotations

from typing import Any

from genesis_pantheon.directives.condense_code import CondenseCode
from genesis_pantheon.directives.craft_code import CraftCode
from genesis_pantheon.directives.diagnose_error import DiagnoseError
from genesis_pantheon.directives.execute_code import ExecuteCode
from genesis_pantheon.directives.generate_tests import GenerateTests
from genesis_pantheon.logger import logger
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.schema import Signal


class QualityGuardian(Persona):
    """Quality Guardian (QA engineer) persona.

    Subscribes to CraftCode signals and writes and executes tests.
    If tests fail, calls DiagnoseError and attempts to fix the code.
    """

    name: str = "Diana"
    profile: str = "Quality Guardian"
    goal: str = (
        "Ensure the software is correct, reliable, and meets "
        "all specified requirements through rigorous testing"
    )
    constraints: str = (
        "Write comprehensive tests; fail fast on critical bugs; "
        "document all defects clearly"
    )
    test_rounds: int = 3

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives(
            [GenerateTests, ExecuteCode, DiagnoseError]
        )
        self._subscribe_to([CraftCode, CondenseCode])

    async def run(
        self, signal: Signal | None = None
    ) -> Signal | None:
        """Run the QA cycle: generate, execute, diagnose.

        Args:
            signal: Optional signal to start from.

        Returns:
            Result Signal or None.
        """
        result = await super().run(signal)
        if result:
            logger.info(
                f"[{self.name}] QA complete "
                f"({len(result.content)} chars)"
            )
        return result


__all__ = ["QualityGuardian"]
