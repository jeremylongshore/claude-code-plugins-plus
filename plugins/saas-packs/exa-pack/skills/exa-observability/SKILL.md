---
name: exa-observability
description: |
  Set up comprehensive observability for Exa integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Exa operations, setting up dashboards,
  or configuring alerting for Exa integration health.
  Trigger with phrases like "exa monitoring", "exa metrics",
  "exa observability", "monitor exa", "exa alerts", "exa tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Observability

## Overview
Monitor Exa AI search API performance, result quality, and cost efficiency. Key metrics include search latency (Exa neural search typically takes 500-2000ms), result relevance (measured by click-through or downstream usage), search volume by type (neural vs keyword vs auto), per-search cost tracking, and cache hit rates for repeated queries.

## Prerequisites
- Exa API integration in production
- Metrics backend (Prometheus, Datadog, or equivalent)
- Request logging infrastructure

## Instructions

### Step 1: Instrument the Exa Client
```typescript
import Exa from 'exa-js';

async function trackedSearch(exa: Exa, query: string, options: any) {
  const start = performance.now();
  try {
    const results = await exa.search(query, options);
    const duration = performance.now() - start;
    emitHistogram('exa_search_duration_ms', duration, { type: options.type || 'auto' });
    emitCounter('exa_searches_total', 1, { type: options.type || 'auto', status: 'success' });
    emitGauge('exa_results_count', results.results.length, { type: options.type || 'auto' });
    return results;
  } catch (err: any) {
    emitCounter('exa_searches_total', 1, { status: 'error', code: err.status });
    throw err;
  }
}
```

### Step 2: Track Result Quality
```typescript
// Measure whether search results are actually used by downstream consumers
function trackResultUsage(searchId: string, resultIndex: number, action: 'clicked' | 'used_in_context' | 'discarded') {
  emitCounter('exa_result_usage', 1, { action, position: String(resultIndex) });
  // Results at position 0-2 should have high usage; if not, query needs tuning
}
```

### Step 3: Monitor Search Budget
```bash
set -euo pipefail
# Check remaining search quota
curl -s https://api.exa.ai/v1/usage \
  -H "x-api-key: $EXA_API_KEY" | \
  jq '{searches_today, searches_this_month, monthly_limit, budget_remaining_pct: (1 - .searches_this_month / .monthly_limit) * 100}'
```

### Step 4: Configure Alerts
```yaml
groups:
  - name: exa
    rules:
      - alert: ExaHighLatency
        expr: histogram_quantile(0.95, rate(exa_search_duration_ms_bucket[5m])) > 3000  # 3000: 3 seconds in ms
        annotations: { summary: "Exa search P95 latency exceeds 3 seconds" }
      - alert: ExaBudgetLow
        expr: exa_monthly_searches_remaining < 1000  # 1000: 1 second in ms
        annotations: { summary: "Exa monthly search budget nearly exhausted" }
      - alert: ExaLowResultQuality
        expr: rate(exa_result_usage{action="discarded"}[1h]) / rate(exa_result_usage[1h]) > 0.5
        annotations: { summary: "Over 50% of Exa search results being discarded" }
      - alert: ExaApiErrors
        expr: rate(exa_searches_total{status="error"}[5m]) > 0.1
        annotations: { summary: "Exa API errors detected" }
```

### Step 5: Build a Search Efficiency Dashboard
Key panels: search volume by type (neural/keyword/auto), latency p50/p95, results per search distribution, result usage rate (used vs discarded), daily cost tracking, and cache hit rate. Low result counts with high latency indicate poorly formed queries.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Implement exponential backoff and request queue |
| Zero results returned | Query too specific or domain filter too narrow | Broaden query, remove `includeDomains` filter |
| Latency spike to 5s+ | Neural search on complex query | Use `type: "keyword"` for simpler lookups |
| Monthly budget exhausted | Uncapped search volume | Add application-level search budget tracking |

## Examples

**Basic usage**: Apply exa observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize exa observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack