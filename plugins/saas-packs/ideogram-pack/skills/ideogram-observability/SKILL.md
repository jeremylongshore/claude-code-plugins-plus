---
name: ideogram-observability
description: |
  Set up comprehensive observability for Ideogram integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Ideogram operations, setting up dashboards,
  or configuring alerting for Ideogram integration health.
  Trigger with phrases like "ideogram monitoring", "ideogram metrics",
  "ideogram observability", "monitor ideogram", "ideogram alerts", "ideogram tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram Observability

## Overview
Monitor Ideogram AI image generation for latency, credit consumption, and output quality. Key metrics include generation time (typically 5-15 seconds per image depending on model and resolution), credit cost per generation (varies by model version and quality setting), generation success rate, and prompt safety filter rejection rate.

## Prerequisites
- Ideogram API account with active credits
- Metrics backend for tracking generation data
- Webhook or polling mechanism for async generation status

## Instructions

### Step 1: Instrument Image Generation Calls
```typescript
async function trackedGeneration(prompt: string, options: any) {
  const start = performance.now();
  try {
    const result = await ideogram.generate({ image_request: { prompt, ...options } });
    const duration = performance.now() - start;
    emitHistogram('ideogram_generation_duration_ms', duration, { model: options.model || 'V_2' });
    emitCounter('ideogram_generations_total', 1, { model: options.model || 'V_2', status: 'success' });
    emitCounter('ideogram_credits_used', result.credits_consumed || 1, { model: options.model || 'V_2' });
    return result;
  } catch (err: any) {
    emitCounter('ideogram_generations_total', 1, { status: 'error', reason: err.code || 'unknown' });
    throw err;
  }
}
```

### Step 2: Track Prompt Safety Rejections
```typescript
// Monitor how often prompts are rejected by the safety filter
function handleSafetyRejection(prompt: string, reason: string) {
  emitCounter('ideogram_safety_rejections_total', 1, { reason });
  console.warn(`Prompt rejected: ${reason}`, { prompt: prompt.substring(0, 50) });
}
```

### Step 3: Monitor Credit Balance
```bash
set -euo pipefail
# Check remaining credits and burn rate
curl -s https://api.ideogram.ai/v1/usage \
  -H "Api-Key: $IDEOGRAM_API_KEY" | \
  jq '{credits_remaining, credits_used_today, credits_used_month, daily_avg: (.credits_used_month / 30), days_remaining: (.credits_remaining / (.credits_used_month / 30 + 0.01))}'
```

### Step 4: Set Up Alerts
```yaml
groups:
  - name: ideogram
    rules:
      - alert: IdeogramGenerationSlow
        expr: histogram_quantile(0.95, rate(ideogram_generation_duration_ms_bucket[30m])) > 20000  # 20000 = configured value
        annotations: { summary: "Ideogram P95 generation time exceeds 20 seconds" }
      - alert: IdeogramCreditBurnHigh
        expr: rate(ideogram_credits_used[1h]) > 100
        annotations: { summary: "Ideogram burning >100 credits/hour" }
      - alert: IdeogramCreditsLow
        expr: ideogram_credits_remaining < 200  # HTTP 200 OK
        annotations: { summary: "Ideogram credits below 200 -- purchase more" }  # HTTP 200 OK
      - alert: IdeogramHighRejectionRate
        expr: rate(ideogram_safety_rejections_total[1h]) / rate(ideogram_generations_total[1h]) > 0.1
        annotations: { summary: "Ideogram safety rejection rate exceeds 10%" }
```

### Step 5: Dashboard Panels
Track: generation volume by model version, latency distribution, credit consumption trend, safety rejection rate, generation success/failure ratio, and average credits per generation. Compare V_2 vs V_2_TURBO for cost-vs-speed tradeoffs.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Generation timeout | Complex prompt or high-res request | Reduce resolution or simplify prompt |
| `402` credit error | Credits exhausted | Purchase more credits on ideogram.ai |
| Safety filter rejection | Prompt contains restricted content | Rephrase prompt, avoid brand names |
| `429` rate limited | Too many concurrent generations | Queue requests with concurrency limit |

## Examples

**Basic usage**: Apply ideogram observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize ideogram observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack