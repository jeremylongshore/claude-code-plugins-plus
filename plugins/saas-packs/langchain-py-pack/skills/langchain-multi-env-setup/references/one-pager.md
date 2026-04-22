# langchain-multi-env-setup — One-Pager

Build reliable dev / staging / prod isolation for LangChain 1.0 services — Pydantic `Settings` with `SecretStr`, GCP/AWS Secret Manager in prod, per-env prompt and model pinning, startup smoke tests that fail fast.

## The Problem

A team deploys a LangChain 1.0 service to staging with `python-dotenv` reading `.env.staging` into `os.environ`. Security runs `docker exec <pod> env` during a routine audit and sees `ANTHROPIC_API_KEY=sk-ant-api03-...` in plain text — sev-1 incident (pain P37). The same week, staging starts answering with prod-tuned prompts and hitting a model that was only rolled out to prod, because the config loader picked `LANGCHAIN_ENV=production` from a stale shell profile. Three failures chain together: secrets in process env, no env-aware config gate, and no startup validation that would have caught the wrong model id before the first request landed.

## The Solution

One `Settings` class built on `pydantic-settings`, `SecretStr` for every key, `Literal["dev","staging","prod"]` typed env switch, and fail-fast validation on import. Secret Manager (GCP / AWS / Vault) pulls values into the in-memory `Settings` object only — never back into `os.environ` — so `docker exec env` returns nothing sensitive. Per-env pins for `model_id`, `prompt_commit_hash`, `vector_index_name`, `checkpointer_url`, and rate-limit budgets live in the `Settings` class so dev / staging / prod diverge by data, not by conditional code. A startup smoke test under 10 seconds verifies every integration is reachable before the health check goes green.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers graduating a LangChain 1.0 service from `.env`-in-dev to real prod infra, or debugging a wrong-env config that shipped |
| **What** | `Settings` skeleton + Secret Manager integration + per-env model/prompt pinning + startup smoke test + env matrix |
| **When** | Before the first staging or prod deploy, or immediately after any incident where a prod secret leaked or a staging request hit the wrong model |

## Key Features

1. **Pydantic `Settings` with `SecretStr` and `Literal` env** — Fail-fast validation on startup, one class as the source of truth, `SecretStr` prevents accidental `print(settings)` leaks, `HttpUrl` validates checkpointer and observability endpoints
2. **Secret Manager pull into memory only** — GCP Secret Manager / AWS Secrets Manager / Vault client pulls keys at startup into the `Settings` object; never writes to `os.environ`, so `docker exec env` and `/proc/<pid>/environ` stay clean (fixes P37)
3. **Per-env pinning matrix** — `model_id`, `prompt_commit_hash`, `vector_index_name`, `checkpointer_url`, `max_cost_usd_per_day` all diverge per env inside `Settings`, not in `if env == "prod":` branches sprinkled through business logic
4. **Startup smoke test under 10 seconds** — One `validate_integrations()` call hits the model (1-token health ping), the vector store (`describe_index`), the checkpointer (`SELECT 1`), and the observability endpoint before the HTTP server accepts traffic

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
