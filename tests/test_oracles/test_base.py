"""Tests for the BaseOracle abstract adapter."""

from __future__ import annotations

from genesis_pantheon.configs.oracle_config import OracleApiType, OracleConfig
from genesis_pantheon.ledger import BudgetLedger
from tests.conftest import MockOracle


def _make_config(**kwargs) -> OracleConfig:
    defaults = {
        "api_type": OracleApiType.OPENAI,
        "api_key": "test-key",
        "model": "gpt-4-turbo",
    }
    defaults.update(kwargs)
    return OracleConfig(**defaults)


class TestBaseOracle:
    def test_oracle_stores_config(self) -> None:
        cfg = _make_config()
        oracle = MockOracle(config=cfg)
        assert oracle.config is cfg

    def test_oracle_default_system_prompt_is_empty(self) -> None:
        oracle = MockOracle()
        assert oracle.system_prompt == ""

    def test_oracle_system_prompt_can_be_set(self) -> None:
        oracle = MockOracle()
        oracle.system_prompt = "You are helpful"
        assert oracle.system_prompt == "You are helpful"

    def test_build_messages_user_only(self) -> None:
        oracle = MockOracle()
        messages = oracle._build_messages("hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "hello"

    def test_build_messages_with_system_prompt(self) -> None:
        oracle = MockOracle()
        oracle.system_prompt = "System context"
        messages = oracle._build_messages("user question")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "System context" in messages[0]["content"]
        assert messages[1]["role"] == "user"

    def test_build_messages_with_extra_system_msgs(self) -> None:
        oracle = MockOracle()
        messages = oracle._build_messages(
            "question", system_msgs=["extra info"]
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "extra info" in messages[0]["content"]

    def test_build_messages_combines_system_prompt_and_msgs(self) -> None:
        oracle = MockOracle()
        oracle.system_prompt = "Base system"
        messages = oracle._build_messages(
            "prompt", system_msgs=["additional"]
        )
        system_content = messages[0]["content"]
        assert "Base system" in system_content
        assert "additional" in system_content

    def test_track_usage_updates_budget(self) -> None:
        budget = BudgetLedger(max_budget=10.0)
        oracle = MockOracle()
        oracle.budget = budget
        oracle._track_usage(prompt_tokens=100, completion_tokens=50)
        assert budget.total_prompt_tokens == 100
        assert budget.total_completion_tokens == 50

    def test_track_usage_without_budget_does_not_raise(self) -> None:
        oracle = MockOracle()
        assert oracle.budget is None
        # Should not raise
        oracle._track_usage(prompt_tokens=10, completion_tokens=5)

    async def test_ask_returns_canned_response(self) -> None:
        oracle = MockOracle(responses=["hello world"])
        response = await oracle.ask("anything")
        assert response == "hello world"

    async def test_ask_cycles_through_responses(self) -> None:
        oracle = MockOracle(responses=["first", "second", "third"])
        r1 = await oracle.ask("q1")
        r2 = await oracle.ask("q2")
        r3 = await oracle.ask("q3")
        r4 = await oracle.ask("q4")  # wraps around
        assert r1 == "first"
        assert r2 == "second"
        assert r3 == "third"
        assert r4 == "first"

    async def test_ask_code_combines_prompts(self) -> None:
        oracle = MockOracle(responses=["code response"])
        result = await oracle.ask_code(["write a function", "use Python"])
        assert result == "code response"

    async def test_ask_batch_concatenates_results(self) -> None:
        oracle = MockOracle(responses=["resp1", "resp2"])
        result = await oracle.ask_batch(["p1", "p2"])
        assert "resp1" in result
        assert "resp2" in result

    async def test_ask_tracks_token_usage(self) -> None:
        budget = BudgetLedger(max_budget=100.0)
        oracle = MockOracle(responses=["short"])
        oracle.budget = budget
        await oracle.ask("hello")
        assert budget.total_prompt_tokens > 0
        assert budget.total_completion_tokens > 0
