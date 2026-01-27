# Oracles

An **Oracle** is GenesisPantheon's abstraction over an LLM provider.
Every Directive calls `self._ask(prompt)` which delegates to the active
Oracle. Swapping providers requires only a config change — no code
changes needed.

---

## What is an Oracle?

```
Directive._ask(prompt)
    └─► BaseOracle.ask(prompt, system_msgs, images, stream)
            └─► Provider API (OpenAI / Anthropic / Gemini / Ollama)
                    └─► str response
```

All oracles share the same interface defined in `BaseOracle`:

```python
class BaseOracle(ABC):
    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images: list[Any] | None = None,
        stream: bool = True,
    ) -> str: ...

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str: ...

    async def ask_code(self, prompts: list[str]) -> str: ...
```

---

## Configuring Each Provider

### OpenAI

```yaml
# blueprint.yaml
llm:
  api_type: openai
  api_key: "${OPENAI_API_KEY}"
  model: gpt-4o
  temperature: 0.0
  max_tokens: 4096
  stream: true
```

```bash
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

Supported models: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`, and any
model available on your account.

### Azure OpenAI

```yaml
llm:
  api_type: azure
  api_key: "${AZURE_OPENAI_API_KEY}"
  base_url: "${AZURE_OPENAI_ENDPOINT}"
  model: "${AZURE_OPENAI_DEPLOYMENT}"
  api_version: "2024-02-01"
  temperature: 0.0
  max_tokens: 4096
```

`model` must match the **deployment name** in your Azure resource, not
the underlying model name.

### Anthropic Claude

```yaml
llm:
  api_type: anthropic
  api_key: "${ANTHROPIC_API_KEY}"
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.0
```

```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Google Gemini

```yaml
llm:
  api_type: gemini
  api_key: "${GOOGLE_API_KEY}"
  model: gemini-1.5-pro
  max_tokens: 4096
  temperature: 0.0
```

```bash
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-1.5-pro
```

### Ollama (local)

```yaml
llm:
  api_type: ollama
  base_url: http://localhost:11434
  model: llama3.2
  api_key: ollama        # placeholder; not used
  temperature: 0.0
  max_tokens: 4096
```

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Make sure Ollama is running (`ollama serve`) and the model is pulled
(`ollama pull llama3.2`) before use.

---

## Instantiating an Oracle Directly

```python
from genesis_pantheon.oracles.openai_oracle import OpenAIOracle
from genesis_pantheon.configs.oracle_config import OracleConfig, OracleApiType

config = OracleConfig(
    api_type=OracleApiType.OPENAI,
    api_key="sk-...",
    model="gpt-4o",
)
oracle = OpenAIOracle(config=config)
response = await oracle.ask("Explain async/await in Python.")
```

---

## Creating a Custom Oracle

Subclass `BaseOracle` and implement `ask` and `ask_batch`:

```python
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.configs.oracle_config import OracleConfig


class MyOracle(BaseOracle):
    """Custom oracle backed by an internal model server."""

    async def ask(
        self,
        prompt: str,
        system_msgs: list[str] | None = None,
        images=None,
        stream: bool = True,
    ) -> str:
        # Build messages
        msgs = self._build_messages(prompt, system_msgs)
        # Call your API
        response = await my_api_client.chat(msgs)
        # Track token usage
        self._track_usage(
            response.prompt_tokens,
            response.completion_tokens,
        )
        return response.text

    async def ask_batch(
        self,
        prompts: list[str],
        system_msgs: list[str] | None = None,
    ) -> str:
        results = []
        for p in prompts:
            results.append(await self.ask(p, system_msgs))
        return "\n".join(results)
```

Register it with the Nexus:

```python
from genesis_pantheon.nexus import Nexus

nexus = Nexus()
nexus._oracle = MyOracle(config=OracleConfig(api_key="..."))
```

---

## Cost Tracking and Budget Management

Every call to `_track_usage(prompt_tokens, completion_tokens)` updates
the `BudgetLedger` attached to the oracle. The ledger accumulates
cost using a per-model pricing table.

```python
from genesis_pantheon.ledger import BudgetLedger
from genesis_pantheon.nexus import Nexus

nexus = Nexus()
nexus.budget.max_budget = 2.0    # $2 cap

# After a run:
print(f"Total spent: ${nexus.budget.total_cost:.4f}")
print(f"Budget remaining: ${nexus.budget.remaining:.4f}")
print(f"Exceeded: {nexus.budget.is_budget_exceeded()}")
```

When `is_budget_exceeded()` returns True inside a `Collective.run()`
loop, a `BudgetExceededError` is raised and the run terminates cleanly.

### Built-in pricing (USD per 1 000 tokens)

| Model | Input | Output |
|-------|-------|--------|
| `gpt-4o` | $0.005 | $0.015 |
| `gpt-4-turbo` | $0.010 | $0.030 |
| `gpt-3.5-turbo` | $0.0005 | $0.0015 |
| `claude-3-5-sonnet-20241022` | $0.003 | $0.015 |
| `claude-3-opus-20240229` | $0.015 | $0.075 |
| `gemini-1.5-pro` | $0.00125 | $0.005 |
| (other models) | $0.010 | $0.030 |

For Ollama (local) usage is tracked by token count but cost is $0.
