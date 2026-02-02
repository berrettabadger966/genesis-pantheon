# Architecture

## High-Level System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          Collective                              │
│  • Owns the Arena and Nexus                                      │
│  • Launches missions (UserDirective signals)                     │
│  • Drives the round loop; enforces budget                        │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                         Arena                            │  │
│   │  • Pub/sub message broker                                │  │
│   │  • Routes Signals to subscribed Personas                 │  │
│   │  • Runs all active Personas concurrently each round      │  │
│   │  • Records all Signals in a Chronicle                    │  │
│   │                                                          │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│   │  │ Persona A│  │ Persona B│  │ Persona C│  ...         │  │
│   │  │          │  │          │  │          │              │  │
│   │  │ observe  │  │ observe  │  │ observe  │              │  │
│   │  │ think    │  │ think    │  │ think    │              │  │
│   │  │ act      │  │ act      │  │ act      │              │  │
│   │  │    │     │  │    │     │  │    │     │              │  │
│   │  │ Directive│  │ Directive│  │ Directive│              │  │
│   │  │    │     │  │    │     │  │    │     │              │  │
│   │  └────┼─────┘  └────┼─────┘  └────┼─────┘              │  │
│   │       │              │              │                    │  │
│   │       └──────────────┴──────────────┘                   │  │
│   │                       │                                 │  │
│   │                    Oracle                               │  │
│   │              (LLM provider adapter)                     │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────┐                                                   │
│   │  Nexus   │  (shared dependency-injection context)            │
│   │  config  │  blueprint.yaml / env vars                        │
│   │  oracle  │  cached LLM adapter instance                      │
│   │  budget  │  BudgetLedger (tracks spend, enforces cap)        │
│   └──────────┘                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Persona

A **Persona** is an autonomous agent that encapsulates:

- **Profile / Goal / Constraints** — used to build the LLM system prompt
- **Directives** — ordered list of tasks the persona can execute
- **Subscriptions** — set of `cause_by` values the persona listens for
- **PersonaContext** — runtime state: signal buffer, chronicle, react mode

The internal `observe → think → act` loop is driven by `Persona.run()`:

1. `_observe()` — drains the signal buffer, filters by subscriptions,
   adds matching signals to the chronicle and news list.
2. `_think()` — selects the next directive to run (by order or by
   reacting to incoming signal types).
3. `_act()` — calls `directive.run(context)`, wraps the result in a
   Signal, and returns it.

**React modes:**

| Mode | Behaviour |
|------|-----------|
| `BY_ORDER` | Runs all directives sequentially on each `run()` call |
| `REACT` | Selects a directive based on the type of incoming signal |
| `PLAN_AND_ACT` | (Extension point) Plan first, then execute |

### Directive

A **Directive** is a discrete unit of work. It:

- Holds a `name` that becomes the `cause_by` of the Signal it produces
- Inherits `NexusMixin` to access the shared Oracle
- Calls `self._ask(prompt)` to query the LLM
- Returns a `DirectiveOutput(content, structured_content)`

Custom directives simply subclass `Directive` and override `run()`.

### Signal

A **Signal** is the typed message envelope that flows through the
system:

```python
class Signal(BaseModel):
    id: str           # auto-generated UUID
    content: str      # plain-text payload
    structured_content: BaseModel | None  # optional typed payload
    role: str         # "user" or "assistant"
    cause_by: str     # directive class name that produced this signal
    sent_from: str    # name of the originating persona
    send_to: set[str] # target persona names, or {"<all>"}
    metadata: dict    # arbitrary extra data
```

### Arena

The **Arena** is the message broker and concurrent executor:

- `add_persona(persona)` — registers an agent and propagates the shared
  Nexus to it.
- `publish_signal(signal)` — appends the signal to the global chronicle
  and pushes it into the buffer of every matching persona.
- `run()` — gathers all non-idle personas and runs them concurrently
  with `asyncio.gather`; each result signal is immediately re-published.
- `is_idle` — True when every persona's buffer is empty.

### Collective

The **Collective** is the top-level orchestrator:

- `recruit(personas)` — adds personas to the arena.
- `launch_mission(mission)` — publishes an initial `UserDirective`
  signal.
- `allocate_budget(amount)` — sets the maximum USD spend.
- `run(n_rounds, mission)` — drives the round loop until all personas
  are idle, the budget is exceeded, or `n_rounds` is exhausted.

### Nexus

The **Nexus** is a lightweight dependency-injection container shared
by the entire system:

- `config` — active `Blueprint` (yaml/env config)
- `oracle()` — lazily creates and caches the LLM adapter
- `budget` — `BudgetLedger` for spend tracking

### Oracle

An **Oracle** is an async LLM adapter. All oracles inherit from
`BaseOracle` and must implement:

- `ask(prompt, system_msgs, images, stream) → str`
- `ask_batch(prompts, system_msgs) → str`

The convenience method `ask_code(prompts)` joins prompts and calls
`ask(..., stream=False)`.

---

## Signal Routing and the Publish/Subscribe Model

```
User Input
    │
    ▼
Signal(cause_by="UserDirective", send_to={"<all>"})
    │
    ▼  Arena.publish_signal()
    ├──► Persona A (subscribes to "UserDirective") ✓ → enqueued
    ├──► Persona B (subscribes to "ResearchDirective") ✗ → skipped
    └──► Persona C (subscribes to "UserDirective") ✓ → enqueued

Round 1: Arena.run()
    Persona A runs → Signal(cause_by="DraftVision")
    Arena re-publishes →
        Persona B (subscribes to "DraftVision") ✓ → enqueued

Round 2: Arena.run()
    Persona B runs → Signal(cause_by="DesignSystem")
    ...
```

Every `Signal.cause_by` equals the `Directive.name` that produced it.
A Persona subscribes by calling `_subscribe_to([SomeDirective])`, which
records `SomeDirective.__name__` (or the string) in
`ctx.subscriptions`. During `_observe()` the persona filters the signal
buffer by this set.

---

## Lifecycle of a Mission

```
1. User calls collective.run(mission="Build a web scraper")
   └─► launch_mission() publishes Signal(cause_by="UserDirective")

2. Round loop starts (up to n_rounds iterations):
   a. Arena checks is_idle → False (at least one persona has signals)
   b. collective._verify_budget() → raises BudgetExceededError if over
   c. arena.run() → gather all active personas concurrently
      i.   Each Persona._observe() drains buffer
      ii.  Each Persona._think() selects next directive
      iii. Each Persona._act() calls directive.run() → DirectiveOutput
      iv.  DirectiveOutput wrapped in Signal and published back
   d. If new signals were published, loop continues

3. All personas become idle (or budget/rounds exhausted)
   └─► arena.archive() called
   └─► arena.history returned to caller
```
