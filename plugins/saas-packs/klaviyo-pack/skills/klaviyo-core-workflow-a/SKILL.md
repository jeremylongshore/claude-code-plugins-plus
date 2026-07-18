---
name: klaviyo-core-workflow-a
description: 'Execute Klaviyo primary workflow: profiles, lists, and subscriptions.

  Use when creating/updating profiles, managing lists, subscribing contacts,

  or syncing customer data to Klaviyo for email/SMS marketing.

  Trigger with phrases like "klaviyo profiles", "klaviyo lists",

  "klaviyo subscribe", "add contacts to klaviyo", "klaviyo customer data".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
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
# Klaviyo Core Workflow A -- Profiles, Lists & Subscriptions

## Overview

Primary money-path workflow: create/update profiles, manage lists, and subscribe contacts for email and SMS marketing via the `klaviyo-api` SDK. This skill covers the six-step path from a raw customer record to a consented, segmentable subscriber. High-level flow lives here; the full code for every step is in [references/implementation.md](references/implementation.md).

## Prerequisites

- Completed the `klaviyo-install-auth` setup so `KLAVIYO_PRIVATE_KEY` is available in the environment.
- A Klaviyo private API key scoped to `profiles:read`, `profiles:write`, `lists:read`, and `lists:write`.
- The `klaviyo-api` npm package installed in the project (`npm install klaviyo-api`).
- Node.js with TypeScript configured, since all examples use the typed SDK.

## Instructions

Every call authenticates through a single `ApiKeySession` built from the private key:

```typescript
import { ApiKeySession, ProfilesApi, ListsApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
const listsApi = new ListsApi(session);
```

The workflow runs in six steps. Use the linked walkthrough for the complete code of each:

1. **Create or update a profile** — prefer `createOrUpdateProfile` (upsert) over `createProfile` so re-syncs don't 409 on an existing email.
2. **Create a list** — `listsApi.createList(...)` returns the `listId` you use downstream; `getLists()` enumerates existing lists.
3. **Add profiles to a list** — `createListRelationships` adds membership only; it does NOT grant marketing consent.
4. **Subscribe profiles** — `subscribeProfiles` records email/SMS marketing consent with a `consentTimestamp`. This is the correct way to create real subscribers.
5. **Query profiles with filters** — `getProfiles({ filter, sort })` supports `equals`, `greater-than`, and `contains` for segmentation.
6. **Bulk import** — batch upserts in groups of 100 to stay within rate limits.

Full code for all six steps: [references/implementation.md](references/implementation.md).

## Output

- Profiles created/updated in Klaviyo
- Lists created and populated
- Subscribers opted in with consent timestamps
- Queryable customer data for segmentation

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| Duplicate profile | 409 | Email exists | Use `createOrUpdateProfile` (upsert) |
| Invalid phone | 400 | Wrong format | Use E.164 format: `+15551234567` |
| List not found | 404 | Wrong list ID | Verify list ID via `getLists()` |
| Missing consent | 400 | No consent timestamp | Always include `consentTimestamp` |
| Rate limited | 429 | >75 req/s burst | See `klaviyo-rate-limits` |

## Examples

Three end-to-end scenarios that string the six steps into complete flows are in [references/examples.md](references/examples.md):

- **Sync a new signup into a newsletter list with consent** — upsert the profile, ensure the list exists, then subscribe with email + SMS consent in one pass.
- **Segment pro-plan customers** — filter by a custom property and export the audience emails for a targeted campaign.
- **Bulk-import a customer CSV** — map records to upsert payloads and process in batches of 100.

Minimal upsert-then-subscribe skeleton:

```typescript
const upserted = await profilesApi.createOrUpdateProfile({
  data: { type: ProfileEnum.Profile, attributes: { email: 'customer@example.com' } },
});
await profilesApi.subscribeProfiles({
  data: {
    type: 'profile-subscription-bulk-create-job',
    attributes: { profiles: { data: [{ type: ProfileEnum.Profile, attributes: {
      email: 'customer@example.com',
      subscriptions: { email: { marketing: { consent: 'SUBSCRIBED', consentTimestamp: new Date().toISOString() } } },
    } }] } },
    relationships: { list: { data: { type: ListEnum.List, id: listId } } },
  },
});
```

## Resources

- [references/implementation.md](references/implementation.md) — full six-step code walkthrough
- [references/examples.md](references/examples.md) — end-to-end worked examples
- [Profiles API](https://developers.klaviyo.com/en/reference/profiles_api_overview)
- [Lists API](https://developers.klaviyo.com/en/reference/lists_api_overview)
- [Subscribe Profiles](https://developers.klaviyo.com/en/reference/bulk_subscribe_profiles)
- [Consent Collection Guide](https://developers.klaviyo.com/en/docs/collect_email_and_sms_consent_via_api)

## Next Steps

For event tracking and campaign triggers, see `klaviyo-core-workflow-b`. To harden against burst limits during bulk imports, see `klaviyo-rate-limits`.
