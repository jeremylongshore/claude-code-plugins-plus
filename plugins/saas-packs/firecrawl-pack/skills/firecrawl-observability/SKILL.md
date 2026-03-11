---
name: firecrawl-observability
description: |
  Set up comprehensive observability for FireCrawl integrations with metrics, traces, and alerts.
  Use when implementing monitoring for FireCrawl operations, setting up dashboards,
  or configuring alerting for FireCrawl integration health.
  Trigger with phrases like "firecrawl monitoring", "firecrawl metrics",
  "firecrawl observability", "monitor firecrawl", "firecrawl alerts", "firecrawl tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Observability

## Overview
Monitor Firecrawl web scraping and crawling jobs for success rates, credit consumption, and extraction quality. Key signals include crawl job completion rate, pages scraped per credit, scrape latency (single page vs full crawl), credit burn velocity, and extraction success rate (did the markdown/structured data extraction return useful content). Firecrawl charges 1 credit per page for scrape and 5+ for crawl jobs, making credit monitoring critical.

## Prerequisites
- Firecrawl account with API access
- Webhook endpoint for job status callbacks
- Metrics backend for tracking

## Instructions

### Step 1: Track Crawl Job Status via Webhooks
```typescript
// firecrawl-webhook-handler.ts
app.post('/webhooks/firecrawl', (req, res) => {
  const { jobId, status, pagesScraped, creditsUsed, failedUrls } = req.body;
  emitCounter('firecrawl_jobs_total', 1, { status });
  emitGauge('firecrawl_pages_per_job', pagesScraped, { job: jobId });
  emitCounter('firecrawl_credits_used', creditsUsed);
  if (failedUrls?.length > 0) {
    emitCounter('firecrawl_page_failures', failedUrls.length, { job: jobId });
  }
  res.sendStatus(200);
});
```

### Step 2: Monitor Credit Consumption
```bash
# Check credit usage and remaining balance
curl https://api.firecrawl.dev/v1/usage \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | \
  jq '{credits_used_today, credits_remaining, daily_avg: .credits_used_month / 30, days_until_empty: (.credits_remaining / (.credits_used_month / 30 + 0.01))}'
```

### Step 3: Measure Extraction Quality
```typescript
// Track whether scraped content is actually usable
function evaluateExtractionQuality(result: any) {
  const markdown = result.markdown || '';
  const metrics = {
    contentLength: markdown.length,
    hasHeadings: /^#{1,3}\s/m.test(markdown),
    hasContent: markdown.length > 200,
    isErrorPage: /404|not found|access denied/i.test(markdown),
  };
  const quality = metrics.hasContent && !metrics.isErrorPage ? 'good' : 'poor';
  emitCounter('firecrawl_extraction_quality', 1, { quality });
  return quality;
}
```

### Step 4: Alert on Crawl Issues
```yaml
groups:
  - name: firecrawl
    rules:
      - alert: FirecrawlHighFailureRate
        expr: rate(firecrawl_page_failures[1h]) / rate(firecrawl_pages_per_job[1h]) > 0.2
        annotations: { summary: "Firecrawl page failure rate exceeds 20%" }
      - alert: FirecrawlCreditBurnHigh
        expr: rate(firecrawl_credits_used[1h]) > 200
        annotations: { summary: "Firecrawl burning >200 credits/hour" }
      - alert: FirecrawlCreditLow
        expr: firecrawl_credits_remaining < 500
        annotations: { summary: "Firecrawl credits below 500 -- refill soon" }
      - alert: FirecrawlPoorExtraction
        expr: rate(firecrawl_extraction_quality{quality="poor"}[1h]) / rate(firecrawl_extraction_quality[1h]) > 0.3
        annotations: { summary: "Over 30% of Firecrawl extractions returning poor quality" }
```

### Step 5: Dashboard Panels
Track: crawl job success/failure rate, pages scraped per hour, credit consumption trend, extraction quality ratio, average scrape latency, and top failed domains (to identify sites blocking scraping).

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High page failure rate | Target site blocking bots | Enable stealth mode or add delays between requests |
| Poor extraction quality | Dynamic JS content not rendering | Enable `waitFor` option to wait for page load |
| Credit burn spike | Crawl job with no `limit` set | Always set `limit` and `maxDepth` on crawl jobs |
| Webhook not firing | Endpoint unreachable | Verify endpoint URL and SSL certificate |

## Examples
```bash
# Quick check: crawl job status
curl -s "https://api.firecrawl.dev/v1/crawl/JOB_ID" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | \
  jq '{status, pages_crawled, credits_used, failed_urls: (.failed | length)}'
```
