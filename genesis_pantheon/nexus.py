"""Global context (Nexus) for configuration and oracle access."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from genesis_pantheon.ledger import BudgetLedger

if TYPE_CHECKING:
    from genesis_pantheon.blueprint import Blueprint
    from genesis_pantheon.configs.oracle_config import OracleConfig
    from genesis_pantheon.oracles.base import BaseOracle


class Nexus(BaseModel):
    """Global dependency-injection context.

    Holds the active Blueprint configuration, the LLM oracle
    instance, and the budget ledger.  A single Nexus is typically
    shared across all components of a Collective run.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _config: Blueprint | None = PrivateAttr(default=None)
    _oracle: BaseOracle | None = PrivateAttr(default=None)
    _budget: BudgetLedger | None = PrivateAttr(default=None)
    kwargs: dict[str, Any] = Field(default_factory=dict)

    # ----------------------------------------------------------------
    # Config
    # ----------------------------------------------------------------

    @property
    def config(self) -> Blueprint:
        """Return the active Blueprint, creating a default if needed.

        Returns:
            Active Blueprint instance.
        """
        if self._config is None:
            from genesis_pantheon.blueprint import Blueprint

            self._config = Blueprint.from_home()
        return self._config

    @config.setter
    def config(self, value: Blueprint) -> None:
        """Replace the current Blueprint.

        Args:
            value: New Blueprint instance.
        """
        self._config = value

    # ----------------------------------------------------------------
    # Budget
    # ----------------------------------------------------------------

    @property
    def budget(self) -> BudgetLedger:
        """Return the active BudgetLedger, creating one if needed.

        Returns:
            Active BudgetLedger.
        """
        if self._budget is None:
            self._budget = BudgetLedger()
        return self._budget

    @budget.setter
    def budget(self, value: BudgetLedger) -> None:
        """Replace the current BudgetLedger.

        Args:
            value: New BudgetLedger.
        """
        self._budget = value

    # ----------------------------------------------------------------
    # Oracle
    # ----------------------------------------------------------------

    def oracle(
        self,
        oracle_config: OracleConfig | None = None,
    ) -> BaseOracle:
        """Return the active oracle, creating one from config if needed.

        Args:
            oracle_config: Optional OracleConfig to use instead of the
                default config.

        Returns:
            Active BaseOracle instance.
        """
        if self._oracle is None or oracle_config is not None:
            from genesis_pantheon.oracles.registry import (
                create_oracle_instance,
            )

            cfg = oracle_config or self.config.llm
            instance = create_oracle_instance(cfg)
            instance.budget = self.budget
            if oracle_config is not None:
                return instance
            self._oracle = instance
        return self._oracle

    # ----------------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------------

    def serialize(self) -> dict[str, Any]:
        """Return a plain-dict representation of the nexus state.

        Returns:
            Serialized nexus data.
        """
        return {
            "config": (
                self._config.model_dump(mode="json")
                if self._config
                else {}
            ),
            "budget": (
                self.budget.model_dump() if self._budget else {}
            ),
            "kwargs": self.kwargs,
        }

    def deserialize(self, data: dict[str, Any]) -> None:
        """Restore nexus state from a serialized dict.

        Args:
            data: Dict produced by :meth:`serialize`.
        """
        from genesis_pantheon.blueprint import Blueprint

        if "config" in data and data["config"]:
            self._config = Blueprint(**data["config"])
        if "budget" in data and data["budget"]:
            self._budget = BudgetLedger(**data["budget"])
        self.kwargs = data.get("kwargs", {})


__all__ = ["Nexus"]
