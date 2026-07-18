---
name: intercom-data-handling
description: 'Implement Intercom data handling for GDPR, contact export, data retention,
  and PII.

  Use when handling sensitive Intercom contact data, fulfilling a data subject
  access or deletion request, redacting PII in logs, or setting retention policy
  for cached Intercom records.

  Trigger with phrases like "intercom data", "intercom PII",

  "intercom GDPR", "intercom data retention", "intercom privacy", "intercom CCPA",

  "intercom data export", "intercom delete contact".

  '
allowed-tools: Read, Write, Edit
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
# Intercom Data Handling

## Overview

Handle sensitive contact data in Intercom integrations with GDPR/CCPA compliance:
data export via the Data Export API, contact deletion with an audit trail, PII
redaction in logs, and data retention policies. This skill gives you a lean map of
the five workflows here; the full copy-ready TypeScript lives in
[references/implementation.md](references/implementation.md) and worked usage in
[references/examples.md](references/examples.md).

## Prerequisites

- Understanding of GDPR/CCPA requirements
- `intercom-client` SDK installed
- Database for audit logging
- Familiarity with Intercom's contact and conversation data model

## Authentication

Every call authenticates with an Intercom access token via a Bearer header. Store
it as `INTERCOM_ACCESS_TOKEN` in the environment — never hardcode it and never log
it:

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
// Raw REST calls use: Authorization: `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}`
```

Grant the token the minimum scopes needed (read contacts/conversations for export,
write/delete for erasure). Rotate it if it ever appears in a log or a diff.

## Data Classification for Intercom

| Category | Intercom Fields | Handling |
|----------|----------------|----------|
| PII | `email`, `name`, `phone`, `location` | Encrypt at rest, redact in logs |
| Identifiers | `id`, `external_id`, `user_id` | Use for lookups, no display |
| Conversation content | `body`, `conversation_parts` | May contain PII, scan before logging |
| Custom attributes | User-defined | Depends on content |
| System metadata | `created_at`, `updated_at`, `role` | Standard handling |

## Instructions

The five workflows below compose into a compliant Intercom data lifecycle. Follow
the summary here, then open [references/implementation.md](references/implementation.md)
for the complete function bodies.

1. **DSAR export** — `exportContactData(contactId)` gathers the contact profile,
   all conversations (with parts), tags, segments, and data events into one bundle.
   This is the "give me all my data" request.
2. **Right to deletion (Article 17)** — `deleteContactData(contactId)` exports for
   the audit trail *first*, then deletes from Intercom and every local cache, and
   records a PII-free audit entry (email is hashed, not stored).
3. **Bulk data export** — `bulkExportMessages(start, end)` kicks off the async
   `/export/messages/data` job; `checkExportStatus(jobId)` polls until a CSV
   `download_url` is returned.
4. **PII redaction in logs** — `redactIntercomData(data)` masks a fixed
   `PII_FIELDS` set (including nested `custom_attributes.*`) before anything is
   logged.
5. **Retention enforcement** — `enforceRetention()` sweeps cached records past
   their `RETENTION` window on a daily cron, and never touches the 7-year audit log.

Data minimization underpins all five: sync only the fields you need so the erasure
and breach surface stays small (see [references/examples.md](references/examples.md)).

Here is the entry-point skeleton — the export that DSAR and deletion both build on:

```typescript
const contact = await client.contacts.find({ contactId });
const convList = await client.conversations.search({
  query: { field: "contact_ids", operator: "=", value: contactId },
});
// ...gather tags, segments, events → return one bundle
```

## Output

Each workflow returns a structured, PII-aware result:

- **DSAR export** → an object with `contact`, `conversations[]`, `tags[]`,
  `segments[]`, and `events[]` — the full data bundle to hand to the requester.
- **Deletion** → `{ deleted: true, auditRecord }` where `auditRecord` holds the
  action, hashed email, timestamp, purged data sources, and conversation count —
  proof of erasure that contains no raw PII.
- **Bulk export** → a `job_identifier`, then a `{ status, downloadUrl }` once the
  CSV is ready.
- **Redaction** → the same object shape with PII fields replaced by `[REDACTED]`.
- **Retention** → `{ deleted: { [cacheType]: count } }` per swept cache type.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Export job stuck in "pending" | Large dataset | Poll every 30s, timeout at 1h |
| Deletion returns 404 | Already deleted | Log and continue (idempotent) |
| PII in conversation bodies | User-submitted content | Scan with regex, redact in logs |
| Audit log gap | Failed write | Use write-ahead log or queue |

## Examples

Full worked examples — fulfilling a DSAR, honoring a deletion request, polling a
bulk export to completion, and redacting before logging — are in
[references/examples.md](references/examples.md). The shortest one:

```typescript
// A user asks for all their data — export the whole bundle to JSON.
const bundle = await exportContactData("5f3c9b2e8a1d4e0012ab34cd");
await fs.writeFile(`dsar/${bundle.contact.id}.json`, JSON.stringify(bundle, null, 2));
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — all five workflows, copy-ready
- [Worked examples](references/examples.md) — end-to-end usage + data minimization
- [Data Export API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/data-export/data_export)
- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Intercom Privacy](https://www.intercom.com/privacy)

## Next Steps

For enterprise access control and permission scoping on top of these data
workflows, see the `intercom-enterprise-rbac` skill in this pack.
