"""Tests for the Collective orchestrator."""

from __future__ import annotations

import pytest

from genesis_pantheon.collective import Collective
from genesis_pantheon.directives.base import Directive, DirectiveOutput
from genesis_pantheon.ledger import BudgetLedger
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.personas.persona import Persona, PersonaReactMode
from genesis_pantheon.utils.exceptions import BudgetExceededError
from tests.conftest import MockOracle


class FastDirective(Directive):
    """Directive that completes instantly."""

    name: str = "FastDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        return DirectiveOutput(content="fast done")


class FastPersona(Persona):
    name: str = "FastBot"
    profile: str = "Fast Agent"
    goal: str = "Finish quickly"
    constraints: str = ""


def _make_nexus() -> Nexus:
    nexus = Nexus()
    nexus._oracle = MockOracle(responses=["ok"])
    return nexus


class TestCollective:
    def test_creates_default_arena(self) -> None:
        c = Collective()
        assert c.arena is not None

    def test_recruit_adds_personas_to_arena(self) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        p = FastPersona()
        c.recruit([p])
        assert "FastBot" in c.arena.personas

    def test_allocate_budget_sets_max(self) -> None:
        c = Collective()
        c.allocate_budget(25.0)
        assert c.budget == 25.0
        assert c.arena.context.budget.max_budget == 25.0

    def test_launch_mission_publishes_signal(self) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        p = FastPersona()
        c.recruit([p])
        c.launch_mission("Build a calculator")
        assert c.mission == "Build a calculator"
        # The signal should be in the persona's buffer
        items = p.ctx.signal_buffer.pop_all()
        assert len(items) == 1
        assert items[0].content == "Build a calculator"

    def test_launch_mission_to_specific_persona(self) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        p1 = FastPersona(name="Target")
        p2 = FastPersona(name="Other")
        c.recruit([p1, p2])
        c.launch_mission("targeted task", send_to="Target")
        target_items = p1.ctx.signal_buffer.pop_all()
        other_items = p2.ctx.signal_buffer.pop_all()
        assert len(target_items) == 1
        assert len(other_items) == 0

    def test_verify_budget_raises_when_exceeded(self) -> None:
        c = Collective()
        c.allocate_budget(0.001)
        # Force the total cost to exceed budget
        c.arena.context.budget.total_cost = 1.0
        with pytest.raises(BudgetExceededError):
            c._verify_budget()

    def test_verify_budget_does_not_raise_within_budget(self) -> None:
        c = Collective()
        c.allocate_budget(100.0)
        c._verify_budget()  # should not raise

    async def test_run_stops_when_idle(self) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        # No personas, always idle
        result = await c.run(n_rounds=5, mission="test")
        assert isinstance(result, list)

    async def test_run_stops_when_budget_exceeded(self) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        p = FastPersona()
        p.nexus = nexus
        p._assign_directives([FastDirective])
        p._subscribe_to([FastDirective])
        c.recruit([p])

        c.allocate_budget(0.0)  # zero budget
        c.arena.context.budget.total_cost = 1.0  # already exceeded

        with pytest.raises(BudgetExceededError):
            await c.run(n_rounds=5, mission="Build something")

    async def test_run_returns_signal_list(self) -> None:
        c = Collective()
        result = await c.run(n_rounds=1, mission="simple task")
        assert isinstance(result, list)

    def test_budget_ledger_property(self) -> None:
        c = Collective()
        ledger = c.budget_ledger
        assert isinstance(ledger, BudgetLedger)

    def test_serialize_and_deserialize(self, tmp_path) -> None:
        c = Collective()
        c.mission = "Test mission"
        c.budget = 42.0
        state_file = tmp_path / "state.json"
        c.serialize(path=state_file)
        assert state_file.exists()

        c2 = Collective.deserialize(state_file)
        assert c2.mission == "Test mission"
        assert c2.budget == 42.0

    def test_serialize_creates_parent_dirs(self, tmp_path) -> None:
        c = Collective()
        nested = tmp_path / "nested" / "deep" / "state.json"
        c.serialize(path=nested)
        assert nested.exists()

    async def test_run_with_active_persona_completes_one_round(
        self,
    ) -> None:
        nexus = _make_nexus()
        c = Collective(context=nexus)
        p = FastPersona()
        nexus2 = _make_nexus()
        p.nexus = nexus2
        p._assign_directives([FastDirective])
        p._subscribe_to(["UserDirective"])
        p.ctx.react_mode = PersonaReactMode.REACT
        p.ctx.max_react_cycles = 1
        c.recruit([p])

        result = await c.run(
            n_rounds=2, mission="go"
        )
        assert isinstance(result, list)
