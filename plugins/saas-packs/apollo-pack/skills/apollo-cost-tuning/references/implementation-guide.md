# Apollo Cost Tuning - Implementation Guide

> Full implementation details and code examples for the `apollo-cost-tuning` skill.

# Apollo Cost Tuning

## Overview
Optimize Apollo.io costs through efficient credit usage, smart caching, deduplication, and usage monitoring.

## Apollo Pricing Model

| Feature | Credit Cost | Notes |
|---------|-------------|-------|
| People Search | 1 credit/result | Paginated results |
| Email Reveal | 1 credit/email | First reveal only |
| Person Enrichment | 1 credit/person | Fresh data |
| Org Enrichment | 1 credit/org | Company data |
| Sequence Emails | Included | Plan limits apply |
| Export | Varies | Bulk operations |

## Cost Reduction Strategies

### 1. Aggressive Caching

```typescript
// src/lib/apollo/cost-aware-cache.ts
import { LRUCache } from 'lru-cache';

interface CachedContact {
  data: any;
  fetchedAt: Date;
  creditCost: number;
}

class CostAwareCache {
  private cache: LRUCache<string, CachedContact>;
  private creditsSaved = 0;

  constructor() {
    this.cache = new LRUCache({
      max: 10000,
      ttl: 7 * 24 * 60 * 60 * 1000, // 7 days for contact data
    });
  }

  getContact(email: string): CachedContact | null {
    const cached = this.cache.get(email);
    if (cached) {
      this.creditsSaved++;
      console.log(`Cache hit for ${email}. Total credits saved: ${this.creditsSaved}`);
    }
    return cached || null;
  }

  setContact(email: string, data: any, creditCost: number = 1): void {
    this.cache.set(email, {
      data,
      fetchedAt: new Date(),
      creditCost,
    });
  }

  getStats() {
    return {
      entriesCount: this.cache.size,
      creditsSaved: this.creditsSaved,
      estimatedSavings: this.creditsSaved * 0.01, // Assuming $0.01/credit
    };
  }
}

export const costAwareCache = new CostAwareCache();
```

### 2. Deduplication

```typescript
// src/lib/apollo/deduplication.ts
class DeduplicationService {
  private seenEmails = new Set<string>();
  private seenDomains = new Set<string>();

  async enrichContactSafe(email: string): Promise<any> {
    // Check if already enriched
    if (this.seenEmails.has(email)) {
      return costAwareCache.getContact(email);
    }

    // Check cache first
    const cached = costAwareCache.getContact(email);
    if (cached) {
      return cached.data;
    }

    // Fetch and cache
    const result = await apollo.enrichPerson({ email });
    costAwareCache.setContact(email, result, 1);
    this.seenEmails.add(email);

    return result;
  }

  async enrichOrgSafe(domain: string): Promise<any> {
    const normalizedDomain = domain.toLowerCase().replace(/^www\./, '');

    if (this.seenDomains.has(normalizedDomain)) {
      return costAwareCache.getContact(`org:${normalizedDomain}`);
    }

    const cached = costAwareCache.getContact(`org:${normalizedDomain}`);
    if (cached) {
      return cached.data;
    }

    const result = await apollo.enrichOrganization(normalizedDomain);
    costAwareCache.setContact(`org:${normalizedDomain}`, result, 1);
    this.seenDomains.add(normalizedDomain);

    return result;
  }
}

export const dedup = new DeduplicationService();
```

### 3. Smart Search Strategies

```typescript
// src/lib/apollo/cost-efficient-search.ts

/**
 * Cost-efficient search: Start broad, then narrow
 * Uses fewer credits by doing initial filtering before enrichment
 */
export async function costEfficientLeadSearch(criteria: LeadCriteria): Promise<Lead[]> {
  // Step 1: Search without enrichment (cheaper)
  const searchResults = await apollo.searchPeople({
    q_organization_domains: criteria.domains,
    person_titles: criteria.titles,
    per_page: 100,
    // Don't request emails yet - just basic info
  });

  // Step 2: Score and filter locally
  const scoredLeads = searchResults.people
    .map(person => ({
      ...person,
      score: calculateLeadScore(person, criteria),
    }))
    .filter(lead => lead.score >= criteria.minScore)
    .sort((a, b) => b.score - a.score)
    .slice(0, criteria.maxEnrichments || 25);

  // Step 3: Only enrich high-quality leads
  const enrichedLeads = await Promise.all(
    scoredLeads.map(async lead => {
      if (!lead.email) {
        // Only spend credit on email reveal if needed
        const enriched = await dedup.enrichContactSafe(lead.id);
        return { ...lead, ...enriched };
      }
      return lead;
    })
  );

  return enrichedLeads;
}

function calculateLeadScore(person: any, criteria: LeadCriteria): number {
  let score = 0;

  // Title match
  if (criteria.titles?.some(t =>
    person.title?.toLowerCase().includes(t.toLowerCase())
  )) {
    score += 30;
  }

  // Seniority
  if (['vp', 'director', 'c-level'].includes(person.seniority)) {
    score += 25;
  }

  // Has LinkedIn
  if (person.linkedin_url) {
    score += 15;
  }

  // Company size fit
  const employees = person.organization?.estimated_num_employees || 0;
  if (employees >= criteria.minEmployees && employees <= criteria.maxEmployees) {
    score += 20;
  }

  // Already has email (no enrichment needed)
  if (person.email) {
    score += 10;
  }

  return score;
}
```

### 4. Usage Monitoring

```typescript
// src/lib/apollo/usage-tracker.ts
interface UsageRecord {
  timestamp: Date;
  operation: string;
  credits: number;
  endpoint: string;
}

class UsageTracker {
  private records: UsageRecord[] = [];
  private monthlyBudget: number;
  private alertThreshold: number;

  constructor(monthlyBudget: number = 10000, alertThreshold: number = 0.8) {
    this.monthlyBudget = monthlyBudget;
    this.alertThreshold = alertThreshold;
  }

  track(operation: string, credits: number, endpoint: string): void {
    this.records.push({
      timestamp: new Date(),
      operation,
      credits,
      endpoint,
    });

    this.checkBudget();
  }

  private checkBudget(): void {
    const monthlyUsage = this.getMonthlyUsage();
    const usagePercent = monthlyUsage / this.monthlyBudget;

    if (usagePercent >= this.alertThreshold) {
      console.warn(`Apollo usage alert: ${(usagePercent * 100).toFixed(1)}% of monthly budget used`);
      // Could trigger webhook, Slack notification, etc.
    }

    if (usagePercent >= 1) {
      console.error('Apollo monthly budget exceeded!');
    }
  }

  getMonthlyUsage(): number {
    const startOfMonth = new Date();
    startOfMonth.setDate(1);
    startOfMonth.setHours(0, 0, 0, 0);

    return this.records
      .filter(r => r.timestamp >= startOfMonth)
      .reduce((sum, r) => sum + r.credits, 0);
  }

  getUsageReport(): UsageReport {
    const monthly = this.getMonthlyUsage();
    const byEndpoint = this.records.reduce((acc, r) => {
      acc[r.endpoint] = (acc[r.endpoint] || 0) + r.credits;
      return acc;
    }, {} as Record<string, number>);

    return {
      monthlyUsage: monthly,
      monthlyBudget: this.monthlyBudget,
      usagePercent: (monthly / this.monthlyBudget) * 100,
      byEndpoint,
      projectedMonthlyUsage: this.projectMonthlyUsage(),
      cacheSavings: costAwareCache.getStats().creditsSaved,
    };
  }

  private projectMonthlyUsage(): number {
    const now = new Date();
    const dayOfMonth = now.getDate();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();

    const currentUsage = this.getMonthlyUsage();
    return (currentUsage / dayOfMonth) * daysInMonth;
  }
}

export const usageTracker = new UsageTracker(
  parseInt(process.env.APOLLO_MONTHLY_BUDGET || '10000'),
  parseFloat(process.env.APOLLO_ALERT_THRESHOLD || '0.8')
);
```

### 5. Budget-Aware Client

```typescript
// src/lib/apollo/budget-client.ts
export class BudgetAwareApolloClient {
  private dailyLimit: number;
  private todayUsage = 0;
  private lastResetDate: string = '';

  constructor(dailyLimit: number = 500) {
    this.dailyLimit = dailyLimit;
  }

  private checkDailyLimit(): void {
    const today = new Date().toISOString().split('T')[0];
    if (today !== this.lastResetDate) {
      this.todayUsage = 0;
      this.lastResetDate = today;
    }

    if (this.todayUsage >= this.dailyLimit) {
      throw new Error('Daily Apollo credit limit reached. Try again tomorrow.');
    }
  }

  async searchPeople(params: any): Promise<any> {
    this.checkDailyLimit();

    const result = await apollo.searchPeople(params);
    const creditsUsed = result.people.length;
    this.todayUsage += creditsUsed;
    usageTracker.track('search', creditsUsed, 'people/search');

    return result;
  }

  async enrichPerson(params: any): Promise<any> {
    this.checkDailyLimit();

    // Check cache first
    const cacheKey = params.email || params.linkedin_url || params.id;
    const cached = costAwareCache.getContact(cacheKey);
    if (cached) {
      return cached.data;
    }

    const result = await apollo.enrichPerson(params);
    this.todayUsage += 1;
    usageTracker.track('enrich', 1, 'people/enrich');
    costAwareCache.setContact(cacheKey, result, 1);

    return result;
  }

  getRemainingCredits(): number {
    return this.dailyLimit - this.todayUsage;
  }
}

export const budgetClient = new BudgetAwareApolloClient();
```

## Cost Optimization Checklist

- [ ] 7-day cache for contact data
- [ ] Deduplication for emails and domains
- [ ] Score leads before enrichment
- [ ] Daily/monthly usage limits
- [ ] Usage alerts at 80% threshold
- [ ] Cost metrics in monitoring dashboard
- [ ] Regular usage report reviews
- [ ] Team-level budget allocation

## Output
- Cost-aware caching strategy
- Deduplication service
- Smart search scoring
- Usage tracking and alerts
- Budget-aware API client

## Error Handling
| Issue | Resolution |
|-------|------------|
| Budget exceeded | Pause operations, alert team |
| High cache misses | Extend TTL, review patterns |
| Duplicate enrichments | Audit dedup logic |
| Unexpected costs | Review usage reports |

## Resources
- [Apollo Pricing](https://www.apollo.io/pricing)
- [Apollo Credit System](https://knowledge.apollo.io/hc/en-us/articles/4415144183053)
- [Usage Dashboard](https://app.apollo.io/settings/billing)

## Next Steps
Proceed to `apollo-reference-architecture` for architecture patterns.
