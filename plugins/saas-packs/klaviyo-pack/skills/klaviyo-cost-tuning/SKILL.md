---
name: klaviyo-cost-tuning
description: |
  Optimize Klaviyo costs through plan selection, contact management, and usage monitoring.
  Use when analyzing Klaviyo billing, reducing active profile costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "klaviyo cost", "klaviyo billing",
  "reduce klaviyo costs", "klaviyo pricing", "klaviyo expensive", "klaviyo budget".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Cost Tuning

## Overview

Optimize Klaviyo costs through active profile management, list hygiene, event sampling, and API usage monitoring. Klaviyo bills primarily by **active profiles** and **message volume**, not API calls.

## Prerequisites

- Access to Klaviyo billing dashboard
- Understanding of active profile definition
- `klaviyo-api` SDK for programmatic management

## Klaviyo Pricing Model

Klaviyo bills based on **active profiles** (contacts who have received or been targeted by marketing), not API requests.

| Component | How It's Billed | Cost Driver |
|-----------|----------------|-------------|
| Email | Per active profile tier | Number of marketable profiles |
| SMS | Per message sent + carrier fees | Message volume |
| Push | Included with email plan | N/A |
| API calls | Free (rate limited, not billed) | N/A |
| Reviews | Per request volume | Review request sends |

### Email Pricing Tiers (Approximate)

| Active Profiles | Monthly Cost |
|----------------|-------------|
| 0 - 250 | Free |
| 251 - 500 | $20/mo |
| 501 - 1,000 | $30/mo |
| 1,001 - 1,500 | $45/mo |
| 1,501 - 5,000 | $60-$100/mo |
| 5,001 - 10,000 | $100-$150/mo |
| 10,001 - 25,000 | $150-$375/mo |
| 25,001+ | Custom pricing |

> **Key insight:** Reducing **active profiles** has the biggest cost impact. Cleaning suppressed/unengaged contacts directly reduces your bill.

## Instructions

### Step 1: Audit Active Profile Count

```typescript
import { ApiKeySession, ProfilesApi, SegmentsApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);

// Count total profiles
let totalProfiles = 0;
let cursor: string | undefined;
do {
  const response = await profilesApi.getProfiles({
    pageCursor: cursor,
    fieldsProfile: ['email'],  // Minimal fields for speed
  });
  totalProfiles += response.body.data.length;
  const nextLink = response.body.links?.next;
  cursor = nextLink ? new URL(nextLink).searchParams.get('page[cursor]') || undefined : undefined;
} while (cursor);

console.log(`Total profiles: ${totalProfiles}`);
```

### Step 2: Identify Unengaged Profiles

```typescript
// Find profiles that haven't opened/clicked in 180+ days
// Create a segment in Klaviyo for this, then query it
const segmentsApi = new SegmentsApi(session);

const segments = await segmentsApi.getSegments({
  filter: 'equals(name,"Unengaged 180+ Days")',
});

if (segments.body.data.length > 0) {
  const segmentId = segments.body.data[0].id;
  const unengaged = await segmentsApi.getSegmentProfiles({
    id: segmentId,
    fieldsProfile: ['email', 'created'],
  });
  console.log(`Unengaged profiles: ${unengaged.body.data.length}+`);
}
```

### Step 3: Suppress Unengaged Contacts

```typescript
// Move unengaged profiles to a suppressed list (removes from active count)
import { ListsApi, ListEnum, ProfileEnum } from 'klaviyo-api';

const listsApi = new ListsApi(session);

// Option 1: Unsubscribe (profile stays but isn't marketable = not billed)
await profilesApi.unsubscribeProfiles({
  data: {
    type: 'profile-subscription-bulk-delete-job',
    attributes: {
      profiles: {
        data: unengagedEmails.map(email => ({
          type: ProfileEnum.Profile,
          attributes: {
            email,
            subscriptions: {
              email: { marketing: { consent: 'UNSUBSCRIBED' } },
            },
          },
        })),
      },
    },
    relationships: {
      list: { data: { type: ListEnum.List, id: 'MAIN_LIST_ID' } },
    },
  },
});

// Option 2: Suppress via profile update (add to global suppression)
for (const email of unengagedEmails) {
  await profilesApi.createOrUpdateProfile({
    data: {
      type: ProfileEnum.Profile,
      attributes: {
        email,
        properties: { suppressedAt: new Date().toISOString(), suppressReason: 'unengaged-180d' },
      },
    },
  });
}
```

### Step 4: Event Sampling for Non-Critical Tracking

```typescript
// Not all events need to be tracked -- sample non-critical ones
function shouldTrackEvent(eventName: string, samplingRates: Record<string, number>): boolean {
  const rate = samplingRates[eventName] ?? 1.0;  // Default: track everything
  return Math.random() < rate;
}

const samplingConfig = {
  'Placed Order': 1.0,       // Always track (revenue attribution)
  'Started Checkout': 1.0,   // Always track (cart abandonment)
  'Viewed Product': 0.25,    // 25% sample (high volume, less critical)
  'Page View': 0.1,          // 10% sample (very high volume)
};

// Before tracking
if (shouldTrackEvent('Viewed Product', samplingConfig)) {
  await eventsApi.createEvent({ /* ... */ });
}
```

### Step 5: API Usage Monitor

```typescript
// Track API call volume to detect runaway processes
class KlaviyoUsageTracker {
  private callCount = 0;
  private readonly startTime = Date.now();

  track(): void {
    this.callCount++;
    // Warn if approaching steady rate limit
    const elapsedMinutes = (Date.now() - this.startTime) / 60000;
    const ratePerMinute = this.callCount / Math.max(elapsedMinutes, 1);

    if (ratePerMinute > 500) {
      console.warn(`[Klaviyo] High API rate: ${Math.round(ratePerMinute)} req/min (limit: 700)`);
    }
  }

  getStats(): { totalCalls: number; ratePerMinute: number } {
    const elapsedMinutes = (Date.now() - this.startTime) / 60000;
    return {
      totalCalls: this.callCount,
      ratePerMinute: Math.round(this.callCount / Math.max(elapsedMinutes, 1)),
    };
  }
}

export const usageTracker = new KlaviyoUsageTracker();
```

## Cost Reduction Checklist

- [ ] Suppress profiles unengaged >180 days
- [ ] Remove hard-bounced email addresses
- [ ] Audit and merge duplicate profiles
- [ ] Use double opt-in to reduce fake signups
- [ ] Sample high-volume, low-value events
- [ ] Batch API calls instead of individual requests
- [ ] Cache frequently-read data (segments, lists)
- [ ] Use sparse fieldsets to reduce transfer size
- [ ] Review SMS sending -- highest per-message cost
- [ ] Set up sunset flow (auto-suppress after N days unengaged)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bill increase | Unengaged profiles grew | Run suppression script |
| SMS costs spiking | Flow sending to full list | Add engaged-only segment filter |
| Duplicate profiles | Multiple identify calls | Merge duplicates, use `createOrUpdateProfile` |
| API rate limits hit | Bulk operations | Use queue with concurrency control |

## Resources

- [Klaviyo Pricing](https://www.klaviyo.com/pricing)
- [Understanding Active Profiles](https://help.klaviyo.com/hc/en-us/articles/115005077967)
- [Sunset Flow Best Practices](https://help.klaviyo.com/hc/en-us/articles/360002360091)
- [Data Privacy API](https://developers.klaviyo.com/en/reference/data_privacy_api_overview)

## Next Steps

For architecture patterns, see `klaviyo-reference-architecture`.
