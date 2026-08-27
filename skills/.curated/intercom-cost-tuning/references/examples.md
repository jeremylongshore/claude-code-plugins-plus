# Intercom Cost Tuning — Worked Examples

These examples tie the six-step workflow together on realistic scenarios. Every
number is derived from the request costs and rate limits documented in SKILL.md
(30s polling ≈ 2,880 req/day per check; API rate limit 10,000 req/min; search
returns up to 150 results per request). Full code for each pattern lives in
[references/implementation.md](implementation.md).

## Example 1: Kill a polling loop (Step 2)

A dashboard polls for new conversations every 30 seconds across three checks
(new conversations, updated tickets, assignment changes).

- **Before:** 3 checks × 2,880 req/day = **8,640 requests/day** of pure polling.
- **After:** subscribe to `conversation.user.created`, `conversation.admin.replied`,
  and `conversation.admin.assigned` webhooks → **0 polling requests/day**, and
  events arrive instantly instead of up to 30s late.

Route each webhook topic to a handler:

```typescript
app.post("/webhooks/intercom", (req, res) => {
  const notification = req.body;
  if (notification.topic === "conversation.user.created") {
    handleNewConversation(notification.data.item);
  }
  res.status(200).json({ received: true });
});
```

## Example 2: Cache repeated contact lookups (Step 3)

An inbox renders 50 conversations, each showing the requester's name. Ten
requesters account for most conversations.

- **Before:** 50 conversations → 50 `contacts.find` calls per render.
- **After:** an LRU cache (`max: 10000`, 10-min TTL) serves repeats from memory →
  ~10 cold requests on first render, **near-zero on subsequent renders** until a
  `contact.updated` webhook invalidates the entry.

## Example 3: Search instead of list + client filter (Step 4)

Find every `pro`-plan user when the workspace has 4,000 contacts.

- **Before:** `contacts.list({ perPage: 50 })` paged to completion = 80 requests,
  filtered client-side.
- **After:** one `contacts.search` with `custom_attributes.plan = "pro"` returns up
  to 150 matches in **1 request** — an 80× reduction on this query.

## Example 4: Budget guard under load (Step 6)

A bulk backfill job iterates thousands of records. Wrap each outbound call in the
`RequestBudgetMonitor.checkBudget()` guard: it warns at 8,000 req/min (80%) and
throttles at 9,500 (95%), so the job self-paces below the 10,000 req/min ceiling
instead of taking a wall of 429s and rebuilding progress from a retry queue.

## Putting it together

A typical support integration applies Steps 2–4 first (they remove the most
requests for the least code), then adds Step 1 instrumentation to confirm the drop
and Step 6 monitoring to keep it from creeping back. The combined effect on the
scenarios above: **~8,640 polling requests/day eliminated**, per-render contact
calls cut to cache misses only, and the pro-user query reduced from 80 requests to 1.
