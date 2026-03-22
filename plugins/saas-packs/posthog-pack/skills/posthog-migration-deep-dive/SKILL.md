---
name: posthog-migration-deep-dive
description: |
  Migrate to PostHog from Google Analytics, Mixpanel, Amplitude, or Segment.
  Covers dual-write strategy, historical data import, event name mapping,
  identity resolution, and feature flag based traffic shifting.
  Trigger: "migrate posthog", "posthog migration", "switch to posthog",
  "posthog from mixpanel", "posthog from GA", "posthog replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, migration]
---

# PostHog Migration Deep Dive

## Current State

!`npm list posthog-js posthog-node 2>/dev/null | grep posthog || echo 'No PostHog SDK found'`
!`npm list @segment/analytics-node mixpanel @google-analytics/data 2>/dev/null | grep -E "segment|mixpanel|google" || echo 'No competitor SDKs found'`

## Overview

Migrate from Google Analytics, Mixpanel, Amplitude, or Segment to PostHog using a dual-write strategy (send events to both old and new platforms) followed by gradual traffic shifting. PostHog's capture API accepts events in a format similar to Segment's track/identify calls, making migration straightforward.

## Migration Types

| Source | Complexity | Duration | Key Challenge |
|--------|-----------|----------|---------------|
| Google Analytics (GA4) | Medium | 2-4 weeks | Event model is fundamentally different |
| Mixpanel | Low | 1-2 weeks | Very similar event model |
| Amplitude | Low | 1-2 weeks | Similar event model |
| Segment | Low | 1 week | PostHog has a Segment destination |
| Custom analytics | Medium | 2-4 weeks | Depends on current implementation |

## Instructions

### Step 1: Event Name Mapping

```typescript
// migration/event-map.ts
// Map old event names to PostHog event taxonomy
const EVENT_MAP: Record<string, string> = {
  // Mixpanel → PostHog
  'Sign Up': 'user_signed_up',
  'Login': 'user_logged_in',
  'Page View': '$pageview',
  'Button Click': 'button_clicked',
  'Purchase': 'payment_completed',
  'Subscription Started': 'subscription_started',

  // GA4 → PostHog
  'page_view': '$pageview',
  'sign_up': 'user_signed_up',
  'login': 'user_logged_in',
  'purchase': 'payment_completed',
  'add_to_cart': 'item_added_to_cart',

  // Amplitude → PostHog
  'Page Viewed': '$pageview',
  'Signed Up': 'user_signed_up',
  'Feature Used': 'feature_used',
};

// Property name mapping
const PROPERTY_MAP: Record<string, string> = {
  // Mixpanel → PostHog
  '$email': 'email',
  '$name': 'name',
  '$city': 'city',
  'Plan': 'plan',
  'MRR': 'mrr',

  // GA4 → PostHog
  'page_title': '$title',
  'page_location': '$current_url',
  'page_referrer': '$referrer',
};
```

### Step 2: Dual-Write Adapter

```typescript
// migration/analytics-adapter.ts
import { PostHog } from 'posthog-node';
import Mixpanel from 'mixpanel'; // or your current platform

interface AnalyticsAdapter {
  capture(userId: string, event: string, properties?: Record<string, any>): void;
  identify(userId: string, properties: Record<string, any>): void;
  shutdown(): Promise<void>;
}

class DualWriteAdapter implements AnalyticsAdapter {
  private posthog: PostHog;
  private mixpanel: typeof Mixpanel; // Replace with your current platform
  private posthogEnabled: boolean;

  constructor() {
    this.posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      host: 'https://us.i.posthog.com',
      personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
    });

    this.mixpanel = Mixpanel.init(process.env.MIXPANEL_TOKEN!);
    this.posthogEnabled = true;
  }

  capture(userId: string, event: string, properties?: Record<string, any>) {
    // Map event name
    const posthogEvent = EVENT_MAP[event] || event.toLowerCase().replace(/\s+/g, '_');
    const mappedProps = this.mapProperties(properties || {});

    // Write to PostHog
    if (this.posthogEnabled) {
      this.posthog.capture({
        distinctId: userId,
        event: posthogEvent,
        properties: { ...mappedProps, migration_source: 'dual-write' },
      });
    }

    // Write to old platform (until migration complete)
    this.mixpanel.track(event, { distinct_id: userId, ...properties });
  }

  identify(userId: string, properties: Record<string, any>) {
    const mappedProps = this.mapProperties(properties);

    if (this.posthogEnabled) {
      this.posthog.identify({ distinctId: userId, properties: mappedProps });
    }

    this.mixpanel.people.set(userId, properties);
  }

  private mapProperties(props: Record<string, any>): Record<string, any> {
    const mapped: Record<string, any> = {};
    for (const [key, value] of Object.entries(props)) {
      const newKey = PROPERTY_MAP[key] || key.toLowerCase().replace(/\s+/g, '_');
      mapped[newKey] = value;
    }
    return mapped;
  }

  async shutdown() {
    await this.posthog.shutdown();
  }
}

export const analytics = new DualWriteAdapter();
```

### Step 3: Historical Data Import

```typescript
// migration/import-historical.ts
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  flushAt: 100,        // Larger batch for import
  flushInterval: 1000, // Flush every second
});

interface HistoricalEvent {
  userId: string;
  event: string;
  properties: Record<string, any>;
  timestamp: string; // ISO 8601
}

async function importHistoricalEvents(events: HistoricalEvent[]) {
  let imported = 0;
  let errors = 0;

  for (const event of events) {
    try {
      const posthogEvent = EVENT_MAP[event.event] || event.event;

      posthog.capture({
        distinctId: event.userId,
        event: posthogEvent,
        properties: {
          ...event.properties,
          $timestamp: event.timestamp, // Preserve original timestamp
          migration_imported: true,
        },
        timestamp: new Date(event.timestamp),
      });

      imported++;

      if (imported % 10000 === 0) {
        await posthog.flush();
        console.log(`Imported ${imported} events...`);
      }
    } catch (error) {
      errors++;
      console.error(`Failed to import event: ${event.event}`, error);
    }
  }

  await posthog.shutdown();
  return { imported, errors };
}

// Usage:
// const events = await exportFromMixpanel(); // Your export function
// await importHistoricalEvents(events);
```

### Step 4: Batch Import via HTTP API

```bash
set -euo pipefail
# Import events in batch via the /batch/ endpoint
# Max request body: 20MB

curl -X POST 'https://us.i.posthog.com/batch/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "'$NEXT_PUBLIC_POSTHOG_KEY'",
    "historical_migration": true,
    "batch": [
      {
        "event": "user_signed_up",
        "distinct_id": "user-001",
        "timestamp": "2025-01-15T10:30:00Z",
        "properties": {"method": "email", "source": "migration"}
      },
      {
        "event": "subscription_started",
        "distinct_id": "user-001",
        "timestamp": "2025-01-16T14:20:00Z",
        "properties": {"plan": "pro", "source": "migration"}
      }
    ]
  }'
```

### Step 5: Feature Flag Controlled Cutover

```typescript
// Use a PostHog feature flag to gradually shift traffic
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
});

async function getAnalyticsBackend(userId: string): Promise<'posthog' | 'legacy' | 'dual'> {
  const migrationPhase = await posthog.getFeatureFlag('analytics-migration', userId);

  switch (migrationPhase) {
    case 'posthog-only':
      return 'posthog';   // Phase 3: PostHog only
    case 'dual-write':
      return 'dual';      // Phase 2: Both platforms
    default:
      return 'legacy';    // Phase 1: Old platform only
  }
}

// Rollout plan:
// Week 1: Flag at 0% → all traffic to legacy
// Week 2: Flag "dual-write" at 10% → dual-write for 10%
// Week 3: Flag "dual-write" at 100% → dual-write for everyone
// Week 4: Validate PostHog data matches legacy
// Week 5: Flag "posthog-only" at 10% → PostHog only for 10%
// Week 6: Flag "posthog-only" at 100% → migration complete
```

### Step 6: Validation

```bash
set -euo pipefail
# Compare event counts between old platform and PostHog
echo "=== PostHog Event Counts (last 7 days) ==="
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/query/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT event, count() AS total FROM events WHERE timestamp > now() - interval 7 day AND properties.migration_source = '"'"'dual-write'"'"' GROUP BY event ORDER BY total DESC LIMIT 20"
    }
  }' | jq '.results[] | {event: .[0], count: .[1]}'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Event counts don't match | Sampling or timing differences | Compare daily totals, allow 5% variance |
| Historical import slow | Single-threaded | Use batch endpoint, increase `flushAt` |
| Identity mismatch | Different user ID formats | Normalize IDs in event map |
| Duplicate events | Dual-write without dedup | Use `migration_source` property to filter |

## Output

- Event name and property mapping from source platform
- Dual-write adapter for gradual migration
- Historical data import script
- Feature flag controlled cutover plan
- Validation queries comparing event counts

## Resources

- [PostHog Capture API](https://posthog.com/docs/api/capture)
- [PostHog Migrate from Mixpanel](https://posthog.com/docs/migrate/mixpanel)
- [PostHog Migrate from Amplitude](https://posthog.com/docs/migrate/amplitude)
- [PostHog Historical Migration](https://posthog.com/docs/migrate)
