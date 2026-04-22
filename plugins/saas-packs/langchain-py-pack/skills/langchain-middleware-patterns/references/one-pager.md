# langchain-middleware-patterns — One-Pager

Compose LangChain 1.0 and LangGraph 1.0 middleware — PII redaction, guardrails, token budgets, caching, retry — in the correct order so cache keys never leak PII and retries never double-bill.

## The Problem

Tenant A sends a prompt containing their customer's email. The cache middleware ran before the redaction middleware, so the raw PII-containing prompt became part of the cache key. Tenant B sends a same-shape prompt, hits the cache, and gets back Tenant A's response — email and all. Same class of incident: retry middleware re-runs the model call after a 429, both attempts emit `on_llm_end`, the token counter double-bills and the per-tenant budget trips twice as fast as it should.

## The Solution

There is a canonical middleware order — **redact → guardrail → budget → cache → retry → model** — and every pair of adjacent middlewares has a named invariant that breaks if you swap them. This skill defines the order, gives production-grade implementations for each of the six layers (with cache-key hashing that includes bound tools per P61, and retry telemetry that tags requests with a `request_id` so aggregators dedupe per P25), and provides an integration test template that asserts the ordering invariant on every build. Pinned to LangChain 1.0.x and LangGraph 1.0.x.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Senior Python engineers hardening LangChain chains and LangGraph agents for multi-tenant production — adding PII redaction, prompt-injection guardrails, per-tenant token budgets, tool-aware caching, and telemetry-safe retry |
| **What** | Canonical 6-layer middleware order, an ordering-invariants matrix covering every adjacent pair, six reference implementations, cache-key hashing that covers `prompt + bound-tools + tenant`, retry telemetry tagging that avoids double-count, and an integration test pattern that proves the order holds |
| **When** | Going to production (multi-tenant or PII-handling), hardening an agent against prompt injection, debugging a cache-poisoning or double-billed-retry incident, or auditing an existing chain before a compliance review |

## Key Features

1. **Canonical ordering invariant: redact → guardrail → budget → cache → retry → model** — every pair has a named failure mode (cache-before-redact = PII in cache; retry-before-budget = budget bypassed; guardrail-after-cache = injection cached; cache-before-budget = budget bypassed on hit), and the invariant is enforced by integration test
2. **Cache-key hash covers `prompt + bound-tools + tenant_id`, not just prompt** — P61 says `InMemoryCache()` hashes prompt string only, so two chains with different tool lists return the same cached response; the reference cache middleware `blake2b`-hashes the full tool schema set plus the tenant id so tools and tenants never collide
3. **Retry telemetry deduped by `request_id`** — P25 double-count is fixed by attaching a stable `request_id` on first call and deduping in the token aggregator; production chains typically run 4-6 middleware layers with <1ms overhead per layer (bench: p50 0.3ms, p99 0.9ms on 100-request sample)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
