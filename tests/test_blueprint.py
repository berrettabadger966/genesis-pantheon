"""Tests for genesis_pantheon.blueprint module."""

from __future__ import annotations

from pathlib import Path

import yaml

from genesis_pantheon.blueprint import Blueprint
from genesis_pantheon.configs.oracle_config import OracleApiType


class TestBlueprint:
    def setup_method(self) -> None:
        """Reset singleton before each test."""
        Blueprint.reset()

    def test_default_llm_config(self) -> None:
        bp = Blueprint()
        assert bp.llm is not None
        assert bp.llm.model == "gpt-4-turbo"
        assert bp.llm.api_type == OracleApiType.OPENAI

    def test_from_yaml_file(self, tmp_path: Path) -> None:
        config_data = {
            "llm": {
                "api_type": "openai",
                "model": "gpt-4o",
                "api_key": "yaml-key",
            }
        }
        config_file = tmp_path / "blueprint.yaml"
        with open(str(config_file), "w") as fh:
            yaml.safe_dump(config_data, fh)

        bp = Blueprint.read(config_file)
        assert bp.llm.model == "gpt-4o"
        assert bp.llm.api_key == "yaml-key"

    def test_from_yaml_string(self) -> None:
        yaml_str = """
llm:
  api_type: anthropic
  model: claude-3-5-sonnet-20241022
  api_key: test-anthropic-key
"""
        bp = Blueprint.from_yaml_string(yaml_str)
        assert bp.llm.api_type == OracleApiType.ANTHROPIC
        assert "claude" in bp.llm.model

    def test_get_oracle_config_default(self) -> None:
        bp = Blueprint()
        cfg = bp.get_oracle_config()
        assert cfg.model == "gpt-4-turbo"

    def test_get_oracle_config_by_name(self) -> None:
        bp = Blueprint()
        from genesis_pantheon.configs.oracle_config import OracleConfig

        bp.role_oracles["VisionDirector"] = OracleConfig(
            api_key="role-key", model="gpt-4o"
        )
        cfg = bp.get_oracle_config("VisionDirector")
        assert cfg.model == "gpt-4o"

    def test_get_oracle_config_fallback(self) -> None:
        bp = Blueprint()
        cfg = bp.get_oracle_config("NonExistentPersona")
        assert cfg.model == bp.llm.model

    def test_workspace_config_defaults(self) -> None:
        bp = Blueprint()
        assert bp.workspace is not None
        assert bp.workspace.path is not None

    def test_search_config_present(self) -> None:
        bp = Blueprint()
        assert bp.search is not None

    def test_browser_config_present(self) -> None:
        bp = Blueprint()
        assert bp.browser is not None

    def test_save_and_reload(self, tmp_path: Path) -> None:
        bp = Blueprint()
        bp.llm.api_key = "saved-key"
        dest = tmp_path / "test_blueprint.yaml"
        bp.save(dest)
        assert dest.exists()
        bp2 = Blueprint.read(dest)
        assert bp2.llm.api_key == "saved-key"

    def test_from_home_returns_blueprint(self) -> None:
        bp = Blueprint.from_home()
        assert isinstance(bp, Blueprint)

    def test_default_singleton(self) -> None:
        bp1 = Blueprint.default()
        bp2 = Blueprint.default()
        assert bp1 is bp2
