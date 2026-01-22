"""Tests for genesis_pantheon.ledger module."""

from __future__ import annotations

from genesis_pantheon.ledger import BudgetLedger, TokenUsage


class TestTokenUsage:
    def test_from_counts(self) -> None:
        usage = TokenUsage.from_counts(100, 50)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_default_zeros(self) -> None:
        usage = TokenUsage()
        assert usage.total_tokens == 0


class TestBudgetLedger:
    def test_initial_state(self) -> None:
        ledger = BudgetLedger()
        assert ledger.total_cost == 0.0
        assert ledger.max_budget == float("inf")
        assert ledger.total_prompt_tokens == 0
        assert ledger.total_completion_tokens == 0

    def test_record_usage_increments_tokens(self) -> None:
        ledger = BudgetLedger()
        ledger.record_usage("gpt-4-turbo", 1000, 500)
        assert ledger.total_prompt_tokens == 1000
        assert ledger.total_completion_tokens == 500

    def test_record_usage_computes_cost(self) -> None:
        ledger = BudgetLedger()
        ledger.record_usage("gpt-4-turbo", 1000, 1000)
        # gpt-4-turbo: in=0.01/1k, out=0.03/1k
        expected = 1000 / 1000 * 0.01 + 1000 / 1000 * 0.03
        assert abs(ledger.total_cost - expected) < 1e-9

    def test_is_budget_exceeded_false(self) -> None:
        ledger = BudgetLedger(max_budget=10.0)
        ledger.record_usage("gpt-4-turbo", 10, 10)
        assert not ledger.is_budget_exceeded()

    def test_is_budget_exceeded_true(self) -> None:
        ledger = BudgetLedger(max_budget=0.001)
        ledger.record_usage("gpt-4-turbo", 10000, 10000)
        assert ledger.is_budget_exceeded()

    def test_remaining_budget(self) -> None:
        ledger = BudgetLedger(max_budget=5.0)
        ledger.record_usage("gpt-4-turbo", 100, 100)
        remaining = ledger.remaining_budget()
        assert remaining > 0
        assert remaining < 5.0

    def test_unlimited_budget(self) -> None:
        ledger = BudgetLedger()  # max_budget = inf
        assert ledger.remaining_budget() == float("inf")
        assert not ledger.is_budget_exceeded()

    def test_total_tokens_property(self) -> None:
        ledger = BudgetLedger()
        ledger.record_usage("gpt-4-turbo", 300, 200)
        assert ledger.total_tokens == 500

    def test_summary_string(self) -> None:
        ledger = BudgetLedger(max_budget=10.0)
        ledger.record_usage("gpt-4-turbo", 1000, 500)
        summary = ledger.summary()
        assert "$" in summary
        assert "1,500" in summary or "1500" in summary

    def test_model_costs_tracked(self) -> None:
        ledger = BudgetLedger()
        ledger.record_usage("gpt-4-turbo", 1000, 500)
        assert "gpt-4-turbo" in ledger.model_costs
        assert ledger.model_costs["gpt-4-turbo"] > 0

    def test_unknown_model_uses_default_pricing(self) -> None:
        ledger = BudgetLedger()
        ledger.record_usage("unknown-model-xyz", 1000, 1000)
        assert ledger.total_cost > 0

    def test_remaining_budget_floored_at_zero(self) -> None:
        ledger = BudgetLedger(max_budget=0.001)
        ledger.record_usage("gpt-4-turbo", 100000, 100000)
        assert ledger.remaining_budget() == 0.0
