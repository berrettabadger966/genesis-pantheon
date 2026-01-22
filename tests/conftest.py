"""Shared pytest fixtures for GenesisPantheon tests."""

from __future__ import annotations

import pytest

from genesis_pantheon.blueprint import Blueprint
from genesis_pantheon.configs.oracle_config import OracleApiType, OracleConfig
from genesis_pantheon.ledger import BudgetLedger
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.schema import Signal


class MockOracle(BaseOracle):
    """Deterministic oracle for testing that returns canned responses."""

    _responses: list[str]
    _call_count: int

    def __init__(
        self,
        config: OracleConfig | None = None,
        responses: list[str] | None = None,
    ) -> None:
        cfg = config or OracleConfig(
            api_type=OracleApiType.OPENAI,
            api_key="test-key",
            model="gpt-4-turbo",
        )
        super().__init__(cfg)
        self._responses = responses or ["Mock oracle response."]
        self._call_count = 0

    async def ask(
        self,
        prompt: str,
        system_msgs=None,
        images=None,
        stream: bool = False,
    ) -> str:
        idx = self._call_count % len(self._responses)
        response = self._responses[idx]
        self._call_count += 1
        self._track_usage(
            prompt_tokens=max(1, len(prompt) // 4),
            completion_tokens=max(1, len(response) // 4),
        )
        return response

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs=None,
    ) -> str:
        parts = []
        for p in prompts:
            parts.append(await self.ask(p, system_msgs))
        return "\n".join(parts)


@pytest.fixture
def mock_oracle() -> MockOracle:
    """Return a deterministic MockOracle instance."""
    return MockOracle(
        responses=[
            "This is a mock PRD response with product goals.",
            "This is a mock design response with file list.",
            "This is a mock code response.\n```python\nprint('hello')\n```",
            "LGTM - the design looks solid.",
            "Task 1: Implement main.py\nTask 2: Implement utils.py",
        ]
    )


@pytest.fixture
def oracle_config() -> OracleConfig:
    """Return a test OracleConfig."""
    return OracleConfig(
        api_type=OracleApiType.OPENAI,
        api_key="test-key-12345",
        model="gpt-4-turbo",
        temperature=0.0,
        max_tokens=1024,
    )


@pytest.fixture
def nexus_fixture(mock_oracle: MockOracle) -> Nexus:
    """Return a Nexus pre-loaded with a mock oracle."""
    nexus = Nexus()
    nexus._oracle = mock_oracle
    nexus._budget = BudgetLedger(max_budget=50.0)
    return nexus


@pytest.fixture
def sample_signal() -> Signal:
    """Return a sample Signal for testing."""
    return Signal(
        content="Build a simple calculator in Python",
        cause_by="UserDirective",
        sent_from="TestUser",
    )


@pytest.fixture
def blueprint_fixture(tmp_path) -> Blueprint:
    """Return a test Blueprint backed by a temp YAML file."""
    bp = Blueprint()
    bp.llm.api_key = "test-key"
    bp.llm.model = "gpt-4-turbo"
    bp.workspace.path = tmp_path / "workspace"
    return bp
