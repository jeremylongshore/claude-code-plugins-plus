---
name: perplexity-observability
description: |
  Set up comprehensive observability for Perplexity integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Perplexity operations, setting up dashboards,
  or configuring alerting for Perplexity integration health.
  Trigger with phrases like "perplexity monitoring", "perplexity metrics",
  "perplexity observability", "monitor perplexity", "perplexity alerts", "perplexity tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Observability

## Overview
Monitor Perplexity AI search API performance, citation quality, and per-query costs. Key signals include search latency (sonar: 1-3s, sonar-pro: 3-8s), citation count per response (more citations generally means higher answer quality), cost per query by model, and cache effectiveness for repeated queries.

## Prerequisites
- Perplexity API integration (pplx-api or OpenAI-compatible endpoint)
- Metrics backend (Prometheus, Datadog, or similar)
- Request logging for cost tracking

## Instructions

### Step 1: Instrument the Perplexity Client
```typescript
async function trackedSearch(query: string, model: string = 'sonar') {
  const start = performance.now();
  const res = await fetch('https://api.perplexity.ai/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${PPLX_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: query }], return_citations: true }),
  });
  const data = await res.json();
  const duration = performance.now() - start;

  emitHistogram('perplexity_latency_ms', duration, { model });
  emitCounter('perplexity_queries_total', 1, { model, status: res.ok ? 'success' : 'error' });
  emitGauge('perplexity_citations_count', data.citations?.length || 0, { model });
  emitCounter('perplexity_tokens_total', data.usage?.total_tokens || 0, { model });
  return data;
}
```

### Step 2: Track Citation Quality
```typescript
// Measure whether responses include high-quality citations
function evaluateCitations(citations: string[]) {
  const domainQuality: Record<string, string> = {
    '.gov': 'authoritative', '.edu': 'authoritative',
    'wikipedia.org': 'reference', 'arxiv.org': 'academic',
  };
  const quality = citations.map(url => {
    const match = Object.entries(domainQuality).find(([domain]) => url.includes(domain));
    return match ? match[1] : 'general';
  });
  const authoritativeCount = quality.filter(q => q === 'authoritative' || q === 'academic').length;
  emitGauge('perplexity_authoritative_citations', authoritativeCount);
}
```

### Step 3: Monitor Cost and Budget
```bash
set -euo pipefail
# Check API usage and budget status
curl -s https://api.perplexity.ai/v1/usage \
  -H "Authorization: Bearer $PPLX_API_KEY" | \
  jq '{queries_today, cost_today_usd, monthly_cost_usd, budget_remaining}'
```

### Step 4: Alert Configuration
```yaml
groups:
  - name: perplexity
    rules:
      - alert: PerplexityHighLatency
        expr: histogram_quantile(0.95, rate(perplexity_latency_ms_bucket[5m])) > 8000  # 8000: API server port
        annotations: { summary: "Perplexity P95 latency exceeds 8 seconds" }
      - alert: PerplexityNoCitations
        expr: perplexity_citations_count == 0
        for: 10m
        annotations: { summary: "Perplexity returning responses with zero citations" }
      - alert: PerplexityCostSpike
        expr: increase(perplexity_tokens_total[1h]) * 0.000005 > 5
        annotations: { summary: "Perplexity spend exceeds $5/hour" }
      - alert: PerplexityErrors
        expr: rate(perplexity_queries_total{status="error"}[5m]) > 0.05
        annotations: { summary: "Perplexity API error rate elevated" }
```

### Step 5: Dashboard Panels
Track: query latency by model (sonar vs sonar-pro), citations per response distribution, query volume over time, cost per query trend, error rate, and cache hit rate if implementing local query caching. Compare sonar vs sonar-pro latency and citation quality to inform model selection.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High latency on sonar-pro | Deep research queries | Expected for complex queries; use sonar for simple ones |
| Zero citations | Query too vague or niche | Rephrase query with more specific terms |
| `429` rate limited | Too many concurrent requests | Add request queue with backoff |
| Budget exhausted | Monthly cap reached | Increase budget or reduce query volume |

## Examples

**Basic usage**: Apply perplexity observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize perplexity observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack