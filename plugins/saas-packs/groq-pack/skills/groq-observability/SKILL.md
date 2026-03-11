---
name: groq-observability
description: |
  Set up comprehensive observability for Groq integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Groq operations, setting up dashboards,
  or configuring alerting for Groq integration health.
  Trigger with phrases like "groq monitoring", "groq metrics",
  "groq observability", "monitor groq", "groq alerts", "groq tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Groq Observability

## Overview
Monitor Groq LPU inference API for latency, token throughput, and cost. Groq's defining characteristic is extreme speed -- responses arrive in 50-200ms for small completions, with token generation rates of 500-800 tokens/second. Key metrics to track include time-to-first-token (TTFT), tokens-per-second throughput, per-model cost (Groq is very cheap but volume adds up), rate limit utilization (RPM and TPM), and error rates by model.

## Prerequisites
- Groq API integration at api.groq.com
- Metrics backend (Prometheus or similar)
- Understanding of Groq's rate limit structure (per-key RPM and TPM)

## Instructions

### Step 1: Instrument the Groq Client
```typescript
import Groq from 'groq-sdk';

async function trackedCompletion(groq: Groq, model: string, messages: any[]) {
  const start = performance.now();
  const res = await groq.chat.completions.create({ model, messages });
  const duration = performance.now() - start;
  const tps = (res.usage?.completion_tokens || 0) / (duration / 1000);

  emitHistogram('groq_latency_ms', duration, { model });
  emitGauge('groq_tokens_per_second', tps, { model });
  emitCounter('groq_tokens_total', res.usage?.total_tokens || 0, { model, direction: 'total' });
  emitCounter('groq_tokens_total', res.usage?.prompt_tokens || 0, { model, direction: 'input' });
  emitCounter('groq_tokens_total', res.usage?.completion_tokens || 0, { model, direction: 'output' });

  // Groq pricing is very low -- track for volume visibility
  const pricing: Record<string, number> = { 'llama-3.3-70b-versatile': 0.59, 'llama-3.1-8b-instant': 0.05, 'mixtral-8x7b-32768': 0.24 };
  const costPer1M = pricing[model] || 0.10;
  emitCounter('groq_cost_usd', (res.usage?.total_tokens || 0) / 1e6 * costPer1M, { model });

  return res;
}
```

### Step 2: Track Rate Limit Headers
```typescript
// Groq returns rate limit info in response headers
function parseRateLimitHeaders(headers: Headers) {
  emitGauge('groq_rate_limit_remaining_requests', parseInt(headers.get('x-ratelimit-remaining-requests') || '0'));
  emitGauge('groq_rate_limit_remaining_tokens', parseInt(headers.get('x-ratelimit-remaining-tokens') || '0'));
  const resetMs = parseInt(headers.get('x-ratelimit-reset-requests') || '0');
  emitGauge('groq_rate_limit_reset_ms', resetMs);
}
```

### Step 3: Alert on Performance Degradation
```yaml
groups:
  - name: groq
    rules:
      - alert: GroqLatencyHigh
        expr: histogram_quantile(0.95, rate(groq_latency_ms_bucket[5m])) > 1000
        annotations: { summary: "Groq P95 latency exceeds 1 second (normally <200ms)" }
      - alert: GroqRateLimitNear
        expr: groq_rate_limit_remaining_requests < 10
        annotations: { summary: "Groq rate limit nearly exhausted -- requests may be throttled" }
      - alert: GroqThroughputDrop
        expr: groq_tokens_per_second < 100
        for: 5m
        annotations: { summary: "Groq tokens/sec dropped below 100 (expected 500+)" }
      - alert: GroqErrors
        expr: rate(groq_errors_total[5m]) > 0.05
        annotations: { summary: "Groq API error rate elevated" }
```

### Step 4: Build a Speed-Focused Dashboard
Key panels: time-to-first-token distribution (Groq's USP), tokens/second by model, rate limit utilization gauge, request volume by model, cumulative cost (low but trackable), and latency comparison across models. Since Groq's main value is speed, latency degradation is the highest-priority alert.

### Step 5: Log Request Metadata
```json
{"ts":"2026-03-10T14:30:00Z","model":"llama-3.3-70b-versatile","latency_ms":142,"ttft_ms":48,"tokens_per_sec":623,"prompt_tokens":256,"completion_tokens":89,"cost_usd":0.00002,"rate_limit_remaining":45}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429` with long retry-after | RPM or TPM limit hit | Implement token-aware request queuing |
| Latency spike to 2s+ | Model overloaded or large prompt | Reduce prompt size or switch to lighter model |
| `503 Service Unavailable` | Groq capacity issue | Implement fallback to alternative provider |
| Tokens/sec drop | Streaming disabled | Enable streaming for better perceived performance |

## Examples
```bash
# Benchmark Groq speed with a quick test
time curl -s -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}' | \
  jq '{model: .model, tokens: .usage.total_tokens, latency: "see shell timing"}'
```
