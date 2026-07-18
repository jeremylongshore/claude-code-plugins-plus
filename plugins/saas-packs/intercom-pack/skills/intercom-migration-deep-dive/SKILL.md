---
name: intercom-migration-deep-dive
description: |
  Use when migrating from Zendesk/Freshdesk/HelpScout to Intercom, bulk-importing
  contacts, or re-platforming to Intercom with the contacts, conversations, and
  articles APIs. Trigger with phrases like "migrate to intercom", "intercom
  migration", "import contacts to intercom", "switch to intercom", "zendesk to
  intercom", "intercom data import".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
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
# Intercom Migration Deep Dive

## Overview

Comprehensive guide for migrating to Intercom from other platforms (Zendesk,
Freshdesk, HelpScout) or bulk-importing data. Covers contact import, company
import, tags, Help Center articles, orchestration, and post-migration
validation. The full runnable TypeScript for every phase lives in
[references/implementation.md](references/implementation.md); this file carries
the workflow and the first-phase skeleton so you can follow it end to end, then
drill into the reference for depth.

## Prerequisites

- Intercom workspace with an access token exported as `INTERCOM_ACCESS_TOKEN`
- Source system data exported (CSV or API access)
- The `intercom-client` SDK installed (`npm install intercom-client`)
- Feature flag infrastructure for gradual cutover
- Rollback strategy tested

## Authentication

All scripts read the workspace access token from the environment — never
hard-code it. Create the token in the Intercom Developer Hub (Settings →
Developers → your app → Authentication), then:

```bash
export INTERCOM_ACCESS_TOKEN="your-workspace-access-token"
```

```typescript
import { IntercomClient, IntercomError } from "intercom-client";
const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
```

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Contact import | Low | Hours | Low |
| Zendesk/Freshdesk migration | Medium | 1-2 weeks | Medium |
| Full re-platform (with history) | High | 2-4 weeks | High |
| Help Center migration | Medium | Days | Low |

## Instructions

Run the phases in dependency order. Each phase is a standalone function in
[references/implementation.md](references/implementation.md); the orchestrator in
Step 5 chains them.

1. **Contacts** (Step 1) — idempotent: search by `external_id`/`email`, then
   update or create. Stamp `migrated_from` + `migration_date` custom attributes
   so rollback can find migrated records. Skeleton below.
2. **Companies** (Step 2) — import before attaching contacts; contacts reference
   companies.
3. **Tags** (Step 3) — create each tag, apply to its contacts, skip missing
   (404) contacts instead of aborting.
4. **Articles** (Step 4) — group into Help Center collections by category,
   creating each collection once.
5. **Orchestrate** (Step 5) — `executeMigration(plan)` runs companies → contacts
   → tags → articles with per-phase progress logging.
6. **Validate** (Step 6) — `validateMigration(expectedCounts)` compares live
   counts against source counts (95% threshold for contacts/articles).

Contact-import skeleton (full body in the reference):

```typescript
async function importContacts(contacts: SourceContact[]) {
  const stats = { created: 0, updated: 0, failed: 0, errors: [] as any[] };
  for (const contact of contacts) {
    const existing = await client.contacts.search({
      query: { operator: "OR", value: [
        { field: "external_id", operator: "=", value: contact.id },
        { field: "email", operator: "=", value: contact.email },
      ] },
    });
    if (existing.data.length > 0) {
      await client.contacts.update({ contactId: existing.data[0].id, /* ...attrs */ });
      stats.updated++;
    } else {
      await client.contacts.create({ role: "user", externalId: contact.id, /* ...attrs */ });
      stats.created++;
    }
  }
  return stats;
}
```

See [references/implementation.md](references/implementation.md) for the complete
error handling, rate limiting, company/tag/article functions, orchestrator, and
validation code.

## Output

- **Contact import** returns `{ created, updated, failed, errors[] }` — a
  reconciliation record where `errors[]` carries per-contact `{ contact_id,
  email, error }` for every failure.
- **Orchestrator** (`executeMigration`) prints a per-phase progress log and a
  final `Migration complete in N minutes` line plus the first 10 failed contacts.
- **Validation** (`validateMigration`) returns `{ passed, checks[] }` where each
  check is `{ name, expected, actual, passed }`, and prints a PASSED/FAILED
  summary with an `OK`/`FAIL` line per resource.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 409 Conflict | Duplicate external_id/email | Search before create |
| 429 Rate Limited | Too fast | Add delays between batches |
| 422 Validation | Bad email/data format | Validate data before import |
| Partial migration | Script crashed | Use idempotent operations, re-run |
| Missing conversations | API doesn't support bulk import | Contact Intercom support for import |

**Rollback:** keep the source system active during migration; only decommission
after validation plus a 2-week parallel run. To reverse, search by
`custom_attributes.migration_date` and delete migrated contacts in batches — see
the Rollback Procedure in
[references/implementation.md](references/implementation.md).

## Examples

- **Bulk contact import from Zendesk** — export contacts to `SourceContact[]`,
  run `importContacts()` (Step 1), then reconcile against the returned
  `errors[]`. Full function: [references/implementation.md](references/implementation.md).
- **Full re-platform with history** — build a `MigrationPlan` (contacts,
  companies, tags, articles) and run `executeMigration(plan)` (Step 5), then
  `validateMigration(expectedCounts)` (Step 6). Full orchestrator +
  validation: [references/implementation.md](references/implementation.md).
- **Help Center article migration** — map categories to collections and run
  `migrateArticles(articles, authorId)` (Step 4):
  [references/implementation.md](references/implementation.md).

## Resources

- [Full implementation walkthrough](references/implementation.md) — all six
  phases, rollback, and validation in runnable TypeScript
- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Companies API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/companies)
- [Articles API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/articles)
- [Import Contacts Guide](https://developers.intercom.com/docs/guides/tickets/import-contacts)
- [Tags API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/tags)
