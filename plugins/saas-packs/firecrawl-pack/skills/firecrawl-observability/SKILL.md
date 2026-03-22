---
name: firecrawl-observability
description: |
  Monitor Firecrawl scraping pipelines with metrics, credit tracking, and quality alerts.
  Use when implementing monitoring for Firecrawl operations, setting up dashboards,
  or configuring alerting for scrape failures and credit consumption.
  Trigger with phrases like "firecrawl monitoring", "firecrawl metrics",
  "firecrawl observability", "monitor firecrawl", "firecrawl alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, monitoring, observability, dashboard]

---
# Firecrawl Observability

## Overview
Monitor Firecrawl web scraping pipelines for success rates, credit consumption, content quality, and latency. Key signals: scrape success rate, crawl job completion, credit burn velocity, extraction quality (did markdown actually contain useful content vs error pages), and webhook delivery health.

## Key Metrics

| Metric | Type | Why It Matters |
|--------|------|---------------|
| `firecrawl_scrapes_total` | Counter | Track scrape volume and success rate |
| `firecrawl_credits_used` | Counter | Monitor credit consumption |
| `firecrawl_scrape_duration_ms` | Histogram | Detect latency issues |
| `firecrawl_content_quality` | Counter | Catch empty/error pages |
| `firecrawl_crawl_jobs_total` | Counter | Track crawl job outcomes |

## Instructions

### Step 1: Instrumented Firecrawl Wrapper
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Counters (use your metrics library: prom-client, statsd, datadog, etc.)
function emit(metric: string, value: number, tags?: Record<string, string>) {
  console.log(JSON.stringify({ metric, value, tags, timestamp: Date.now() }));
}

export async function instrumentedScrape(url: string) {
  const start = Date.now();
  try {
    const result = await firecrawl.scrapeUrl(url, {
      formats: ["markdown"],
      onlyMainContent: true,
    });

    const duration = Date.now() - start;
    const quality = evaluateQuality(result);

    emit("firecrawl_scrapes_total", 1, { status: "success" });
    emit("firecrawl_scrape_duration_ms", duration);
    emit("firecrawl_credits_used", 1);
    emit("firecrawl_content_quality", 1, { quality });

    return result;
  } catch (error: any) {
    emit("firecrawl_scrapes_total", 1, {
      status: "error",
      error_code: String(error.statusCode || "unknown"),
    });
    emit("firecrawl_scrape_duration_ms", Date.now() - start);
    throw error;
  }
}

function evaluateQuality(result: any): string {
  const md = result.markdown || "";
  if (md.length < 100) return "empty";
  if (/404|not found|access denied|captcha/i.test(md)) return "error_page";
  if (!/^#{1,3}\s/m.test(md)) return "no_structure";
  return "good";
}
```

### Step 2: Credit Consumption Monitor
```typescript
async function checkCreditHealth() {
  const response = await fetch("https://api.firecrawl.dev/v1/team/credits", {
    headers: { Authorization: `Bearer ${process.env.FIRECRAWL_API_KEY}` },
  });
  const data = await response.json();

  emit("firecrawl_credits_remaining", data.credits_remaining || 0);

  if (data.credits_remaining < 1000) {
    console.warn(`LOW CREDITS: ${data.credits_remaining} remaining`);
    emit("firecrawl_credit_alert", 1, { level: "warning" });
  }
  if (data.credits_remaining < 100) {
    emit("firecrawl_credit_alert", 1, { level: "critical" });
  }

  return data;
}

// Run every hour
setInterval(checkCreditHealth, 3600000);
```

### Step 3: Crawl Job Tracking
```typescript
export async function monitoredCrawl(url: string, limit: number) {
  const start = Date.now();

  const job = await firecrawl.asyncCrawlUrl(url, {
    limit,
    scrapeOptions: { formats: ["markdown"] },
  });

  emit("firecrawl_crawl_jobs_total", 1, { status: "started" });

  // Poll with metrics
  let status = await firecrawl.checkCrawlStatus(job.id);
  while (status.status === "scraping") {
    emit("firecrawl_crawl_progress", status.completed || 0, { jobId: job.id });
    await new Promise(r => setTimeout(r, 5000));
    status = await firecrawl.checkCrawlStatus(job.id);
  }

  const duration = Date.now() - start;
  emit("firecrawl_crawl_jobs_total", 1, { status: status.status });
  emit("firecrawl_crawl_duration_ms", duration);
  emit("firecrawl_crawl_pages", status.data?.length || 0);
  emit("firecrawl_credits_used", status.data?.length || 0);

  return status;
}
```

### Step 4: Prometheus Alert Rules
```yaml
groups:
  - name: firecrawl
    rules:
      - alert: FirecrawlHighFailureRate
        expr: rate(firecrawl_scrapes_total{status="error"}[1h]) / rate(firecrawl_scrapes_total[1h]) > 0.1
        annotations:
          summary: "Firecrawl error rate exceeds 10%"

      - alert: FirecrawlCreditLow
        expr: firecrawl_credits_remaining < 500
        annotations:
          summary: "Firecrawl credits below 500 — refill soon"

      - alert: FirecrawlHighLatency
        expr: histogram_quantile(0.95, firecrawl_scrape_duration_ms) > 15000
        annotations:
          summary: "Firecrawl p95 latency exceeds 15 seconds"

      - alert: FirecrawlPoorQuality
        expr: rate(firecrawl_content_quality{quality="empty"}[1h]) / rate(firecrawl_content_quality[1h]) > 0.2
        annotations:
          summary: "Over 20% of scrapes returning empty content"
```

### Step 5: Dashboard Panels
Track these in Grafana/Datadog:
- **Scrape volume**: `sum(rate(firecrawl_scrapes_total[5m]))` by status
- **Credit burn rate**: `sum(rate(firecrawl_credits_used[1h]))` — credits/hour
- **Latency p50/p95**: `histogram_quantile(0.5, firecrawl_scrape_duration_ms)`
- **Content quality**: Pie chart of `firecrawl_content_quality` by quality label
- **Credits remaining**: Single stat with thresholds (green > 1000, yellow > 100, red < 100)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High failure rate | Target sites blocking | Enable `waitFor`, rotate target URLs |
| Poor content quality | JS not rendering | Increase `waitFor` or use `actions` |
| Credit burn spike | Unbounded crawl | Enforce `limit` on all crawl calls |
| Missing metrics | Wrapper not used | Ensure all scrape calls go through instrumented wrapper |

## Resources
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)
- [prom-client (Prometheus for Node.js)](https://github.com/siimon/prom-client)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## Next Steps
For incident response, see `firecrawl-incident-runbook`.
