---
name: klaviyo-reference-architecture
description: |
  Implement Klaviyo reference architecture with best-practice project layout.
  Use when designing new Klaviyo integrations, reviewing project structure,
  or establishing architecture standards for email/SMS marketing applications.
  Trigger with phrases like "klaviyo architecture", "klaviyo project structure",
  "klaviyo design", "how to organize klaviyo", "klaviyo layout".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Reference Architecture

## Overview

Production-ready architecture for Klaviyo integrations: layered project structure, service patterns, event-driven sync, and the `klaviyo-api` SDK wired into a real application.

## Prerequisites

- TypeScript project with `klaviyo-api` installed
- Understanding of layered architecture
- Redis (for caching/queuing) and database (for audit/sync state)

## Project Structure

```
src/
├── klaviyo/                     # SDK layer (thin wrappers)
│   ├── session.ts               # ApiKeySession singleton
│   ├── api.ts                   # Lazy API client getters
│   ├── types.ts                 # Shared Klaviyo types
│   └── errors.ts                # Error parsing/classification
├── services/                    # Business logic layer
│   ├── profile-sync.ts          # Bidirectional profile sync
│   ├── event-tracker.ts         # Server-side event tracking
│   ├── campaign-manager.ts      # Campaign create/send
│   ├── list-manager.ts          # List/subscription management
│   └── segment-query.ts         # Segment membership queries
├── webhooks/                    # Inbound webhook handlers
│   ├── router.ts                # Topic-based event routing
│   ├── verify.ts                # HMAC-SHA256 signature verification
│   └── handlers/
│       ├── profile-events.ts    # profile.created, profile.updated
│       ├── list-events.ts       # list.member.added/removed
│       └── campaign-events.ts   # campaign.sent, delivered
├── jobs/                        # Background jobs
│   ├── profile-sync-job.ts      # Scheduled bidirectional sync
│   ├── list-cleanup-job.ts      # Unengaged profile suppression
│   └── metrics-export-job.ts    # Export Klaviyo metrics to BI
├── middleware/
│   └── klaviyo-rate-limiter.ts  # Request queue + retry logic
├── config/
│   └── klaviyo.ts               # Environment-specific config
└── health/
    └── klaviyo.ts               # Health check endpoint
```

## Layer Architecture

```
┌──────────────────────────────────────────────┐
│              API / Webhook Layer              │
│    Express routes, webhook handlers           │
├──────────────────────────────────────────────┤
│              Service Layer                    │
│    profile-sync, event-tracker, campaigns     │
│    Business logic, orchestration, validation  │
├──────────────────────────────────────────────┤
│              Klaviyo SDK Layer                │
│    ApiKeySession, ProfilesApi, EventsApi      │
│    Error parsing, retry logic                 │
├──────────────────────────────────────────────┤
│              Infrastructure Layer             │
│    Cache (Redis), Queue (BullMQ),            │
│    Database (Prisma), Monitoring (OTel)       │
└──────────────────────────────────────────────┘
```

**Rules:**
- API layer calls Service layer only
- Service layer calls SDK layer and Infrastructure
- SDK layer never calls upward
- Webhooks are treated as API endpoints

## Instructions

### Step 1: Config Layer

```typescript
// src/config/klaviyo.ts
export interface KlaviyoConfig {
  privateKey: string;
  publicKey: string;
  webhookSecret: string;
  environment: 'development' | 'staging' | 'production';
  rateLimits: { burstPerSecond: number; steadyPerMinute: number };
  cache: { enabled: boolean; ttlMs: number };
}

export function loadConfig(): KlaviyoConfig {
  const env = process.env.NODE_ENV || 'development';
  return {
    privateKey: process.env.KLAVIYO_PRIVATE_KEY || '',
    publicKey: process.env.KLAVIYO_PUBLIC_KEY || '',
    webhookSecret: process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET || '',
    environment: env as KlaviyoConfig['environment'],
    rateLimits: { burstPerSecond: 75, steadyPerMinute: 700 },
    cache: {
      enabled: env !== 'development',
      ttlMs: env === 'production' ? 300000 : 60000,
    },
  };
}
```

### Step 2: Service Layer -- Profile Sync

```typescript
// src/services/profile-sync.ts
import { ProfilesApi, ProfileEnum } from 'klaviyo-api';
import { getSession } from '../klaviyo/session';
import { withRateLimitRetry } from '../middleware/klaviyo-rate-limiter';

export class ProfileSyncService {
  private profilesApi: ProfilesApi;

  constructor() {
    this.profilesApi = new ProfilesApi(getSession());
  }

  /** Sync a user from your DB to Klaviyo (upsert) */
  async syncToKlaviyo(user: {
    email: string;
    firstName?: string;
    lastName?: string;
    phone?: string;
    metadata?: Record<string, any>;
  }): Promise<string> {
    const result = await withRateLimitRetry(() =>
      this.profilesApi.createOrUpdateProfile({
        data: {
          type: ProfileEnum.Profile,
          attributes: {
            email: user.email,
            firstName: user.firstName,
            lastName: user.lastName,
            phoneNumber: user.phone,
            properties: {
              ...user.metadata,
              lastSyncedAt: new Date().toISOString(),
              syncSource: 'app-db',
            },
          },
        },
      })
    );
    return result.body.data.id;
  }

  /** Fetch a Klaviyo profile and sync back to your DB */
  async syncFromKlaviyo(email: string): Promise<any> {
    const result = await withRateLimitRetry(() =>
      this.profilesApi.getProfiles({
        filter: `equals(email,"${email}")`,
        fieldsProfile: ['email', 'first_name', 'last_name', 'phone_number', 'properties'],
      })
    );

    const profile = result.body.data[0];
    if (!profile) return null;

    return {
      klaviyoId: profile.id,
      email: profile.attributes.email,
      firstName: profile.attributes.firstName,
      lastName: profile.attributes.lastName,
      phone: profile.attributes.phoneNumber,
      properties: profile.attributes.properties,
    };
  }
}
```

### Step 3: Service Layer -- Event Tracker

```typescript
// src/services/event-tracker.ts
import { EventsApi, ProfileEnum } from 'klaviyo-api';
import { getSession } from '../klaviyo/session';
import { withRateLimitRetry } from '../middleware/klaviyo-rate-limiter';

export class EventTracker {
  private eventsApi: EventsApi;

  constructor() {
    this.eventsApi = new EventsApi(getSession());
  }

  async trackPurchase(order: {
    email: string;
    orderId: string;
    total: number;
    items: Array<{ sku: string; name: string; qty: number; price: number }>;
  }): Promise<void> {
    await withRateLimitRetry(() =>
      this.eventsApi.createEvent({
        data: {
          type: 'event',
          attributes: {
            metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
            profile: { data: { type: 'profile', attributes: { email: order.email } } },
            properties: {
              orderId: order.orderId,
              items: order.items,
              itemCount: order.items.reduce((sum, i) => sum + i.qty, 0),
            },
            value: order.total,
            uniqueId: order.orderId,
            time: new Date().toISOString(),
          },
        },
      })
    );
  }

  async trackCustomEvent(email: string, eventName: string, properties: Record<string, any>): Promise<void> {
    await withRateLimitRetry(() =>
      this.eventsApi.createEvent({
        data: {
          type: 'event',
          attributes: {
            metric: { data: { type: 'metric', attributes: { name: eventName } } },
            profile: { data: { type: 'profile', attributes: { email } } },
            properties,
            time: new Date().toISOString(),
          },
        },
      })
    );
  }
}
```

### Step 4: Data Flow Diagram

```
Your App                          Klaviyo
─────────                         ───────

User signs up ──→ ProfileSyncService.syncToKlaviyo()
                        │
                        ▼
                  POST /api/profiles/  ──→  Profile created
                                              │
                                              ▼
                                        Welcome Flow triggered
                                              │
                                              ▼
User purchases ──→ EventTracker.trackPurchase()
                        │
                        ▼
                  POST /api/events/  ──→  "Placed Order" event
                                              │
                                              ▼
                                        Post-purchase Flow
                                              │
                                              ▼
Profile updated ◀── Webhook ◀──────── profile.updated event
       │
       ▼
WebhookRouter.routeEvent()
       │
       ▼
Update local DB
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular deps | Wrong layering | Services call SDK, never the reverse |
| Sync conflicts | Both sides update | Last-write-wins with sync timestamp |
| Queue backlog | Klaviyo slow/down | Circuit breaker + dead letter queue |
| Type mismatches | SDK version mismatch | Pin SDK version, run `tsc --noEmit` in CI |

## Resources

- [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview)
- [Custom Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)
- [Ecommerce Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)

## Next Steps

For multi-environment setup, see `klaviyo-multi-env-setup`.
