# Intercom Performance Tuning — Full Implementation

Complete, copy-pasteable implementations for each of the six optimization techniques
summarized in `SKILL.md`. All snippets assume the `intercom-client` SDK and a bearer
token in `process.env.INTERCOM_ACCESS_TOKEN`.

## Step 1: Response Caching

Cache frequently accessed contacts and conversations to avoid repeated API calls.

```typescript
import { LRUCache } from "lru-cache";
import { IntercomClient } from "intercom-client";
import { Intercom } from "intercom-client";

const contactCache = new LRUCache<string, Intercom.Contact>({
  max: 5000,
  ttl: 5 * 60 * 1000,  // 5 minutes
});

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

async function getContact(contactId: string): Promise<Intercom.Contact> {
  const cached = contactCache.get(contactId);
  if (cached) return cached;

  const contact = await client.contacts.find({ contactId });
  contactCache.set(contactId, contact);
  return contact;
}

// Invalidate on update
async function updateContact(
  contactId: string,
  data: Partial<Intercom.UpdateContactRequest>
): Promise<Intercom.Contact> {
  contactCache.delete(contactId);
  const updated = await client.contacts.update({ contactId, ...data });
  contactCache.set(contactId, updated);
  return updated;
}

// Webhook-driven cache invalidation
function handleContactWebhook(notification: any): void {
  const contactId = notification.data?.item?.id;
  if (contactId) {
    contactCache.delete(contactId);
  }
}
```

## Step 2: Efficient Search Queries

Minimize search latency by using selective queries and limiting fields.

```typescript
// BAD: Overly broad search, fetching too many results
const allUsers = await client.contacts.search({
  query: { field: "role", operator: "=", value: "user" },
  pagination: { per_page: 150 },  // Max is 150
});

// GOOD: Targeted search with specific filters
const recentPro = await client.contacts.search({
  query: {
    operator: "AND",
    value: [
      { field: "role", operator: "=", value: "user" },
      { field: "custom_attributes.plan", operator: "=", value: "pro" },
      { field: "last_seen_at", operator: ">", value: Math.floor(Date.now() / 1000) - 86400 },
    ],
  },
  pagination: { per_page: 25 },
  sort: { field: "last_seen_at", order: "descending" },
});
```

## Step 3: Optimized Pagination

```typescript
// Stream contacts with memory-efficient cursor pagination
async function* streamContacts(
  client: IntercomClient,
  perPage = 50
): AsyncGenerator<Intercom.Contact> {
  let startingAfter: string | undefined;

  do {
    const page = await client.contacts.list({ perPage, startingAfter });

    for (const contact of page.data) {
      yield contact;
    }

    startingAfter = page.pages?.next?.startingAfter ?? undefined;

    // Small delay to avoid rate limits on large datasets
    if (startingAfter) {
      await new Promise(r => setTimeout(r, 100));
    }
  } while (startingAfter);
}

// Process contacts in batches for efficiency
async function processContactsInBatches(
  client: IntercomClient,
  processor: (contacts: Intercom.Contact[]) => Promise<void>,
  batchSize = 100
): Promise<number> {
  let batch: Intercom.Contact[] = [];
  let total = 0;

  for await (const contact of streamContacts(client)) {
    batch.push(contact);
    if (batch.length >= batchSize) {
      await processor(batch);
      total += batch.length;
      batch = [];
    }
  }

  if (batch.length > 0) {
    await processor(batch);
    total += batch.length;
  }

  return total;
}
```

## Step 4: Connection Pooling

```typescript
import { Agent } from "https";

// Reuse TCP connections (HTTP keep-alive)
const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,       // Max concurrent connections
  maxFreeSockets: 5,     // Keep idle connections warm
  timeout: 30000,        // Connection timeout
});

// Apply to fetch calls if using raw API
const response = await fetch("https://api.intercom.io/contacts", {
  headers: { Authorization: `Bearer ${token}` },
  agent,
} as any);
```

## Step 5: Parallel Requests with Rate Awareness

```typescript
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 5,        // Max parallel requests
  interval: 1000,        // Per second
  intervalCap: 100,      // Max per interval
});

// Batch-lookup contacts by ID
async function getContactsBatch(
  client: IntercomClient,
  contactIds: string[]
): Promise<Map<string, Intercom.Contact>> {
  const results = new Map<string, Intercom.Contact>();

  await Promise.all(
    contactIds.map(id =>
      queue.add(async () => {
        // Check cache first
        const cached = contactCache.get(id);
        if (cached) {
          results.set(id, cached);
          return;
        }
        try {
          const contact = await client.contacts.find({ contactId: id });
          contactCache.set(id, contact);
          results.set(id, contact);
        } catch {
          // Skip not-found contacts
        }
      })
    )
  );

  return results;
}
```

## Step 6: Performance Monitoring

```typescript
async function measuredCall<T>(
  name: string,
  operation: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await operation();
    const duration = performance.now() - start;
    console.log(JSON.stringify({
      metric: "intercom.api.call",
      operation: name,
      duration_ms: Math.round(duration),
      status: "success",
    }));
    return result;
  } catch (error) {
    const duration = performance.now() - start;
    console.error(JSON.stringify({
      metric: "intercom.api.call",
      operation: name,
      duration_ms: Math.round(duration),
      status: "error",
      error: (error as Error).message,
    }));
    throw error;
  }
}

// Usage
const contact = await measuredCall("contacts.find", () =>
  client.contacts.find({ contactId: "abc123" })
);
```
