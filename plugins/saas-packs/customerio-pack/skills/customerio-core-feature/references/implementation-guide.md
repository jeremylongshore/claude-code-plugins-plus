# Customerio Core Feature - Implementation Guide

# Customer.io Core Feature Integration

## Overview
Implement Customer.io core features: segments, transactional messaging, data pipelines, and broadcast campaigns.

## Prerequisites
- Customer.io SDK configured
- Understanding of customer data model
- App API credentials for transactional emails

## Instructions

### Feature 1: Transactional Messages
```typescript
// lib/customerio-transactional.ts
import { APIClient, RegionUS, SendEmailRequest } from '@customerio/track';

const apiClient = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS
});

interface TransactionalEmailOptions {
  to: string;
  transactionalMessageId: string;
  messageData?: Record<string, any>;
  identifiers?: { id?: string; email?: string };
}

export async function sendTransactionalEmail(options: TransactionalEmailOptions) {
  const request: SendEmailRequest = {
    to: options.to,
    transactional_message_id: options.transactionalMessageId,
    message_data: options.messageData,
    identifiers: options.identifiers
  };

  return apiClient.sendEmail(request);
}

// Usage examples
// Password reset
await sendTransactionalEmail({
  to: 'user@example.com',
  transactionalMessageId: 'password_reset',
  messageData: {
    reset_link: 'https://app.example.com/reset?token=abc123',
    expiry_hours: 24
  }
});

// Order confirmation
await sendTransactionalEmail({
  to: 'customer@example.com',
  transactionalMessageId: 'order_confirmation',
  messageData: {
    order_id: 'ORD-12345',
    items: [
      { name: 'Product A', quantity: 2, price: 29.99 }
    ],
    total: 59.98
  },
  identifiers: { id: 'user-456' }
});
```

### Feature 2: Segments
```typescript
// lib/customerio-segments.ts
import { TrackClient } from '@customerio/track';

// Update user attributes for segment membership
export async function updateUserForSegments(
  client: TrackClient,
  userId: string,
  attributes: {
    // Engagement metrics
    last_active_at?: number;
    session_count?: number;
    total_time_spent?: number;

    // Business metrics
    total_revenue?: number;
    order_count?: number;
    average_order_value?: number;

    // Feature usage
    features_used?: string[];
    premium_features_used?: boolean;

    // Risk indicators
    churn_risk_score?: number;
    days_since_last_login?: number;
  }
) {
  await client.identify(userId, attributes);
}

// Segment-triggering attribute updates
const segmentExamples = {
  // High-value customer segment
  highValue: {
    total_revenue: 1000,
    order_count: 10
  },

  // At-risk segment
  atRisk: {
    days_since_last_login: 30,
    churn_risk_score: 0.8
  },

  // Power user segment
  powerUser: {
    session_count: 100,
    premium_features_used: true
  }
};
```

### Feature 3: Anonymous Tracking
```typescript
// lib/customerio-anonymous.ts
import { TrackClient } from '@customerio/track';

export class AnonymousTracker {
  constructor(private client: TrackClient) {}

  // Track anonymous page views
  async trackPageView(anonymousId: string, page: string, referrer?: string) {
    await this.client.trackAnonymous({
      anonymous_id: anonymousId,
      name: 'page_viewed',
      data: {
        page,
        referrer,
        timestamp: new Date().toISOString()
      }
    });
  }

  // Merge anonymous activity when user signs up
  async mergeOnSignup(anonymousId: string, userId: string, email: string) {
    // First, identify the user with the anonymous_id
    await this.client.identify(userId, {
      email,
      anonymous_id: anonymousId,
      created_at: Math.floor(Date.now() / 1000)
    });

    // Customer.io will automatically merge anonymous activity
  }
}
```

### Feature 4: Object Tracking (Companies/Accounts)
```typescript
// lib/customerio-objects.ts
import { TrackClient } from '@customerio/track';

export class ObjectTracker {
  constructor(private client: TrackClient) {}

  // Track company/account as an object
  async trackCompany(companyId: string, attributes: {
    name: string;
    plan: string;
    mrr: number;
    employee_count: number;
    industry?: string;
  }) {
    // Use object tracking for B2B scenarios
    await this.client.identify(`company:${companyId}`, {
      ...attributes,
      object_type: 'company',
      updated_at: Math.floor(Date.now() / 1000)
    });
  }

  // Associate user with company
  async associateUserWithCompany(userId: string, companyId: string, role: string) {
    await this.client.identify(userId, {
      company_id: companyId,
      company_role: role
    });
  }
}
```

### Feature 5: Data Pipeline Integration
```typescript
// lib/customerio-data-pipeline.ts
export interface DataPipelineConfig {
  source: 'segment' | 'rudderstack' | 'mparticle' | 'custom';
  mappings: {
    userId: string;
    email: string;
    customAttributes: Record<string, string>;
  };
}

// Webhook handler for incoming CDP data
export async function handleCDPWebhook(
  client: TrackClient,
  event: {
    type: 'identify' | 'track';
    userId: string;
    traits?: Record<string, any>;
    event?: string;
    properties?: Record<string, any>;
  }
) {
  if (event.type === 'identify' && event.traits) {
    await client.identify(event.userId, event.traits);
  } else if (event.type === 'track' && event.event) {
    await client.track(event.userId, {
      name: event.event,
      data: event.properties
    });
  }
}
```

## Output
- Transactional email sending capability
- Segment-ready user attributes
- Anonymous to known user merging
- B2B object tracking (companies)
- CDP data pipeline integration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid template | Wrong message ID | Verify transactional_message_id in dashboard |
| Missing required data | Template variables missing | Check message_data contains all variables |
| Segment not updating | Attribute not matching | Verify attribute types and operators |

## Resources
- [Transactional API](https://customer.io/docs/transactional-api/)
- [Segments](https://customer.io/docs/segments/)
- [Anonymous Events](https://customer.io/docs/anonymous-events/)

## Next Steps
After implementing core features, proceed to `customerio-common-errors` to learn troubleshooting.
