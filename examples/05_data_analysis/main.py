"""Data Analysis — Collective with budget limits.

Demonstrates:
- High-level Collective API
- Recruiting multiple custom personas
- Setting a budget cap
- Running a mission with n_rounds
- Inspecting spend after the run

Run with: python main.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from genesis_pantheon.collective import Collective
from genesis_pantheon.configs.oracle_config import OracleConfig
from genesis_pantheon.directives.base import Directive
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.personas.persona import Persona, PersonaReactMode
from genesis_pantheon.schema import DirectiveOutput

# ---------------------------------------------------------------------------
# Mock oracle that fakes token usage for budget tracking
# ---------------------------------------------------------------------------


class AnalysisOracle(BaseOracle):
    """Returns canned analysis; tracks fake token usage."""

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str:
        p = prompt.lower()
        if "clean" in p or "preprocess" in p or "missing" in p:
            result = (
                "Data cleaned: removed 12 duplicate rows, "
                "imputed 3 missing values in column 'revenue'. "
                "Dataset now has 988 rows and 5 columns."
            )
        elif "analyse" in p or "insight" in p or "pattern" in p:
            result = (
                "Analysis complete:\n"
                "- Revenue shows 15% YoY growth.\n"
                "- Q4 consistently outperforms Q1 by 22%.\n"
                "- Top 3 products account for 68% of revenue.\n"
                "- Customer churn peaked in March (8.3%)."
            )
        else:
            result = "Processing complete."
        # Record fake token usage so BudgetLedger tracks cost
        self._track_usage(prompt_tokens=150, completion_tokens=80)
        return result

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        return await self.ask(prompts[0] if prompts else "")


# ---------------------------------------------------------------------------
# Custom directives
# ---------------------------------------------------------------------------


class CleanDataDirective(Directive):
    """Clean and preprocess raw dataset."""

    name: str = "CleanDataDirective"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        prompt = (
            "You are a data engineer. Clean and preprocess the "
            "following dataset description. Report what was changed.\n\n"
            f"Dataset info: {context}"
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


class AnalyseDataDirective(Directive):
    """Produce insights from cleaned data."""

    name: str = "AnalyseDataDirective"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        prompt = (
            "You are a senior data analyst. Analyse the following "
            "cleaned dataset and provide actionable business insights.\n\n"
            f"Data summary: {context}"
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


# ---------------------------------------------------------------------------
# Custom personas
# ---------------------------------------------------------------------------


class DataEngineer(Persona):
    """Cleans and preprocesses raw data."""

    name: str = "DataEngineer"
    profile: str = "Data Engineer"
    goal: str = "Deliver clean, analysis-ready datasets"
    constraints: str = "Document every transformation applied"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives([CleanDataDirective])
        self._subscribe_to([UserDirective])
        self.ctx.react_mode = PersonaReactMode.BY_ORDER


class DataAnalyst(Persona):
    """Derives insights from cleaned data."""

    name: str = "DataAnalyst"
    profile: str = "Data Analyst"
    goal: str = "Surface actionable business insights from data"
    constraints: str = "Quantify claims with numbers; avoid vague language"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives([AnalyseDataDirective])
        # Listens for output from DataEngineer
        self._subscribe_to([CleanDataDirective])
        self.ctx.react_mode = PersonaReactMode.BY_ORDER


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    # Shared nexus with budget-tracking oracle
    nexus = Nexus()
    nexus._oracle = AnalysisOracle(config=OracleConfig(api_key="fake"))

    # Build the Collective with a $1 budget cap
    collective = Collective(context=nexus)
    collective.allocate_budget(1.0)

    # Recruit personas
    collective.recruit([DataEngineer(), DataAnalyst()])

    print("=== Launching data analysis mission ===\n")
    signals = await collective.run(
        mission=(
            "Analyse the sales dataset: 1000 rows, columns "
            "[date, product, region, units_sold, revenue]. "
            "Data has some missing values and duplicates."
        ),
        n_rounds=4,
    )

    print("=== Signals produced ===")
    for sig in signals:
        if sig.content:
            print(f"\n[{sig.sent_from}] ({sig.cause_by})")
            print(sig.content[:300])

    print("\n=== Budget Report ===")
    ledger = collective.budget_ledger
    print(f"Total spent : ${ledger.total_cost:.4f}")
    print(f"Budget cap  : ${ledger.max_budget:.2f}")
    print(f"Exceeded?   : {ledger.is_budget_exceeded()}")


if __name__ == "__main__":
    asyncio.run(main())
