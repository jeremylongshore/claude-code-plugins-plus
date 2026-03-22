---
name: customerio-known-pitfalls
description: |
  Identify and avoid Customer.io anti-patterns and gotchas.
  Use when reviewing integrations, onboarding developers,
  or auditing existing Customer.io code.
  Trigger: "customer.io mistakes", "customer.io anti-patterns",
  "customer.io gotchas", "customer.io pitfalls", "customer.io code review".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, best-practices, anti-patterns]

---
# Customer.io Known Pitfalls

## Overview

The 12 most common Customer.io integration mistakes, with the wrong pattern, the correct pattern, and why it matters. Use this as a code review checklist and developer onboarding reference.

## The Pitfall Catalog

### Pitfall 1: Wrong API Key Type

```typescript
// WRONG — using Track API key for transactional messages
const api = new APIClient(process.env.CUSTOMERIO_TRACK_API_KEY!);
// Gets 401 because App API uses a DIFFERENT bearer token

// CORRECT — use the App API key
const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!);
```

**Why:** Customer.io has two separate authentication systems. Track API uses Basic Auth (Site ID + Track Key). App API uses Bearer Auth (App Key). They are not interchangeable.

### Pitfall 2: Millisecond Timestamps

```typescript
// WRONG — JavaScript Date.now() returns milliseconds
await cio.identify("user-1", {
  created_at: Date.now(),           // 1704067200000 → year 55976
});

// CORRECT — Customer.io expects Unix seconds
await cio.identify("user-1", {
  created_at: Math.floor(Date.now() / 1000),  // 1704067200
});
```

**Why:** Customer.io accepts millisecond values without error but interprets them as seconds, resulting in dates thousands of years in the future. Segments using date comparisons silently break.

### Pitfall 3: Track Before Identify

```typescript
// WRONG — tracking before identifying creates orphaned events
await cio.track("new-user", { name: "signed_up", data: {} });
// User profile doesn't exist yet — event may be lost

// CORRECT — always identify first
await cio.identify("new-user", { email: "user@example.com" });
await cio.track("new-user", { name: "signed_up", data: {} });
```

**Why:** Track calls on non-existent users may be silently dropped. Always `identify()` before `track()`.

### Pitfall 4: Using Email as User ID

```typescript
// WRONG — email can change, creating duplicate profiles
await cio.identify("user@example.com", { email: "user@example.com" });
// When user changes email, old profile orphaned, new one created

// CORRECT — use immutable database ID
await cio.identify("usr_abc123", {
  email: "user@example.com",    // Email as attribute, not ID
});
```

**Why:** The first argument to `identify()` is the permanent user ID. If you use email and the user changes it, you get two profiles. Use your database primary key instead.

### Pitfall 5: Missing Email Attribute

```typescript
// WRONG — user can't receive email campaigns
await cio.identify("user-1", {
  first_name: "Jane",
  plan: "pro",
  // No email attribute!
});

// CORRECT — always include email for email campaigns
await cio.identify("user-1", {
  email: "jane@example.com",
  first_name: "Jane",
  plan: "pro",
});
```

**Why:** Without an `email` attribute, the user profile exists but can't receive any email campaigns or transactional messages.

### Pitfall 6: Dynamic Event Names

```typescript
// WRONG — creates hundreds of unique event names
await cio.track("user-1", {
  name: `viewed_${productId}`,       // "viewed_SKU-12345"
  data: {},
});

// CORRECT — use a static name with data properties
await cio.track("user-1", {
  name: "product_viewed",             // Consistent, filterable
  data: { product_id: productId },    // Dynamic data in properties
});
```

**Why:** Dynamic event names pollute your event catalog and make it impossible to create campaign triggers. Use a fixed set of event names and pass variations as data properties.

### Pitfall 7: Blocking Request Path

```typescript
// WRONG — API call adds 200ms+ to every request
app.post("/api/action", async (req, res) => {
  const result = await doBusinessLogic(req.body);
  await cio.track(req.user.id, { name: "action_taken", data: {} }); // BLOCKS response
  res.json(result);
});

// CORRECT — fire-and-forget for non-critical tracking
app.post("/api/action", async (req, res) => {
  const result = await doBusinessLogic(req.body);
  cio.track(req.user.id, { name: "action_taken", data: {} })
    .catch((err) => console.error("CIO track failed:", err.message));
  res.json(result);  // Returns immediately
});
```

**Why:** Customer.io tracking is non-critical analytics. Don't add 200ms+ latency to every user request.

### Pitfall 8: No Bounce Handling

```typescript
// WRONG — keep sending to bounced addresses, damaging sender reputation
// (No webhook handler for bounces)

// CORRECT — suppress users who bounce
async function handleBounceWebhook(event: { customer_id: string }) {
  await cio.suppress(event.customer_id);
  console.warn(`Suppressed bounced user: ${event.customer_id}`);
}
```

**Why:** Continuing to send to bounced addresses damages your sender reputation, eventually causing all your emails to go to spam.

### Pitfall 9: New Client Per Request

```typescript
// WRONG — creates a new TCP connection for every API call
app.post("/track", async (req, res) => {
  const cio = new TrackClient(siteId, apiKey, { region: RegionUS });
  await cio.track(req.body.userId, req.body.event);
  res.sendStatus(200);
});

// CORRECT — singleton, created once
const cio = new TrackClient(siteId, apiKey, { region: RegionUS });

app.post("/track", async (req, res) => {
  await cio.track(req.body.userId, req.body.event);
  res.sendStatus(200);
});
```

**Why:** Each `new TrackClient()` creates fresh connections. Singleton reuses TCP connections, reducing latency by 50-80%.

### Pitfall 10: Inconsistent Event Names

```typescript
// WRONG — multiple naming conventions
await cio.track(userId, { name: "UserSignedUp" });      // PascalCase
await cio.track(userId, { name: "user-signed-up" });     // kebab-case
await cio.track(userId, { name: "user signed up" });     // spaces

// CORRECT — consistent snake_case everywhere
await cio.track(userId, { name: "user_signed_up" });
```

**Why:** Event names are case-sensitive. Inconsistent naming means campaign triggers only match one variant, and your event catalog becomes a mess.

### Pitfall 11: No Rate Limiting

```typescript
// WRONG — blasting API at full speed during import
for (const user of allUsers) {
  await cio.identify(user.id, user.attrs);  // 1000+ req/sec → 429 errors
}

// CORRECT — rate-limited processing
import Bottleneck from "bottleneck";
const limiter = new Bottleneck({ maxConcurrent: 10, minTime: 15 });

for (const user of allUsers) {
  await limiter.schedule(() => cio.identify(user.id, user.attrs));
}
```

**Why:** Customer.io rate limits at ~100 req/sec. Without throttling, bulk operations trigger 429 errors and potentially get your API key temporarily blocked.

### Pitfall 12: PII in Event Names

```typescript
// WRONG — PII in event names is unsanitizable
await cio.track(userId, { name: `email_sent_to_john@example.com` });

// CORRECT — PII only in data properties (can be deleted per GDPR)
await cio.track(userId, {
  name: "email_sent",
  data: { recipient: "john@example.com" },
});
```

**Why:** Event names are indexed and cached. PII in event names can't be deleted for GDPR compliance. Always put PII in event `data` properties.

## Quick Reference

| # | Pitfall | Fix |
|---|---------|-----|
| 1 | Wrong API key type | Track key for tracking, App key for transactional |
| 2 | Millisecond timestamps | `Math.floor(Date.now() / 1000)` |
| 3 | Track before identify | Always `identify()` first |
| 4 | Email as user ID | Use immutable database ID |
| 5 | Missing email attribute | Include `email` in `identify()` |
| 6 | Dynamic event names | Static names, dynamic data properties |
| 7 | Blocking request path | Fire-and-forget with `.catch()` |
| 8 | No bounce handling | Suppress bounced users via webhook |
| 9 | New client per request | Singleton pattern |
| 10 | Inconsistent event names | Always `snake_case` |
| 11 | No rate limiting | Use Bottleneck or p-queue |
| 12 | PII in event names | PII in `data` properties only |

## Integration Audit Script

```bash
# Quick grep audit for common pitfalls in your codebase
echo "=== Customer.io Pitfall Audit ==="

echo "--- Checking for Date.now() without /1000 ---"
grep -rn "created_at.*Date.now()" --include="*.ts" --include="*.js" \
  | grep -v "/ 1000" || echo "OK"

echo "--- Checking for new TrackClient inside functions ---"
grep -rn "new TrackClient" --include="*.ts" --include="*.js" \
  | grep -v "^.*const\|^.*let\|^.*export" || echo "OK"

echo "--- Checking for dynamic event names ---"
grep -rn "name:.*\`" --include="*.ts" --include="*.js" \
  | grep "track\|Track" || echo "OK"

echo "--- Checking for blocking await in routes ---"
grep -rn "await.*cio\.\|await.*track\.\|await.*identify" --include="*.ts" \
  | grep "router\.\|app\." || echo "Review these for fire-and-forget"
```

## Resources

- [Customer.io Best Practices](https://docs.customer.io/get-started/)
- [Track API Reference](https://docs.customer.io/integrations/api/track/)
- [customerio-node SDK](https://github.com/customerio/customerio-node)

## Next Steps

After reviewing pitfalls, use `customerio-reliability-patterns` for fault tolerance.
