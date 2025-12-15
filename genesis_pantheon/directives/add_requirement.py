"""AddRequirement directive: publishes a new user requirement."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import Signal


class AddRequirement(Directive):
    """Publishes an additional requirement into the arena.

    This directive is used to inject follow-up requirements after
    the initial mission has already been launched.
    """

    name: str = "AddRequirement"

    async def run(  # type: ignore[override]
        self, requirement: str = ""
    ) -> Signal:
        """Wrap the requirement in a Signal.

        Args:
            requirement: Requirement text to publish.

        Returns:
            Signal ready for publishing.
        """
        return Signal(
            content=requirement,
            cause_by="UserDirective",
        )


__all__ = ["AddRequirement"]
