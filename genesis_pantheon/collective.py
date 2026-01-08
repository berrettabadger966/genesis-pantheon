"""Collective: orchestrates multiple personas toward a shared goal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from genesis_pantheon.arena.base import Arena
from genesis_pantheon.logger import logger
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.schema import Signal
from genesis_pantheon.utils.common import serialize_decorator
from genesis_pantheon.utils.exceptions import BudgetExceededError


class Collective(BaseModel):
    """Orchestrates multiple personas toward a shared mission.

    A Collective wraps an Arena and provides high-level controls:
    recruiting personas, setting budgets, launching missions, and
    running the full execution loop.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    arena: Arena | None = None
    budget: float = Field(default=10.0)
    mission: str = Field(default="")

    def __init__(
        self,
        context: Nexus | None = None,
        **data: Any,
    ) -> None:
        super().__init__(**data)
        ctx = context or Nexus()
        if self.arena is None:
            self.arena = Arena(context=ctx)
        else:
            self.arena.context = ctx
        # Recruit personas passed at construction time
        if "personas" in data:
            self.recruit(data["personas"])

    def recruit(self, personas: list[Any]) -> None:
        """Add personas to the collective's arena.

        Args:
            personas: List of Persona instances to register.
        """
        if self.arena:
            self.arena.add_personas(personas)

    def allocate_budget(self, amount: float) -> None:
        """Set the maximum spend for this collective run.

        Args:
            amount: Maximum budget in USD.
        """
        self.budget = amount
        if self.arena:
            self.arena.context.budget.max_budget = amount
        logger.info(f"[Collective] Budget set to ${amount:.2f}")

    def launch_mission(
        self, mission: str, send_to: str = ""
    ) -> None:
        """Publish a UserDirective signal to start the workflow.

        Args:
            mission: Mission description / user requirement.
            send_to: Optional specific persona name to address.
        """
        self.mission = mission
        signal = Signal(
            content=mission,
            cause_by="UserDirective",
            send_to={send_to} if send_to else {"<all>"},
        )
        if self.arena:
            self.arena.publish_signal(signal)
        logger.info(f"[Collective] Mission launched: {mission[:80]}")

    def _verify_budget(self) -> None:
        """Raise BudgetExceededError when the budget is exhausted.

        Raises:
            BudgetExceededError: When total cost >= max budget.
        """
        if self.arena is None:
            return
        budget = self.arena.context.budget
        if budget.is_budget_exceeded():
            raise BudgetExceededError(
                budget.total_cost,
                f"Budget exceeded: spent ${budget.total_cost:.4f} "
                f"of ${budget.max_budget:.2f}",
            )

    @serialize_decorator
    async def run(
        self,
        n_rounds: int = 3,
        mission: str = "",
        send_to: str = "",
        auto_archive: bool = True,
    ) -> list[Signal]:
        """Run the collective until the mission is complete or budget exhausted.

        Args:
            n_rounds: Maximum number of execution rounds.
            mission: If provided, launches this mission before running.
            send_to: Optional persona name to address the mission to.
            auto_archive: Whether to archive the arena after the run.

        Returns:
            Full list of signals produced during the run.
        """
        if mission:
            self.launch_mission(mission=mission, send_to=send_to)

        while n_rounds > 0:
            if self.arena is None or self.arena.is_idle:
                logger.debug(
                    "[Collective] All personas are idle. Stopping."
                )
                break
            n_rounds -= 1
            self._verify_budget()
            await self.arena.run()
            logger.debug(f"[Collective] Rounds remaining: {n_rounds}")

        if self.arena:
            self.arena.archive(auto_archive)
            return self.arena.history
        return []

    def serialize(self, path: Path | None = None) -> None:
        """Persist collective state to JSON.

        Args:
            path: Destination file path. Defaults to
                ``~/.genesis_pantheon/collective_state.json``.
        """
        dest = path or (
            Path.home()
            / ".genesis_pantheon"
            / "collective_state.json"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "mission": self.mission,
            "budget": self.budget,
            "context": (
                self.arena.context.serialize()
                if self.arena
                else {}
            ),
        }
        with open(str(dest), "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        logger.debug(f"[Collective] State saved to {dest}")

    @classmethod
    def deserialize(
        cls,
        path: Path,
        context: Nexus | None = None,
    ) -> Collective:
        """Restore a Collective from a previously serialised state.

        Args:
            path: Path to the state JSON file.
            context: Optional Nexus to use (loaded from state if
                not provided).

        Returns:
            Restored Collective instance.
        """
        with open(str(path), encoding="utf-8") as fh:
            data = json.load(fh)
        ctx = context or Nexus()
        if "context" in data:
            ctx.deserialize(data["context"])
        collective = cls(context=ctx)
        collective.mission = data.get("mission", "")
        collective.budget = data.get("budget", 10.0)
        return collective

    @property
    def budget_ledger(self):
        """Convenience accessor for the budget ledger.

        Returns:
            BudgetLedger from the arena's context.
        """
        if self.arena:
            return self.arena.context.budget
        from genesis_pantheon.ledger import BudgetLedger

        return BudgetLedger()


__all__ = ["Collective"]
