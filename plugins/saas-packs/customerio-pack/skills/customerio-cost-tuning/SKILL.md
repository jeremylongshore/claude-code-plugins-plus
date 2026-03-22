---
name: customerio-cost-tuning
description: |
  Optimize Customer.io costs and usage efficiency.
  Use when reducing profile count, cleaning inactive users,
  deduplicating events, or right-sizing your plan.
  Trigger: "customer.io cost", "reduce customer.io spend",
  "customer.io billing", "customer.io pricing", "customer.io cleanup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, cost-optimization, billing]

---
# Customer.io Cost Tuning

## Overview

Optimize Customer.io costs by managing profile count (the primary billing driver), suppressing/deleting inactive users, deduplicating events, reducing unnecessary API calls, and monitoring usage trends.

## How Customer.io Pricing Works

Customer.io bills based on **profile count** (number of identified people in your workspace) and **email/SMS volume**. Key cost drivers:

| Factor | Impact | Optimization Strategy |
|--------|--------|----------------------|
| Total profiles | Primary cost driver | Delete inactive profiles |
| Email sends | Per-email cost above tier | Suppress unengaged users |
| SMS sends | Per-SMS cost | Only send to opt-in users |
| Overidentification | Creates unnecessary profiles | Don't identify users who'll never receive messages |
| Event volume | Can increase processing costs | Deduplicate and sample |

## Instructions

### Step 1: Profile Audit

```typescript
// scripts/cio-profile-audit.ts
// Audit your Customer.io integration for cost optimization opportunities

import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Check: Are you identifying users who'll never receive messages?
const AUDIT_RULES = {
  // Users without email can't receive email campaigns
  noEmail: "Don't identify users without email unless using push/SMS",

  // Test users should be cleaned up
  testUsers: "Suppress and delete test-*, ci-*, dev-* prefixed users",

  // Anonymous users that never convert inflate profile count
  staleAnonymous: "Delete anonymous profiles older than 90 days without conversion",

  // Inactive users who haven't opened email in 6+ months
  unengaged: "Suppress users with no email opens in 180+ days",
};

console.log("=== Customer.io Cost Audit Rules ===\n");
for (const [rule, action] of Object.entries(AUDIT_RULES)) {
  console.log(`${rule}: ${action}`);
}
console.log("\nRun these checks in Customer.io dashboard:");
console.log("1. People > Segments > Create 'Inactive 90 days' segment");
console.log("2. People > Segments > Create 'No email attribute' segment");
console.log("3. People > Filter by created_at < 90 days ago AND email_opened = 0");
```

### Step 2: Suppress and Delete Inactive Users

```typescript
// scripts/cio-cleanup-inactive.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

interface CleanupTarget {
  userId: string;
  reason: string;
}

async function cleanupInactiveUsers(
  targets: CleanupTarget[],
  dryRun: boolean = true
): Promise<void> {
  let suppressed = 0;
  let deleted = 0;
  let errors = 0;

  for (const target of targets) {
    if (dryRun) {
      console.log(`[DRY RUN] Would suppress+delete: ${target.userId} (${target.reason})`);
      continue;
    }

    try {
      // Step 1: Suppress — stops all messaging immediately
      await cio.suppress(target.userId);
      suppressed++;

      // Step 2: Destroy — removes from billing
      await cio.destroy(target.userId);
      deleted++;

      // Rate limit to 50/sec for bulk operations
      await new Promise((r) => setTimeout(r, 20));
    } catch (err: any) {
      errors++;
      console.error(`Failed ${target.userId}: ${err.message}`);
    }

    if ((suppressed + errors) % 100 === 0) {
      console.log(`Progress: ${suppressed} deleted, ${errors} errors`);
    }
  }

  console.log(`\nResult: ${suppressed} suppressed, ${deleted} deleted, ${errors} errors`);
}

// Usage: Build target list from your database
// const inactiveUsers = await db.query(`
//   SELECT id FROM users
//   WHERE last_login_at < NOW() - INTERVAL '180 days'
//   AND email_verified = false
// `);
```

### Step 3: Event Deduplication

```typescript
// lib/customerio-dedup-events.ts
// Prevent sending duplicate events that inflate volume

import { createHash } from "crypto";
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Simple LRU dedup (use Redis in production)
const recentEvents = new Map<string, number>();
const MAX_CACHE = 50_000;
const DEDUP_WINDOW_MS = 60 * 1000;  // 1 minute window

function isDuplicate(userId: string, eventName: string, data?: any): boolean {
  const hash = createHash("sha256")
    .update(`${userId}:${eventName}:${JSON.stringify(data ?? {})}`)
    .digest("hex")
    .substring(0, 12);

  const last = recentEvents.get(hash);
  if (last && Date.now() - last < DEDUP_WINDOW_MS) {
    return true;
  }

  recentEvents.set(hash, Date.now());

  // Prevent unbounded growth
  if (recentEvents.size > MAX_CACHE) {
    const cutoff = Date.now() - DEDUP_WINDOW_MS;
    for (const [key, time] of recentEvents) {
      if (time < cutoff) recentEvents.delete(key);
    }
  }

  return false;
}

export async function trackDeduped(
  userId: string,
  name: string,
  data?: Record<string, any>
): Promise<void> {
  if (isDuplicate(userId, name, data)) {
    return; // Skip duplicate
  }
  await cio.track(userId, { name, data });
}
```

### Step 4: Event Sampling for High-Volume Events

```typescript
// lib/customerio-sampling.ts
// Sample high-volume events to reduce API calls

const EVENT_SAMPLE_RATES: Record<string, number> = {
  page_viewed: 0.1,          // Sample 10% of page views
  button_clicked: 0.25,      // Sample 25% of clicks
  search_performed: 0.5,     // Sample 50% of searches
  signed_up: 1.0,            // Always track signups
  checkout_completed: 1.0,   // Always track purchases
  subscription_cancelled: 1.0, // Always track cancellations
};

export function shouldTrack(eventName: string): boolean {
  const rate = EVENT_SAMPLE_RATES[eventName] ?? 1.0;
  return Math.random() < rate;
}

// Usage
if (shouldTrack("page_viewed")) {
  await cio.track(userId, {
    name: "page_viewed",
    data: { url: "/pricing", sampled: true },
  });
}
```

### Step 5: Usage Monitoring

```typescript
// scripts/cio-usage-monitor.ts
// Track your Customer.io usage trends

interface UsageMetrics {
  identifyCalls: number;
  trackCalls: number;
  transactionalSends: number;
  broadcastTriggers: number;
  webhooksReceived: number;
}

class UsageMonitor {
  private metrics: UsageMetrics = {
    identifyCalls: 0,
    trackCalls: 0,
    transactionalSends: 0,
    broadcastTriggers: 0,
    webhooksReceived: 0,
  };

  increment(metric: keyof UsageMetrics): void {
    this.metrics[metric]++;
  }

  report(): void {
    console.log("\n=== Customer.io Usage Report ===");
    console.log(`Period: ${new Date().toISOString()}`);
    for (const [key, value] of Object.entries(this.metrics)) {
      console.log(`  ${key}: ${value.toLocaleString()}`);
    }
    const total = Object.values(this.metrics).reduce((a, b) => a + b, 0);
    console.log(`  TOTAL API calls: ${total.toLocaleString()}`);
  }

  reset(): void {
    for (const key of Object.keys(this.metrics)) {
      this.metrics[key as keyof UsageMetrics] = 0;
    }
  }
}

export const usageMonitor = new UsageMonitor();
```

## Cost Savings Estimates

| Optimization | Typical Savings | Implementation Effort |
|--------------|-----------------|----------------------|
| Delete inactive profiles (180+ days) | 15-30% profile cost | Low |
| Event deduplication | 5-15% event volume | Low |
| Event sampling (analytics events) | 50-80% event volume for sampled events | Low |
| Suppress bounced emails | 2-5% email cost | Low |
| Don't identify email-less users | 5-20% profile cost | Medium |
| Annual billing | 10-20% total cost | None |

## Monthly Cost Review Checklist

- [ ] Review profile count trend (People > Overview)
- [ ] Identify and delete stale test profiles
- [ ] Review segment for users with no email attribute
- [ ] Check bounce rate and suppress chronic bouncers
- [ ] Review event volume by type (optimize high-volume/low-value events)
- [ ] Compare plan tier vs actual usage

## Resources

- [Customer.io Pricing](https://customer.io/pricing/)
- [Track API - Suppress/Destroy](https://docs.customer.io/integrations/api/track/)

## Next Steps

After cost optimization, proceed to `customerio-reference-architecture` for enterprise patterns.
