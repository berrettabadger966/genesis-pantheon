"""UserDirective: Marks the initial user requirement signal."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import Signal


class UserDirective(Directive):
    """Sentinel directive that marks signals originating from a user.

    The ``cause_by`` field of all initial signals is automatically
    set to ``"UserDirective"`` by the Signal validator.
    """

    name: str = "UserDirective"

    async def run(  # type: ignore[override]
        self, requirement: str = ""
    ) -> Signal:
        """Wrap a requirement string in a Signal.

        Args:
            requirement: User's requirement text.

        Returns:
            Signal ready for publishing.
        """
        return Signal(
            content=requirement, cause_by="UserDirective"
        )


__all__ = ["UserDirective"]
