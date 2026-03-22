---
name: anthropic-reliability-patterns
description: |
  Build fault-tolerant Claude integrations — retries, circuit breakers,
  fallbacks, timeouts, and graceful degradation.
  Trigger with "anthropic reliability", "claude fault tolerance",
  "anthropic circuit breaker", "claude fallback".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, reliability, resilience]
---

# Anthropic Reliability Patterns

## Overview
Core functionality and patterns for anthropic-reliability-patterns.


## Built-In SDK Retries
The SDK retries 429 (rate limit) and 529 (overloaded) automatically:
```typescript
const client = new Anthropic({
  maxRetries: 3, // default: 2
  timeout: 120_000, // 2 minutes
});
```

## Model Fallback Chain
```typescript
const FALLBACK_CHAIN = ['claude-sonnet-4-20250514', 'claude-haiku-4-5-20251001'];

async function callWithFallback(params: Anthropic.MessageCreateParams) {
  for (const model of FALLBACK_CHAIN) {
    try {
      return await client.messages.create({ ...params, model });
    } catch (err) {
      if (err instanceof Anthropic.APIError && err.status >= 500) {
        console.warn(`${model} failed (${err.status}), trying next...`);
        continue;
      }
      throw err; // Don't retry client errors (4xx)
    }
  }
  throw new Error('All models failed');
}
```

## Circuit Breaker
```typescript
class ClaudeCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold = 5;
  private readonly resetMs = 60_000;

  async call(params: Anthropic.MessageCreateParams) {
    if (this.failures >= this.threshold && Date.now() - this.lastFailure < this.resetMs) {
      throw new Error('Circuit open — Claude API unavailable');
    }

    try {
      const result = await client.messages.create(params);
      this.failures = 0;
      return result;
    } catch (err) {
      if (err instanceof Anthropic.APIError && err.status >= 500) {
        this.failures++;
        this.lastFailure = Date.now();
      }
      throw err;
    }
  }
}
```

## Graceful Degradation
```typescript
async function getResponse(userInput: string): Promise<string> {
  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      messages: [{ role: 'user', content: userInput }],
    });
    return message.content[0].text;
  } catch (err) {
    // Return cached/static response instead of failing
    console.error('Claude unavailable, using fallback');
    return "I'm temporarily unable to process your request. Please try again shortly.";
  }
}
```

## Timeout Handling
```typescript
const client = new Anthropic({
  timeout: 30_000, // 30s for most requests
});

// Override per-request for long-running tasks
const message = await client.messages.create(params, {
  timeout: 120_000, // 2 minutes for complex prompts
});
```

## Output
- Successful operation confirmed
- Results logged to console

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| API Error | Check error type and status code | See `anthropic-common-errors` |

## Examples
See code blocks above for complete examples.

## Resources
- [Error Types](https://docs.anthropic.com/en/api/errors)
- [SDK Retries](https://github.com/anthropics/anthropic-sdk-typescript#retries)

## Next Steps
See `anthropic-policy-guardrails` for content safety patterns.

## Prerequisites
- Completed `anthropic-reliability-install-auth` setup
- Valid API credentials configured

## Instructions
Follow the steps in the sections above.
