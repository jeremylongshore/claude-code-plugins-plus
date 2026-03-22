# clade-performance-tuning — One-Pager

Optimize Claude API latency with streaming, prompt caching, model routing, and parallel requests.

## The Problem

Claude API latency has two components -- time to first token (TTFT) and tokens per second (TPS) -- and each requires different optimization strategies. Without tuning, applications suffer from slow perceived response times (waiting for full generation before displaying), wasted TTFT on large uncached system prompts, and serial execution of independent API calls that could run in parallel.

## The Solution

This skill provides six concrete optimization strategies with latency benchmarks: always-on streaming for instant perceived responsiveness, prompt caching to slash TTFT for large system prompts, Haiku routing for speed-critical classification tasks (200ms TTFT), client instance reuse to avoid connection overhead, parallel requests via Promise.all, and output token minimization through concise system prompts and tight max_tokens.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building user-facing applications where Claude response latency matters |
| **What** | Applies six latency optimization strategies targeting TTFT and TPS across the request lifecycle |
| **When** | When users complain about slow responses, or before launching a latency-sensitive feature |

## Key Features

1. **Prompt Caching** — Cache large system prompts with ephemeral cache_control to drop TTFT from ~2s to ~500ms on cache hits
2. **Model Routing to Haiku** — Route classification, extraction, and routing decisions to Haiku (200ms TTFT, 150 TPS) while reserving Sonnet/Opus for complex tasks
3. **Parallel Request Execution** — Fire independent Claude calls concurrently via Promise.all instead of awaiting them sequentially

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
