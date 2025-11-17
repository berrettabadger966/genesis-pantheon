"""Mixin providing Nexus (context/config/oracle) access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from genesis_pantheon.blueprint import Blueprint
    from genesis_pantheon.nexus import Nexus
    from genesis_pantheon.oracles.base import BaseOracle


class NexusMixin(BaseModel):
    """Provides shared access to the global Nexus context.

    Any class that inherits from NexusMixin can get configuration,
    the current oracle, and budget tracking through a single
    shared Nexus instance.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _nexus: Nexus | None = PrivateAttr(default=None)
    _private_nexus: Nexus | None = PrivateAttr(default=None)

    @property
    def nexus(self) -> Nexus:
        """Return the active Nexus, falling back to a default.

        Returns:
            Active Nexus instance.
        """
        from genesis_pantheon.nexus import Nexus

        if self._nexus is not None:
            return self._nexus
        if self._private_nexus is not None:
            return self._private_nexus
        self._private_nexus = Nexus()
        return self._private_nexus

    @nexus.setter
    def nexus(self, value: Nexus) -> None:
        """Set the active Nexus context.

        Args:
            value: New Nexus instance to adopt.
        """
        self._nexus = value

    @property
    def config(self) -> Blueprint:
        """Convenience accessor for the Blueprint configuration.

        Returns:
            Blueprint from the active Nexus.
        """
        return self.nexus.config

    @property
    def oracle(self) -> BaseOracle:
        """Convenience accessor for the active LLM oracle.

        Returns:
            BaseOracle from the active Nexus.
        """
        return self.nexus.oracle()

    @oracle.setter
    def oracle(self, value: BaseOracle) -> None:
        """Replace the oracle on the active Nexus.

        Args:
            value: New BaseOracle instance.
        """
        self.nexus._oracle = value


__all__ = ["NexusMixin"]
