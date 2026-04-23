# GitHub Actions Workflow Reference

Full, copy-pasteable `.github/workflows/tests.yml` with unit + integration + eval + lint jobs, caching strategy, secret injection, and matrix configuration. Pinned: `actions/checkout@v4`, `actions/setup-python@v5`.

## Complete workflow

```yaml
name: tests

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    # Nightly live-API re-record check, 06:00 UTC
    - cron: "0 6 * * *"
  workflow_dispatch:
    inputs:
      run_live:
        description: "Run integration tests against LIVE provider APIs"
        required: false
        default: "false"

concurrency:
  # Cancel in-progress runs for the same ref when a new push arrives.
  # Keep OFF for `main` pushes to preserve the nightly-cron trail.
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

permissions:
  contents: read
  pull-requests: write    # eval job posts comments
  checks: write

jobs:
  unit:
    name: unit (py${{ matrix.python }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
          cache-dependency-path: |
            pyproject.toml
            requirements*.txt

      - name: Install
        run: pip install -e ".[test]"

      - name: Run unit tests (-W error)
        run: pytest tests/unit/ -W error --timeout=30 -q --tb=short
        env:
          # Belt-and-suspenders: if anything tries to hit a real provider,
          # it will fail fast with a clear auth error instead of hanging.
          ANTHROPIC_API_KEY: "sk-ant-FAKE-UNIT-TEST-KEY"
          OPENAI_API_KEY: "sk-FAKE-UNIT-TEST-KEY"
          GOOGLE_API_KEY: "AIzaFAKE-UNIT-TEST-KEY"

  integration:
    name: integration (VCR ${{ env.VCR_MODE }})
    needs: unit
    if: >
      github.event_name == 'schedule' ||
      github.event_name == 'workflow_dispatch' ||
      contains(github.event.pull_request.labels.*.name, 'run-integration')
    runs-on: ubuntu-latest
    env:
      RUN_INTEGRATION: "1"
      VCR_MODE: ${{ github.event_name == 'schedule' && 'once' || 'none' }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: |
            pyproject.toml
            requirements*.txt

      - name: Install
        run: pip install -e ".[test,integration]"

      - name: Inject provider keys (nightly only)
        if: github.event_name == 'schedule' || github.event.inputs.run_live == 'true'
        run: |
          echo "ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}" >> "$GITHUB_ENV"
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> "$GITHUB_ENV"
          echo "GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}" >> "$GITHUB_ENV"

      - name: Run integration tests
        run: pytest tests/integration/ -W error --timeout=60 -q

      - name: Scan cassettes for leaked secrets (P44)
        run: python scripts/scan_cassettes.py tests/integration/cassettes/

      - name: Commit re-recorded cassettes (nightly only)
        if: github.event_name == 'schedule'
        run: |
          if ! git diff --quiet tests/integration/cassettes/; then
            git config user.name "ci-record-bot"
            git config user.email "ci@example.com"
            git add tests/integration/cassettes/
            git commit -m "chore(ci): re-record VCR cassettes (nightly)"
            git push
          fi

  eval:
    name: eval regression (n=100)
    needs: unit
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # need base ref for delta comparison

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -e ".[test,eval]"

      - name: Run regression eval
        run: python scripts/run_eval.py --baseline origin/${{ github.base_ref }} --head HEAD --n 100
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}

  lint:
    name: lint + dryrun
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: python scripts/dryrun_load_chains.py
      - run: python scripts/scan_cassettes.py tests/integration/cassettes/
```

## Caching strategy

- `cache: pip` with `cache-dependency-path` covering `pyproject.toml` and any `requirements*.txt`. The cache key rotates automatically when dependencies change.
- Do **not** cache `~/.cache/langchain` — LangChain's internal cache can contain provider responses, which means a stale eval result could be reused across runs.
- For `uv` users: swap `setup-python` + `pip install` for `astral-sh/setup-uv@v4` and `uv sync`. `uv` is ~3× faster on cold cache.

## Matrix notes

- Unit job runs on 3 Python versions to catch typing / syntax drift. Integration and eval stay single-version to control cost.
- `fail-fast: false` so a Python-3.10-specific failure does not hide a Python-3.12 failure.
- If you add Python 3.13 to the matrix, gate it behind `continue-on-error: true` until LangChain's minimum support lands.

## Required status checks

Configure in repo Settings → Branches → Branch protection rule for `main`:

- `unit (py3.10)`, `unit (py3.11)`, `unit (py3.12)` — required
- `lint + dryrun` — required
- `eval regression (n=100)` — required
- `integration (VCR none)` — **not** required (label-gated)

## Common failure modes

- `actions/setup-python@v5` cannot find the Python version → matrix has a typo (`3.12` vs `3.12.0`); use the `setup-python` MAJOR.MINOR format.
- `pip` cache misses every run → `cache-dependency-path` does not match the actual files in repo. Confirm with `ls pyproject.toml requirements*.txt`.
- Concurrency cancels the nightly cron → remove `main` from `cancel-in-progress`. The workflow above already does.
- `permissions` block missing → `GITHUB_TOKEN` cannot post PR comments. Add `pull-requests: write`.

## Cross-references

- Unit-test fixtures — see `langchain-local-dev-loop` (F23)
- VCR cassette *recording* workflow — see F23
- Eval harness internals — see `langchain-eval-harness`
- Prompt-convention lint rules — see `claude-prompt-conventions`
