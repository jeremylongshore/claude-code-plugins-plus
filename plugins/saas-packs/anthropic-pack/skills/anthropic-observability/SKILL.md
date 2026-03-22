---
name: anthropic-observability
description: |
  Monitor Claude API calls — log tokens, latency, costs, errors, and
  set up alerts for production Claude integrations.
  Trigger with "anthropic monitoring", "claude observability",
  "track claude usage", "anthropic logging".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, monitoring, observability]
---

# Anthropic Observability

## Overview
Every `messages.create` call should be instrumented. Track tokens, latency, cost, model, and errors.

## Logging Wrapper
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

async function trackedCreate(params: Anthropic.MessageCreateParams) {
  const start = performance.now();
  try {
    const message = await client.messages.create(params);
    const durationMs = Math.round(performance.now() - start);

    const log = {
      timestamp: new Date().toISOString(),
      model: message.model,
      input_tokens: message.usage.input_tokens,
      output_tokens: message.usage.output_tokens,
      cache_read_tokens: message.usage.cache_read_input_tokens || 0,
      duration_ms: durationMs,
      stop_reason: message.stop_reason,
      estimated_cost: estimateCost(message.model, message.usage),
    };
    console.log('anthropic_request', JSON.stringify(log));

    return message;
  } catch (err) {
    const durationMs = Math.round(performance.now() - start);
    console.error('anthropic_error', JSON.stringify({
      timestamp: new Date().toISOString(),
      model: params.model,
      error_type: err instanceof Anthropic.APIError ? err.error?.type : 'unknown',
      status: err instanceof Anthropic.APIError ? err.status : null,
      request_id: err instanceof Anthropic.APIError ? err.headers?.['request-id'] : null,
      duration_ms: durationMs,
    }));
    throw err;
  }
}

function estimateCost(model: string, usage: Anthropic.Usage): number {
  const rates: Record<string, [number, number]> = {
    'claude-opus-4-20250514': [15, 75],
    'claude-sonnet-4-20250514': [3, 15],
    'claude-haiku-4-5-20251001': [0.80, 4],
  };
  const [inputRate, outputRate] = rates[model] || [3, 15];
  return (usage.input_tokens * inputRate + usage.output_tokens * outputRate) / 1_000_000;
}
```

## Key Metrics to Track
| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Error rate | error logs | > 5% over 5 minutes |
| p95 latency | duration_ms | > 10s (Sonnet) |
| Daily cost | estimated_cost sum | > 2x daily average |
| 429 rate | error_type = rate_limit | > 10/minute |
| 529 rate | error_type = overloaded | > 5/minute |
| Token usage | input_tokens + output_tokens | > daily budget |

## Anthropic Console Monitoring
- **Usage dashboard**: console.anthropic.com → Usage
- **Spending limits**: console.anthropic.com → Settings → Limits
- **API logs**: Not available via API — use your own logging

## Resources
- [Usage Dashboard](https://console.anthropic.com/settings/usage)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)

## Next Steps
See `anthropic-incident-runbook` for when things go wrong.
