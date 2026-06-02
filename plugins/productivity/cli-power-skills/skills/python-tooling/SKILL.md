---
name: python-tooling
description: "Use when managing Python packages, virtual environments, or linting and formatting Python code"
allowed-tools: [Bash(uv*), Bash(ruff*), Read, Glob]
version: 1.0.0
author: ykotik
license: MIT
---

# Python Tooling

## When to Use
- Installing Python packages or creating virtual environments
- Running Python scripts with dependency isolation
- Linting Python code for errors, style issues, or import sorting
- Formatting Python code consistently
- Managing Python project dependencies (pyproject.toml)
- Auto-fixing Python lint issues

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **uv** | Ultra-fast Python package manager and venv tool (Rust, 10-100x faster than pip) | N/A (status messages) |
| **Ruff** | Extremely fast Python linter + formatter (Rust, replaces black + flake8 + isort) | `--output-format json` for JSON |

## Patterns

### Create a virtual environment
```bash
uv venv
```

### Create venv with specific Python version
```bash
uv venv --python 3.12
```

### Install packages into current venv
```bash
uv pip install requests pandas numpy
```

### Install from requirements.txt
```bash
uv pip install -r requirements.txt
```

### Run a script with auto-managed dependencies
```bash
uv run --with requests --with beautifulsoup4 script.py
```

### Run a script with inline dependencies (PEP 723)
```bash
uv run script.py
```
Where `script.py` has:
```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "rich"]
# ///
```

### Initialize a new Python project
```bash
uv init myproject
cd myproject
uv add requests
```

### Add a dependency to pyproject.toml
```bash
uv add fastapi uvicorn
```

### Add a dev dependency
```bash
uv add --dev pytest pytest-cov
```

### Lint Python code with JSON output
```bash
ruff check --output-format json .
```

### Lint and show only errors (no warnings)
```bash
ruff check --select E .
```

### Auto-fix all fixable lint issues
```bash
ruff check --fix .
```

### Format Python code
```bash
ruff format .
```

### Check formatting without changing files
```bash
ruff format --check .
```

### Lint specific rules (e.g., unused imports + isort)
```bash
ruff check --select F401,I .
```

## Pipelines

### New project → install deps → lint → format
```bash
uv init myproject && cd myproject
uv add requests fastapi
ruff check --fix .
ruff format .
```
Each stage: uv scaffolds project and installs deps, Ruff fixes lint issues, Ruff formats code.

### Lint → count issues by rule
```bash
ruff check --output-format json . | jq 'group_by(.code) | map({rule: .[0].code, count: length}) | sort_by(-.count)'
```
Each stage: Ruff lints to JSON, jq aggregates issue counts by rule code.

### Install from lockfile → run tests
```bash
uv sync && uv run pytest -v
```
Each stage: uv installs exact locked dependencies, runs pytest in the managed environment.

## Prefer Over
- Prefer **uv** over `pip` / `pip3` for package installation — 10-100x faster, better dependency resolution
- Prefer **uv** over `python -m venv` for virtual environments — faster creation, better Python version management
- Prefer **Ruff** over `black` + `flake8` + `isort` — single tool replaces all three, 10-100x faster
- Prefer **uv run** over global installs for one-off scripts — isolated environment, no pollution

## Do NOT Use When
- Project uses **poetry** or **pdm** with an existing lockfile — respect the existing toolchain, don't switch mid-project
- Project has a **Makefile** or **justfile** with established lint/format commands — use those instead
- Need to publish to PyPI — uv can build but `twine` or `flit` may be expected by the project
