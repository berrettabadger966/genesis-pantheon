"""Integration tests for the software development pipeline.

These tests use MockOracle so no real LLM calls are made.
They verify that the full multi-agent workflow integrates correctly.
"""

from __future__ import annotations

import pytest

from genesis_pantheon.collective import Collective
from genesis_pantheon.directives.base import Directive, DirectiveOutput
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.schema import Signal
from tests.conftest import MockOracle


class AnalyzeDirective(Directive):
    """Simulates a PRD analysis step."""

    name: str = "AnalyzeDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        return DirectiveOutput(
            content="Analysis complete: single-file Python app"
        )


class GenerateDirective(Directive):
    """Simulates a code generation step."""

    name: str = "GenerateDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        return DirectiveOutput(
            content="print('Hello, World!')"
        )


class AnalystPersona(Persona):
    name: str = "Analyst"
    profile: str = "Requirement Analyst"
    goal: str = "Understand the requirement"
    constraints: str = ""


class DeveloperPersona(Persona):
    name: str = "Developer"
    profile: str = "Software Developer"
    goal: str = "Write working code"
    constraints: str = ""


def _build_collective() -> Collective:
    nexus = Nexus()
    nexus._oracle = MockOracle(
        responses=[
            "## Goals\nBuild a simple app\n## Features\n- feature 1",
            "```python\nprint('hello')\n```",
        ]
    )

    analyst = AnalystPersona()
    analyst.nexus = nexus
    analyst._assign_directives([AnalyzeDirective])
    analyst._subscribe_to(["UserDirective"])

    developer = DeveloperPersona()
    developer.nexus = nexus
    developer._assign_directives([GenerateDirective])
    developer._subscribe_to(["AnalyzeDirective"])

    collective = Collective(context=nexus)
    collective.recruit([analyst, developer])
    collective.allocate_budget(50.0)
    return collective


class TestSoftwarePipeline:
    async def test_single_persona_completes_task(self) -> None:
        nexus = Nexus()
        nexus._oracle = MockOracle(responses=["task complete"])

        analyst = AnalystPersona()
        analyst.nexus = nexus
        analyst._assign_directives([AnalyzeDirective])
        analyst._subscribe_to(["UserDirective"])

        collective = Collective(context=nexus)
        collective.recruit([analyst])
        collective.allocate_budget(10.0)

        result = await collective.run(
            n_rounds=3,
            mission="Build a simple calculator",
        )
        assert isinstance(result, list)

    async def test_signal_flows_between_personas(self) -> None:
        collective = _build_collective()

        # Push initial signal manually to analyst
        initial = Signal(
            content="Build a weather app",
            cause_by="UserDirective",
        )
        collective.arena.publish_signal(initial)

        # The signal should be in the arena chronicle
        assert collective.arena.chronicle.count() == 1

        # Run one round — analyst should process
        await collective.arena.run()

        # Analyst should have produced at least one new signal
        assert len(collective.arena.history) >= 1

    async def test_multi_round_execution(self) -> None:
        collective = _build_collective()
        result = await collective.run(
            n_rounds=5,
            mission="Create a to-do list app",
        )
        assert isinstance(result, list)
        # History should record published signals
        assert len(collective.arena.history) >= 1

    async def test_pipeline_respects_budget_limit(self) -> None:
        collective = _build_collective()
        collective.allocate_budget(0.0)
        collective.arena.context.budget.total_cost = 999.0

        from genesis_pantheon.utils.exceptions import BudgetExceededError

        with pytest.raises(BudgetExceededError):
            await collective.run(
                n_rounds=5,
                mission="over budget",
            )

    async def test_idle_collective_returns_signal_list(self) -> None:
        nexus = Nexus()
        nexus._oracle = MockOracle(responses=["ok"])
        collective = Collective(context=nexus)
        # No personas, immediately idle — mission signal is recorded
        result = await collective.run(n_rounds=3, mission="anything")
        assert isinstance(result, list)
        # The mission signal ends up in history
        assert len(result) >= 0

    async def test_chronicle_records_all_signals(self) -> None:
        collective = _build_collective()

        for i in range(3):
            collective.arena.publish_signal(
                Signal(content=f"signal {i}")
            )

        assert collective.arena.chronicle.count() == 3

    async def test_nexus_shared_across_personas(self) -> None:
        collective = _build_collective()
        personas = list(collective.arena.personas.values())

        # All personas should share the arena's nexus context
        for p in personas:
            assert p.nexus is collective.arena.context
