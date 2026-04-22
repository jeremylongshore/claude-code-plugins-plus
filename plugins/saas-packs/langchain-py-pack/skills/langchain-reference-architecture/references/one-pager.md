# langchain-reference-architecture — One-Pager

A reference layered architecture for production LangChain 1.0 / LangGraph 1.0 services that prevents the chain-in-route-handler, import-time-retriever, and per-env-checkpointer tangles that strangle 8-month-old codebases.

## The Problem

By month eight, a LangChain service that started as a single FastAPI route has accumulated twelve chain definitions inlined in handlers, three retrievers constructed at module-import scope, `max_retries=6` hardcoded in four places, no tenant scoping, a `RunnableWithMessageHistory` backed by `InMemoryChatMessageHistory` that loses every conversation on pod restart (P22), and a retriever that was bound to `tenant_id="acme"` at import and now returns Acme's documents to every other tenant (P33). A code review turns up the P33 leak on a Friday. The fix is not "move one line" — the fix is an architecture that made the wrong thing hard to write in the first place.

## The Solution

Five layers with a strict dependency direction — `app/` (FastAPI routes) → `services/` (chain and graph definitions) → `adapters/` (LLM factory, retriever factory, vendor clients) → `config/` (Pydantic `Settings`) → `domain/` (Pydantic models, typed state). Chains take their dependencies through constructor arguments, not imports. An LLM factory is the single source of version-safe defaults (timeout 30s, max_retries 2, cache). A chain/graph registry replaces scattered import sites with `registry.get("support_agent", tenant=...)`. Retriever and tool factories are keyed by request — not module — scope, so P33 cannot happen. Config is one Pydantic `Settings` class with `SecretStr` for keys and `Literal[...]` for env names. Middleware composition order (redact → cache → model, per L31) is wired once in the DI layer. Checkpointer selection is per env: `MemorySaver` in dev, `PostgresSaver` in staging and prod. Import-linter enforces the layer graph in CI.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Tech leads and architects designing a new LangChain 1.0 / LangGraph 1.0 service, or refactoring a tangled chain, or onboarding a team to existing code |
| **What** | Layered directory tree, LLM factory, chain/graph registry, per-request retriever and tool factories, Pydantic `Settings` module, middleware composition order, per-env checkpointer selection, import-linter config, testing strategy, 4 deep references |
| **When** | At project kickoff (before file 3), or at the code review that surfaces P22 / P33 / scattered `max_retries=6`, or during onboarding — this skill is the paper map that prevents the 30-file mess |

## Key Features

1. **5-layer dependency rule enforced by import-linter** — `app` → `services` → `adapters` → `config` → `domain`, never the reverse; CI fails the PR if a route imports a vendor client directly, so the tangles never accumulate
2. **LLM factory + chain/graph registry** — Single source of version-safe defaults (`timeout=30`, `max_retries=2`) reused by every chain; registry exposes `registry.get("support_agent", tenant=...)` so there is one place to look, not twelve
3. **Per-request retriever/tool factories + per-env checkpointer** — Retriever construction time stays under 5ms so per-request construction is cheap; P33 is architecturally impossible because no retriever is ever bound at import; `MemorySaver` in dev, `PostgresSaver` in staging/prod means P22 is impossible in the environments that matter

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
