---
name: klaviyo-cost-tuning
description: 'Optimize Klaviyo costs through plan selection, contact management, and
  usage monitoring.

  Use when analyzing Klaviyo billing, reducing active profile costs,

  or implementing usage monitoring and budget alerts.

  Trigger with phrases like "klaviyo cost", "klaviyo billing",

  "reduce klaviyo costs", "klaviyo pricing", "klaviyo expensive", "klaviyo budget".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Cost Tuning

## Overview

Optimize Klaviyo costs through active profile management, list hygiene, event sampling, and API usage monitoring. Klaviyo bills primarily by **active profiles** and **message volume**, not API calls.

## Prerequisites

- Access to Klaviyo billing dashboard
- Understanding of active profile definition
- `klaviyo-api` SDK for programmatic management

## Klaviyo Pricing Model

Klaviyo bills based on **active profiles** (contacts who have received or been targeted by marketing), not API requests.

| Component | How It's Billed | Cost Driver |
|-----------|----------------|-------------|
| Email | Per active profile tier | Number of marketable profiles |
| SMS | Per message sent + carrier fees | Message volume |
| Push | Included with email plan | N/A |
| API calls | Free (rate limited, not billed) | N/A |
| Reviews | Per request volume | Review request sends |

### Email Pricing Tiers (Approximate)

| Active Profiles | Monthly Cost |
|----------------|-------------|
| 0 - 250 | Free |
| 251 - 500 | $20/mo |
| 501 - 1,000 | $30/mo |
| 1,001 - 1,500 | $45/mo |
| 1,501 - 5,000 | $60-$100/mo |
| 5,001 - 10,000 | $100-$150/mo |
| 10,001 - 25,000 | $150-$375/mo |
| 25,001+ | Custom pricing |

> **Key insight:** Reducing **active profiles** has the biggest cost impact. Cleaning suppressed/unengaged contacts directly reduces your bill.

## Instructions

Work the levers in order — active-profile reduction has the largest impact, so start
there before touching event sampling or API monitoring. Each step maps to a `klaviyo-api`
routine in the full walkthrough; the [complete five-step implementation](references/implementation.md)
carries the runnable code for every step, and [worked examples](references/examples.md) show
the dollar impact of each.

1. **Audit active profile count** — page through `ProfilesApi.getProfiles` with a minimal
   fieldset to establish the current tier. Skeleton below.
2. **Identify unengaged profiles** — query an "Unengaged 180+ Days" segment via `SegmentsApi`.
3. **Suppress unengaged contacts** — unsubscribe (stays but unmarketable = not billed) or
   add a global suppression property. This is what actually lowers the bill.
4. **Sample non-critical events** — keep revenue events at 100%, sample high-volume/low-value
   events (`Viewed Product`, `Page View`) to cut ingestion.
5. **Monitor API usage** — wrap SDK calls in a rate tracker to catch runaway processes before
   they trip the 700 req/min limit.

Establish a session once, then run the audit (Step 1):

```typescript
import { ApiKeySession, ProfilesApi, SegmentsApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);

// Count total profiles (paginate with page[cursor])
let totalProfiles = 0;
let cursor: string | undefined;
do {
  const response = await profilesApi.getProfiles({
    pageCursor: cursor,
    fieldsProfile: ['email'],  // Minimal fields for speed
  });
  totalProfiles += response.body.data.length;
  const nextLink = response.body.links?.next;
  cursor = nextLink ? new URL(nextLink).searchParams.get('page[cursor]') || undefined : undefined;
} while (cursor);

console.log(`Total profiles: ${totalProfiles}`);
```

Steps 2–5 (segment query, suppression job, event sampling, usage tracker) live in the
[full implementation walkthrough](references/implementation.md).

## Output

Applying this skill produces:

- **A current active-profile count** and the pricing tier it falls into (see the tables above).
- **A list of unengaged profiles** (180+ days no open/click) eligible for suppression.
- **A suppression run** — profiles unsubscribed or globally suppressed, lowering the billed
  active count (often enough to drop a tier).
- **An event-sampling config** that keeps revenue-critical events at 100% while sampling noise.
- **A `KlaviyoUsageTracker`** emitting `[Klaviyo] High API rate: N req/min` warnings before the
  700 req/min steady limit is reached.

## Examples

- **Drop a pricing tier:** suppressing 3,100 unengaged profiles takes an account from 12,400 to
  9,300 active profiles, moving it from the 10,001–25,000 tier down to 5,001–10,000.
- **Cut SMS spend:** gating the abandoned-cart flow on an engaged-only segment stops full-list
  texting and its per-message carrier charges.
- **Sample noisy events:** a 0.25/0.10 sample on `Viewed Product`/`Page View` cuts ingestion of
  those events ~75–90% with no loss to revenue attribution.

See [references/examples.md](references/examples.md) for the full before/after figures and code
for each scenario.

## Cost Reduction Checklist

- [ ] Suppress profiles unengaged >180 days
- [ ] Remove hard-bounced email addresses
- [ ] Audit and merge duplicate profiles
- [ ] Use double opt-in to reduce fake signups
- [ ] Sample high-volume, low-value events
- [ ] Batch API calls instead of individual requests
- [ ] Cache frequently-read data (segments, lists)
- [ ] Use sparse fieldsets to reduce transfer size
- [ ] Review SMS sending -- highest per-message cost
- [ ] Set up sunset flow (auto-suppress after N days unengaged)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bill increase | Unengaged profiles grew | Run suppression script |
| SMS costs spiking | Flow sending to full list | Add engaged-only segment filter |
| Duplicate profiles | Multiple identify calls | Merge duplicates, use `createOrUpdateProfile` |
| API rate limits hit | Bulk operations | Use queue with concurrency control |

## Resources

- [Full implementation walkthrough](references/implementation.md) — runnable code for all five steps
- [Worked examples](references/examples.md) — before/after cost scenarios
- [Klaviyo Pricing](https://www.klaviyo.com/pricing)
- [Data Privacy API](https://developers.klaviyo.com/en/reference/data_privacy_api_overview)
- For architecture patterns, see the `klaviyo-reference-architecture` skill in this pack.
