# Example 01 — Hello World

The simplest possible GenesisPantheon program.

## What it does

1. Creates a `Nexus` and injects an `EchoOracle` that mirrors prompts
   back — no API key or network required.
2. Defines a `GreetDirective` that asks the oracle to greet a named
   user.
3. Creates a single `Persona` subscribed to `UserDirective` signals.
4. Publishes a signal with the text `"Hello, GenesisPantheon!"` and
   prints the persona's response.

## Running

```bash
cd examples/01_hello_world
python main.py
```

Expected output:

```
Agent response: Echo: Say a warm greeting to: Hello, GenesisPantheon!
```

## Key concepts demonstrated

| Concept | Where |
|---------|-------|
| `EchoOracle` | Custom `BaseOracle` subclass; no provider needed |
| `GreetDirective` | Custom `Directive`; calls `self._ask()` |
| `Persona` | Agent configured with directives and subscriptions |
| `Signal` | Typed message that triggers the agent |
| `PersonaReactMode.BY_ORDER` | Runs all directives sequentially |
