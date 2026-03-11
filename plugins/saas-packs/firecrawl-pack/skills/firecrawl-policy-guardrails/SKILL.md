---
name: firecrawl-policy-guardrails
description: |
  Implement FireCrawl lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for FireCrawl integrations, implementing
  pre-commit hooks, or configuring CI policy checks for FireCrawl best practices.
  Trigger with phrases like "firecrawl policy", "firecrawl lint",
  "firecrawl guardrails", "firecrawl best practices check", "firecrawl eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Policy Guardrails

## Overview
Policy enforcement for Firecrawl web scraping pipelines. Web scraping raises legal (robots.txt, ToS), ethical (rate limiting, attribution), and cost (credit burn) concerns that need automated guardrails.

## Prerequisites
- Firecrawl API configured
- Understanding of web scraping legal considerations
- Credit monitoring setup

## Instructions

### Step 1: Enforce Domain-Level Scraping Policies

Block scraping of sensitive or prohibited domains.

```typescript
const SCRAPE_POLICY = {
  blockedDomains: [
    'facebook.com', 'linkedin.com',   // ToS prohibit scraping
    'bank*.com', 'healthcare*.com',   // sensitive data
  ],
  maxPagesPerDomain: 500,
  requireRobotsTxt: true,
};

function validateScrapeTarget(url: string): void {
  const domain = new URL(url).hostname;
  for (const blocked of SCRAPE_POLICY.blockedDomains) {
    const pattern = new RegExp('^' + blocked.replace('*', '.*') + '$');
    if (pattern.test(domain)) {
      throw new PolicyViolation(`Domain ${domain} is blocked by scraping policy`);
    }
  }
}
```

### Step 2: Credit Budget Enforcement

Prevent crawls from exceeding allocated credit budgets.

```typescript
class CrawlBudget {
  private dailyLimit: number;
  private usage: Map<string, number> = new Map();

  constructor(dailyLimit = 5000) { this.dailyLimit = dailyLimit; }

  authorize(estimatedPages: number): boolean {
    const today = new Date().toISOString().split('T')[0];
    const used = this.usage.get(today) || 0;
    if (used + estimatedPages > this.dailyLimit) {
      throw new PolicyViolation(
        `Daily limit exceeded: ${used} + ${estimatedPages} > ${this.dailyLimit}`
      );
    }
    return true;
  }

  record(pagesScraped: number) {
    const today = new Date().toISOString().split('T')[0];
    this.usage.set(today, (this.usage.get(today) || 0) + pagesScraped);
  }
}
```

### Step 3: Content Type Filtering

Only retain scraped content that matches expected types; discard binary files, media, and error pages.

```typescript
function validateScrapedContent(result: any): boolean {
  if (!result.markdown || result.markdown.length < 50) return false;
  const lower = result.markdown.toLowerCase();
  // Reject error pages
  if (lower.includes('403 forbidden') || lower.includes('access denied')) return false;
  // Reject login walls
  if (lower.includes('sign in to continue') || lower.includes('create an account')) return false;
  return true;
}
```

### Step 4: Rate Limiting Per Target Domain

Respect target site capacity even when Firecrawl allows faster crawling.

```typescript
const DOMAIN_RATE_LIMITS: Record<string, number> = {
  'docs.example.com': 2,    // 2 pages/second
  'blog.example.com': 1,    // 1 page/second
  'default': 5              // default rate
};

function getCrawlDelay(domain: string): number {
  const rate = DOMAIN_RATE_LIMITS[domain] || DOMAIN_RATE_LIMITS['default'];
  return 1000 / rate;  // milliseconds between requests
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Legal risk from scraping | Blocked domain not filtered | Enforce domain blocklist |
| Credit overrun | No budget tracking | Implement daily credit caps |
| Junk data in pipeline | Error pages scraped | Validate content quality |
| Target site blocking IP | Too aggressive crawling | Enforce per-domain rate limits |

## Examples

### Policy-Checked Crawl
```typescript
validateScrapeTarget(url);
budget.authorize(estimatedPages);
const results = await firecrawl.crawlUrl(url, { limit: estimatedPages });
const valid = results.filter(validateScrapedContent);
budget.record(valid.length);
```

## Resources
- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Web Scraping Legal Guide](https://www.eff.org/issues/web-scraping)
