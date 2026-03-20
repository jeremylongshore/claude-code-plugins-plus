---
name: juicebox-cost-tuning
description: |
  Optimize Juicebox costs and usage.
  Use when reducing API costs, optimizing quota usage,
  or implementing cost-effective Juicebox patterns.
  Trigger with phrases like "juicebox cost", "juicebox budget",
  "optimize juicebox usage", "juicebox pricing".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Cost Tuning

## Overview

Minimize Juicebox API spend while maximizing sourcing output. Covers usage tracking against tier limits, TTL-aware caching for search results and enriched profiles, request deduplication to prevent redundant API calls, batch enrichment to collapse per-profile calls, and a usage dashboard that projects end-of-month spend.

## Prerequisites

- Juicebox API credentials configured (`JUICEBOX_USERNAME`, `JUICEBOX_API_TOKEN`)
- Knowledge of your current Juicebox pricing tier (Free/Pro/Business/Enterprise)
- Node.js 18+ with a persistent store for caching (Redis, SQLite, or filesystem)
- Baseline understanding of your monthly search and enrichment volumes

## Instructions

### Step 1: Track API Usage Against Tier Limits

Build a tracker that counts every API call and alerts when approaching quota boundaries.

```typescript
// lib/usage-tracker.ts
export interface TierLimits {
  searchesPerMonth: number;
  enrichmentsPerMonth: number;
  costPerSearch: number;    // in dollars
  costPerEnrichment: number;
}

const TIER_LIMITS: Record<string, TierLimits> = {
  free:       { searchesPerMonth: 500,    enrichmentsPerMonth: 100,    costPerSearch: 0,      costPerEnrichment: 0 },
  pro:        { searchesPerMonth: 10_000, enrichmentsPerMonth: 2_000,  costPerSearch: 0.0099, costPerEnrichment: 0.0495 },
  business:   { searchesPerMonth: 50_000, enrichmentsPerMonth: 10_000, costPerSearch: 0.00998, costPerEnrichment: 0.0499 },
  enterprise: { searchesPerMonth: Infinity, enrichmentsPerMonth: Infinity, costPerSearch: 0, costPerEnrichment: 0 },
};

export class UsageTracker {
  private searches = 0;
  private enrichments = 0;
  private readonly limits: TierLimits;
  private readonly periodStart = new Date();

  constructor(tier: keyof typeof TIER_LIMITS) {
    this.limits = TIER_LIMITS[tier];
  }

  recordSearch(): void {
    this.searches++;
    this.checkThresholds();
  }

  recordEnrichment(count = 1): void {
    this.enrichments += count;
    this.checkThresholds();
  }

  getUsage() {
    return {
      searches: this.searches,
      enrichments: this.enrichments,
      searchPct: (this.searches / this.limits.searchesPerMonth) * 100,
      enrichPct: (this.enrichments / this.limits.enrichmentsPerMonth) * 100,
      estimatedCost:
        this.searches * this.limits.costPerSearch +
        this.enrichments * this.limits.costPerEnrichment,
    };
  }

  projectEndOfMonth(): { projectedSearches: number; projectedEnrichments: number; projectedCost: number } {
    const daysSoFar = Math.max(1, (Date.now() - this.periodStart.getTime()) / 86_400_000);
    const daysInMonth = 30;
    const rate = daysInMonth / daysSoFar;
    return {
      projectedSearches: Math.round(this.searches * rate),
      projectedEnrichments: Math.round(this.enrichments * rate),
      projectedCost:
        this.searches * rate * this.limits.costPerSearch +
        this.enrichments * rate * this.limits.costPerEnrichment,
    };
  }

  private checkThresholds(): void {
    const usage = this.getUsage();
    if (usage.searchPct >= 90) {
      console.warn(`[JUICEBOX] Search quota at ${usage.searchPct.toFixed(1)}% — ${this.limits.searchesPerMonth - this.searches} remaining`);
    }
    if (usage.enrichPct >= 90) {
      console.warn(`[JUICEBOX] Enrichment quota at ${usage.enrichPct.toFixed(1)}% — ${this.limits.enrichmentsPerMonth - this.enrichments} remaining`);
    }
  }
}
```

### Step 2: Implement TTL-Aware Caching

Cache search results (short TTL) and enriched profiles (long TTL) to avoid repeating expensive calls. Enrichments cost more than searches, so they get a longer cache window.

```typescript
// lib/cost-aware-cache.ts
interface CacheEntry<T> {
  data: T;
  expiresAt: number;
  operation: string;
}

export class CostAwareCache {
  private store = new Map<string, CacheEntry<unknown>>();

  // TTLs tuned to Juicebox cost tiers (seconds)
  private readonly ttlMap: Record<string, number> = {
    search:          5 * 60,          // 5 min — results change frequently
    "profile.basic": 60 * 60,        // 1 hour — basic profile data is stable
    "profile.enriched": 24 * 60 * 60, // 24 hours — enrichments are expensive
    enrichment:      7 * 24 * 60 * 60, // 7 days — enrichment data rarely changes
  };

  async getOrFetch<T>(
    operation: string,
    key: string,
    fetchFn: () => Promise<T>
  ): Promise<{ data: T; fromCache: boolean }> {
    const cached = this.store.get(key) as CacheEntry<T> | undefined;
    if (cached && cached.expiresAt > Date.now()) {
      return { data: cached.data, fromCache: true };
    }

    const data = await fetchFn();
    const ttlSeconds = this.ttlMap[operation] ?? 300;
    this.store.set(key, {
      data,
      expiresAt: Date.now() + ttlSeconds * 1000,
      operation,
    });
    return { data, fromCache: false };
  }

  invalidate(key: string): void {
    this.store.delete(key);
  }

  getStats(): { entries: number; byOperation: Record<string, number> } {
    const byOp: Record<string, number> = {};
    for (const entry of this.store.values()) {
      byOp[entry.operation] = (byOp[entry.operation] ?? 0) + 1;
    }
    return { entries: this.store.size, byOperation: byOp };
  }
}
```

### Step 3: Deduplicate In-Flight Requests

When multiple parts of the application request the same profile simultaneously, collapse them into a single API call.

```typescript
// lib/request-deduplicator.ts
export class RequestDeduplicator {
  private inflight = new Map<string, Promise<unknown>>();
  private dedupeCount = 0;

  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const existing = this.inflight.get(key);
    if (existing) {
      this.dedupeCount++;
      return existing as Promise<T>;
    }

    const promise = fn().finally(() => this.inflight.delete(key));
    this.inflight.set(key, promise);
    return promise;
  }

  get savedCalls(): number {
    return this.dedupeCount;
  }
}

// Usage — prevents duplicate profile fetches
const dedup = new RequestDeduplicator();
const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;

async function getProfile(id: string): Promise<Profile> {
  return dedup.dedupe(`profile:${id}`, async () => {
    const res = await fetch(
      `https://api.juicebox.ai/api/v1/profiles/${id}`,
      { headers: { Authorization: authHeader } }
    );
    return res.json();
  });
}
```

### Step 4: Batch Enrichment to Reduce API Calls

Instead of enriching profiles one at a time, batch them into a single POST to `/api/v1/enrichments`. One call for 50 profiles costs the same as one enrichment API call.

```typescript
// lib/batch-enricher.ts
const BATCH_LIMIT = 50; // Juicebox batch endpoint max

export async function batchEnrich(
  profileIds: string[],
  fields: string[] = ["email", "phone", "social_profiles"]
): Promise<EnrichedProfile[]> {
  const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;
  const results: EnrichedProfile[] = [];

  for (let i = 0; i < profileIds.length; i += BATCH_LIMIT) {
    const batch = profileIds.slice(i, i + BATCH_LIMIT);
    const res = await fetch("https://api.juicebox.ai/api/v1/enrichments", {
      method: "POST",
      headers: {
        Authorization: authHeader,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ profile_ids: batch, fields }),
    });

    if (!res.ok) throw new Error(`Enrichment failed: ${res.status}`);
    const data = await res.json();
    results.push(...data.profiles);
  }

  console.log(
    `Enriched ${results.length} profiles in ${Math.ceil(profileIds.length / BATCH_LIMIT)} API calls ` +
    `(saved ${profileIds.length - Math.ceil(profileIds.length / BATCH_LIMIT)} calls vs individual enrichment)`
  );
  return results;
}

// Selective enrichment — only fetch missing fields
export async function smartEnrich(
  profile: Profile,
  requiredFields: string[]
): Promise<Profile> {
  const missing = requiredFields.filter((f) => !(f in profile) || profile[f] == null);
  if (missing.length === 0) return profile; // No API call needed

  const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;
  const res = await fetch("https://api.juicebox.ai/api/v1/enrichments", {
    method: "POST",
    headers: { Authorization: authHeader, "Content-Type": "application/json" },
    body: JSON.stringify({ profile_ids: [profile.id], fields: missing }),
  });

  const data = await res.json();
  return { ...profile, ...data.profiles[0] };
}
```

### Step 5: Build a Usage Dashboard

Aggregate tracker data into a cost dashboard that shows current spend, projections, and savings from caching/deduplication.

```typescript
// lib/usage-dashboard.ts
import { UsageTracker } from "./usage-tracker";
import { CostAwareCache } from "./cost-aware-cache";
import { RequestDeduplicator } from "./request-deduplicator";

export function buildDashboard(
  tracker: UsageTracker,
  cache: CostAwareCache,
  dedup: RequestDeduplicator
) {
  const usage = tracker.getUsage();
  const projection = tracker.projectEndOfMonth();
  const cacheStats = cache.getStats();

  return {
    currentPeriod: {
      searches: usage.searches,
      enrichments: usage.enrichments,
      searchQuotaUsedPct: usage.searchPct.toFixed(1) + "%",
      enrichQuotaUsedPct: usage.enrichPct.toFixed(1) + "%",
      estimatedCostUSD: `$${usage.estimatedCost.toFixed(2)}`,
    },
    projection: {
      endOfMonthSearches: projection.projectedSearches,
      endOfMonthEnrichments: projection.projectedEnrichments,
      projectedCostUSD: `$${projection.projectedCost.toFixed(2)}`,
    },
    savings: {
      cachedEntries: cacheStats.entries,
      cacheBreakdown: cacheStats.byOperation,
      deduplicatedCalls: dedup.savedCalls,
    },
  };
}

// Print dashboard to console
export function printDashboard(
  tracker: UsageTracker,
  cache: CostAwareCache,
  dedup: RequestDeduplicator
): void {
  const d = buildDashboard(tracker, cache, dedup);
  console.log("\n=== Juicebox Usage Dashboard ===");
  console.log(`Searches:     ${d.currentPeriod.searches} (${d.currentPeriod.searchQuotaUsedPct} of quota)`);
  console.log(`Enrichments:  ${d.currentPeriod.enrichments} (${d.currentPeriod.enrichQuotaUsedPct} of quota)`);
  console.log(`Current cost: ${d.currentPeriod.estimatedCostUSD}`);
  console.log(`Projected:    ${d.projection.projectedCostUSD} by end of month`);
  console.log(`Cache hits:   ${d.savings.cachedEntries} entries cached`);
  console.log(`Deduped:      ${d.savings.deduplicatedCalls} redundant calls prevented`);
  console.log("================================\n");
}
```

## Output

- `lib/usage-tracker.ts` — Per-tier usage counter with quota alerts and end-of-month projections
- `lib/cost-aware-cache.ts` — TTL-aware cache keyed by operation cost (enrichments cached longest)
- `lib/request-deduplicator.ts` — In-flight request deduplication with savings counter
- `lib/batch-enricher.ts` — Batch enrichment and selective field-level enrichment
- `lib/usage-dashboard.ts` — Aggregated cost dashboard with spend, projections, and savings breakdown

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Quota exceeded (402/429) | Monthly search or enrichment limit hit | Check `tracker.getUsage()`; upgrade tier or wait for reset |
| Cache miss storm | Many concurrent requests after cache expiry | Use `RequestDeduplicator` to collapse identical fetches |
| Stale enrichment data | Cached enrichment is outdated | Call `cache.invalidate(key)` for specific profiles |
| Batch too large | More than 50 IDs in single enrichment request | `batchEnrich` auto-chunks; verify `BATCH_LIMIT` constant |
| Projection inaccurate | Tracker reset mid-month or usage is bursty | Use at least 7 days of data before trusting projections |

## Examples

### Full Cost-Optimized Search Pipeline

```typescript
import { UsageTracker } from "./lib/usage-tracker";
import { CostAwareCache } from "./lib/cost-aware-cache";
import { RequestDeduplicator } from "./lib/request-deduplicator";
import { batchEnrich } from "./lib/batch-enricher";
import { printDashboard } from "./lib/usage-dashboard";

const tracker = new UsageTracker("pro");
const cache = new CostAwareCache();
const dedup = new RequestDeduplicator();
const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;

// Search with caching
const { data: searchResults } = await cache.getOrFetch(
  "search",
  "search:senior-engineer-sf",
  async () => {
    tracker.recordSearch();
    const res = await fetch(
      `https://api.juicebox.ai/api/v1/search?q=${encodeURIComponent("senior engineer")}&location=San+Francisco&limit=50`,
      { headers: { Authorization: authHeader } }
    );
    return res.json();
  }
);

// Batch enrich top candidates (1 API call instead of 20)
const topIds = searchResults.profiles.slice(0, 20).map((p: Profile) => p.id);
const enriched = await batchEnrich(topIds, ["email", "phone"]);
tracker.recordEnrichment(enriched.length);

// Print cost dashboard
printDashboard(tracker, cache, dedup);
```

### Monitoring Usage via GitHub Issue

```bash
# Create a GitHub issue with monthly usage report
gh issue create \
  --title "Juicebox Usage Report — $(date +%B\ %Y)" \
  --body "$(curl -s \
    -H 'Authorization: token '${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN} \
    'https://api.juicebox.ai/api/v1/search?q=test&limit=1' \
    -D /dev/stderr 2>&1 1>/dev/null \
    | grep -i x-ratelimit \
    | sed 's/^/- /')"
```

## Resources

- [Juicebox Pricing Page](https://juicebox.ai/pricing)
- [Usage Dashboard](https://app.juicebox.ai/usage)
- [API Rate Limits](https://juicebox.ai/docs/rate-limits)
- [Batch Enrichment API](https://juicebox.ai/docs/api/enrichments)

## Next Steps

After implementing cost optimization, see `juicebox-reference-architecture` for full system architecture patterns, or `juicebox-rate-limits` for advanced throttling strategies.
