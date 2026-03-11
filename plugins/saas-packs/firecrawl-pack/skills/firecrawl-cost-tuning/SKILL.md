---
name: firecrawl-cost-tuning
description: |
  Optimize FireCrawl costs through tier selection, sampling, and usage monitoring.
  Use when analyzing FireCrawl billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "firecrawl cost", "firecrawl billing",
  "reduce firecrawl costs", "firecrawl pricing", "firecrawl expensive", "firecrawl budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Firecrawl Cost Tuning

## Overview
Reduce Firecrawl web scraping costs by limiting crawl depth, caching scraped content, and choosing the right scrape mode. Firecrawl charges credits per page: 1 credit for single-page scrape, variable credits for crawl jobs (each discovered page costs credits).

## Prerequisites
- Firecrawl account with credit balance visibility
- Understanding of your scraping patterns (single page vs crawl)
- Cache infrastructure for storing scraped content

## Instructions

### Step 1: Always Set Crawl Limits
```bash
set -euo pipefail
# BAD: Unbounded crawl (could consume thousands of credits)
curl -X POST https://api.firecrawl.dev/v1/crawl \
  -d '{"url": "https://docs.example.com"}'

# GOOD: Bounded crawl with depth and page limits
curl -X POST https://api.firecrawl.dev/v1/crawl \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -d '{
    "url": "https://docs.example.com",
    "maxDepth": 2,
    "limit": 50,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
# Saves: potentially hundreds or thousands of credits per crawl
```

### Step 2: Use Scrape for Known URLs Instead of Crawl
```typescript
// If you know the specific pages you need, scrape individually instead of crawling
const targetUrls = [
  'https://docs.example.com/api/authentication',
  'https://docs.example.com/api/endpoints',
  'https://docs.example.com/api/errors',
];

// Scrape 3 specific pages: 3 credits
for (const url of targetUrls) {
  await firecrawl.scrapeUrl(url, { formats: ['markdown'] });
}
// vs. Crawl entire docs site: potentially 500+ credits  # HTTP 500 Internal Server Error
```

### Step 3: Cache Scraped Content
```typescript
import { createHash } from 'crypto';

const scrapeCache = new Map<string, { content: string; timestamp: number }>();
const CACHE_TTL = 24 * 3600 * 1000; // 24 hours  # 1000: 3600: timeout: 1 hour

async function cachedScrape(url: string): Promise<string> {
  const key = createHash('md5').update(url).digest('hex');
  const cached = scrapeCache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) return cached.content;

  const result = await firecrawl.scrapeUrl(url, { formats: ['markdown'] });
  scrapeCache.set(key, { content: result.markdown, timestamp: Date.now() });
  return result.markdown;
}
// Typical savings: 50-80% credit reduction for recurring scrape patterns
```

### Step 4: Choose Minimal Scrape Options
```bash
set -euo pipefail
# Only request what you need -- each format option has cost implications
# Minimal (cheapest): markdown only
curl -X POST https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}'

# Avoid requesting screenshots, PDFs, or rawHtml unless actually needed
# Each additional format increases processing time and may affect credit usage
```

### Step 5: Monitor Credit Efficiency
```bash
set -euo pipefail
# Find which crawl jobs consumed the most credits
curl -s https://api.firecrawl.dev/v1/usage \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | \
  jq '{
    credits_remaining: .credits_remaining,
    credits_used_today: .credits_used_today,
    avg_credits_per_job: (.credits_used_month / (.jobs_count + 0.01)),
    projected_monthly: (.credits_used_today * 30)
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits drained by one crawl | No `limit` or `maxDepth` set | Always set both on crawl jobs |
| Duplicate scraping costs | Same URLs scraped daily | Implement URL-based caching |
| High credit per page | Requesting all formats | Request only `markdown` format |
| Budget overrun | Automated crawls without caps | Set per-job credit limits and daily caps |

## Examples

**Basic usage**: Apply firecrawl cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize firecrawl cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack