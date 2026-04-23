# langchain-rate-limits — One-Pager

Rate-limit LangChain 1.0 calls correctly across multi-worker deployments — Redis-backed limiters, `asyncio.Semaphore`, narrow exception whitelists, and provider-specific throttle handling.

## The Problem

`InMemoryRateLimiter(requests_per_second=10)` is per-process. A team deploying 10 Cloud Run workers each configured at 10 RPS sends **100 RPS** to Anthropic and trips the 50 RPM tier-1 ceiling within 30 seconds. Default `max_retries=6` on `ChatOpenAI` bills one logical call as up to **seven** requests on flaky networks. Anthropic's RPM limit counts cached and uncached calls separately — a 429 on cache writes can fire while the input-token budget still shows headroom. And the default `.with_fallbacks([backup])` catches `KeyboardInterrupt` on Python <3.12 — Ctrl+C during a retry storm silently hands off to the fallback chain and keeps billing.

## The Solution

This skill walks through measuring actual demand before picking a limit; when `InMemoryRateLimiter` is safe (single-process dev) and when it is dangerous (multi-worker prod); a Redis-backed limiter pattern for cluster-wide enforcement; `asyncio.Semaphore` for per-worker in-flight caps; the narrow `exceptions_to_handle` tuple that preserves `KeyboardInterrupt`; `max_retries=2` vs `max_retries=6` math; and a provider-specific limit taxonomy (RPM, ITPM, OTPM, concurrent, cached-vs-uncached) with a 2026-04 tier-snapshot you must re-verify before shipping. Pinned to LangChain 1.0.x.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers handling production LangChain 1.0 throughput — horizontal scaling, provider tier management, 429 storms |
| **What** | Demand measurement, limiter-selection decision tree, Redis-backed limiter pattern, `asyncio.Semaphore` cap, narrow fallback whitelist, provider tier matrix (Anthropic / OpenAI / Gemini), backoff shape, 4 references |
| **When** | When you see 429s in production, before scaling from 1 worker to N, when upgrading to a higher provider tier, or when `InMemoryRateLimiter` is already in your codebase and you have not audited it for multi-process deployment |

## Key Features

1. **Redis-backed rate limiter pattern** — Cluster-wide enforcement via atomic Lua script or Redis 6.2+ GCRA (`CL.THROTTLE`); per-tenant keys; sliding vs fixed window tradeoffs; keeps N workers at a combined target RPS instead of N×RPS
2. **Narrow `exceptions_to_handle` tuple that preserves `KeyboardInterrupt`** — `(RateLimitError, APITimeoutError, APIConnectionError)` per provider, never `(Exception,)`; cross-provider fallback with provider-specific error imports; P07-safe on Python 3.10 and 3.11
3. **Provider tier matrix with cached-vs-uncached separation** — Anthropic (free 5 RPM, tier-1 50 RPM, tier-4 4K RPM) with separate cache-read/write accounting; OpenAI tiers 1-5; Gemini free vs paid; 2026-04 snapshot pinned, with "re-verify before shipping" call-out

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
