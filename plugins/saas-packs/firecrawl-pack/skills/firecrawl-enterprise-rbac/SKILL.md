---
name: firecrawl-enterprise-rbac
description: |
  Configure Firecrawl team access control with per-key credit limits and domain restrictions.
  Use when managing multiple API keys per team, implementing credit budgets per consumer,
  or controlling which domains each team can scrape.
  Trigger with phrases like "firecrawl RBAC", "firecrawl teams",
  "firecrawl enterprise", "firecrawl access control", "firecrawl permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, rbac]

---
# Firecrawl Enterprise RBAC

## Overview
Control access to Firecrawl scraping resources through API key management, domain allowlists, and credit budgets per team. Firecrawl's credit-based pricing means access control is primarily about limiting credit consumption and restricting scrape targets per consumer.

## Prerequisites
- Firecrawl Team or Scale plan
- Dashboard access at [firecrawl.dev/app](https://firecrawl.dev/app)
- Understanding of credit-per-page billing

## Instructions

### Step 1: Separate API Keys per Consumer
```bash
set -euo pipefail
# Create dedicated keys at firecrawl.dev/app for each team/service

# Content indexing pipeline — high volume
# Key: fc-content-indexer-prod (monthly credit limit: 50,000)

# Sales team prospect research — scrape only
# Key: fc-sales-research (monthly credit limit: 5,000)

# Dev/testing — minimal
# Key: fc-dev-testing (monthly credit limit: 500)
```

### Step 2: Gateway Proxy with Domain Allowlists
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const TEAM_POLICIES: Record<string, {
  apiKey: string;
  allowedDomains: string[];
  maxPagesPerCrawl: number;
  dailyCreditLimit: number;
}> = {
  "content-team": {
    apiKey: process.env.FIRECRAWL_KEY_CONTENT!,
    allowedDomains: ["docs.*", "*.readthedocs.io", "medium.com"],
    maxPagesPerCrawl: 200,
    dailyCreditLimit: 2000,
  },
  "sales-team": {
    apiKey: process.env.FIRECRAWL_KEY_SALES!,
    allowedDomains: ["linkedin.com", "crunchbase.com", "g2.com"],
    maxPagesPerCrawl: 20,
    dailyCreditLimit: 500,
  },
  "engineering": {
    apiKey: process.env.FIRECRAWL_KEY_ENGINEERING!,
    allowedDomains: ["*"],  // unrestricted
    maxPagesPerCrawl: 100,
    dailyCreditLimit: 1000,
  },
};

function isDomainAllowed(team: string, url: string): boolean {
  const policy = TEAM_POLICIES[team];
  if (!policy) return false;
  const domain = new URL(url).hostname;
  return policy.allowedDomains.some(pattern =>
    pattern === "*" || domain.endsWith(pattern.replace("*.", "").replace("*", ""))
  );
}

function getTeamClient(team: string): FirecrawlApp {
  const policy = TEAM_POLICIES[team];
  if (!policy) throw new Error(`Unknown team: ${team}`);
  return new FirecrawlApp({ apiKey: policy.apiKey });
}
```

### Step 3: Credit Budget Enforcement
```typescript
class TeamBudget {
  private usage = new Map<string, Map<string, number>>(); // team -> date -> credits

  record(team: string, credits: number) {
    const today = new Date().toISOString().split("T")[0];
    if (!this.usage.has(team)) this.usage.set(team, new Map());
    const teamUsage = this.usage.get(team)!;
    teamUsage.set(today, (teamUsage.get(today) || 0) + credits);
  }

  canAfford(team: string, credits: number): boolean {
    const policy = TEAM_POLICIES[team];
    if (!policy) return false;
    const today = new Date().toISOString().split("T")[0];
    const used = this.usage.get(team)?.get(today) || 0;
    return used + credits <= policy.dailyCreditLimit;
  }

  getUsage(team: string): number {
    const today = new Date().toISOString().split("T")[0];
    return this.usage.get(team)?.get(today) || 0;
  }
}

const budget = new TeamBudget();
```

### Step 4: Policy-Enforced Scraping
```typescript
export async function teamScrape(team: string, url: string) {
  // Check domain policy
  if (!isDomainAllowed(team, url)) {
    throw new Error(`Team "${team}" is not allowed to scrape ${new URL(url).hostname}`);
  }

  // Check credit budget
  if (!budget.canAfford(team, 1)) {
    throw new Error(`Team "${team}" has exceeded daily credit limit`);
  }

  // Scrape with team's API key
  const client = getTeamClient(team);
  const result = await client.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
  });

  budget.record(team, 1);
  return result;
}

export async function teamCrawl(team: string, url: string, pages: number) {
  const policy = TEAM_POLICIES[team];
  if (!policy) throw new Error(`Unknown team: ${team}`);

  if (!isDomainAllowed(team, url)) {
    throw new Error(`Domain not allowed for team "${team}"`);
  }

  const limit = Math.min(pages, policy.maxPagesPerCrawl);
  if (!budget.canAfford(team, limit)) {
    throw new Error(`Crawl of ${limit} pages exceeds "${team}" daily budget`);
  }

  const client = getTeamClient(team);
  const result = await client.crawlUrl(url, {
    limit,
    maxDepth: 3,
    scrapeOptions: { formats: ["markdown"] },
  });

  budget.record(team, result.data?.length || 0);
  return result;
}
```

### Step 5: Key Rotation Schedule
```bash
set -euo pipefail
# Rotate keys quarterly:
# 1. Create new key at firecrawl.dev/app
# 2. Deploy new key alongside old (both valid)
# 3. Verify new key works
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $NEW_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq .success
# 4. Remove old key from all services
# 5. Delete old key in dashboard after 48-hour overlap
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `402 Payment Required` | Team credit limit reached | Increase limit or wait for reset |
| `403` on domain | Domain not in allowlist | Add domain to team policy |
| Unexpected credit burn | No crawl limit enforced | Use `maxPagesPerCrawl` from policy |
| Wrong team key used | Config error | Verify key-to-team mapping |

## Examples

### Audit Team Usage
```typescript
for (const team of Object.keys(TEAM_POLICIES)) {
  console.log(`${team}: ${budget.getUsage(team)} credits today`);
}
```

## Resources
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Firecrawl Rate Limits](https://docs.firecrawl.dev/rate-limits)
- [Firecrawl Pricing](https://firecrawl.dev/pricing)

## Next Steps
For migration strategies, see `firecrawl-migration-deep-dive`.
