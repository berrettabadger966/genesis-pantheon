# Configuration Reference

GenesisPantheon is configured through a YAML blueprint file, environment
variables, or a combination of both. Environment variables always take
precedence over file-based values.

---

## Config File

Create `~/.genesis_pantheon/blueprint.yaml` (the default location) or
point to a custom path with `GP_CONFIG_PATH`:

```yaml
llm:
  api_type: openai          # openai | azure | anthropic | gemini | ollama
  model: gpt-4o
  api_key: "${OPENAI_API_KEY}"
  base_url: ""              # override endpoint (Azure, Ollama, proxy)
  api_version: ""           # Azure only
  temperature: 0.0          # 0.0–2.0
  max_tokens: 4096
  stream: true
  timeout: 300              # seconds
  max_retries: 3
  calc_usage: true          # track token usage in BudgetLedger

project:
  path: /tmp/genesis_output
  name: my_project

budget:
  max_budget: 10.0          # USD cap; 0.0 = unlimited
```

---

## Oracle Config Keys

### OpenAI

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_type` | str | `openai` | Must be `"openai"` |
| `api_key` | str | — | OpenAI API key |
| `model` | str | `gpt-4-turbo` | Model name |
| `base_url` | str | `""` | Optional custom endpoint |
| `temperature` | float | `0.0` | Sampling temperature |
| `max_tokens` | int | `4096` | Max completion tokens |
| `stream` | bool | `true` | Enable streaming |

### Azure OpenAI

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_type` | str | — | Must be `"azure"` |
| `api_key` | str | — | Azure OpenAI key |
| `base_url` | str | — | `https://<resource>.openai.azure.com/` |
| `api_version` | str | — | e.g. `"2024-02-01"` |
| `model` | str | — | Deployment name |
| `temperature` | float | `0.0` | Sampling temperature |
| `max_tokens` | int | `4096` | Max completion tokens |

### Anthropic Claude

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_type` | str | — | Must be `"anthropic"` |
| `api_key` | str | — | Anthropic API key |
| `model` | str | `claude-3-5-sonnet-20241022` | Model name |
| `max_tokens` | int | `4096` | Max completion tokens |
| `temperature` | float | `0.0` | Sampling temperature |

### Google Gemini

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_type` | str | — | Must be `"gemini"` |
| `api_key` | str | — | Google AI Studio key |
| `model` | str | `gemini-1.5-pro` | Model name |
| `max_tokens` | int | `4096` | Max output tokens |
| `temperature` | float | `0.0` | Sampling temperature |

### Ollama (local)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_type` | str | — | Must be `"ollama"` |
| `base_url` | str | `http://localhost:11434` | Ollama server URL |
| `model` | str | `llama3.2` | Local model name |
| `api_key` | str | `ollama` | Placeholder (not used) |
| `temperature` | float | `0.0` | Sampling temperature |

---

## Environment Variables

Copy `.env.example` to `.env` in the project root:

```dotenv
# GenesisPantheon Environment Configuration

# --- OpenAI ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# --- Azure OpenAI ---
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# --- Anthropic ---
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# --- Google Gemini ---
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-1.5-pro

# --- Ollama ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# --- Global limits ---
GP_MAX_BUDGET=10.0
GP_MAX_TOKENS=4096
```

The framework uses `pydantic-settings` to load these values
automatically. Variables prefixed with the provider name map to the
corresponding `OracleConfig` fields.

---

## Collective Configuration

Budget and timeout controls live in the `Collective` and `BudgetLedger`:

```python
from genesis_pantheon.collective import Collective
from genesis_pantheon.nexus import Nexus

nexus = Nexus()
nexus.budget.max_budget = 5.0        # USD hard cap

collective = Collective(context=nexus, budget=5.0)
collective.allocate_budget(5.0)      # can also be set at runtime

signals = await collective.run(
    mission="Analyse the data pipeline",
    n_rounds=5,                      # max execution rounds
)
```

`BudgetLedger` tracks:

- `total_cost` — cumulative USD spent
- `max_budget` — cap (0.0 = unlimited)
- `is_budget_exceeded()` — returns True when `total_cost >= max_budget`

When the budget is exceeded a `BudgetExceededError` is raised and the
run halts cleanly.

---

## Generating a Default Config

```bash
genesispan init-config
```

This writes a starter `blueprint.yaml` to `~/.genesis_pantheon/` with
all fields commented and documented.
