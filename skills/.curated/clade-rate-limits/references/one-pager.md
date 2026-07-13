# clade-rate-limits — One-Pager

Understand, handle, and optimize around Anthropic's rate limit tiers.

## The Problem

Anthropic enforces three concurrent limits — requests per minute, input tokens per minute, and output tokens per minute — that vary by spend tier. Without proper handling, 429 errors throttle your app and degrade user experience, especially during traffic spikes.

## The Solution

Identify your rate limit tier, configure SDK auto-retries, implement custom exponential backoff with jitter for high-throughput paths, and apply throughput optimization strategies like Message Batches (bypass limits entirely), prompt caching (cached tokens skip input TPM), and pre-counting tokens to avoid wasted requests.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building applications that make frequent or bursty Claude API calls |
| **What** | Rate limit tier reference, SDK retry config, custom backoff, throughput optimization |
| **When** | When hitting 429 errors, planning for scale, or optimizing API throughput |

## Key Features

1. **Tier reference table** — RPM, input TPM, and output TPM limits for Tiers 1-4 and Scale, plus response header field names
2. **Custom backoff with jitter** — Production-ready TypeScript implementation that reads the `retry-after` header and adds randomized jitter
3. **Throughput bypass strategies** — Message Batches API (no rate limits), prompt caching (cached tokens excluded from TPM), token pre-counting via `countTokens`

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
