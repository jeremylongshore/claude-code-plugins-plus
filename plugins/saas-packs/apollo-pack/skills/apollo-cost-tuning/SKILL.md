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
---
# Apollo Cost Tuning

## Overview
Optimize Apollo.io API costs through credit-aware caching, contact deduplication, smart enrichment scoring, usage tracking, and budget-controlled API clients. Apollo charges enrichment credits per unique contact/company lookup.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Track Credit Usage
```typescript
// src/cost/credit-tracker.ts
interface CreditUsage {
  enrichments: number;
  searches: number;
  timestamp: string;
}

class CreditTracker {
  private usage: CreditUsage[] = [];
  private readonly budgetPerDay: number;

  constructor(dailyBudget: number = 200) {
    this.budgetPerDay = dailyBudget;
  }

  record(type: 'enrichments' | 'searches', count: number = 1) {
    const today = new Date().toISOString().split('T')[0];
    let entry = this.usage.find((u) => u.timestamp === today);
    if (!entry) {
      entry = { enrichments: 0, searches: 0, timestamp: today };
      this.usage.push(entry);
    }
    entry[type] += count;
  }

  todayUsage(): CreditUsage | undefined {
    const today = new Date().toISOString().split('T')[0];
    return this.usage.find((u) => u.timestamp === today);
  }

  isOverBudget(): boolean {
    const today = this.todayUsage();
    if (!today) return false;
    return today.enrichments >= this.budgetPerDay;
  }

  report(): string {
    const today = this.todayUsage();
    const used = today?.enrichments ?? 0;
    return `Credits: ${used}/${this.budgetPerDay} (${Math.round((used / this.budgetPerDay) * 100)}%)`;
  }
}

export const creditTracker = new CreditTracker(
  parseInt(process.env.APOLLO_DAILY_CREDIT_BUDGET ?? '200', 10),
);
```

### Step 2: Implement Contact Deduplication
```typescript
// src/cost/dedup.ts
import { LRUCache } from 'lru-cache';

// Track already-enriched contacts to avoid paying twice
const enrichedContacts = new LRUCache<string, boolean>({
  max: 50_000,
  ttl: 30 * 24 * 60 * 60 * 1000,  // 30 days
});

export function isAlreadyEnriched(identifier: string): boolean {
  return enrichedContacts.has(identifier);
}

export function markEnriched(identifier: string) {
  enrichedContacts.set(identifier, true);
}

// Use before making enrichment calls:
// const key = email || linkedinUrl || `${firstName}:${lastName}:${domain}`;
// if (isAlreadyEnriched(key)) {
//   console.log('Skipping — already enriched within 30 days');
//   return cachedResult;
// }
```

### Step 3: Smart Enrichment Scoring (Enrich Only High-Value Leads)
```typescript
// src/cost/enrichment-scorer.ts
interface LeadSignals {
  title: string;
  seniority?: string;
  companySize?: number;
  hasEmail: boolean;
  hasLinkedIn: boolean;
}

function shouldEnrich(signals: LeadSignals): boolean {
  let score = 0;

  // Seniority scoring — prioritize decision-makers
  const highSeniority = ['c_suite', 'vp', 'director', 'founder', 'owner'];
  if (highSeniority.includes(signals.seniority ?? '')) score += 40;
  else if (signals.seniority === 'manager') score += 20;
  else score += 5;

  // Company size — mid-market is highest value
  if (signals.companySize && signals.companySize >= 50 && signals.companySize <= 1000) {
    score += 30;
  } else if (signals.companySize && signals.companySize > 1000) {
    score += 15;
  }

  // Already have contact info?
  if (!signals.hasEmail) score += 20;   // worth enriching
  if (!signals.hasLinkedIn) score += 10;

  // Only enrich if score exceeds threshold
  return score >= 40;
}
```

### Step 4: Build a Budget-Aware API Client
```typescript
// src/cost/budget-client.ts
import axios from 'axios';
import { creditTracker } from './credit-tracker';
import { isAlreadyEnriched, markEnriched } from './dedup';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
  headers: { 'Content-Type': 'application/json' },
});

// Credit-consuming endpoints
const CREDIT_ENDPOINTS = ['/people/match', '/organizations/enrich'];

client.interceptors.request.use((config) => {
  const isCreditEndpoint = CREDIT_ENDPOINTS.some(
    (ep) => config.url?.includes(ep),
  );

  if (isCreditEndpoint && creditTracker.isOverBudget()) {
    throw new Error(
      `Daily credit budget exceeded (${creditTracker.report()}). ` +
      'Increase APOLLO_DAILY_CREDIT_BUDGET or wait until tomorrow.',
    );
  }

  return config;
});

client.interceptors.response.use((response) => {
  const isCreditEndpoint = CREDIT_ENDPOINTS.some(
    (ep) => response.config.url?.includes(ep),
  );

  if (isCreditEndpoint) {
    creditTracker.record('enrichments');
    // Mark contact as enriched for dedup
    const email = response.data?.person?.email ?? response.config.data?.email;
    if (email) markEnriched(email);
  } else {
    creditTracker.record('searches');
  }

  return response;
});

export { client as budgetClient };
```

### Step 5: Generate Cost Reports
```typescript
// src/scripts/cost-report.ts
function generateCostReport() {
  const usage = creditTracker.todayUsage();
  const estimatedCostPerCredit = 0.03;  // varies by plan

  console.log('=== Apollo Cost Report ===');
  console.log(`Date:           ${new Date().toISOString().split('T')[0]}`);
  console.log(`Enrichments:    ${usage?.enrichments ?? 0}`);
  console.log(`Searches:       ${usage?.searches ?? 0}`);
  console.log(`Est. Cost:      $${((usage?.enrichments ?? 0) * estimatedCostPerCredit).toFixed(2)}`);
  console.log(`Budget Used:    ${creditTracker.report()}`);
  console.log(`Over Budget:    ${creditTracker.isOverBudget() ? 'YES' : 'No'}`);
}
```

## Output
- `CreditTracker` class with daily budget enforcement and usage reporting
- LRU-based contact deduplication preventing duplicate enrichment charges
- Lead scoring function to enrich only high-value contacts
- Budget-aware axios client that blocks requests when credits are exhausted
- Daily cost report with estimated dollar amounts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Budget exceeded | Increase `APOLLO_DAILY_CREDIT_BUDGET` env var or wait for daily reset |
| High cache misses | Extend dedup TTL from 30 to 60 days |
| Duplicate enrichments | Verify dedup key uses email or LinkedIn URL as primary identifier |
| Unexpected costs | Run `generateCostReport()` daily, review enrichment-to-search ratio |

## Examples

### Cost-Optimized Enrichment Pipeline
```typescript
import { budgetClient } from './cost/budget-client';
import { shouldEnrich } from './cost/enrichment-scorer';
import { isAlreadyEnriched } from './cost/dedup';

async function enrichHighValueLeads(people: any[]) {
  let enriched = 0, skipped = 0, deduplicated = 0;

  for (const person of people) {
    if (isAlreadyEnriched(person.email)) { deduplicated++; continue; }
    if (!shouldEnrich({ title: person.title, seniority: person.seniority, hasEmail: !!person.email, hasLinkedIn: !!person.linkedin_url })) { skipped++; continue; }

    await budgetClient.post('/people/match', { email: person.email });
    enriched++;
  }

  console.log(`Enriched: ${enriched}, Skipped (low-value): ${skipped}, Deduped: ${deduplicated}`);
  console.log(creditTracker.report());
}
```

## Resources
- [Apollo Pricing](https://www.apollo.io/pricing)
- [Apollo Credit System](https://knowledge.apollo.io/hc/en-us/articles/4415144183053)
- [Apollo Usage Dashboard](https://app.apollo.io/settings/billing)

## Next Steps
Proceed to `apollo-reference-architecture` for architecture patterns.
