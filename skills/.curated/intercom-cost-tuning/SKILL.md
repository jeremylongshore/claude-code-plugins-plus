---
name: intercom-cost-tuning
description: 'Optimize Intercom API costs through caching, request reduction, and
  usage monitoring.

  Use when analyzing Intercom API usage, reducing unnecessary requests,

  or implementing usage tracking and budget awareness.

  Trigger with phrases like "intercom cost", "intercom billing",

  "reduce intercom requests", "intercom pricing", "intercom usage", "intercom budget".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
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

## Prerequisites

- An Intercom workspace with an [access token](https://developers.intercom.com/docs/build-an-integration/getting-started/) and the Node/TypeScript Intercom client installed.
- `lru-cache` available for the contact-caching step (`npm install lru-cache`).
- A public HTTPS endpoint to receive webhooks (Step 2) if you want to eliminate polling.
- Read access to the integration source so you can audit call sites: use **Grep** to find polling loops (`setInterval`, `.list(`) and **Read** to inspect the surrounding call site before refactoring.

## Instructions

Work top-down — Steps 2-4 remove the most requests for the least code; Steps 1 and 6 confirm and protect the gains. Full copy-paste code for every step is in [references/implementation.md](references/implementation.md).

1. **Audit current API usage.** Instrument every call with an `IntercomUsageTracker` that counts calls and average latency per endpoint, then prints a rate estimate against the 10K req/min limit. You cannot cut what you have not measured.
2. **Replace polling with webhooks.** A 30-second poll loop costs ~2,880 requests/day per check; a webhook subscription costs zero and fires instantly:

   ```typescript
   app.post("/webhooks/intercom", (req, res) => {
     const n = req.body;
     if (n.topic === "conversation.user.created") handleNewConversation(n.data.item);
     res.status(200).json({ received: true });
   });
   ```

3. **Cache contact lookups.** Wrap `contacts.find` in an LRU cache (10-min TTL) and invalidate entries on `contact.updated` webhooks so repeat reads never hit the API.
4. **Use search instead of list + client filter.** One `contacts.search` / `conversations.search` returns up to 150 filtered results in a single request instead of paging every record and filtering in memory.
5. **Batch conversation lookups.** Replace per-id `find` loops with a single filtered `conversations.search`.
6. **Monitor request budget.** A `RequestBudgetMonitor` warns at 80% of the limit and hard-stops at 95% to prevent 429 cascades.

## Output

Applying this skill produces:

- A per-endpoint **usage report** (call counts, average latency, estimated req/min vs the 10K limit) from Step 1.
- A refactored integration where polling loops are replaced by webhook handlers, contact/conversation reads are cached or searched, and outbound calls pass through a budget guard.
- A measurable **request-volume reduction** — e.g. polling checks dropping from thousands of requests/day to zero, and list+filter queries collapsing from N pages to a single search request.
- Console warnings when request rate crosses 80% / 95% of the rate limit, replacing surprise 429 errors.

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

## Examples

Worked, number-by-number scenarios are in [references/examples.md](references/examples.md):

- **Kill a polling loop** — 3 checks × 2,880 req/day → 0 via webhooks.
- **Cache contact lookups** — 50 `find` calls per inbox render → cache misses only.
- **Search instead of list** — 4,000-contact `pro`-plan query from 80 requests → 1.
- **Budget guard under load** — a bulk job self-paces below 10K req/min instead of taking a wall of 429s.

## Resources

- [Intercom Pricing](https://www.intercom.com/pricing)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)

## Next Steps

For architecture patterns, see the `intercom-reference-architecture` skill in this pack, and drill into [references/implementation.md](references/implementation.md) for the full step-by-step code.
