# langchain-ci-integration — One-Pager

Wire LangChain 1.0 / LangGraph 1.0 tests into a GitHub Actions pipeline with unit/integration/eval job separation, VCR cassette hygiene, and eval-regression merge gates.

## The Problem

A PR that passes locally fails in CI with `pytest` aborting during collection — the org runs `pytest -W error` and a provider SDK (e.g. `langchain_community.llms`) emits a `DeprecationWarning` on import (P45). Separately, the integration suite is flaky: a VCR cassette was recorded at `temperature=0` against Anthropic (still nucleus sampling per P05), drifted, and now mismatches on a snapshot assertion. The team also just discovered an `Authorization: Bearer sk-ant-...` header checked into a cassette file six weeks ago (P44). And the fake-model unit tests pass locally but fail in CI because a downstream callback asserts on `response_metadata["token_usage"]` which `FakeListChatModel` never emits (P43).

## The Solution

This skill wires four CI jobs that isolate failure modes: (1) a **unit** job using fake models + pinned `filterwarnings` to neutralize P45; (2) an **integration** job gated by label / cron / `RUN_INTEGRATION=1` that replays VCR cassettes with enforced `filter_headers` (P44); (3) an **eval-regression** job that runs the `langchain-eval-harness` harness on PR, posts a metric-delta comment, and blocks merge if aggregate regression >2% or per-example >5%; (4) a **pre-merge validator** that dry-run-loads all chains to catch `ImportError` migration breaks (complements `langchain-sdk-patterns`). Pre-commit hooks catch `sk-*` / `sk-ant-*` in cassettes before they ever reach the branch. Pinned to LangChain 1.0.x + LangGraph 1.0.x + GHA current (`actions/checkout@v4`, `actions/setup-python@v5`).

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python / DevOps engineers wiring a GitHub Actions (or equivalent) pipeline for a LangChain 1.0 / LangGraph 1.0 codebase — unit tests with fake models, gated integration tests with real API or VCR replay, eval regression merge gates |
| **What** | GHA workflow (matrix over Python versions, `uv` install, pip cache), 4 CI jobs (unit / integration / eval / lint), gate-policy table, pre-commit secret-scan + prompt-convention lint, 4 references (gha-workflow / integration-gating / eval-regression-gate / pre-commit-hooks) |
| **When** | Wiring a new repo, hardening an existing pipeline after a P44 cassette-leak incident, or after `langchain-local-dev-loop` (F23) makes the inner loop reliable and you need the outer loop |

## Key Features

1. **Four-job GHA workflow with targeted gates** — unit (<2 min, runs on every push), integration (<5 min, gated by `RUN_INTEGRATION=1` / label / nightly cron), eval (n≥100, blocks merge on regression >2% agg / >5% per-example), lint + dry-run chain loader
2. **VCR cassette hygiene baked in** — `filter_headers=["authorization", "x-api-key", "anthropic-version"]` enforced at record time, pre-commit hook greps for `sk-*` / `sk-ant-*` / `AIza*`, CI re-verifies (P44)
3. **`pytest -W error` survival kit** — `filterwarnings` config in `pyproject.toml` that neutralizes provider-SDK `DeprecationWarning` at collection time without masking real warnings (P45); pairs with F23's fake-model fixtures

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
