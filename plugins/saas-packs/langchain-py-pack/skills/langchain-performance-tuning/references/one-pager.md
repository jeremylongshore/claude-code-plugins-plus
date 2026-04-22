# langchain-performance-tuning — One-Pager

Make a working LangChain 1.0 / LangGraph 1.0 Python app faster and cheaper under real load without rewriting the chain.

## The Problem
Production chains miss p95 targets and burn budget because `.batch()` silently serializes (default `max_concurrency=1`), sync `invoke` calls block FastAPI event loops, `InMemoryChatMessageHistory` wipes on restart, and semantic caches at the default 0.95 threshold return under 5% hit rate. Teams blame "the LLM" when the bottleneck is configuration.

## The Solution
Turn on explicit batch concurrency per provider, switch every hot path to `ainvoke` / `astream_events(version="v2")`, move exact + semantic caches behind Redis with tuned thresholds on a golden set, and back chat history with `RedisChatMessageHistory` (TTL) or a LangGraph checkpointer. Result: 5-10x throughput on batch, TTFT under 1s, cache hit rate north of 30%, zero history loss on deploy.

## Who / What / When
| Aspect | Details |
|--------|---------|
| **Who** | Senior Python engineers, SREs, and platform leads operating LangChain 1.0 / LangGraph 1.0 chains or agents at scale. |
| **What** | Latency + throughput + cost tuning playbook: concurrency table, cache configuration, persistent history wiring, async-safety checklist, latency-breakdown template. |
| **When** | Chain already works functionally but misses p95 latency targets, throughput ceilings, cost budgets, or suffers history loss after a process restart. |

## Key Features
1. **Batch concurrency fix (P08)** — one-line config change (`max_concurrency=10`) that unlocks 5-10x throughput on `.abatch()`, with a per-provider RPM table and semaphore patterns for multi-worker saturation.
2. **Redis-backed history + cache** — `RedisChatMessageHistory` with TTL replaces in-process memory (P22), `RedisSemanticCache` with 0.85-0.90 threshold tuned on a golden set replaces the near-useless default 0.95 (P62).
3. **Async-safety playbook** — grep patterns to find sync-in-async (P48), FastAPI lifespan hooks for retriever pool cleanup (P59), the `BackgroundTasks`-for-streaming gotcha (P60), and `astream_events(version="v2")` for accurate TTFT instrumentation (P01).

## Quick Start
See [SKILL.md](../SKILL.md) for full instructions.
