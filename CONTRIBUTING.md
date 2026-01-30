# Contributing to GenesisPantheon

Thank you for considering a contribution! We welcome bug reports, feature
requests, documentation improvements, and pull requests.

---

## Code of Conduct

By participating in this project you agree to abide by the
[Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Please be respectful and constructive in all interactions.

---

## Development Setup

1. **Fork** the repository on GitHub and **clone** your fork:

   ```bash
   git clone https://github.com/<your-username>/GenesisPantheon.git
   cd GenesisPantheon
   ```

2. Create a virtual environment and install in editable mode with all
   development dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Copy the environment template and fill in your API keys:

   ```bash
   cp .env.example .env
   # edit .env with your keys
   ```

---

## Running Tests

```bash
pytest tests/ -v --cov=genesis_pantheon
```

To see a detailed HTML coverage report:

```bash
pytest tests/ --cov=genesis_pantheon --cov-report=html
open htmlcov/index.html
```

All PRs must keep coverage at or above **80 %**.

---

## Linting

We use [ruff](https://github.com/astral-sh/ruff) for linting and
formatting checks:

```bash
# Check for issues
ruff check genesis_pantheon/ tests/

# Auto-fix safe issues
ruff check --fix genesis_pantheon/ tests/
```

All PRs must pass `ruff check` with zero errors.

---

## Branch Naming Conventions

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes only |
| `refactor/` | Code refactoring without behaviour change |
| `test/` | Test additions or changes |
| `chore/` | Build, CI, dependency updates |

Examples: `feat/gemini-streaming`, `fix/budget-exceeded-edge-case`

---

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Examples:**

```
feat(oracles): add streaming support for Gemini oracle
fix(arena): handle exception when persona raises during run()
docs(readme): add quick-start code example
test(collective): cover budget-exceeded path
```

---

## Pull Request Checklist

Before marking your PR ready for review, confirm:

- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] Coverage is maintained at 80 %+
- [ ] `ruff check genesis_pantheon/ tests/` reports zero errors
- [ ] New public functions/classes include docstrings
- [ ] `CHANGELOG.md` is updated with a brief entry under `[Unreleased]`
- [ ] The PR description explains **what** changed and **why**
- [ ] Branch is up to date with `main`

---

## Reporting Issues

Please use the GitHub Issues tracker. Include:

- Python version and OS
- Minimal reproducible example
- Full traceback (if applicable)
- Steps to reproduce
