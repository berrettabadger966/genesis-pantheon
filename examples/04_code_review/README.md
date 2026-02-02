# Example 04 — Code Review with CodeCrafter

Shows how to enable CodeCrafter's built-in self-review capability and
how it processes a task allocation signal.

## What it does

1. Creates `CodeCrafter(code_review=True)`, which adds `ReviewCode` to
   its directive pipeline between `CraftCode` and `CondenseCode`.
2. Injects a `CodeReviewOracle` that returns canned code, review
   feedback, and a condensed summary.
3. Publishes an `AllocateTasks` signal (the directive type CodeCrafter
   subscribes to) with a code-generation task.
4. Runs the persona and prints the final output.

## Running

```bash
cd examples/04_code_review
python main.py
```

Expected output:

```
Directives: ['CraftCode', 'ReviewCode', 'CondenseCode']

=== CodeCrafter Output ===
Module contains two arithmetic functions: `add` and `subtract`. ...
```

## Key concepts demonstrated

| Concept | Where |
|---------|-------|
| `CodeCrafter(code_review=True)` | Enables `ReviewCode` directive |
| Directive pipeline | `CraftCode → ReviewCode → CondenseCode` |
| `AllocateTasks` subscription | Signal `cause_by` matches subscription |
| Oracle routing | Different prompts return different canned responses |
