# Example 02 — Custom Persona

Shows how to build a fully custom `Directive` and `Persona` subclass.

## What it does

1. Defines `SummariserDirective` — asks the oracle to condense any text
   into three bullet points.
2. Defines `SummariserPersona` — wires the directive in `__init__` and
   subscribes to `UserDirective` signals.
3. Injects a `MockOracle` that returns a canned summary (no API key
   needed).
4. Runs the persona on a paragraph about AI and prints the bullets.

## Running

```bash
cd examples/02_custom_persona
python main.py
```

Expected output:

```
=== Summary ===
• AI refers to intelligence demonstrated by machines.
• The field studies intelligent agents that maximise goal-achievement.
• Historically the term covered machines mimicking human cognitive skills.
```

## Key concepts demonstrated

| Concept | Where |
|---------|-------|
| Custom `Directive` subclass | `SummariserDirective.run()` |
| Custom `Persona` subclass | `SummariserPersona.__init__()` |
| `_assign_directives()` | Instantiates and registers directives |
| `_subscribe_to()` | Registers subscriptions by directive class |
| `PersonaReactMode.BY_ORDER` | Runs all directives in sequence |
