---
name: firecrawl-reliability-patterns
description: |
  Implement Firecrawl reliability patterns: circuit breakers, crawl fallbacks, and content validation.
  Use when building fault-tolerant scraping pipelines, implementing crawl-to-scrape fallback,
  or adding content quality gates to Firecrawl integrations.
  Trigger with phrases like "firecrawl reliability", "firecrawl circuit breaker",
  "firecrawl fallback", "firecrawl resilience", "firecrawl fault tolerant".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, firecrawl-reliability]

---
# Firecrawl Reliability Patterns

## Overview
Production reliability patterns for Firecrawl scraping pipelines. Firecrawl's async crawl model, JS rendering, and credit-based pricing create specific reliability challenges: crawl jobs may time out, scraped content may be empty (bot detection, JS failures), and credits can be burned by runaway crawls. This skill covers battle-tested patterns for each.

## Instructions

### Step 1: Robust Crawl with Timeout and Backoff
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

async function reliableCrawl(
  url: string,
  opts: { limit: number; paths?: string[] },
  timeoutMs = 600000
) {
  const job = await firecrawl.asyncCrawlUrl(url, {
    limit: opts.limit,
    includePaths: opts.paths,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });

  const deadline = Date.now() + timeoutMs;
  let pollInterval = 2000;

  while (Date.now() < deadline) {
    const status = await firecrawl.checkCrawlStatus(job.id);

    if (status.status === "completed") return status;
    if (status.status === "failed") {
      throw new Error(`Crawl failed: ${status.error}`);
    }

    await new Promise(r => setTimeout(r, pollInterval));
    pollInterval = Math.min(pollInterval * 1.5, 30000); // back off to 30s max
  }

  throw new Error(`Crawl timed out after ${timeoutMs}ms (job: ${job.id})`);
}
```

### Step 2: Content Quality Validation
```typescript
interface ScrapedPage {
  url: string;
  markdown: string;
  metadata: { title?: string; statusCode?: number };
}

function validateContent(page: ScrapedPage): {
  valid: boolean;
  reason?: string;
} {
  if (!page.markdown || page.markdown.length < 100) {
    return { valid: false, reason: "Content too short" };
  }

  if (page.metadata.statusCode && page.metadata.statusCode >= 400) {
    return { valid: false, reason: `HTTP ${page.metadata.statusCode}` };
  }

  const errorPatterns = [
    "access denied", "403 forbidden", "page not found",
    "captcha", "please verify", "enable javascript",
  ];
  const lower = page.markdown.toLowerCase();
  for (const pattern of errorPatterns) {
    if (lower.includes(pattern)) {
      return { valid: false, reason: `Error page detected: "${pattern}"` };
    }
  }

  return { valid: true };
}
```

### Step 3: Crawl-to-Scrape Fallback
```typescript
// If a full crawl fails, fall back to scraping critical pages individually
async function resilientFetch(urls: string[]): Promise<any[]> {
  // Try batch scrape first (most efficient)
  try {
    const batch = await firecrawl.batchScrapeUrls(urls, {
      formats: ["markdown"],
      onlyMainContent: true,
    });

    const results = (batch.data || []).filter(page => {
      const { valid } = validateContent({
        url: page.metadata?.sourceURL || "",
        markdown: page.markdown || "",
        metadata: page.metadata || {},
      });
      return valid;
    });

    if (results.length >= urls.length * 0.5) {
      return results; // batch succeeded (>50% valid)
    }
  } catch (batchError) {
    console.warn("Batch scrape failed, falling back to individual scrapes");
  }

  // Fallback: scrape individually with retries
  const results: any[] = [];
  for (const url of urls) {
    try {
      const result = await firecrawl.scrapeUrl(url, {
        formats: ["markdown"],
        onlyMainContent: true,
        waitFor: 5000,
      });
      if (validateContent({ url, markdown: result.markdown || "", metadata: result.metadata || {} }).valid) {
        results.push(result);
      }
    } catch (e) {
      console.error(`Failed to scrape ${url}: ${(e as Error).message}`);
    }
    // Delay between individual scrapes to avoid rate limits
    await new Promise(r => setTimeout(r, 1000));
  }

  return results;
}
```

### Step 4: Circuit Breaker for Firecrawl
```typescript
class FirecrawlCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  private threshold: number;
  private resetTimeMs: number;

  constructor(threshold = 5, resetTimeMs = 60000) {
    this.threshold = threshold;
    this.resetTimeMs = resetTimeMs;
  }

  async execute<T>(operation: () => Promise<T>, fallback?: () => T): Promise<T> {
    // Check if circuit should reset
    if (this.state === "open" && Date.now() - this.lastFailure > this.resetTimeMs) {
      this.state = "half-open";
    }

    if (this.state === "open") {
      console.warn("Circuit breaker OPEN — using fallback");
      if (fallback) return fallback();
      throw new Error("Firecrawl circuit breaker is open");
    }

    try {
      const result = await operation();
      if (this.state === "half-open") {
        this.state = "closed";
        this.failures = 0;
      }
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= this.threshold) {
        this.state = "open";
        console.error(`Circuit breaker OPENED after ${this.failures} failures`);
      }
      throw error;
    }
  }
}

const breaker = new FirecrawlCircuitBreaker(5, 60000);

async function protectedScrape(url: string) {
  return breaker.execute(
    () => firecrawl.scrapeUrl(url, { formats: ["markdown"] }),
    () => ({ markdown: getCachedContent(url), metadata: { fromCache: true } })
  );
}
```

### Step 5: Credit-Aware Processing
```typescript
class CreditGuard {
  private dailyUsage = new Map<string, number>();
  private dailyLimit: number;

  constructor(dailyLimit = 5000) {
    this.dailyLimit = dailyLimit;
  }

  canAfford(credits: number): boolean {
    const today = new Date().toISOString().split("T")[0];
    return (this.dailyUsage.get(today) || 0) + credits <= this.dailyLimit;
  }

  record(credits: number) {
    const today = new Date().toISOString().split("T")[0];
    this.dailyUsage.set(today, (this.dailyUsage.get(today) || 0) + credits);
  }

  remaining(): number {
    const today = new Date().toISOString().split("T")[0];
    return this.dailyLimit - (this.dailyUsage.get(today) || 0);
  }
}

const creditGuard = new CreditGuard(5000);

async function budgetedCrawl(url: string, limit: number) {
  if (!creditGuard.canAfford(limit)) {
    throw new Error(`Budget exceeded: ${creditGuard.remaining()} credits remaining`);
  }

  const result = await reliableCrawl(url, { limit });
  creditGuard.record(result.data?.length || 0);
  return result;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Crawl timeout | Large site, slow rendering | Set timeout, reduce limit |
| Empty markdown | Bot detection or JS failure | Increase `waitFor`, use `actions` |
| Credit overrun | No budget tracking | Implement credit guard |
| Cascade failures | Single scrape failure crashes pipeline | Circuit breaker + fallback |
| Partial crawl results | Some pages blocked | Validate content, retry failed URLs |

## Examples

### Full Resilient Pipeline
```typescript
async function resilientPipeline(url: string) {
  const map = await firecrawl.mapUrl(url);
  const urls = (map.links || []).filter(u => u.includes("/docs/")).slice(0, 50);

  if (!creditGuard.canAfford(urls.length)) {
    console.warn("Budget tight — reducing scope");
    urls.splice(20); // trim to 20
  }

  const pages = await resilientFetch(urls);
  const valid = pages.filter(p => validateContent(p).valid);
  creditGuard.record(urls.length);

  return { scraped: urls.length, valid: valid.length, remaining: creditGuard.remaining() };
}
```

## Resources
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)
- [Firecrawl Rate Limits](https://docs.firecrawl.dev/rate-limits)

## Next Steps
For policy enforcement, see `firecrawl-policy-guardrails`.
