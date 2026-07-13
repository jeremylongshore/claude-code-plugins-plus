# langchain-cost-tuning — One-Pager

Control LangChain 1.0 AI spend with streaming-accurate token accounting, model tiering, provider-specific cache hit tuning, per-tenant budgets, and retry dedup — the five places where an untuned production app loses 40-80% of its bill to instrumentation error or the wrong default.

## The Problem

Cost dashboards wired to `on_llm_end` undercount by the full stream duration on Anthropic (P01) and miss retried calls that fire the callback twice (P25), so engineers believe spend is fine while `max_retries=6` quietly bills seven requests per flaky call (P30). Anthropic prompt-cache savings show up per-call but never aggregate — you cannot tell if caching is paying for itself (P04). `InMemoryCache` hashes only the prompt string and returns wrong answers when bound tools differ (P61); `RedisSemanticCache` ships with a 0.95 similarity threshold that hits less than 5% of the time (P62). Agents blow past `recursion_limit=25` on vague prompts and burn a session's budget before `GraphRecursionError` surfaces (P10).

## The Solution

Canonical token accounting via `AIMessage.usage_metadata` and `astream_events(version="v2")` for incremental attribution; request-ID tagging so the retry middleware does not double-bill (P25); a per-1M price-aware model-tiering decision tree (draft on `gpt-4o-mini` or `claude-haiku-4-5`, finalize on `claude-sonnet-4-6` or `gpt-4o`); Anthropic cache aggregation with break-even math; cache-key discipline that includes bound tools; semantic-cache threshold calibration procedure (0.85-0.90 after gold-set evaluation); and a per-tenant budget middleware with soft-and-hard caps backed by a Redis counter. Pinned to `langchain-core 1.0.x`; prices snapshotted 2026-04.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Senior engineers owning a LangChain 1.0 production app's AI spend — infra/platform engineers, FinOps partners, team leads investigating a cost regression |
| **What** | Streaming-accurate token meter, retry-dedup aggregator, model-tier router with per-1M price table, Anthropic cache aggregation + break-even analysis, semantic-cache threshold tuning procedure, per-tenant budget middleware, 4 deep references |
| **When** | After `langchain-performance-tuning` — when AI spend grows faster than traffic, after a cost regression lands, before onboarding a high-volume tenant, or when FinOps asks for per-tenant attribution |

## Key Features

1. **Streaming-accurate, retry-aware token meter** — Reads `AIMessage.usage_metadata` (canonical in 1.0, not `response_metadata["token_usage"]`), aggregates from `on_chat_model_stream` events, dedupes on `request_id` so retry middleware cannot double-bill (fixes P01 + P25 in one handler)
2. **Model-tiering decision tree with per-1M pricing** — Concrete draft-vs-finalize split with routes for intent classification, small vs large context, and high-stakes extraction; includes 2026-04 price snapshot (`gpt-4o-mini` $0.15/$0.60 per 1M in/out, `claude-sonnet-4-6` $3.00/$15.00) and cache-read discount multipliers (Anthropic 0.1x on reads)
3. **Per-tenant budget middleware + cache-key discipline** — Redis-backed counter with soft (warn) and hard (refuse) caps, grace period for in-flight calls; cache keys that include hashed tool schemas (P61); semantic-cache threshold tuning procedure (0.85-0.90 with gold-pair calibration, P62)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
