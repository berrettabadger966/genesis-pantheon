# Changelog

All notable changes to GenesisPantheon are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2024-12-01

### Added

- **Core framework**
  - `Signal` — typed message envelope with pub/sub routing
  - `SignalQueue` — async-safe queue for inter-persona communication
  - `Directive` — abstract base for all agent actions
  - `Persona` — autonomous agent with observe/think/act loop and
    three react modes: `REACT`, `BY_ORDER`, `PLAN_AND_ACT`
  - `Arena` — concurrent message broker and execution environment
  - `Collective` — high-level orchestrator with round loop and budget
    enforcement
  - `Nexus` — shared dependency-injection context (config + oracle +
    budget)
  - `BudgetLedger` — token-usage tracking and USD spend capping

- **Oracle layer**
  - `BaseOracle` — abstract LLM adapter interface
  - `OpenAIOracle` — OpenAI API adapter with streaming support
  - `AzureOracle` — Azure OpenAI adapter
  - `AnthropicOracle` — Anthropic Claude adapter
  - `GeminiOracle` — Google Gemini adapter
  - `OllamaOracle` — local Ollama adapter
  - `HumanOracle` — interactive human-in-the-loop adapter
  - `OracleConfig` — unified provider configuration model
  - `OracleRegistry` — factory for creating oracle instances by type

- **Built-in personas**
  - `VisionDirector` — requirements to PRD
  - `SystemArchitect` — PRD to system design
  - `MissionCoordinator` — design to task files
  - `CodeCrafter` — task files to Python code (with optional
    self-review via `code_review=True`)
  - `QualityGuardian` — code to test suites + execution
  - `InsightHunter` — user query to research report

- **Built-in directives**
  - `UserDirective`, `DraftVision`, `DesignSystem`, `ReviewDesign`
  - `AllocateTasks`, `CraftCode`, `ReviewCode`, `CondenseCode`
  - `GenerateTests`, `ExecuteCode`, `DiagnoseError`
  - `AddRequirement`

- **Configuration**
  - `Blueprint` — YAML/env-driven configuration model
  - `OracleConfig` — per-provider LLM settings with pricing table

- **CLI** (`genesispan`)
  - `launch` — run a mission from the command line
  - `init-config` — generate a default `blueprint.yaml`
  - `list-oracles` — enumerate supported providers
  - `version` — print the framework version

- **Chronicle** — append-only signal history with filtering by action

- **Developer tooling**
  - Full test suite: 321 tests, 80 %+ coverage
  - `ruff` linting with zero errors
  - GitHub Actions CI (lint + test matrix: Python 3.10 / 3.11 / 3.12)
  - `Makefile` with `install`, `dev`, `test`, `lint`, `clean` targets
  - Five runnable examples in `examples/`
  - Documentation in `docs/` covering architecture, configuration,
    personas, and oracles

[Unreleased]: https://github.com/daniell-olaitan/GenesisPantheon/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/daniell-olaitan/GenesisPantheon/releases/tag/v0.1.0
