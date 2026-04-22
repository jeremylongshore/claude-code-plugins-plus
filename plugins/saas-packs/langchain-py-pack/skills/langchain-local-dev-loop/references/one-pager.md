# langchain-local-dev-loop — One-Pager

Build a fast, deterministic local test loop for LangChain 1.0 / LangGraph 1.0 — `FakeListChatModel` fixtures, pytest config, VCR cassettes with key redaction, warning-filter policy.

## The Problem

An engineer writes `assert chain.invoke(input).content == "expected"` — it passes locally at `temperature=0` against Claude but fails intermittently in CI, because Anthropic's `temperature=0` still samples (P05). They switch to `FakeListChatModel` — now downstream token callbacks blow up with `KeyError: 'token_usage'` because the fake model emits no `response_metadata` (P43). They record a VCR cassette for an integration smoke test, and PR review flags `Authorization: Bearer sk-ant-...` committed into the fixture file (P44). On top of that, pytest collection itself fails before any test runs because `langchain_community` imports emit `DeprecationWarning` and the suite runs `-W error` (P45).

## The Solution

This skill installs a four-layer local dev loop: (1) `FakeListChatModel` and `FakeListLLM` for deterministic unit tests, with a subclass that synthesizes `response_metadata` so downstream token counters keep working; (2) pytest fixtures that wire the fake model into chains, agents, retrievers, and embedders; (3) VCR cassettes for integration tests with `filter_headers=["authorization","x-api-key","anthropic-version"]` and a pre-commit hook grepping for `sk-*` / `sk-ant-*`; (4) `pyproject.toml` `filterwarnings` policy plus an `@pytest.mark.integration` gate that defaults-skips unless `RUN_INTEGRATION=1`. LangGraph tests use `MemorySaver` with a fixed `thread_id` per test and assert state shape per node. Pinned to LangChain 1.0.x / LangGraph 1.0.x / pytest current / vcrpy current.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers and researchers adding tests to a LangChain 1.0 / LangGraph 1.0 codebase — unit, integration, smoke, or load |
| **What** | Fake-model fixtures (with metadata subclass), VCR cassette policy + key-leak pre-commit hook, `pyproject.toml` pytest/markers/filterwarnings skeleton, LangGraph per-test `thread_id` pattern, 4 references (fake-model-fixtures, vcr-cassette-hygiene, pytest-config, langgraph-test-patterns) |
| **When** | Adding tests to a new chain or graph; fixing a flaky test caused by provider non-determinism; making an integration test reproducible without real API calls; wiring CI for deterministic runs |

## Key Features

1. **`FakeListChatModel` + metadata-emitting subclass** — Deterministic responses cycled from a `responses=[...]` list; subclass overrides `_generate` to inject `generation_info={"token_usage": {...}}` so downstream callbacks reading `response_metadata["token_usage"]` keep working (P43 fix)
2. **VCR cassette hygiene** — `filter_headers` config removes `authorization` / `x-api-key` / `anthropic-version` before any cassette is written, paired with a pre-commit hook that greps cassette files for `sk-` / `sk-ant-` and blocks the commit on a match (P44 fix)
3. **`pyproject.toml` pytest skeleton** — `filterwarnings = ["ignore::DeprecationWarning:langchain_community.*"]` (P45 fix), `markers = ["integration: requires RUN_INTEGRATION=1"]`, env-var gate that defaults-skips integration tests unless `RUN_INTEGRATION=1`, per-provider `testpaths`

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
