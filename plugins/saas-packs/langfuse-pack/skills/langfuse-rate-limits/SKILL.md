---
name: langfuse-rate-limits
description: |
  Implement Langfuse rate limiting, batching, and backoff patterns.
  Use when handling rate limit errors, optimizing trace ingestion,
  or managing high-volume LLM observability workloads.
  Trigger with phrases like "langfuse rate limit", "langfuse throttling",
  "langfuse 429", "langfuse batching", "langfuse high volume".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse Rate Limits

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Handle Langfuse rate limits gracefully with optimized batching, exponential backoff, concurrent request limiting, and sampling strategies for high-volume workloads.

## Prerequisites
- Langfuse SDK installed
- Understanding of async/await patterns
- High-volume trace workload

## Instructions

### Step 1: Configure Optimal Batching
Set `flushAt` to 50 events and `flushInterval` to 5000ms. Use 30s request timeout for large batches.

### Step 2: Implement Exponential Backoff
Create retry logic with configurable max retries (5), base delay (1s), max delay (30s), and jitter (500ms). Honor `Retry-After` headers. Only retry on 429 and 5xx errors.

### Step 3: Build Rate Limit-Aware Wrapper
Wrap the Langfuse client with a concurrency limiter (max 100 pending events). Queue excess requests and release capacity on completion.

### Step 4: Add Sampling for Ultra-High Volume
Implement configurable sampling (e.g., 10% of traces) with an `alwaysSample` predicate for errors and critical traces. Return no-op traces for unsampled requests.

### Step 5: Monitor Rate Limit Usage
Track `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers. Pre-emptively throttle when remaining requests drop below 10.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Optimized batching configuration
- Exponential backoff with jitter
- Concurrent request limiting
- Configurable sampling
- Rate limit monitoring

## Error Handling
| Header/Error | Description | Action |
|--------------|-------------|--------|
| 429 Too Many Requests | Rate limited | Use exponential backoff |
| Retry-After | Seconds to wait | Honor this value exactly |
| X-RateLimit-Remaining | Requests left | Pre-emptive throttling |
| 503 Service Unavailable | Overloaded | Back off significantly |

## Examples

### Rate Limit Tiers
| Tier | Events/min | Events/hour | Batch Size |
|------|------------|-------------|------------|
| Free | 1,000 | 10,000 | 15 |
| Pro | 10,000 | 100,000 | 50 |
| Enterprise | Custom | Custom | Custom |

### Queue-Based Rate Limiting
```typescript
import PQueue from "p-queue";
const queue = new PQueue({ concurrency: 10, interval: 1000, intervalCap: 50 });
async function queuedTrace(params) {
  return queue.add(() => langfuse.trace(params));
}
```

## Resources
- [Langfuse Rate Limits](https://langfuse.com/docs/api-reference)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Langfuse SDK Configuration](https://langfuse.com/docs/sdk)
