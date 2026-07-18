---
name: klaviyo-migration-deep-dive
description: 'Use when you are moving an email/CDP stack onto Klaviyo — off the
  deprecated v1/v2 APIs, off a competitor ESP (Mailchimp, SendGrid), or re-platforming
  gradually with the strangler fig pattern — and need field mapping, batch import,
  and post-migration validation.

  Trigger with phrases like "migrate to klaviyo", "klaviyo migration",

  "switch to klaviyo", "klaviyo replatform", "mailchimp to klaviyo",

  "legacy to klaviyo", "v1 to v2 klaviyo".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
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
# Klaviyo Migration Deep Dive

## Overview

Comprehensive guide for migrating to Klaviyo from legacy APIs (v1/v2), competing ESPs (Mailchimp, SendGrid, etc.), or re-platforming with the strangler fig pattern. Covers data migration, API mapping, batch import, and post-migration validation.

This SKILL.md is the high-level workflow. The full, copy-paste code for every step
lives in [references/implementation.md](references/implementation.md); worked
end-to-end scenarios live in [references/examples.md](references/examples.md).

## Prerequisites

- Target Klaviyo account configured
- `klaviyo-api` SDK installed (`npm install klaviyo-api`)
- Source system access for data export
- Feature flag infrastructure (for gradual rollout)
- **Auth:** a Klaviyo **private API key** (`pk_***`) exported as `KLAVIYO_PRIVATE_KEY` — used by the SDK's `ApiKeySession`. Legacy v1/v2 calls used a public token in the request body; the current REST API uses the private key in the session header. See [references/implementation.md](references/implementation.md#authentication).

## Migration Types

| Migration | Complexity | Duration | Risk |
|-----------|-----------|----------|------|
| Klaviyo v1/v2 to current API | Low-Medium | 1-2 weeks | Low |
| Mailchimp/SendGrid to Klaviyo | Medium | 2-4 weeks | Medium |
| Custom ESP to Klaviyo | High | 4-8 weeks | High |
| Full re-platform | High | 2-3 months | High |

## Instructions

Pick your migration type from the table above, then work the five steps. Each step
has full code in [references/implementation.md](references/implementation.md).

1. **Legacy v1/v2 to current API** — replace deprecated `track` / `identify` / `v2 subscribe` HTTP calls with the `klaviyo-api` SDK (`createOrUpdateProfile`, `createEvent`, `subscribeProfiles`). The session skeleton every step builds on:

   ```typescript
   import { ApiKeySession, ProfilesApi, EventsApi } from 'klaviyo-api';

   const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
   const profilesApi = new ProfilesApi(session);
   const eventsApi = new EventsApi(session);
   ```

2. **API field mapping** — rename v1/v2 fields to the current schema: drop the `$` prefix, camelCase everything (`$first_name` → `firstName`), and nest address fields under `location`. Full mapping table in [references/implementation.md](references/implementation.md#step-2-api-field-mapping-v1v2-to-current).
3. **Competitor migration** — write a transform adapter that maps the competitor's contact shape to a Klaviyo profile, then batch-import (50 per batch) with `Promise.allSettled`, progress logging, and rate-limit delays. Skip suppressed/unsubscribed contacts.
4. **Strangler fig pattern** — route traffic through a `MigrationRouter` behind a feature flag, ramping Klaviyo from 0% to 100% while optionally dual-writing for comparison.
5. **Post-migration validation** — run `validateMigration()` to compare profile counts, sample data integrity, and list membership against the source before decommissioning the legacy system.

Full migration checklist (export → map → import → validate → cut over → decommission) is in [references/implementation.md](references/implementation.md#migration-checklist).

## Output

Working through this skill produces:

- **Migrated code** — v1/v2 HTTP calls replaced with `klaviyo-api` SDK calls, or a competitor-to-Klaviyo transform adapter plus a batch-import runner.
- **An import result** — `{ imported, skipped, failed[] }` from `migrateContacts`, with the `failed` list ready for a targeted retry.
- **A `MigrationRouter`** (for gradual cutovers) that routes a configurable percentage of traffic to Klaviyo behind a feature flag.
- **A validation report** — `{ passed, checks[] }` from `validateMigration` covering profile count, data integrity, and list membership, used as the go/no-go gate before decommissioning the legacy system.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate profiles | Same email imported twice | Use `createOrUpdateProfile` (upsert) |
| Phone format errors | Non-E.164 format | Pre-validate and format to E.164 (`+<countrycode><subscriber>`) |
| Rate limited during import | Too fast | Reduce batch size, add delays |
| Missing consent timestamps | Historical data | Set `historicalImport: true` flag |
| Template rendering errors | Incompatible template syntax | Convert to Klaviyo Django template syntax |

## Examples

Worked, end-to-end scenarios are in [references/examples.md](references/examples.md):

- **Mailchimp export → Klaviyo import** — load a CSV, skip suppressed contacts, batch-import with progress output.
- **Cut over a v1 `identify` call** to `createOrUpdateProfile`, showing the field renames.
- **Feature-flagged cutover** — route 10% of events to Klaviyo while campaigns stay legacy.
- **Gate a deployment** on a `validateMigration` pass.

Minimal first cutover — one profile upsert on the current API:

```typescript
await profilesApi.createOrUpdateProfile({
  data: {
    type: 'profile',
    attributes: { email: 'user@example.com', firstName: 'Jane', properties: { plan: 'pro' } },
  },
});
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — verbatim code for all five steps + checklist
- [Worked examples](references/examples.md) — end-to-end migration scenarios
- [v1/v2 Migration Best Practices](https://developers.klaviyo.com/en/v2024-10-15/docs/best_practices_v1v2_migration)
- [Relationship Migration Guide](https://developers.klaviyo.com/en/v2024-10-15/docs/migrate_to_2023_07_15_relationships)
- [Custom Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
