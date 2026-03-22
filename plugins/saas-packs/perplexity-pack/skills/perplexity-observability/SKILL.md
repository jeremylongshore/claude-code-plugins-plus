---
name: perplexity-observability
description: |
  Set up monitoring for Perplexity Sonar API with latency, cost, citation quality, and error tracking.
  Use when implementing monitoring dashboards, setting up alerts,
  or tracking Perplexity API health in production.
  Trigger with phrases like "perplexity monitoring", "perplexity metrics",
  "perplexity observability", "monitor perplexity", "perplexity dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, monitoring, observability, dashboard]

---
# Perplexity Observability

## Overview
Monitor Perplexity Sonar API performance, cost, and quality. Key signals unique to Perplexity: citation count per response (quality indicator), search latency variability (web search is non-deterministic), and per-model cost differences.

## Key Metrics

| Metric | sonar (typical) | sonar-pro (typical) | Alert Threshold |
|--------|----------------|--------------------|--------------  |
| Latency p50 | 1-2s | 3-5s | p95 > 15s |
| Citations/response | 3-5 | 5-10 | 0 for 10min |
| Error rate | <1% | <1% | >5% |
| Cost/query | $0.005 | $0.02 | >$0.10 |

## Prerequisites
- Perplexity API integration running
- Metrics backend (Prometheus, Datadog, or custom)
- Alerting system configured

## Instructions

### Step 1: Instrument the Perplexity Client
```typescript
import OpenAI from "openai";

interface SearchMetrics {
  model: string;
  latencyMs: number;
  status: "success" | "error";
  citationCount: number;
  totalTokens: number;
  cached: boolean;
  errorCode?: number;
}

const metrics: SearchMetrics[] = [];

async function instrumentedSearch(
  client: OpenAI,
  query: string,
  model: string = "sonar",
  cached: boolean = false
): Promise<{ response: any; metrics: SearchMetrics }> {
  const start = performance.now();
  let searchMetrics: SearchMetrics;

  try {
    const response = await client.chat.completions.create({
      model,
      messages: [{ role: "user", content: query }],
    });

    searchMetrics = {
      model,
      latencyMs: performance.now() - start,
      status: "success",
      citationCount: (response as any).citations?.length || 0,
      totalTokens: response.usage?.total_tokens || 0,
      cached,
    };

    metrics.push(searchMetrics);
    return { response, metrics: searchMetrics };
  } catch (err: any) {
    searchMetrics = {
      model,
      latencyMs: performance.now() - start,
      status: "error",
      citationCount: 0,
      totalTokens: 0,
      cached,
      errorCode: err.status,
    };

    metrics.push(searchMetrics);
    throw err;
  }
}
```

### Step 2: Prometheus Metrics Export
```typescript
// Export metrics in Prometheus format
function prometheusMetrics(): string {
  const lines: string[] = [];

  // Latency histogram
  lines.push("# HELP perplexity_latency_ms Search response latency");
  lines.push("# TYPE perplexity_latency_ms histogram");

  // Query counter
  const byModel = metrics.reduce((acc, m) => {
    const key = `${m.model}_${m.status}`;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  for (const [key, count] of Object.entries(byModel)) {
    const [model, status] = key.split("_");
    lines.push(`perplexity_queries_total{model="${model}",status="${status}"} ${count}`);
  }

  // Citation gauge
  const recentCitations = metrics.slice(-100).filter((m) => m.status === "success");
  const avgCitations = recentCitations.reduce((s, m) => s + m.citationCount, 0) / Math.max(recentCitations.length, 1);
  lines.push(`perplexity_avg_citations ${avgCitations.toFixed(1)}`);

  // Token counter
  const totalTokens = metrics.reduce((s, m) => s + m.totalTokens, 0);
  lines.push(`perplexity_tokens_total ${totalTokens}`);

  return lines.join("\n");
}
```

### Step 3: Citation Quality Scoring
```typescript
function evaluateCitationQuality(citations: string[]): {
  total: number;
  authoritative: number;
  qualityScore: number;
} {
  const authoritativeTLDs = [".gov", ".edu"];
  const authoritativeDomains = ["wikipedia.org", "arxiv.org", "nature.com", "science.org"];

  let authoritative = 0;
  for (const url of citations) {
    const isAuth = authoritativeTLDs.some((tld) => url.includes(tld)) ||
                   authoritativeDomains.some((d) => url.includes(d));
    if (isAuth) authoritative++;
  }

  return {
    total: citations.length,
    authoritative,
    qualityScore: citations.length > 0 ? authoritative / citations.length : 0,
  };
}
```

### Step 4: Cost Tracking
```typescript
const COST_PER_MILLION_TOKENS: Record<string, { input: number; output: number }> = {
  "sonar":              { input: 1, output: 1 },
  "sonar-pro":          { input: 3, output: 15 },
  "sonar-reasoning-pro": { input: 3, output: 15 },
  "sonar-deep-research": { input: 2, output: 8 },
};

function estimateCost(model: string, usage: { prompt_tokens: number; completion_tokens: number }): number {
  const rates = COST_PER_MILLION_TOKENS[model] || COST_PER_MILLION_TOKENS["sonar"];
  return (usage.prompt_tokens * rates.input + usage.completion_tokens * rates.output) / 1_000_000;
}
```

### Step 5: Alert Rules (Prometheus/Alertmanager)
```yaml
groups:
  - name: perplexity
    rules:
      - alert: PerplexityHighLatency
        expr: histogram_quantile(0.95, rate(perplexity_latency_ms_bucket[5m])) > 15000
        for: 5m
        annotations:
          summary: "Perplexity P95 latency exceeds 15 seconds"

      - alert: PerplexityNoCitations
        expr: perplexity_avg_citations == 0
        for: 10m
        annotations:
          summary: "Perplexity returning responses with zero citations"

      - alert: PerplexityHighErrorRate
        expr: rate(perplexity_queries_total{status="error"}[5m]) / rate(perplexity_queries_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Perplexity API error rate exceeds 5%"

      - alert: PerplexityCostSpike
        expr: increase(perplexity_tokens_total[1h]) > 1000000
        annotations:
          summary: "Perplexity token usage spike (>1M tokens/hour)"
```

## Dashboard Panels
Track these metrics on your dashboard:
- Query latency by model (sonar vs sonar-pro histogram)
- Citations per response distribution
- Query volume over time (by model)
- Cost per query trend
- Error rate by status code (429 vs 500)
- Cache hit rate

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High latency on sonar-pro | Complex multi-source search | Expected; use sonar for simple queries |
| Zero citations alert | Vague queries or API issue | Review query patterns |
| Cost spike | Burst of sonar-pro queries | Check for runaway batch jobs |
| Error rate elevated | Rate limiting or API issue | Check for 429s in error breakdown |

## Output
- Instrumented Perplexity client with latency/error/citation tracking
- Prometheus metrics export endpoint
- Citation quality scoring
- Cost estimation per query
- Alert rules for latency, errors, and cost

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Prometheus Documentation](https://prometheus.io/docs/)

## Next Steps
For incident response, see `perplexity-incident-runbook`.
