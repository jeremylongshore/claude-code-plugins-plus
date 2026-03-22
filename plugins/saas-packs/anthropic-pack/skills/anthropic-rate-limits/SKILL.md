---
name: anthropic-rate-limits
description: |
  Handle Anthropic rate limits — understand tiers, implement backoff,
  optimize throughput, and monitor usage.
  Trigger with "anthropic rate limit", "claude 429", "anthropic throttling",
  "anthropic usage limits", "claude tokens per minute".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, rate-limits]
---

# Anthropic Rate Limits

## Overview
Anthropic enforces three types of limits: requests per minute (RPM), input tokens per minute (TPM), and output tokens per minute. Limits depend on your spend tier.

## Rate Limit Tiers

| Tier | Qualification | RPM | Input TPM | Output TPM |
|------|--------------|-----|-----------|------------|
| Tier 1 | Free | 50 | 40,000 | 8,000 |
| Tier 2 | $40+ spend | 1,000 | 80,000 | 16,000 |
| Tier 3 | $200+ spend | 2,000 | 160,000 | 32,000 |
| Tier 4 | $400+ spend | 4,000 | 400,000 | 80,000 |
| Scale | Custom | Custom | Custom | Custom |

> **Check your tier:** console.anthropic.com → Settings → Limits

## Response Headers
Every API response includes rate limit headers:
```
anthropic-ratelimit-requests-limit: 1000
anthropic-ratelimit-requests-remaining: 998
anthropic-ratelimit-requests-reset: 2025-01-01T00:01:00Z
anthropic-ratelimit-tokens-limit: 80000
anthropic-ratelimit-tokens-remaining: 79500
anthropic-ratelimit-tokens-reset: 2025-01-01T00:01:00Z
retry-after: 5
```

## Built-In SDK Retries
The SDK automatically retries 429 and 529 errors with exponential backoff:
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  maxRetries: 3, // default: 2. Set to 0 to disable.
});
```

## Custom Backoff
```typescript
async function callWithBackoff(params: Anthropic.MessageCreateParams, maxRetries = 5) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await client.messages.create(params);
    } catch (err) {
      if (err instanceof Anthropic.RateLimitError) {
        const retryAfter = Number(err.headers?.['retry-after'] || 2 ** attempt);
        const jitter = Math.random() * 1000;
        console.log(`Rate limited. Retry in ${retryAfter}s (attempt ${attempt + 1})`);
        await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      } else {
        throw err;
      }
    }
  }
  throw new Error('Exceeded max retries');
}
```

## Throughput Optimization
| Strategy | Impact |
|----------|--------|
| Use Message Batches API | Bypasses rate limits entirely (async, 24h SLA) |
| Use prompt caching | Cached tokens don't count toward input TPM |
| Use smaller models for simple tasks | Lower token counts = more requests per minute |
| Pre-count tokens with `countTokens` | Avoid wasted requests that will fail |
| Queue and batch requests | Smooth out bursts |

## Token Counting
```typescript
// Count before sending — avoid burning RPM on requests that'll fail
const count = await client.messages.countTokens({
  model: 'claude-sonnet-4-20250514',
  messages,
  system: systemPrompt,
});
console.log(`This request will use ${count.input_tokens} input tokens`);
```

## Python
```python
import anthropic
import time

client = anthropic.Anthropic(max_retries=5)

# Or manual handling:
try:
    message = client.messages.create(...)
except anthropic.RateLimitError as e:
    retry_after = float(e.response.headers.get("retry-after", 5))
    time.sleep(retry_after)
```

## Resources
- [Rate Limits Docs](https://docs.anthropic.com/en/api/rate-limits)
- [Message Batches](https://docs.anthropic.com/en/api/creating-message-batches) — no rate limits
- [Token Counting](https://docs.anthropic.com/en/api/counting-tokens)

## Next Steps
See `anthropic-cost-tuning` for cost optimization strategies.
