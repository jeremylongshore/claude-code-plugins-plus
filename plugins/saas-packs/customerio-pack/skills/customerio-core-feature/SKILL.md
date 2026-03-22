---
name: customerio-core-feature
description: |
  Implement Customer.io core features: transactional messages,
  API-triggered broadcasts, segments, and person merge.
  Trigger: "customer.io segments", "customer.io transactional",
  "customer.io broadcast", "customer.io merge users", "customer.io send email".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, transactional, broadcasts, segments]

---
# Customer.io Core Features

## Overview

Implement Customer.io's key platform features: transactional emails/push (password resets, receipts), API-triggered broadcasts (one-to-many on demand), segment-driving attributes, anonymous-to-known user merging, and person suppression/deletion.

## Prerequisites

- `customerio-node` installed
- Track API credentials (`CUSTOMERIO_SITE_ID` + `CUSTOMERIO_TRACK_API_KEY`)
- App API credential (`CUSTOMERIO_APP_API_KEY`) — required for transactional + broadcasts

## Instructions

### Feature 1: Transactional Email

Transactional messages are opt-in-implied messages (receipts, password resets). Create the template in Customer.io dashboard first, then call the API with data.

```typescript
// lib/customerio-transactional.ts
import { APIClient, SendEmailRequest, RegionUS } from "customerio-node";

const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS,
});

// Send a transactional email
// transactional_message_id comes from the Customer.io dashboard template
async function sendPasswordReset(email: string, userId: string, resetUrl: string) {
  const request = new SendEmailRequest({
    to: email,
    transactional_message_id: "3",  // Template ID from dashboard
    message_data: {
      reset_url: resetUrl,
      expiry_hours: 24,
      support_email: "help@yourapp.com",
    },
    identifiers: { id: userId },    // Links delivery metrics to user profile
  });

  const response = await api.sendEmail(request);
  // response = { delivery_id: "abc123", queued_at: 1704067200 }
  return response;
}

// Send an order confirmation with complex data
async function sendOrderConfirmation(
  email: string,
  userId: string,
  order: { id: string; items: { name: string; qty: number; price: number }[]; total: number }
) {
  const request = new SendEmailRequest({
    to: email,
    transactional_message_id: "5",
    message_data: {
      order_id: order.id,
      items: order.items,        // Accessible as {{ event.items }} in Liquid
      total: order.total,
      order_date: new Date().toISOString(),
    },
    identifiers: { id: userId },
  });

  return api.sendEmail(request);
}
```

**Dashboard setup:** Create transactional message at Transactional > Create Message. Use Liquid syntax: `{{ data.reset_url }}`, `{{ data.order_id }}`, `{% for item in data.items %}`.

### Feature 2: Transactional Push

```typescript
import { APIClient, SendPushRequest, RegionUS } from "customerio-node";

const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS,
});

async function sendPushNotification(userId: string, title: string, body: string) {
  const request = new SendPushRequest({
    transactional_message_id: "7",  // Push template ID
    identifiers: { id: userId },
    message_data: { title, body },
  });

  return api.sendPush(request);
}
```

### Feature 3: API-Triggered Broadcasts

Broadcasts send to a pre-defined segment on demand. Define the segment and message in the dashboard, then trigger via API.

```typescript
// lib/customerio-broadcasts.ts
import { APIClient, RegionUS } from "customerio-node";

const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS,
});

// Trigger a broadcast to a pre-defined segment
async function triggerProductUpdateBroadcast(version: string, changelog: string) {
  await api.triggerBroadcast(
    42,                           // Broadcast ID from dashboard
    { version, changelog },       // Data merged into Liquid template
    { segment: { id: 15 } }      // Target segment (defined in dashboard)
  );
}

// Trigger broadcast to specific emails
async function triggerBroadcastToEmails(
  broadcastId: number,
  emails: string[],
  data: Record<string, any>
) {
  await api.triggerBroadcast(
    broadcastId,
    data,
    {
      emails,
      email_ignore_missing: true,  // Don't error on unknown emails
      email_add_duplicates: false,  // Skip if user already in broadcast
    }
  );
}

// Trigger broadcast to specific user IDs
async function triggerBroadcastToUsers(
  broadcastId: number,
  userIds: string[],
  data: Record<string, any>
) {
  await api.triggerBroadcast(broadcastId, data, { ids: userIds });
}
```

### Feature 4: Segment-Driving Attributes

Segments in Customer.io are data-driven — they automatically include/exclude people based on attributes you set via `identify()`.

```typescript
// services/customerio-segments.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Update attributes that drive segment membership
async function updateEngagementAttributes(userId: string, metrics: {
  lastActiveAt: Date;
  sessionCount: number;
  totalRevenue: number;
  daysSinceLastLogin: number;
}) {
  await cio.identify(userId, {
    last_active_at: Math.floor(metrics.lastActiveAt.getTime() / 1000),
    session_count: metrics.sessionCount,
    total_revenue: metrics.totalRevenue,
    days_since_last_login: metrics.daysSinceLastLogin,
    engagement_tier: metrics.sessionCount > 50 ? "power_user"
      : metrics.sessionCount > 10 ? "active"
      : "casual",
  });
}

// Segment examples built in dashboard:
// "Power Users": engagement_tier = "power_user"
// "At Risk": days_since_last_login > 30 AND plan != "free"
// "High Value": total_revenue > 500
// "Trial Expiring": plan = "trial" AND trial_end_at < now + 3 days
```

### Feature 5: Merge Duplicate People

```typescript
// Merge a secondary (duplicate) person into a primary person.
// The secondary is deleted permanently after merge.
async function mergeUsers(
  primaryId: string,
  secondaryId: string,
  identifierType: "id" | "email" | "cio_id" = "id"
) {
  await cio.mergeCustomers(
    identifierType,
    primaryId,
    identifierType,
    secondaryId
  );
  // Secondary person is permanently deleted.
  // Their attributes and activity merge into the primary.
}
```

### Feature 6: Suppress and Delete People

```typescript
// Suppress: user stays in system but receives no messages
async function suppressUser(userId: string): Promise<void> {
  await cio.suppress(userId);
}

// Delete: remove user entirely from Customer.io
async function deleteUser(userId: string): Promise<void> {
  await cio.destroy(userId);
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422` on transactional | Wrong `transactional_message_id` | Verify template ID in Customer.io dashboard |
| Missing Liquid variable | `message_data` incomplete | Ensure all `{{ data.x }}` variables are in `message_data` |
| Broadcast `404` | Invalid broadcast ID | Check broadcast ID in dashboard Broadcasts section |
| Segment not updating | Attribute type mismatch | Dashboard segments compare types strictly — number vs string matters |
| Merge fails | Secondary person doesn't exist | Verify both people exist before merging |

## Resources

- [Transactional API](https://docs.customer.io/journeys/transactional-api/)
- [Transactional Examples](https://docs.customer.io/journeys/transactional-api-examples/)
- [API-Triggered Broadcasts](https://docs.customer.io/journeys/api-triggered-broadcasts/)
- [Manual Segments](https://docs.customer.io/journeys/manual-segments/)

## Next Steps

After implementing core features, proceed to `customerio-common-errors` for troubleshooting.
