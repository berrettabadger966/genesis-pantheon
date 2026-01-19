"""Tests for built-in Persona implementations."""

from __future__ import annotations

from genesis_pantheon.nexus import Nexus
from genesis_pantheon.personas.code_crafter import CodeCrafter
from genesis_pantheon.personas.insight_hunter import InsightHunter
from genesis_pantheon.personas.mission_coordinator import (
    MissionCoordinator,
)
from genesis_pantheon.personas.quality_guardian import QualityGuardian
from genesis_pantheon.personas.system_architect import SystemArchitect
from genesis_pantheon.personas.vision_director import VisionDirector
from tests.conftest import MockOracle


def _nexus() -> Nexus:
    nexus = Nexus()
    nexus._oracle = MockOracle(responses=["ok"])
    return nexus


class TestVisionDirector:
    def test_instantiation(self) -> None:
        p = VisionDirector()
        assert p.name == "Alice"
        assert p.profile == "Vision Director"

    def test_has_two_directives(self) -> None:
        p = VisionDirector()
        assert len(p.directives) == 2

    def test_subscribes_to_user_directive(self) -> None:
        p = VisionDirector()
        assert "UserDirective" in p.ctx.subscriptions

    def test_states_reflect_directives(self) -> None:
        p = VisionDirector()
        assert len(p.states) == 2


class TestSystemArchitect:
    def test_instantiation(self) -> None:
        p = SystemArchitect()
        assert p.name == "Bob"
        assert p.profile == "System Architect"

    def test_subscribes_to_draft_vision(self) -> None:
        p = SystemArchitect()
        assert "DraftVision" in p.ctx.subscriptions

    def test_has_one_directive(self) -> None:
        p = SystemArchitect()
        assert len(p.directives) >= 1


class TestCodeCrafter:
    def test_instantiation(self) -> None:
        p = CodeCrafter()
        assert p.name == "Charlie"
        assert p.profile == "Code Crafter"

    def test_without_review(self) -> None:
        p = CodeCrafter(code_review=False)
        directive_names = [d.name for d in p.directives]
        assert "ReviewCode" not in directive_names

    def test_with_review(self) -> None:
        p = CodeCrafter(code_review=True)
        directive_names = [d.name for d in p.directives]
        assert "ReviewCode" in directive_names

    def test_subscribes_to_design_signals(self) -> None:
        p = CodeCrafter()
        assert any(
            s in p.ctx.subscriptions
            for s in {"AllocateTasks", "DesignSystem"}
        )

    async def test_run_with_no_signal_returns_none(self) -> None:
        p = CodeCrafter()
        p.nexus = _nexus()
        result = await p.run()
        assert result is None


class TestQualityGuardian:
    def test_instantiation(self) -> None:
        p = QualityGuardian()
        assert p.profile == "Quality Guardian"

    def test_has_directives(self) -> None:
        p = QualityGuardian()
        assert len(p.directives) >= 1

    def test_subscribes_to_code_crafter_output(self) -> None:
        p = QualityGuardian()
        assert any(s for s in p.ctx.subscriptions)


class TestMissionCoordinator:
    def test_instantiation(self) -> None:
        p = MissionCoordinator()
        assert p.profile == "Mission Coordinator"

    def test_has_directive(self) -> None:
        p = MissionCoordinator()
        assert len(p.directives) >= 1

    def test_subscribes_to_design_output(self) -> None:
        p = MissionCoordinator()
        assert any(s for s in p.ctx.subscriptions)


class TestInsightHunter:
    def test_instantiation(self) -> None:
        p = InsightHunter()
        assert p.profile == "Insight Hunter"

    def test_has_directives(self) -> None:
        p = InsightHunter()
        assert len(p.directives) >= 1
