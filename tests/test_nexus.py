"""Tests for genesis_pantheon.nexus module."""

from __future__ import annotations

from genesis_pantheon.ledger import BudgetLedger
from genesis_pantheon.nexus import Nexus


class TestNexus:
    def test_nexus_creates_default_blueprint(self) -> None:
        nexus = Nexus()
        bp = nexus.config
        assert bp is not None
        assert bp.llm is not None

    def test_nexus_budget_initialized(self) -> None:
        nexus = Nexus()
        budget = nexus.budget
        assert isinstance(budget, BudgetLedger)
        assert budget.total_cost == 0.0

    def test_nexus_budget_setter(self) -> None:
        nexus = Nexus()
        new_budget = BudgetLedger(max_budget=5.0)
        nexus.budget = new_budget
        assert nexus.budget.max_budget == 5.0

    def test_nexus_config_setter(self) -> None:
        from genesis_pantheon.blueprint import Blueprint

        nexus = Nexus()
        bp = Blueprint()
        bp.llm.api_key = "custom-key"
        nexus.config = bp
        assert nexus.config.llm.api_key == "custom-key"

    def test_nexus_oracle_created_from_config(
        self, nexus_fixture: Nexus
    ) -> None:
        oracle = nexus_fixture.oracle()
        assert oracle is not None

    def test_nexus_oracle_returns_same_instance(
        self, nexus_fixture: Nexus
    ) -> None:
        o1 = nexus_fixture.oracle()
        o2 = nexus_fixture.oracle()
        assert o1 is o2

    def test_nexus_serialize(self) -> None:
        nexus = Nexus()
        nexus.budget.record_usage("gpt-4-turbo", 100, 50)
        state = nexus.serialize()
        assert "budget" in state

    def test_nexus_deserialize(self) -> None:
        nexus = Nexus()
        nexus.budget.record_usage("gpt-4-turbo", 1000, 500)
        state = nexus.serialize()

        nexus2 = Nexus()
        nexus2.deserialize(state)
        assert nexus2.budget.total_prompt_tokens == 1000

    def test_nexus_kwargs_field(self) -> None:
        nexus = Nexus(kwargs={"project": "test"})
        assert nexus.kwargs["project"] == "test"
