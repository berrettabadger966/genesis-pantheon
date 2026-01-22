"""Tests for the SoftwareArena."""

from __future__ import annotations

from genesis_pantheon.arena.software_arena import SoftwareArena
from genesis_pantheon.nexus import Nexus
from tests.conftest import MockOracle


def _make_nexus() -> Nexus:
    nexus = Nexus()
    nexus._oracle = MockOracle(responses=["ok"])
    return nexus


class TestSoftwareArena:
    def test_instantiation_without_project(self) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        assert arena.project_name == ""
        assert arena.project_path == ""
        assert arena.repo is None

    def test_instantiation_with_project_path(
        self, tmp_path
    ) -> None:
        nexus = _make_nexus()
        # Enable git for the config
        nexus.config.workspace.use_git = False
        arena = SoftwareArena(
            context=nexus,
            project_name="myapp",
            project_path=str(tmp_path),
        )
        assert arena.repo is not None
        import os

        assert os.path.exists(str(tmp_path / "myapp"))

    def test_is_idle_initially(self) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        assert arena.is_idle is True

    def test_archive_without_repo_does_not_raise(self) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        arena.archive(auto=True)  # should not raise

    def test_archive_with_auto_false_does_not_commit(
        self,
    ) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        arena.archive(auto=False)  # should not raise

    async def test_run_without_personas_returns_empty(self) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        result = await arena.run()
        assert result == []

    def test_history_initially_empty(self) -> None:
        nexus = _make_nexus()
        arena = SoftwareArena(context=nexus)
        assert arena.history == []
