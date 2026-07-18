# Klaviyo Reference Architecture — Implementation Walkthrough

Working code for each layer of the reference architecture in
[architecture.md](architecture.md). Build the layers bottom-up: config first, then
the services that consume it. Every Klaviyo call routes through
`withRateLimitRetry` from the rate-limiter middleware.

## Step 1: Config Layer

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

## Step 2: Service Layer -- Profile Sync

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

## Step 3: Service Layer -- Event Tracker

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
