---
name: notion-data-handling
description: |
  Implement data handling, PII protection, and GDPR/CCPA compliance for Notion
  integrations. Use when handling sensitive data from Notion pages, implementing
  data redaction, exporting or deleting a user's data on request, or ensuring
  compliance with privacy regulations. Trigger with phrases like "notion data",
  "notion PII", "notion GDPR", "notion data retention", "notion privacy",
  "notion CCPA".
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Data Handling

## Overview

Handle sensitive data correctly when integrating with Notion: detect PII in page
properties and text content, redact sensitive fields before logging or exporting,
minimize data exposure with `filter_properties`, and implement GDPR/CCPA compliance
patterns — right-of-access exports, right-of-deletion (archive or field clearing), and
retention-based archival, all with audit logging.

The full, copy-ready TypeScript and Python implementations live in `references/` so this
file stays a navigable map. Read top-to-bottom for the workflow; drill into a reference
file when you need the complete code for a step.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Understanding of which Notion databases contain personal data
- Audit logging infrastructure (structured logs, SIEM, or Notion audit database)
- Legal guidance on applicable regulations (GDPR, CCPA, HIPAA, etc.)

## Authentication

All examples authenticate with an internal integration token read from the environment —
never hardcode it:

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

Create the token at [notion.so/my-integrations](https://www.notion.so/my-integrations) and
share each target database with the integration. Deletion and retention flows additionally
require the integration to hold **Update** capability, or `pages.update` returns 403.

## Instructions

Work through three stages. Each links to a reference file with the complete implementation.

### Step 1 — Detect PII

Notion pages carry PII in dedicated `email`/`phone_number`/`people` properties **and**
embedded in free-text `rich_text`/`title` values. Scan both: check known-sensitive
property types directly, and run regex matchers (email, phone, SSN, credit card, IP) over
text. Loop the whole database through pagination until `has_more` is false. Skeleton:

```typescript
function scanPageForPII(page: PageObjectResponse): PIIFinding[] {
  // check email / phone_number / people property types,
  // then run PII_PATTERNS regexes over rich_text + title text
}
```

Full TS + Python scanners: [pii-detection.md](references/pii-detection.md).

### Step 2 — Redact and minimize

Never log or export raw page objects. Pass every page through an allowlist-shaped redactor
that masks sensitive property types and named fields while letting vetted scalar types pass
through. Then cut exposure at the source with `filter_properties`, which returns only the
properties you name:

```typescript
notion.databases.query({ database_id: dbId, filter_properties: ['Status', 'Name'] });
```

Full `redactPageProperties` implementation and minimization guidance:
[redaction-minimization.md](references/redaction-minimization.md).

### Step 3 — Serve GDPR/CCPA requests

Three data-subject workflows, each emitting a structured audit event you retain as proof:

- **Right of access (Article 15)** — query every database for the user and export their
  pages, then audit-log the export.
- **Right of deletion (Article 17)** — choose `archive` (soft-delete the whole page,
  recoverable ~30 days) or `clear_pii` (null the PII fields, keep the record). Throttle
  bulk updates to ~3 req/s.
- **Retention** — archive pages whose `last_edited_time` is older than the retention window.

Full export, deletion, and retention functions: [compliance-patterns.md](references/compliance-patterns.md).

## Output

- PII detection scanning all property types and text content (TS + Python)
- Redaction layer preventing PII leakage in logs and exports
- Data minimization via `filter_properties` in API queries
- GDPR Article 15 data export with audit logging
- GDPR Article 17 deletion (archive or field clearing) with rate limiting
- Retention-based archival with structured compliance logging
- Audit trail for all data access, export, and deletion events

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| PII in application logs | Missing redaction layer | Use `redactPageProperties` for all logging |
| Deletion fails on pages (403) | Integration lacks Update capability | Edit integration at notion.so/my-integrations |
| Export missing pages | Pagination not handled | Use `start_cursor` loop until `has_more` is false |
| Rate limit during bulk deletion | Too many update calls | Throttle to 3 requests/second with delays |
| Regex false positives | Overly broad patterns | Tune patterns for your data; consider allowlists |
| Regex misses on second page | Stateful `g`-flag `lastIndex` | Reset `pattern.lastIndex = 0` before each `.test()` |
| Audit log gaps | Async logging dropped events | Use synchronous logging for compliance events |

## Examples

A quick database PII audit and a compact Python export, composing the building blocks
above:

```typescript
const findings = await auditDatabaseForPII(process.env.NOTION_DB_ID!);
console.log(`PII audit: ${findings.length} pages with PII detected`);
```

Both full examples (TS audit summary + Python Article 15 export):
[examples.md](references/examples.md).

## Resources

- [pii-detection.md](references/pii-detection.md) — full TS + Python PII scanners
- [redaction-minimization.md](references/redaction-minimization.md) — redactor + `filter_properties`
- [compliance-patterns.md](references/compliance-patterns.md) — export, deletion, retention
- [examples.md](references/examples.md) — end-to-end snippets
- [Notion Page Properties Reference](https://developers.notion.com/reference/page-property-values) — all property types
- [Database Query with filter_properties](https://developers.notion.com/reference/post-database-query) — data minimization
- [Notion API Update Page](https://developers.notion.com/reference/patch-page) — archive and property updates
- [CCPA Overview](https://oag.ca.gov/privacy/ccpa) — California Consumer Privacy Act requirements
- For enterprise access control and multi-workspace permissions, see `notion-enterprise-rbac`.
