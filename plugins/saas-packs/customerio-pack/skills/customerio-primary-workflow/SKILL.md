---
name: customerio-primary-workflow
description: |
  Implement Customer.io primary messaging workflow.
  Use when setting up campaign triggers, welcome sequences,
  onboarding flows, or event-driven email automation.
  Trigger: "customer.io campaign", "customer.io workflow",
  "customer.io email automation", "customer.io messaging", "customer.io onboarding".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, workflow, campaigns, automation]

---
# Customer.io Primary Workflow

## Overview

Implement Customer.io's core messaging workflow: identify users with segment-ready attributes, track lifecycle events that trigger campaigns, and set up the data layer for automated onboarding, nurture, and re-engagement sequences.

## Prerequisites

- `customerio-node` configured with Track API credentials
- Campaigns created in Customer.io dashboard (triggered by events you define)
- Understanding of your user lifecycle stages

## How Campaigns Work

```
Your App (SDK)           Customer.io Dashboard          User
─────────────           ────────────────────          ────
cio.identify(user)  →   Profile created/updated
cio.track("signed_up")  →   Campaign trigger fires
                             Wait 1 day             →   Welcome email
                             Check: verified?
                             ├─ No                  →   Verification reminder
                             └─ Yes → Wait 3 days   →   Feature tips email
```

Events tracked via the SDK trigger campaigns you build in the dashboard. The SDK sends the **data**; the dashboard defines the **workflow logic**.

## Instructions

### Step 1: Define Your Event Taxonomy

```typescript
// lib/customerio-events.ts
import { TrackClient, RegionUS } from "customerio-node";

// Central event definitions — every event your app tracks
export const CIO_EVENTS = {
  // Onboarding
  SIGNED_UP: "signed_up",
  EMAIL_VERIFIED: "email_verified",
  PROFILE_COMPLETED: "profile_completed",
  FIRST_PROJECT_CREATED: "first_project_created",

  // Engagement
  FEATURE_USED: "feature_used",
  INVITED_TEAMMATE: "invited_teammate",
  UPGRADE_STARTED: "upgrade_started",
  UPGRADE_COMPLETED: "upgrade_completed",

  // Lifecycle
  SUBSCRIPTION_RENEWED: "subscription_renewed",
  SUBSCRIPTION_CANCELLED: "subscription_cancelled",
  TRIAL_EXPIRING: "trial_expiring",

  // Commerce
  CHECKOUT_STARTED: "checkout_started",
  CHECKOUT_COMPLETED: "checkout_completed",
  REFUND_REQUESTED: "refund_requested",
} as const;

type EventName = (typeof CIO_EVENTS)[keyof typeof CIO_EVENTS];
```

### Step 2: Build the Messaging Service

```typescript
// services/customerio-messaging.ts
import { TrackClient, RegionUS } from "customerio-node";
import { CIO_EVENTS } from "../lib/customerio-events";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName?: string;
  plan: string;
  companyName?: string;
}

export class MessagingService {
  /** Call on user signup — creates profile and triggers onboarding campaign */
  async onSignup(user: UserProfile, signupMethod: string): Promise<void> {
    // 1. Identify with all attributes campaigns need
    await cio.identify(user.id, {
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName ?? "",
      plan: user.plan,
      company: user.companyName ?? "",
      created_at: Math.floor(Date.now() / 1000),
      onboarding_step: "signed_up",
    });

    // 2. Track the event that triggers the onboarding campaign
    await cio.track(user.id, {
      name: CIO_EVENTS.SIGNED_UP,
      data: {
        method: signupMethod,  // "google", "email", "github"
        plan: user.plan,
      },
    });
  }

  /** Call when user verifies email — updates profile + tracks event */
  async onEmailVerified(userId: string): Promise<void> {
    await cio.identify(userId, {
      email_verified: true,
      email_verified_at: Math.floor(Date.now() / 1000),
      onboarding_step: "verified",
    });

    await cio.track(userId, {
      name: CIO_EVENTS.EMAIL_VERIFIED,
    });
  }

  /** Call on feature usage — drives engagement segments and campaigns */
  async onFeatureUsed(
    userId: string,
    feature: string,
    metadata?: Record<string, any>
  ): Promise<void> {
    await cio.track(userId, {
      name: CIO_EVENTS.FEATURE_USED,
      data: { feature, ...metadata },
    });

    // Update engagement metrics on the profile for segmentation
    await cio.identify(userId, {
      last_active_at: Math.floor(Date.now() / 1000),
    });
  }

  /** Call on plan upgrade — triggers upgrade confirmation campaign */
  async onUpgrade(userId: string, from: string, to: string, mrr: number): Promise<void> {
    await cio.identify(userId, {
      plan: to,
      mrr,
      upgraded_at: Math.floor(Date.now() / 1000),
    });

    await cio.track(userId, {
      name: CIO_EVENTS.UPGRADE_COMPLETED,
      data: { from_plan: from, to_plan: to, mrr },
    });
  }

  /** Call on cancellation — triggers win-back campaign */
  async onCancellation(userId: string, reason: string): Promise<void> {
    await cio.identify(userId, {
      plan: "cancelled",
      cancelled_at: Math.floor(Date.now() / 1000),
      cancellation_reason: reason,
    });

    await cio.track(userId, {
      name: CIO_EVENTS.SUBSCRIPTION_CANCELLED,
      data: { reason },
    });
  }
}
```

### Step 3: Integrate into Application Routes

```typescript
// routes/auth.ts (Express example)
import { MessagingService } from "../services/customerio-messaging";

const messaging = new MessagingService();

router.post("/signup", async (req, res) => {
  const user = await db.createUser(req.body);

  // Fire-and-forget — don't block the signup response
  messaging.onSignup(
    {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      plan: user.plan,
    },
    req.body.signupMethod
  ).catch((err) => console.error("CIO signup tracking failed:", err));

  res.json({ user });
});

router.post("/verify-email", async (req, res) => {
  await db.verifyEmail(req.user.id);
  messaging.onEmailVerified(req.user.id).catch(console.error);
  res.json({ verified: true });
});
```

### Step 4: Dashboard Campaign Configuration

In Customer.io dashboard, create campaigns triggered by these events:

**Onboarding Campaign:**
1. **Trigger:** Event `signed_up`
2. **Wait** 5 minutes
3. **Send** welcome email (use `{{ customer.first_name }}` and `{{ event.method }}` Liquid)
4. **Wait** 1 day
5. **Branch:** Is `email_verified` true?
   - No → Send verification reminder
   - Yes → Continue
6. **Wait** 3 days
7. **Send** feature tips email
8. **Wait** 7 days
9. **Branch:** Has `first_project_created` event?
   - No → Send activation nudge
   - Yes → End (move to engagement campaign)

**Cancellation Win-back Campaign:**
1. **Trigger:** Event `subscription_cancelled`
2. **Wait** 3 days
3. **Send** "We miss you" email with `{{ event.reason }}` Liquid variable
4. **Wait** 7 days
5. **Send** discount offer email

## Liquid Template Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{ customer.first_name }}` | `identify()` attributes | "Jane" |
| `{{ customer.plan }}` | `identify()` attributes | "pro" |
| `{{ event.method }}` | `track()` event data | "google" |
| `{{ event.reason }}` | `track()` event data | "too_expensive" |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Campaign not triggering | Event name mismatch | Event names are case-sensitive — verify exact match |
| User not receiving email | Missing `email` attribute | Always include `email` in `identify()` |
| Duplicate sends | Multiple event fires | Use fire-and-forget with deduplication |
| Liquid rendering `{{ }}` | Missing data property | Ensure `data` object has all template variables |

## Resources

- [Campaigns Documentation](https://docs.customer.io/journeys/campaigns-in-customerio/)
- [Liquid Personalization](https://docs.customer.io/journeys/using-liquid/)
- [Custom Events](https://docs.customer.io/integrations/data-in/custom-events/)

## Next Steps

After implementing primary workflow, proceed to `customerio-core-feature` for transactional messages, segments, and broadcasts.
