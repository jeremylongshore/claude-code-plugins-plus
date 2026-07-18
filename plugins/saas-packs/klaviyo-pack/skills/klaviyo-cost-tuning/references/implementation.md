# Klaviyo Cost Tuning — Full Implementation Walkthrough

The full five-step programmatic workflow for auditing active profiles, suppressing
unengaged contacts, sampling non-critical events, and monitoring API usage. Each step
uses the `klaviyo-api` SDK with an `ApiKeySession` built from `KLAVIYO_PRIVATE_KEY`.

## Step 1: Audit Active Profile Count

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

## Step 2: Identify Unengaged Profiles

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

## Step 3: Suppress Unengaged Contacts

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

## Step 4: Event Sampling for Non-Critical Tracking

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

## Step 5: API Usage Monitor

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
