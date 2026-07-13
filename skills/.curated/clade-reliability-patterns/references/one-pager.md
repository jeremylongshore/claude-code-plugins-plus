# clade-reliability-patterns — One-Pager

Fault-tolerant Claude integrations with retries, circuit breakers, fallbacks, and graceful degradation.

## The Problem

Claude API calls can fail from rate limits (429), server overload (529), network issues, or outages. Without reliability patterns, a single API failure cascades into broken user experiences, and repeated retries against a struggling endpoint make things worse.

## The Solution

Layer multiple resilience strategies: SDK built-in retries for transient errors, a model fallback chain (Sonnet to Haiku) for server-side failures, a circuit breaker that stops hammering the API after repeated failures, graceful degradation returning cached or static responses during outages, and per-request timeout configuration for different use cases.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Engineers building high-availability applications on top of Claude |
| **What** | SDK retry config, model fallback chain, circuit breaker class, degradation handler, timeout tuning |
| **When** | When your app needs to stay functional during API instability or outages |

## Key Features

1. **Model fallback chain** — Automatically tries cheaper models (Sonnet to Haiku) when the primary model returns 5xx errors, with explicit 4xx pass-through
2. **Circuit breaker** — Tracks consecutive failures and opens the circuit after a threshold, preventing cascading load on a degraded API for a configurable cooldown period
3. **Graceful degradation** — Returns static or cached responses when Claude is completely unavailable, keeping the app functional instead of erroring out

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
