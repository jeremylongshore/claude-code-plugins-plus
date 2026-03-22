---
name: langchain-rate-limits
description: |
  Implement LangChain rate limiting, retry strategies, and backoff.
  Use when handling API rate limits, controlling request throughput,
  or implementing concurrency-safe batch processing.
  Trigger: "langchain rate limit", "langchain throttling",
  "langchain backoff", "langchain retry", "API quota", "429 error".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, api, llm]

---
# LangChain Rate Limits

## Overview

Handle API rate limits gracefully with built-in retries, exponential backoff, concurrency control, provider fallbacks, and custom rate limiters.

## Provider Rate Limits (2026)

| Provider | Model | RPM | TPM |
|----------|-------|-----|-----|
| OpenAI | gpt-4o | 10,000 | 800,000 |
| OpenAI | gpt-4o-mini | 10,000 | 4,000,000 |
| Anthropic | claude-sonnet | 4,000 | 400,000 |
| Anthropic | claude-haiku | 4,000 | 400,000 |
| Google | gemini-1.5-pro | 360 | 4,000,000 |

RPM = requests/minute, TPM = tokens/minute. Actual limits depend on your tier.

## Strategy 1: Built-in Retry (Simplest)

```typescript
import { ChatOpenAI } from "@langchain/openai";

// Built-in exponential backoff on 429/500/503
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 5,      // retries with exponential backoff
  timeout: 30000,     // 30s timeout per request
});

// This automatically retries on rate limit errors
const response = await model.invoke("Hello");
```

## Strategy 2: Concurrency-Controlled Batch

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("Summarize: {text}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", maxRetries: 3 }))
  .pipe(new StringOutputParser());

const inputs = articles.map((text) => ({ text }));

// batch() with maxConcurrency prevents flooding the API
const results = await chain.batch(inputs, {
  maxConcurrency: 5,  // max 5 parallel requests
});
```

## Strategy 3: Provider Fallback on Rate Limit

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const primary = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 2,
  timeout: 10000,
});

const fallback = new ChatAnthropic({
  model: "claude-sonnet-4-20250514",
  maxRetries: 2,
});

// Automatically switches to Anthropic if OpenAI rate-limits
const resilientModel = primary.withFallbacks({
  fallbacks: [fallback],
});

const chain = prompt.pipe(resilientModel).pipe(new StringOutputParser());
```

## Strategy 4: Custom Rate Limiter

```typescript
class TokenBucketLimiter {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private maxTokens: number,    // bucket size
    private refillRate: number,   // tokens per second
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();
    while (this.tokens < 1) {
      const waitMs = (1 / this.refillRate) * 1000;
      await new Promise((r) => setTimeout(r, waitMs));
      this.refill();
    }
    this.tokens -= 1;
  }

  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }
}

// Usage: 100 requests per minute
const limiter = new TokenBucketLimiter(100, 100 / 60);

async function rateLimitedInvoke(chain: any, input: any) {
  await limiter.acquire();
  return chain.invoke(input);
}
```

## Strategy 5: Async Batch with Semaphore

```typescript
async function batchWithSemaphore<T>(
  chain: { invoke: (input: any) => Promise<T> },
  inputs: any[],
  maxConcurrent = 5,
): Promise<T[]> {
  let active = 0;
  const results: T[] = [];
  const queue = [...inputs.entries()];

  return new Promise((resolve, reject) => {
    function next() {
      while (active < maxConcurrent && queue.length > 0) {
        const [index, input] = queue.shift()!;
        active++;
        chain.invoke(input)
          .then((result) => {
            results[index] = result;
            active--;
            if (queue.length === 0 && active === 0) resolve(results);
            else next();
          })
          .catch(reject);
      }
    }
    next();
  });
}

// Process 100 items, 5 at a time
const results = await batchWithSemaphore(chain, inputs, 5);
```

## Python Equivalent

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableConfig

# Built-in retry
llm = ChatOpenAI(model="gpt-4o-mini", max_retries=5, request_timeout=30)

# Fallback
primary = ChatOpenAI(model="gpt-4o-mini", max_retries=2)
fallback = ChatAnthropic(model="claude-sonnet-4-20250514")
robust = primary.with_fallbacks([fallback])

# Batch with concurrency control
results = chain.batch(
    [{"text": t} for t in texts],
    config=RunnableConfig(max_concurrency=10),
)
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `429 Too Many Requests` | Rate limit hit | Increase `maxRetries`, reduce `maxConcurrency` |
| `Timeout` | Response too slow | Increase `timeout`, check network |
| `QuotaExceeded` | Monthly limit hit | Upgrade tier or switch provider |
| Batch partially fails | Some items rate limited | Use `.batch()` with `returnExceptions: true` |

## Resources

- [OpenAI Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [Anthropic Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [LangChain Batch Processing](https://js.langchain.com/docs/how_to/batch/)

## Next Steps

Proceed to `langchain-security-basics` for security best practices.
