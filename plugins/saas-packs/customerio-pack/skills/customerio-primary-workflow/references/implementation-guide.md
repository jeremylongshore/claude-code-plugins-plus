# Customerio Primary Workflow - Implementation Guide

# Customer.io Primary Workflow

## Overview
Implement Customer.io's primary messaging workflow: identify users, track events, and trigger automated campaigns.

## Prerequisites
- Customer.io SDK configured
- Campaign/workflow created in Customer.io dashboard
- Understanding of your user lifecycle events

## Instructions

### Step 1: Define User Lifecycle Events
```typescript
// events/user-events.ts
export const USER_EVENTS = {
  // Onboarding
  SIGNED_UP: 'signed_up',
  EMAIL_VERIFIED: 'email_verified',
  PROFILE_COMPLETED: 'profile_completed',
  FIRST_LOGIN: 'first_login',

  // Engagement
  FEATURE_USED: 'feature_used',
  CONTENT_VIEWED: 'content_viewed',
  SEARCH_PERFORMED: 'search_performed',

  // Conversion
  TRIAL_STARTED: 'trial_started',
  SUBSCRIPTION_STARTED: 'subscription_started',
  UPGRADE_COMPLETED: 'upgrade_completed',
  PURCHASE_COMPLETED: 'purchase_completed',

  // Churn Risk
  INACTIVE_WARNING: 'inactive_warning',
  SUBSCRIPTION_CANCELLED: 'subscription_cancelled',
  ACCOUNT_DELETED: 'account_deleted',
} as const;

export type UserEvent = typeof USER_EVENTS[keyof typeof USER_EVENTS];
```

### Step 2: Implement Event Tracking Service
```typescript
// services/customerio-service.ts
import { TrackClient, RegionUS } from '@customerio/track';
import { USER_EVENTS, UserEvent } from '../events/user-events';

interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  plan?: string;
}

export class CustomerIOService {
  private client: TrackClient;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  }

  // Called on user signup
  async onSignup(user: User): Promise<void> {
    await this.client.identify(user.id, {
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName,
      created_at: Math.floor(Date.now() / 1000),
      plan: 'free',
      onboarding_status: 'started'
    });

    await this.track(user.id, USER_EVENTS.SIGNED_UP, {
      signup_source: 'web',
      signup_date: new Date().toISOString()
    });
  }

  // Called when email is verified
  async onEmailVerified(userId: string): Promise<void> {
    await this.updateUser(userId, {
      email_verified: true,
      email_verified_at: Math.floor(Date.now() / 1000)
    });
    await this.track(userId, USER_EVENTS.EMAIL_VERIFIED);
  }

  // Called on subscription change
  async onSubscriptionStarted(userId: string, plan: string): Promise<void> {
    await this.updateUser(userId, {
      plan,
      subscription_started_at: Math.floor(Date.now() / 1000)
    });
    await this.track(userId, USER_EVENTS.SUBSCRIPTION_STARTED, { plan });
  }

  // Generic tracking method
  async track(userId: string, event: UserEvent, data?: Record<string, any>): Promise<void> {
    await this.client.track(userId, {
      name: event,
      data: {
        ...data,
        timestamp: new Date().toISOString()
      }
    });
  }

  // Update user attributes
  async updateUser(userId: string, attributes: Record<string, any>): Promise<void> {
    await this.client.identify(userId, attributes);
  }
}

export const cioService = new CustomerIOService();
```

### Step 3: Integrate with Application
```typescript
// routes/auth.ts
import { cioService } from '../services/customerio-service';

app.post('/signup', async (req, res) => {
  const user = await createUser(req.body);

  // Fire and forget - don't block signup on analytics
  cioService.onSignup({
    id: user.id,
    email: user.email,
    firstName: user.firstName,
    lastName: user.lastName
  }).catch(err => console.error('Customer.io error:', err));

  res.json({ user });
});

app.post('/verify-email', async (req, res) => {
  const userId = await verifyEmailToken(req.body.token);

  cioService.onEmailVerified(userId)
    .catch(err => console.error('Customer.io error:', err));

  res.json({ success: true });
});
```

### Step 4: Create Dashboard Campaign
In Customer.io Dashboard:
1. Go to Campaigns > Create Campaign
2. Select trigger: Event "signed_up"
3. Add workflow steps:
   - Wait 1 day
   - Send welcome email
   - Wait 3 days
   - Branch: if email_verified = false, send reminder
   - Continue nurture sequence

## Output
- User lifecycle event definitions
- Customer.io service integration
- Application route integration
- Campaign workflow triggering

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Event not triggering | Wrong event name | Match exact event name in dashboard |
| User not receiving | Missing email attribute | Ensure email is set on identify |
| Duplicate sends | Multiple event fires | Deduplicate or use idempotency |

## Resources
- [Customer.io Campaigns](https://customer.io/docs/campaigns/)
- [Trigger Events](https://customer.io/docs/events/)

## Next Steps
After implementing primary workflow, proceed to `customerio-core-feature` for advanced features.
