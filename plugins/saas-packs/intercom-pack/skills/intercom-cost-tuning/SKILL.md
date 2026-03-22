---
name: intercom-cost-tuning
description: |
  Optimize Intercom API costs through caching, request reduction, and usage monitoring.
  Use when analyzing Intercom API usage, reducing unnecessary requests,
  or implementing usage tracking and budget awareness.
  Trigger with phrases like "intercom cost", "intercom billing",
  "reduce intercom requests", "intercom pricing", "intercom usage", "intercom budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Cost Tuning

## Overview

Reduce Intercom API costs through smart caching, search optimization, webhook-driven architecture, and usage monitoring. Intercom pricing is primarily seat-based and feature-based, but API efficiency reduces infrastructure costs and avoids rate limits.

## Intercom Pricing Model

| Component | Pricing Basis | Cost Driver |
|-----------|--------------|-------------|
| Seats | Per agent/month | Number of teammates |
| Fin AI Agent | Per resolution | AI-handled conversations |
| Proactive Support | Per message sent | Outbound messages volume |
| Help Center | Included | N/A |
| API | Included (rate-limited) | Request volume determines infra cost |

**Key insight:** The API itself is free to use, but hitting rate limits (10K req/min) forces you to build queuing infrastructure. Reducing requests saves engineering time and infrastructure costs.

## Instructions

### Step 1: Audit Current API Usage

```typescript
// Instrument all API calls to track usage patterns
class IntercomUsageTracker {
  private calls = new Map<string, { count: number; totalMs: number }>();

  track(endpoint: string, durationMs: number): void {
    const existing = this.calls.get(endpoint) || { count: 0, totalMs: 0 };
    existing.count++;
    existing.totalMs += durationMs;
    this.calls.set(endpoint, existing);
  }

  report(): void {
    console.log("\n=== Intercom API Usage Report ===");
    const sorted = [...this.calls.entries()].sort((a, b) => b[1].count - a[1].count);

    for (const [endpoint, stats] of sorted) {
      console.log(
        `${endpoint}: ${stats.count} calls, avg ${(stats.totalMs / stats.count).toFixed(0)}ms`
      );
    }

    const total = sorted.reduce((sum, [, s]) => sum + s.count, 0);
    console.log(`\nTotal: ${total} API calls`);
    console.log(`Estimated rate: ${(total / 60).toFixed(0)} req/min (limit: 10,000)`);
  }
}
```

### Step 2: Replace Polling with Webhooks

```typescript
// BAD: Polling for new conversations every 30 seconds
// Cost: ~2,880 requests/day for ONE check
setInterval(async () => {
  const conversations = await client.conversations.list();
  // Check for new conversations...
}, 30000);

// GOOD: Webhook-driven (0 requests, instant notification)
app.post("/webhooks/intercom", (req, res) => {
  const notification = req.body;
  if (notification.topic === "conversation.user.created") {
    handleNewConversation(notification.data.item);
  }
  res.status(200).json({ received: true });
});
```

### Step 3: Cache Contact Lookups

```typescript
import { LRUCache } from "lru-cache";

const contactCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 10 * 60 * 1000, // 10 min TTL
});

// Before: 1 API call per contact lookup
async function getContactName(contactId: string): Promise<string> {
  const contact = await client.contacts.find({ contactId });
  return contact.name;
}

// After: API call only on cache miss
async function getContactNameCached(contactId: string): Promise<string> {
  let name = contactCache.get(contactId) as string | undefined;
  if (!name) {
    const contact = await client.contacts.find({ contactId });
    name = contact.name;
    contactCache.set(contactId, name);
  }
  return name;
}

// Invalidate cache via webhooks
function onContactUpdated(contactId: string): void {
  contactCache.delete(contactId);
}
```

### Step 4: Use Search Instead of List + Filter

```typescript
// BAD: Fetch all contacts, filter client-side
// Cost: N pages * 1 request each
let startingAfter: string | undefined;
const matchingContacts = [];
do {
  const page = await client.contacts.list({ perPage: 50, startingAfter });
  matchingContacts.push(...page.data.filter(c => c.customAttributes?.plan === "pro"));
  startingAfter = page.pages?.next?.startingAfter;
} while (startingAfter);

// GOOD: Server-side search (1 request for up to 150 results)
const proUsers = await client.contacts.search({
  query: {
    operator: "AND",
    value: [
      { field: "role", operator: "=", value: "user" },
      { field: "custom_attributes.plan", operator: "=", value: "pro" },
    ],
  },
  pagination: { per_page: 150 },
});
```

### Step 5: Batch Conversation Lookups

```typescript
// BAD: N individual conversation lookups
for (const id of conversationIds) {
  const convo = await client.conversations.find({ conversationId: id });
  process(convo);
}

// GOOD: Search conversations with filter
const conversations = await client.conversations.search({
  query: {
    operator: "AND",
    value: [
      { field: "state", operator: "=", value: "open" },
      { field: "admin_assignee_id", operator: "=", value: adminId },
    ],
  },
  pagination: { per_page: 50 },
});
```

### Step 6: Monitor Request Budget

```typescript
class RequestBudgetMonitor {
  private requestsThisMinute = 0;
  private resetTime = Date.now() + 60000;

  async checkBudget(): Promise<void> {
    if (Date.now() > this.resetTime) {
      this.requestsThisMinute = 0;
      this.resetTime = Date.now() + 60000;
    }

    this.requestsThisMinute++;

    // Warn at 80% of limit
    if (this.requestsThisMinute > 8000) {
      console.warn(
        `[Intercom] High request rate: ${this.requestsThisMinute}/10000 per minute`
      );
    }

    // Hard stop at 95% to prevent 429s
    if (this.requestsThisMinute > 9500) {
      const waitMs = this.resetTime - Date.now();
      console.warn(`[Intercom] Throttling: waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
    }
  }
}
```

## Cost Reduction Checklist

- [ ] Replace polling loops with webhooks
- [ ] Cache contact and conversation lookups (5-10 min TTL)
- [ ] Use search instead of list + client-side filter
- [ ] Batch related lookups into single search queries
- [ ] Track API request volume per endpoint
- [ ] Set up alerts at 80% rate limit usage
- [ ] Remove unnecessary API calls in hot paths

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Implement request queuing |
| Stale cached data | TTL too long | Use webhook cache invalidation |
| High infra costs | Queue + retry infrastructure | Reduce request volume first |
| Search too slow | Complex query | Simplify filters, reduce per_page |

## Resources

- [Intercom Pricing](https://www.intercom.com/pricing)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)

## Next Steps

For architecture patterns, see `intercom-reference-architecture`.
