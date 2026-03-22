---
name: apollo-cost-tuning
description: |
  Optimize Apollo.io costs and credit usage.
  Use when managing Apollo credits, reducing API costs,
  or optimizing subscription usage.
  Trigger with phrases like "apollo cost", "apollo credits",
  "apollo billing", "reduce apollo costs", "apollo usage".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api, cost-optimization]

---
# Apollo Cost Tuning

## Overview
Optimize Apollo.io API costs through credit-aware enrichment. Key cost model: **search is free, enrichment costs credits.** Apollo charges per unique contact/company lookup. Credits do not roll over. Strategies: deduplicate before enriching, score leads before spending credits, and track daily budget.

## Prerequisites
- Valid Apollo API key
- Node.js 18+

## Instructions

### Step 1: Understand Apollo's Credit Model
```
Action                      | Credits | Notes
----------------------------+---------+-----------------------------------
People Search               | 0       | /mixed_people/api_search (free!)
Organization Search         | 0       | /mixed_companies/search (free!)
People Enrichment (single)  | 1       | /people/match
People Enrichment (bulk)    | 1/match | /people/bulk_match (up to 10/call)
Organization Enrichment     | 1       | /organizations/enrich
Reveal Personal Email       | +1      | reveal_personal_emails param
Reveal Phone Number         | +1      | reveal_phone_number param
```

Plans (approximate):
- **Free**: 50 credits/month
- **Basic**: 1,200 credits/month (~$0.04/credit)
- **Professional**: 6,000 credits/month
- **Organization**: 12,000+ credits/month

### Step 2: Track Credit Usage
```typescript
// src/cost/credit-tracker.ts
class CreditTracker {
  private daily: Map<string, number> = new Map();
  private readonly budget: number;

  constructor(dailyBudget: number = 200) {
    this.budget = dailyBudget;
  }

  record(count: number = 1) {
    const today = new Date().toISOString().split('T')[0];
    this.daily.set(today, (this.daily.get(today) ?? 0) + count);
  }

  todayUsage(): number {
    const today = new Date().toISOString().split('T')[0];
    return this.daily.get(today) ?? 0;
  }

  isOverBudget(): boolean {
    return this.todayUsage() >= this.budget;
  }

  report(): string {
    const used = this.todayUsage();
    return `${used}/${this.budget} credits (${Math.round((used / this.budget) * 100)}%)`;
  }
}

export const creditTracker = new CreditTracker(
  parseInt(process.env.APOLLO_DAILY_CREDIT_BUDGET ?? '200', 10),
);
```

### Step 3: Deduplicate Before Enriching
```typescript
// src/cost/dedup.ts
import { LRUCache } from 'lru-cache';

// Track enriched contacts to avoid paying twice
const enrichedCache = new LRUCache<string, boolean>({
  max: 50_000,
  ttl: 30 * 24 * 60 * 60 * 1000,  // 30 days
});

export function enrichmentKey(params: { email?: string; linkedin_url?: string;
  first_name?: string; last_name?: string; organization_domain?: string }): string {
  // Prefer email as unique key, fall back to LinkedIn, then name+domain
  return params.email
    ?? params.linkedin_url
    ?? `${params.first_name}:${params.last_name}:${params.organization_domain}`;
}

export function isAlreadyEnriched(key: string): boolean {
  return enrichedCache.has(key);
}

export function markEnriched(key: string) {
  enrichedCache.set(key, true);
}
```

### Step 4: Score Leads Before Enriching
Only spend credits on leads worth contacting.

```typescript
// src/cost/lead-scorer.ts
interface LeadSignals {
  seniority?: string;
  title?: string;
  companyEmployees?: number;
  hasEmail: boolean;
  hasPhone: boolean;
  hasLinkedIn: boolean;
}

export function shouldEnrich(signals: LeadSignals, threshold: number = 40): boolean {
  let score = 0;

  // Seniority — only enrich decision-makers
  const topSeniority = ['c_suite', 'vp', 'founder', 'owner'];
  if (topSeniority.includes(signals.seniority ?? '')) score += 40;
  else if (signals.seniority === 'director') score += 30;
  else if (signals.seniority === 'manager') score += 15;
  else score += 5;

  // Company size — mid-market is highest value
  if (signals.companyEmployees && signals.companyEmployees >= 50 && signals.companyEmployees <= 1000) score += 25;
  else if (signals.companyEmployees && signals.companyEmployees > 1000) score += 15;

  // Missing data — worth enriching if we need the contact info
  if (!signals.hasEmail) score += 20;
  if (!signals.hasPhone) score += 10;

  return score >= threshold;
}
```

### Step 5: Budget-Aware API Client
```typescript
// src/cost/budget-client.ts
import axios from 'axios';
import { creditTracker } from './credit-tracker';
import { isAlreadyEnriched, markEnriched, enrichmentKey } from './dedup';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

// Credit-consuming endpoints
const CREDIT_ENDPOINTS = ['/people/match', '/people/bulk_match', '/organizations/enrich'];

// Block requests when over budget
client.interceptors.request.use((config) => {
  const isCreditEndpoint = CREDIT_ENDPOINTS.some((ep) => config.url?.includes(ep));
  if (isCreditEndpoint && creditTracker.isOverBudget()) {
    throw new Error(`Daily credit budget exceeded (${creditTracker.report()})`);
  }
  return config;
});

// Track credit usage on success
client.interceptors.response.use((response) => {
  const isCreditEndpoint = CREDIT_ENDPOINTS.some((ep) => response.config.url?.includes(ep));
  if (isCreditEndpoint) {
    // Bulk match: count matches, not calls
    const matchCount = response.data?.matches?.length ?? 1;
    creditTracker.record(matchCount);

    // Mark as enriched for dedup
    const email = response.data?.person?.email;
    if (email) markEnriched(email);
  }
  return response;
});

export { client as budgetClient };
```

### Step 6: Cost-Optimized Pipeline
```typescript
import { budgetClient } from './cost/budget-client';
import { shouldEnrich } from './cost/lead-scorer';
import { isAlreadyEnriched, enrichmentKey } from './cost/dedup';
import { creditTracker } from './cost/credit-tracker';

async function enrichHighValueLeads(people: any[]) {
  let enriched = 0, skipped = 0, deduped = 0;

  const toEnrich: any[] = [];

  for (const person of people) {
    const key = enrichmentKey({ email: person.email, linkedin_url: person.linkedin_url,
      first_name: person.first_name, last_name: person.last_name });

    if (isAlreadyEnriched(key)) { deduped++; continue; }
    if (!shouldEnrich({ seniority: person.seniority, hasEmail: !!person.email,
      hasPhone: false, hasLinkedIn: !!person.linkedin_url })) { skipped++; continue; }

    toEnrich.push(person);
  }

  // Bulk enrich in batches of 10
  for (let i = 0; i < toEnrich.length; i += 10) {
    const batch = toEnrich.slice(i, i + 10);
    await budgetClient.post('/people/bulk_match', {
      details: batch.map((p: any) => ({
        first_name: p.first_name, last_name: p.last_name,
        organization_domain: p.organization?.primary_domain,
      })),
    });
    enriched += batch.length;
  }

  console.log(`Enriched: ${enriched}, Skipped (low-value): ${skipped}, Deduped: ${deduped}`);
  console.log(`Credits: ${creditTracker.report()}`);
}
```

## Output
- Credit model reference table (free vs paid operations)
- `CreditTracker` with daily budget enforcement
- LRU deduplication preventing double-enrichment charges
- Lead scoring to enrich only high-value contacts
- Budget-aware client blocking requests at daily limit
- Cost-optimized pipeline combining all strategies

## Error Handling
| Issue | Resolution |
|-------|------------|
| Budget exceeded | Increase `APOLLO_DAILY_CREDIT_BUDGET` or wait until tomorrow |
| High dedup misses | Extend LRU TTL, verify key generation logic |
| Enriching low-value leads | Lower the `shouldEnrich` threshold |
| Month-end credit crunch | Spread enrichment evenly with daily budgets |

## Resources
- [Apollo API Pricing](https://docs.apollo.io/docs/api-pricing)
- [Apollo Plans](https://www.apollo.io/pricing)
- [View API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

## Next Steps
Proceed to `apollo-reference-architecture` for architecture patterns.
