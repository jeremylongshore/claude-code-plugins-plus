---
name: brightdata-cost-tuning
description: |
  Optimize Bright Data costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Bright Data billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "brightdata cost", "brightdata billing",
  "reduce brightdata costs", "brightdata pricing", "brightdata expensive", "brightdata budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Cost Tuning

## Overview

Optimize Bright Data costs through product selection, caching, and usage monitoring. Bright Data charges per request (Web Unlocker, SERP API), per GB (Residential Proxy), or per page (Datasets). Choosing the right product and avoiding redundant requests is the primary cost lever.

## Prerequisites

- Access to Bright Data billing dashboard
- Understanding of current scraping volumes
- Usage monitoring configured (optional)

## Pricing Model

| Product | Pricing | Typical Cost | Best For |
|---------|---------|-------------|----------|
| Residential Proxy | Per GB transferred | $8-15/GB | High-volume, simple pages |
| Web Unlocker | Per successful request | $1-3/1000 req | Anti-bot protected sites |
| Scraping Browser | Per browser session | $5-10/1000 sessions | JS-heavy SPAs |
| SERP API | Per search | $2-5/1000 searches | Search engine results |
| Datasets (pre-built) | Per record | $0.001-0.01/record | Bulk data (Amazon, LinkedIn) |
| Web Scraper API | Per page | Varies by dataset | Custom async scraping |

## Instructions

### Step 1: Product Selection Cost Matrix

```typescript
function estimateMonthlyCost(config: {
  product: 'residential' | 'web_unlocker' | 'scraping_browser' | 'serp_api';
  requestsPerMonth: number;
  avgPageSizeKB?: number;
}) {
  switch (config.product) {
    case 'residential':
      const gbTransferred = (config.requestsPerMonth * (config.avgPageSizeKB || 200)) / 1_000_000;
      return { cost: gbTransferred * 10, unit: 'GB', quantity: gbTransferred };
    case 'web_unlocker':
      return { cost: config.requestsPerMonth * 0.002, unit: 'requests', quantity: config.requestsPerMonth };
    case 'scraping_browser':
      return { cost: config.requestsPerMonth * 0.008, unit: 'sessions', quantity: config.requestsPerMonth };
    case 'serp_api':
      return { cost: config.requestsPerMonth * 0.003, unit: 'searches', quantity: config.requestsPerMonth };
  }
}

// Example: 50,000 product pages/month
console.log(estimateMonthlyCost({ product: 'web_unlocker', requestsPerMonth: 50000 }));
// { cost: 100, unit: 'requests', quantity: 50000 }
console.log(estimateMonthlyCost({ product: 'residential', requestsPerMonth: 50000, avgPageSizeKB: 300 }));
// { cost: 150, unit: 'GB', quantity: 15 }
```

### Step 2: Reduce Costs with Caching

```typescript
// Response caching is the single biggest cost saver
// Cache policy by data freshness requirements
const CACHE_TTLS = {
  product_price: 3600000,     // 1 hour — prices change frequently
  product_details: 86400000,  // 24 hours — descriptions rarely change
  search_results: 1800000,    // 30 minutes — SERPs change often
  static_page: 604800000,     // 7 days — about/contact pages
};

// Track cache savings
let cacheSavings = 0;
function trackCacheHit(product: string) {
  const costPerRequest = { web_unlocker: 0.002, scraping_browser: 0.008, serp_api: 0.003 };
  cacheSavings += costPerRequest[product] || 0.002;
  console.log(`Cache savings this session: $${cacheSavings.toFixed(4)}`);
}
```

### Step 3: Use Bulk APIs for Volume Jobs

```typescript
// Individual requests: 50,000 requests * $0.002 = $100
// Web Scraper API: 1 trigger with 50,000 URLs = typically cheaper (volume discounts)

async function bulkScrapeForCost(urls: string[]) {
  // Batch into single trigger — one API call, lower cost
  const response = await fetch(
    `https://api.brightdata.com/datasets/v3/trigger?dataset_id=${DATASET_ID}&format=json`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.BRIGHTDATA_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(urls.map(url => ({ url }))),
    }
  );
  return response.json();
}
```

### Step 4: Usage Monitoring

```typescript
class BrightDataUsageTracker {
  private dailyRequests = 0;
  private dailyCost = 0;
  private readonly budgetAlert: number;

  constructor(dailyBudgetUSD: number) {
    this.budgetAlert = dailyBudgetUSD * 0.8;
  }

  track(product: string) {
    this.dailyRequests++;
    const costs = { web_unlocker: 0.002, scraping_browser: 0.008, serp_api: 0.003, residential: 0.0001 };
    this.dailyCost += costs[product] || 0.002;

    if (this.dailyCost > this.budgetAlert) {
      console.warn(`BUDGET ALERT: Daily cost $${this.dailyCost.toFixed(2)} exceeds 80% of budget`);
    }
  }

  report() {
    return {
      requests: this.dailyRequests,
      estimatedCost: `$${this.dailyCost.toFixed(2)}`,
      projectedMonthly: `$${(this.dailyCost * 30).toFixed(2)}`,
    };
  }
}
```

### Step 5: Cost Reduction Checklist

- [ ] Cache responses to avoid re-scraping same URLs
- [ ] Use Residential Proxy for simple pages (cheaper per request)
- [ ] Use Web Scraper API for 100+ URL bulk jobs
- [ ] Use Datasets API for common targets (Amazon, LinkedIn) — pre-built scrapers
- [ ] Set budget alerts in Bright Data CP > Billing
- [ ] Monitor daily usage with tracker class above
- [ ] Avoid Scraping Browser for pages that don't need JavaScript

## Output

- Product selection matching cost requirements
- Response caching reducing redundant requests
- Budget monitoring and alerting
- Projected monthly cost estimates

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected charges | Using expensive product for simple pages | Switch to Residential Proxy |
| Budget exceeded | No monitoring | Implement usage tracker |
| Overpaying for data | Scraping what Datasets API provides | Check pre-built datasets first |
| High per-request cost | No caching | Add response cache (biggest lever) |

## Resources

- [Bright Data Pricing](https://brightdata.com/pricing)
- [Billing Dashboard](https://brightdata.com/cp/billing)
- [Pre-built Datasets](https://brightdata.com/products/datasets)

## Next Steps

For architecture patterns, see `brightdata-reference-architecture`.
