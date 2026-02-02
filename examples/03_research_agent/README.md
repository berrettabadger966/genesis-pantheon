# Example 03 — Research Agent Pipeline

A two-persona pipeline that chains InsightHunter output into a
Synthesiser persona via the Arena's pub/sub routing.

## What it does

1. Creates a shared `Nexus` with a `MockOracle`.
2. Registers `InsightHunter` (subscribes to `UserDirective`) and a
   custom `Synthesiser` (subscribes to `ResearchDirective`).
3. Publishes an initial `UserDirective` signal to the Arena.
4. **Round 1:** InsightHunter runs, produces a research report, and
   publishes it as a `ResearchDirective` signal.
5. **Round 2:** Synthesiser receives that signal, distils it into an
   executive summary, and publishes the result.

## Running

```bash
cd examples/03_research_agent
python main.py
```

Expected output (truncated):

```
=== Round 1: InsightHunter researches ===
[Frank] ## Research Report: Python Async
...

=== Round 2: Synthesiser synthesises ===
[Synthesiser] **Executive Synthesis:**
...

Total signals in chronicle: 3
```

## Key concepts demonstrated

| Concept | Where |
|---------|-------|
| Multi-persona Arena | `arena.add_personas([hunter, synthesiser])` |
| Signal chaining | `ResearchDirective` output triggers `Synthesiser` |
| Pub/sub routing | `_subscribe_to([ResearchDirective])` |
| Manual round control | `await arena.run()` called twice |
| Built-in `InsightHunter` | Imported from `genesis_pantheon.personas` |
