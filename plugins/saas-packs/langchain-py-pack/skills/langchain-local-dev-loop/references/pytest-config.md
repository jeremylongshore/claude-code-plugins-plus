# Pytest Config Reference

Single-source `pyproject.toml` skeleton for LangChain 1.0 / LangGraph 1.0
projects. Covers warning policy (P45 fix), markers, integration gating,
coverage, and parallel execution.

## Minimum viable `[tool.pytest.ini_options]`

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-ra",                  # summary of all non-passing results
    "--strict-markers",     # unknown @pytest.mark.xyz → error
    "--strict-config",      # unknown config key → error
    "--tb=short",
    "-W", "error",          # warnings → failures; overrides via filterwarnings
]

markers = [
    "integration: hits real APIs or replays VCR cassettes (set RUN_INTEGRATION=1 to run)",
    "smoke: minimal healthcheck tests, run in every CI job",
    "slow: takes > 1s per test; skipped in quick runs via -m 'not slow'",
    "vcr: uses pytest-recording cassette replay",
]

filterwarnings = [
    "error",                                               # treat warnings as errors
    "ignore::DeprecationWarning:langchain_community.*",    # P45: noisy import-time DW
    "ignore::DeprecationWarning:pydantic.*",               # pydantic v1 compat warnings
    "ignore::PendingDeprecationWarning:langchain_core.*",
    "ignore::UserWarning:langsmith.*",                     # telemetry warnings
    "ignore:Pydantic serializer warnings:UserWarning",
]
```

## Why `filterwarnings = ["error", ...]` and not `addopts = ["-W", "error"]`

Both exist; they interact. Prefer `filterwarnings` because:

- `filterwarnings` is applied per-test (scoped properly)
- `-W error` in `addopts` fires at import / collection time, before filters
  attach — so any warning emitted during `collect` bypasses your ignores and
  crashes the suite (P45 symptom)

If you truly want warnings-as-errors at collection too, include `"error"` as
the *first* entry of `filterwarnings`, then the specific `ignore::...` rules
after it. Pytest evaluates rules top-to-bottom; specific overrides global.

## Integration gate — conftest.py

```python
# tests/conftest.py
import os
import pytest

def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.integration unless RUN_INTEGRATION=1 is set."""
    if os.getenv("RUN_INTEGRATION") == "1":
        return
    skip = pytest.mark.skip(reason="set RUN_INTEGRATION=1 to run integration tests")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
```

Usage:

```bash
pytest                                   # unit only (default, fast)
RUN_INTEGRATION=1 pytest -m integration  # integration only (VCR or live)
pytest -m "not slow"                     # everything except slow tests
pytest -m smoke                          # quickest subset for CI health
```

## Coverage config (optional but recommended)

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "src/*/migrations/*"]

[tool.coverage.report]
show_missing = true
skip_covered = false
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

Run with: `pytest --cov=src --cov-report=term-missing`

## Parallel execution

`pytest-xdist` runs tests across workers. Works cleanly with `FakeListChatModel`
because fakes are stateless per fixture. Does **not** work with shared VCR
cassettes (file-write contention on record; file-read concurrency is fine on
replay if `record_mode=none`).

```toml
[tool.pytest.ini_options]
addopts = [
    "-ra",
    "--strict-markers",
    "-n", "auto",  # enable xdist with worker-per-CPU
]
```

Exclude integration from xdist if cassettes collide:

```bash
pytest -n auto -m "not integration"
RUN_INTEGRATION=1 pytest -n 0 -m integration
```

## CI matrix pattern

```yaml
# .github/workflows/test.yml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest -n auto -m "not integration"

  integration:
    runs-on: ubuntu-latest
    needs: unit
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: RUN_INTEGRATION=1 pytest -m integration
        env:
          # Cassettes replay, no live keys needed.
          # Live nightly job uses secrets: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Common pytest flags for LangChain projects

| Flag | Use |
|------|-----|
| `--record-mode=none` | Force replay (CI default) |
| `--record-mode=once` | Record missing cassettes (local only) |
| `--block-network` (pytest-recording) | Fail any test that makes a real HTTP call — safety net |
| `-x` | Stop on first failure — great for debugging a cascade |
| `--lf` | Last-failed only — iterate fast after a regression |
| `-k "summarize"` | Substring-match test names |

## Gotchas

- `strict-markers` will fail the suite if a dev adds `@pytest.mark.newthing`
  without declaring it. That is the point — forces marker discipline.
- `pythonpath = ["src"]` lets you `import my_app` without an editable install.
  Remove it if you install with `pip install -e .`.
- `filterwarnings` is evaluated first-match; order matters. Put `"error"`
  first, then specific `ignore::...` rules.
