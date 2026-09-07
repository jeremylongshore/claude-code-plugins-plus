# Intercom Performance Tuning — Worked Examples

End-to-end usage patterns that combine the techniques from `references/implementation.md`.

## Example 1: Cached single-contact lookup

Read-through cache: first call hits the API, subsequent calls within the TTL are served
from memory.

```typescript
async function getContact(contactId: string): Promise<Intercom.Contact> {
  const cached = contactCache.get(contactId);
  if (cached) return cached;

  const contact = await client.contacts.find({ contactId });
  contactCache.set(contactId, contact);
  return contact;
}
```

## Example 2: Narrow search instead of a broad scan

The BAD form pulls up to 150 unfiltered rows per page; the GOOD form pushes the
predicate into the query so the API returns only the 25 rows you actually need.

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

## Example 3: Stream and batch-process every contact

Cursor pagination keeps memory flat over an unbounded contact list, and the batch
processor flushes work in fixed-size chunks.

```typescript
const total = await processContactsInBatches(
  client,
  async (contacts) => {
    // e.g. enrich, export, or re-index each batch
    await exportToWarehouse(contacts);
  },
  100
);
console.log(`Processed ${total} contacts`);
```

## Example 4: Parallel batch lookup with rate awareness

Resolve many contact IDs concurrently while respecting the rate limit via `p-queue`,
checking the cache before each network call.

```typescript
const ids = ["abc123", "def456", "ghi789"];
const contacts = await getContactsBatch(client, ids);

for (const [id, contact] of contacts) {
  console.log(id, contact.email);
}
```

## Example 5: Wrap any call in latency instrumentation

`measuredCall` emits a structured JSON metric line per call so you can chart P50/P95
against the baselines in `SKILL.md`.

```typescript
const contact = await measuredCall("contacts.find", () =>
  client.contacts.find({ contactId: "abc123" })
);
// → {"metric":"intercom.api.call","operation":"contacts.find","duration_ms":84,"status":"success"}
```
