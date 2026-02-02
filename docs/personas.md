# Personas

A **Persona** is an autonomous agent with a profile, goal, constraints,
and a list of directives it can execute. Personas communicate
exclusively through typed Signals published to the Arena.

---

## VisionDirector

**File:** `genesis_pantheon/personas/vision_director.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Victoria` |
| Profile | `Vision Director` |
| Goal | Translate user requirements into a clear, structured product vision |
| Constraints | Focus on user needs; avoid technical implementation details |

**Directives:**

| Directive | Purpose |
|-----------|---------|
| `DraftVision` | Produces a product requirements document (PRD) |

**Subscriptions:** `UserDirective`

The VisionDirector is the entry point for software missions. It receives
raw user requirements and transforms them into a structured PRD that
downstream personas consume.

---

## SystemArchitect

**File:** `genesis_pantheon/personas/system_architect.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Alex` |
| Profile | `System Architect` |
| Goal | Design robust, scalable system architectures |
| Constraints | Prioritise simplicity; document all design decisions |

**Directives:**

| Directive | Purpose |
|-----------|---------|
| `DesignSystem` | Creates a technical system design document |
| `ReviewDesign` | Reviews and refines an existing design |

**Subscriptions:** `DraftVision`

The SystemArchitect converts the PRD into a concrete system design,
covering modules, interfaces, data flows, and technology choices.

---

## CodeCrafter

**File:** `genesis_pantheon/personas/code_crafter.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Charlie` |
| Profile | `Code Crafter` |
| Goal | Write clean, efficient, well-tested Python code |
| Constraints | Follow PEP 8; no stubs; include docstrings and type hints |

**Directives (default):**

| Directive | Purpose |
|-----------|---------|
| `CraftCode` | Generates Python source files |
| `CondenseCode` | Summarises multi-file codebases |

**Directives (with `code_review=True`):**

| Directive | Purpose |
|-----------|---------|
| `CraftCode` | Generates Python source files |
| `ReviewCode` | Self-reviews and improves generated code |
| `CondenseCode` | Summarises multi-file codebases |

**Subscriptions:** `AllocateTasks`, `DesignSystem`

**Options:**

```python
from genesis_pantheon.personas.code_crafter import CodeCrafter

# Enable self-review after generation
crafter = CodeCrafter(code_review=True)
```

---

## QualityGuardian

**File:** `genesis_pantheon/personas/quality_guardian.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Quinn` |
| Profile | `Quality Guardian` |
| Goal | Ensure code quality through comprehensive testing |
| Constraints | Achieve high test coverage; test edge cases and failure paths |

**Directives:**

| Directive | Purpose |
|-----------|---------|
| `GenerateTests` | Writes pytest test suites for generated code |
| `ExecuteCode` | Runs tests and captures stdout / return code |
| `DiagnoseError` | Analyses test failures and suggests fixes |

**Subscriptions:** `CraftCode`, `CondenseCode`

---

## MissionCoordinator

**File:** `genesis_pantheon/personas/mission_coordinator.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Morgan` |
| Profile | `Mission Coordinator` |
| Goal | Break down designs into granular, prioritised task files |
| Constraints | Tasks must be unambiguous; assign clear ownership |

**Directives:**

| Directive | Purpose |
|-----------|---------|
| `AllocateTasks` | Decomposes design into task files for CodeCrafter |

**Subscriptions:** `DraftVision`

The MissionCoordinator reads the system design and produces task files
that tell CodeCrafter exactly which files to implement and in what order.

---

## InsightHunter

**File:** `genesis_pantheon/personas/insight_hunter.py`

| Attribute | Value |
|-----------|-------|
| Default name | `Frank` |
| Profile | `Insight Hunter` |
| Goal | Gather comprehensive, accurate information and transform it into actionable insights |
| Constraints | Rely only on verified information; distinguish facts from analysis |

**Directives:**

| Directive | Purpose |
|-----------|---------|
| `ResearchDirective` | Conducts research and produces a structured report |

**Subscriptions:** `UserDirective`

InsightHunter is designed for research-heavy workflows. Pair it with a
synthesiser persona to build automated research pipelines.

---

## Creating a Custom Persona

Subclass `Persona`, define your directives, and wire subscriptions in
`__init__`:

```python
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.directives.base import Directive
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.schema import DirectiveOutput


class SummariseDirective(Directive):
    """Summarise any text to three bullet points."""

    name: str = "SummariseDirective"

    async def run(self, context=None, **kwargs):
        prompt = (
            f"Summarise the following in exactly 3 bullet points:\n\n"
            f"{context}"
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


class Summariser(Persona):
    """A persona that summarises incoming signals."""

    name: str = "Summariser"
    profile: str = "Text Summariser"
    goal: str = "Produce concise three-bullet summaries"
    constraints: str = "Exactly 3 bullets; no more, no less"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._assign_directives([SummariseDirective])
        self._subscribe_to([UserDirective])
```

Then recruit it into a Collective:

```python
import asyncio
from genesis_pantheon.collective import Collective

async def main():
    collective = Collective()
    collective.recruit([Summariser()])
    signals = await collective.run(
        mission="Python is a high-level, interpreted programming language "
                "known for its clear syntax and readability.",
    )
    for s in signals:
        print(s.content)

asyncio.run(main())
```

### Key rules for custom personas

1. Call `self._assign_directives([DirectiveClass, ...])` — this
   instantiates each directive and sets `nexus` on them.
2. Call `self._subscribe_to([DirectiveClass, ...])` — registers the
   directive names as subscriptions so signals are delivered.
3. Override `run()` only if you need custom pre/post processing; the
   base `Persona.run()` handles the observe/think/act loop.
