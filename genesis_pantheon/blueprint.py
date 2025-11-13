"""YAML-based configuration system for GenesisPantheon."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import Field, model_validator

from genesis_pantheon.configs.browser_config import BrowserConfig
from genesis_pantheon.configs.oracle_config import (
    OracleApiType,
    OracleConfig,
)
from genesis_pantheon.configs.search_config import SearchConfig
from genesis_pantheon.configs.workspace_config import WorkspaceConfig
from genesis_pantheon.constants import DEFAULT_CONFIG_FILE
from genesis_pantheon.utils.yaml_model import YamlModel


class Blueprint(YamlModel):
    """Top-level configuration for a GenesisPantheon deployment.

    Loaded from ``~/.genesis_pantheon/blueprint.yaml`` by default.
    All sensitive values (API keys) may be overridden via environment
    variables using the pattern ``GP_<SECTION>_<KEY>`` in uppercase.
    """

    llm: OracleConfig = Field(
        default_factory=OracleConfig.default_openai
    )
    embedding: OracleConfig | None = None
    search: SearchConfig = Field(default_factory=SearchConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    workspace: WorkspaceConfig = Field(
        default_factory=WorkspaceConfig
    )
    # Named per-role overrides: {"VisionDirector": OracleConfig(...)}
    role_oracles: dict[str, OracleConfig] = Field(
        default_factory=dict
    )

    # Singleton instance
    _instance: Blueprint | None = None

    @model_validator(mode="after")
    def _apply_env_overrides(self) -> Blueprint:
        """Override config values from environment variables."""
        env_key = os.environ.get("GP_LLM_API_KEY", "")
        if env_key:
            self.llm.api_key = env_key
        env_model = os.environ.get("GP_LLM_MODEL", "")
        if env_model:
            self.llm.model = env_model
        env_base = os.environ.get("GP_LLM_BASE_URL", "")
        if env_base:
            self.llm.base_url = env_base
        env_type = os.environ.get("GP_LLM_API_TYPE", "")
        if env_type:
            try:
                self.llm.api_type = OracleApiType(env_type.lower())
            except ValueError:
                pass
        return self

    @classmethod
    def from_home(cls) -> Blueprint:
        """Load Blueprint from the default config file location.

        Silently returns a default Blueprint when the file does not
        exist.

        Returns:
            Loaded or default Blueprint instance.
        """
        path = DEFAULT_CONFIG_FILE
        if path.exists():
            try:
                data = cls.read_yaml(path)
                return cls(**data)
            except Exception:
                pass
        return cls()

    @classmethod
    def default(cls) -> Blueprint:
        """Return the global singleton Blueprint instance.

        The singleton is populated on first call from the default
        config file path.

        Returns:
            Singleton Blueprint.
        """
        if cls._instance is None:
            cls._instance = cls.from_home()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clear the singleton so the next call re-loads from disk.

        Primarily useful in tests.
        """
        cls._instance = None

    def get_oracle_config(
        self, name: str = ""
    ) -> OracleConfig:
        """Return an OracleConfig by persona name or API type string.

        Falls back to the default ``llm`` config when the requested
        name is not found.

        Args:
            name: Persona name or OracleApiType string.

        Returns:
            Matching OracleConfig.
        """
        if name in self.role_oracles:
            return self.role_oracles[name]
        try:
            api_type = OracleApiType(name.lower())
            # Build a copy of the default config with this type
            cfg = self.llm.model_copy()
            cfg.api_type = api_type
            return cfg
        except ValueError:
            return self.llm

    def save(
        self, path: str | Path | None = None
    ) -> None:
        """Write the current configuration to a YAML file.

        Args:
            path: Destination path. Defaults to the standard
                config file location.
        """
        dest = Path(path) if path else DEFAULT_CONFIG_FILE
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.write(dest)

    @classmethod
    def from_yaml_string(cls, yaml_str: str) -> Blueprint:
        """Parse a Blueprint from a raw YAML string.

        Args:
            yaml_str: YAML-encoded configuration string.

        Returns:
            Blueprint instance.
        """
        data = yaml.safe_load(yaml_str) or {}
        return cls(**data)

    class Config:
        arbitrary_types_allowed = True


__all__ = ["Blueprint"]
