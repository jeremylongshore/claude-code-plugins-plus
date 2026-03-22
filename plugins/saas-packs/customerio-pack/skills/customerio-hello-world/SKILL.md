---
name: customerio-hello-world
description: |
  Create a minimal working Customer.io example.
  Use when learning Customer.io basics, testing SDK setup,
  or creating your first identify + track integration.
  Trigger: "customer.io hello world", "first customer.io message",
  "test customer.io", "customer.io example", "customer.io quickstart".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, quickstart, testing]

---
# Customer.io Hello World

## Overview

Create a minimal working Customer.io integration: identify a user (create/update their profile), track an event, and send a transactional email. This covers the three fundamental Customer.io operations.

## Prerequisites

- `customerio-node` installed (`npm install customerio-node`)
- `CUSTOMERIO_SITE_ID` and `CUSTOMERIO_TRACK_API_KEY` configured
- `CUSTOMERIO_APP_API_KEY` configured (for transactional email example)

## Instructions

### Step 1: Identify a User (Create/Update Profile)

```typescript
// hello-customerio.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// identify() creates the user if they don't exist, or updates if they do.
// The first argument is your internal user ID (immutable — use DB primary key).
await cio.identify("user-123", {
  email: "hello@example.com",          // Required for email campaigns
  first_name: "Jane",
  last_name: "Doe",
  plan: "pro",
  created_at: Math.floor(Date.now() / 1000),  // Unix seconds, NOT milliseconds
});

console.log("User identified in Customer.io");
```

**Key rules:**
- `id` (first arg) should be your immutable database ID — never use email as ID
- `email` attribute is required if you want to send email campaigns
- `created_at` must be Unix timestamp in **seconds** (not ms) — `Math.floor(Date.now() / 1000)`
- All custom attributes are stored on the user profile and usable in segments + Liquid templates

### Step 2: Track an Event

```typescript
// Track a custom event on the user's activity timeline.
// Events trigger campaigns — the event name must match exactly in the dashboard.
await cio.track("user-123", {
  name: "signed_up",                   // snake_case, matches campaign trigger
  data: {
    signup_method: "google_oauth",
    referral_source: "product_hunt",
    timestamp: Math.floor(Date.now() / 1000),
  },
});

console.log("Event tracked in Customer.io");
```

**Key rules:**
- User must be identified before tracking events (call `identify()` first)
- Event `name` is case-sensitive and must match your campaign trigger exactly
- Use `snake_case` for event names — `signed_up`, not `Signed Up` or `signedUp`
- `data` properties are accessible in Liquid templates as `{{ event.property_name }}`

### Step 3: Track an Anonymous Event

```typescript
// Track events before the user signs up — merge later on identification
await cio.trackAnonymous({
  anonymous_id: "anon-abc-123",         // Your anonymous tracking ID (cookie, device ID)
  name: "page_viewed",
  data: {
    url: "/pricing",
    referrer: "https://google.com",
  },
});

console.log("Anonymous event tracked");
```

When the anonymous user signs up, include `anonymous_id` in the `identify()` call to merge their pre-signup activity:

```typescript
await cio.identify("user-123", {
  email: "hello@example.com",
  anonymous_id: "anon-abc-123",         // Merges anonymous activity
});
```

### Step 4: Send a Transactional Email

```typescript
import { APIClient, SendEmailRequest, RegionUS } from "customerio-node";

const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS,
});

const request = new SendEmailRequest({
  to: "hello@example.com",
  transactional_message_id: "1",        // ID from Customer.io dashboard
  message_data: {                       // Populates {{ liquid }} variables
    welcome_name: "Jane",
    login_url: "https://app.example.com/login",
  },
  identifiers: { id: "user-123" },      // Links delivery to user profile
});

const response = await api.sendEmail(request);
console.log("Email queued:", response.delivery_id);
```

### Step 5: Verify in Dashboard

1. Go to https://fly.customer.io
2. Navigate to **People** and search for "hello@example.com"
3. Verify the profile shows `first_name`, `plan`, and other attributes
4. Click the **Activity** tab to see the `signed_up` event
5. Check **Deliveries** for the transactional email

## Complete Example

```typescript
// scripts/hello-customerio.ts
import {
  TrackClient, APIClient, SendEmailRequest, RegionUS
} from "customerio-node";

async function main() {
  // Track API client — identify and track
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  // 1. Identify
  await cio.identify("user-hello-world", {
    email: "hello@example.com",
    first_name: "Jane",
    created_at: Math.floor(Date.now() / 1000),
  });
  console.log("1. User identified");

  // 2. Track event
  await cio.track("user-hello-world", {
    name: "hello_world_completed",
    data: { sdk: "customerio-node", step: "quickstart" },
  });
  console.log("2. Event tracked");

  // 3. Clean up test user (optional)
  await cio.suppress("user-hello-world");
  console.log("3. Test user suppressed (won't receive messages)");
}

main().catch(console.error);
```

Run: `npx tsx scripts/hello-customerio.ts`

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Verify Site ID + Track API Key in dashboard |
| `400 Bad Request` | Malformed payload | Check attribute types and event name format |
| User not in People tab | `identify()` not called | Always call `identify()` before `track()` |
| Event not in Activity | Dashboard propagation delay | Wait 1-2 minutes and refresh |
| Transactional email fails | Wrong `transactional_message_id` | Verify the ID matches your template in Customer.io |

## Resources

- [Track API Reference](https://docs.customer.io/integrations/api/track/)
- [Transactional API Concepts](https://docs.customer.io/journeys/transactional-api/)
- [customerio-node README](https://github.com/customerio/customerio-node)

## Next Steps

After verifying hello world works, proceed to `customerio-local-dev-loop` to set up your development workflow.
