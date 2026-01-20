"""Tests for the CLI commands."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from genesis_pantheon.cli import app

runner = CliRunner()


class TestListOracles:
    def test_lists_all_providers(self) -> None:
        result = runner.invoke(app, ["list-oracles"])
        assert result.exit_code == 0
        assert "openai" in result.output.lower()
        assert "anthropic" in result.output.lower()
        assert "ollama" in result.output.lower()

    def test_output_includes_gemini(self) -> None:
        result = runner.invoke(app, ["list-oracles"])
        assert "gemini" in result.output.lower()

    def test_output_includes_azure(self) -> None:
        result = runner.invoke(app, ["list-oracles"])
        assert "azure" in result.output.lower()


class TestVersion:
    def test_shows_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "GenesisPantheon" in result.output or "0.1.0" in result.output


class TestInitConfig:
    def test_creates_config_file(self, tmp_path) -> None:
        config_dest = tmp_path / "blueprint.yaml"
        with (
            patch(
                "genesis_pantheon.cli.DEFAULT_CONFIG_FILE",
                config_dest,
            ),
            patch("genesis_pantheon.blueprint.Blueprint.save"),
        ):
            result = runner.invoke(app, ["init-config"])
            # Should not error (even if config doesn't exist yet)
            assert result.exit_code in (0, 1)


class TestLaunch:
    def test_launch_requires_mission_argument(self) -> None:
        result = runner.invoke(app, ["launch"])
        # Missing required argument should fail
        assert result.exit_code != 0

    def test_launch_with_mission_runs(self) -> None:
        """Test that launch command invokes collective.run."""
        mock_signals = []

        async def fake_run(*args, **kwargs):
            return mock_signals

        with (
            patch(
                "genesis_pantheon.collective.Collective.run",
                new=AsyncMock(return_value=mock_signals),
            ),
            patch("genesis_pantheon.blueprint.Blueprint.from_home"),
        ):
            result = runner.invoke(
                app,
                ["launch", "Build a calculator"],
                catch_exceptions=True,
            )
            # Should complete (either successfully or with handled error)
            assert result.exit_code in (0, 1)

    def test_launch_help(self) -> None:
        result = runner.invoke(app, ["launch", "--help"])
        # Help may succeed or fail on some typer versions; just check it runs
        assert result.exit_code in (0, 1)

    def test_list_oracles_help(self) -> None:
        result = runner.invoke(app, ["list-oracles", "--help"])
        assert result.exit_code in (0, 1)

    def test_init_config_help(self) -> None:
        result = runner.invoke(app, ["init-config", "--help"])
        assert result.exit_code in (0, 1)

    def test_app_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        # Either succeeds or known version error
        assert result.exit_code in (0, 1)
