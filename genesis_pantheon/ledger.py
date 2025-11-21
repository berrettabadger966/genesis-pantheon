"""Budget and token usage tracking for GenesisPantheon."""

from __future__ import annotations

from pydantic import BaseModel, Field

from genesis_pantheon.logger import logger


class TokenUsage(BaseModel):
    """Token counts for a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_counts(
        cls, prompt: int, completion: int
    ) -> TokenUsage:
        """Convenience constructor.

        Args:
            prompt: Number of prompt tokens.
            completion: Number of completion tokens.

        Returns:
            TokenUsage instance with totals computed.
        """
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        )


class BudgetLedger(BaseModel):
    """Tracks cumulative token usage and cost across all oracle calls.

    When ``max_budget`` is set the caller should check
    :meth:`is_budget_exceeded` after each oracle call.
    """

    total_cost: float = 0.0
    max_budget: float = float("inf")
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    # Per-model accumulated costs
    model_costs: dict[str, float] = Field(default_factory=dict)

    # Pricing map (USD / 1k tokens): (input_rate, output_rate)
    _PRICING: dict[str, tuple] = {
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4o": (0.005, 0.015),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-opus-20240229": (0.015, 0.075),
        "gemini-1.5-pro": (0.00125, 0.005),
    }

    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Update totals with a new oracle call's usage.

        Args:
            model: Model name used for this call.
            prompt_tokens: Input token count.
            completion_tokens: Output token count.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        in_rate, out_rate = self._PRICING.get(
            model.lower(), (0.01, 0.03)
        )
        call_cost = (
            prompt_tokens / 1000 * in_rate
            + completion_tokens / 1000 * out_rate
        )
        self.total_cost += call_cost
        self.model_costs[model] = (
            self.model_costs.get(model, 0.0) + call_cost
        )
        logger.debug(
            f"Usage recorded | model={model} "
            f"prompt={prompt_tokens} "
            f"completion={completion_tokens} "
            f"call_cost=${call_cost:.6f} "
            f"total=${self.total_cost:.6f}"
        )

    def is_budget_exceeded(self) -> bool:
        """Return True when the total cost exceeds the max budget.

        Returns:
            Boolean budget-exceeded flag.
        """
        return self.total_cost >= self.max_budget

    def remaining_budget(self) -> float:
        """Return the remaining budget in USD.

        Returns:
            Remaining USD, or ``inf`` when no limit is set.
        """
        if self.max_budget == float("inf"):
            return float("inf")
        return max(0.0, self.max_budget - self.total_cost)

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (prompt + completion).

        Returns:
            Integer token count.
        """
        return self.total_prompt_tokens + self.total_completion_tokens

    def summary(self) -> str:
        """Return a human-readable summary string.

        Returns:
            Formatted usage summary.
        """
        return (
            f"Total cost: ${self.total_cost:.4f} / "
            f"${self.max_budget:.2f} | "
            f"Tokens: {self.total_tokens:,} "
            f"(prompt={self.total_prompt_tokens:,}, "
            f"completion={self.total_completion_tokens:,})"
        )


__all__ = ["TokenUsage", "BudgetLedger"]
