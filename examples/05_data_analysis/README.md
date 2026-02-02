# Example 05 — Data Analysis with Budget Limits

Shows the high-level `Collective` API with budget enforcement and a
two-persona data pipeline.

## What it does

1. Creates a `Nexus` with an `AnalysisOracle` that records fake token
   usage on every call so the `BudgetLedger` tracks cost.
2. Sets a **$1.00 budget cap** via `collective.allocate_budget(1.0)`.
3. Recruits two custom personas:
   - `DataEngineer` — subscribes to `UserDirective`, cleans the data.
   - `DataAnalyst` — subscribes to `CleanDataDirective` output,
     produces business insights.
4. Calls `collective.run(mission=..., n_rounds=4)` — the Collective
   drives the round loop and stops automatically when all personas are
   idle or the budget is exceeded.
5. Prints all produced signals and a budget report.

## Running

```bash
cd examples/05_data_analysis
python main.py
```

Expected output (truncated):

```
=== Launching data analysis mission ===

=== Signals produced ===

[DataEngineer] (CleanDataDirective)
Data cleaned: removed 12 duplicate rows ...

[DataAnalyst] (AnalyseDataDirective)
Analysis complete:
- Revenue shows 15% YoY growth. ...

=== Budget Report ===
Total spent : $0.0030
Budget cap  : $1.00
Exceeded?   : False
```

## Key concepts demonstrated

| Concept | Where |
|---------|-------|
| `Collective` API | `collective.run(mission=..., n_rounds=4)` |
| Budget cap | `collective.allocate_budget(1.0)` |
| `BudgetLedger` reporting | `collective.budget_ledger` |
| `_track_usage()` | `AnalysisOracle.ask()` records tokens |
| Chained signal routing | `CleanDataDirective` → `DataAnalyst` |
