---
name: firecrawl-policy-guardrails
description: |
  Implement Firecrawl scraping policy enforcement: domain blocklists, credit budgets,
  content filtering, and robots.txt compliance guardrails.
  Use when setting up scraping policies, enforcing crawl limits, or preventing
  accidental scraping of prohibited domains.
  Trigger with phrases like "firecrawl policy", "firecrawl guardrails",
  "firecrawl domain blocklist", "firecrawl scraping rules", "firecrawl compliance".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, firecrawl-policy]

---
# Firecrawl Policy Guardrails

## Overview
Automated guardrails for Firecrawl scraping pipelines. Web scraping carries legal (robots.txt, ToS), ethical (rate limiting, attribution), and cost (credit burn) risks. This skill implements domain blocklists, credit budgets, content quality gates, and per-domain rate limits as enforceable policies.

## Instructions

### Step 1: Domain Policy Enforcement
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

class ScrapePolicy {
  // Domains that explicitly prohibit scraping in their ToS
  static BLOCKED_DOMAINS = [
    "facebook.com", "instagram.com",  // Meta ToS
    "linkedin.com",                    // LinkedIn ToS
    "twitter.com", "x.com",           // X/Twitter ToS
  ];

  // Domains with sensitive/regulated content
  static SENSITIVE_DOMAINS = [
    "*.gov", "*.mil",                 // Government
    "*.edu",                          // Educational (FERPA)
  ];

  static validateUrl(url: string): void {
    const hostname = new URL(url).hostname;

    for (const blocked of this.BLOCKED_DOMAINS) {
      if (hostname === blocked || hostname.endsWith(`.${blocked}`)) {
        throw new PolicyViolation(`Domain "${hostname}" is blocked: ToS prohibits scraping`);
      }
    }

    for (const pattern of this.SENSITIVE_DOMAINS) {
      const regex = new RegExp("^" + pattern.replace("*.", ".*\\.") + "$");
      if (regex.test(hostname)) {
        console.warn(`CAUTION: "${hostname}" matches sensitive domain pattern "${pattern}"`);
      }
    }
  }
}

class PolicyViolation extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PolicyViolation";
  }
}
```

### Step 2: Credit Budget Enforcement
```typescript
class CrawlBudget {
  private usage = new Map<string, number>();
  private dailyLimit: number;

  constructor(dailyLimit = 5000) {
    this.dailyLimit = dailyLimit;
  }

  authorize(estimatedPages: number): void {
    const today = new Date().toISOString().split("T")[0];
    const used = this.usage.get(today) || 0;

    if (used + estimatedPages > this.dailyLimit) {
      throw new PolicyViolation(
        `Daily credit limit would be exceeded: ${used} used + ${estimatedPages} requested > ${this.dailyLimit} limit`
      );
    }
  }

  record(pagesScraped: number) {
    const today = new Date().toISOString().split("T")[0];
    this.usage.set(today, (this.usage.get(today) || 0) + pagesScraped);
  }
}

const budget = new CrawlBudget(5000);
```

### Step 3: Content Quality Gate
```typescript
function validateScrapedContent(result: any): {
  accepted: boolean;
  reason?: string;
} {
  const md = result.markdown || "";

  // Reject thin content
  if (md.length < 50) {
    return { accepted: false, reason: "Content too short (<50 chars)" };
  }

  // Reject error pages
  if (/403 forbidden|access denied|captcha/i.test(md)) {
    return { accepted: false, reason: "Error page detected" };
  }

  // Reject login walls
  if (/sign in to continue|create an account|login required/i.test(md)) {
    return { accepted: false, reason: "Login wall detected" };
  }

  // Reject cookie consent pages (only content is cookie notice)
  if (md.length < 500 && /cookie|consent|gdpr/i.test(md)) {
    return { accepted: false, reason: "Cookie consent page only" };
  }

  return { accepted: true };
}
```

### Step 4: Crawl Limit Enforcement
```typescript
const MAX_CRAWL_LIMIT = 500;
const MAX_DEPTH = 5;

async function policedCrawl(url: string, requestedLimit: number) {
  // Validate URL
  ScrapePolicy.validateUrl(url);

  // Enforce hard limits
  const limit = Math.min(requestedLimit, MAX_CRAWL_LIMIT);
  if (requestedLimit > MAX_CRAWL_LIMIT) {
    console.warn(`Crawl limit capped: ${requestedLimit} -> ${MAX_CRAWL_LIMIT}`);
  }

  // Check budget
  budget.authorize(limit);

  // Execute with enforced limits
  const result = await firecrawl.crawlUrl(url, {
    limit,
    maxDepth: MAX_DEPTH,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });

  // Record actual usage
  const pagesScraped = result.data?.length || 0;
  budget.record(pagesScraped);

  // Filter by content quality
  const validPages = (result.data || []).filter(page => {
    const { accepted, reason } = validateScrapedContent(page);
    if (!accepted) console.log(`Rejected: ${page.metadata?.sourceURL} — ${reason}`);
    return accepted;
  });

  console.log(`Crawl: ${pagesScraped} scraped, ${validPages.length} accepted, ${pagesScraped - validPages.length} rejected`);
  return validPages;
}
```

### Step 5: Per-Domain Rate Limiting
```typescript
const DOMAIN_RATE_LIMITS: Record<string, number> = {
  "docs.example.com": 2,    // 2 requests/second
  "blog.example.com": 1,    // 1 request/second
  default: 5,               // 5 requests/second
};

const lastRequest = new Map<string, number>();

async function rateLimitedScrape(url: string) {
  const domain = new URL(url).hostname;
  const rate = DOMAIN_RATE_LIMITS[domain] || DOMAIN_RATE_LIMITS.default;
  const minInterval = 1000 / rate;

  const last = lastRequest.get(domain) || 0;
  const elapsed = Date.now() - last;
  if (elapsed < minInterval) {
    await new Promise(r => setTimeout(r, minInterval - elapsed));
  }

  lastRequest.set(domain, Date.now());
  return firecrawl.scrapeUrl(url, { formats: ["markdown"] });
}
```

## Policy Summary

| Policy | Enforcement | Consequence |
|--------|-------------|-------------|
| Domain blocklist | Pre-request check | Request rejected with PolicyViolation |
| Credit budget | Pre-request check | Request rejected if over daily limit |
| Crawl limit | Hard cap at 500 | Silently capped, logged |
| Content quality | Post-scrape filter | Invalid pages excluded from results |
| Per-domain rate | Pre-request delay | Automatic throttling |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PolicyViolation thrown | Blocked domain | Remove from scrape targets |
| Budget exceeded | Heavy scraping day | Increase daily limit or wait |
| Many rejected pages | Error/login pages | Check target site, adjust URL patterns |
| Slow scraping | Per-domain rate limit | Expected behavior, protects target site |

## Examples

### Policy-Checked Pipeline
```typescript
async function scrapePipeline(urls: string[]) {
  const results = [];
  for (const url of urls) {
    try {
      ScrapePolicy.validateUrl(url);
      budget.authorize(1);
      const result = await rateLimitedScrape(url);
      const { accepted } = validateScrapedContent(result);
      if (accepted) results.push(result);
      budget.record(1);
    } catch (e) {
      if (e instanceof PolicyViolation) {
        console.warn(`Policy: ${e.message}`);
      } else {
        console.error(`Error: ${(e as Error).message}`);
      }
    }
  }
  return results;
}
```

## Resources
- [Firecrawl Docs](https://docs.firecrawl.dev)
- [robots.txt Spec](https://www.robotstxt.org/robotstxt.html)
- [Web Scraping Legal Guide](https://www.eff.org/issues/web-scraping)

## Next Steps
For architecture patterns, see `firecrawl-architecture-variants`.
