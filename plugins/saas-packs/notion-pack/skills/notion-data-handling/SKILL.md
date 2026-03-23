---
name: notion-data-handling
description: |
  Implement data handling, PII protection, and GDPR/CCPA compliance for Notion integrations.
  Use when handling sensitive data from Notion pages, implementing data redaction,
  or ensuring compliance with privacy regulations.
  Trigger with phrases like "notion data", "notion PII",
  "notion GDPR", "notion data retention", "notion privacy", "notion CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Data Handling

## Overview

Handle sensitive data correctly when integrating with Notion: detect PII in page properties and block content, redact sensitive fields before logging or exporting, minimize data exposure with `filter_properties`, and implement GDPR/CCPA compliance patterns including right-of-access exports, right-of-deletion (archive or field clearing), and retention-based archival with audit logging.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Understanding of which Notion databases contain personal data
- Audit logging infrastructure (structured logs, SIEM, or Notion audit database)
- Legal guidance on applicable regulations (GDPR, CCPA, HIPAA, etc.)

## Instructions

### Step 1: PII Detection in Notion Content

Notion pages can contain PII in any property type. Scan systematically:

```typescript
import { Client } from '@notionhq/client';
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// PII pattern matchers
const PII_PATTERNS = [
  { type: 'email',      pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone_us',   pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'phone_intl', pattern: /\+\d{1,3}[-.\s]?\d{4,14}/g },
  { type: 'ssn',        pattern: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g },
  { type: 'ip_address', pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g },
];

interface PIIFinding {
  propertyName: string;
  piiType: string;
  location: 'property' | 'content';
}

function scanPageForPII(page: PageObjectResponse): PIIFinding[] {
  const findings: PIIFinding[] = [];

  for (const [name, prop] of Object.entries(page.properties)) {
    // Direct PII property types
    if (prop.type === 'email' && prop.email) {
      findings.push({ propertyName: name, piiType: 'email', location: 'property' });
    }
    if (prop.type === 'phone_number' && prop.phone_number) {
      findings.push({ propertyName: name, piiType: 'phone', location: 'property' });
    }
    if (prop.type === 'people' && prop.people.length > 0) {
      findings.push({ propertyName: name, piiType: 'user_reference', location: 'property' });
    }

    // Text properties may contain embedded PII
    if (prop.type === 'rich_text' || prop.type === 'title') {
      const textParts = prop.type === 'title' ? prop.title : prop.rich_text;
      const text = textParts.map(t => t.plain_text).join('');

      for (const { type, pattern } of PII_PATTERNS) {
        // Reset regex lastIndex for each check
        pattern.lastIndex = 0;
        if (pattern.test(text)) {
          findings.push({ propertyName: name, piiType: type, location: 'property' });
        }
      }
    }
  }

  return findings;
}

// Scan an entire database for PII
async function auditDatabaseForPII(dbId: string) {
  const findings: { pageId: string; pageTitle: string; pii: PIIFinding[] }[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      page_size: 100,
      start_cursor: cursor,
    });

    for (const page of response.results) {
      if (!('properties' in page)) continue;
      const pii = scanPageForPII(page as PageObjectResponse);
      if (pii.length > 0) {
        const titleProp = Object.values(page.properties)
          .find(p => p.type === 'title');
        const title = titleProp?.type === 'title'
          ? titleProp.title.map(t => t.plain_text).join('')
          : 'Untitled';
        findings.push({ pageId: page.id, pageTitle: title, pii });
      }
    }

    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return findings;
}
```

**Python — PII scanner:**

```python
import re
from notion_client import Client

client = Client(auth=os.environ["NOTION_TOKEN"])

PII_PATTERNS = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("phone", re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

def scan_page_for_pii(page: dict) -> list[dict]:
    findings = []
    for name, prop in page["properties"].items():
        if prop["type"] == "email" and prop.get("email"):
            findings.append({"property": name, "type": "email"})
        if prop["type"] == "phone_number" and prop.get("phone_number"):
            findings.append({"property": name, "type": "phone"})
        if prop["type"] in ("rich_text", "title"):
            parts = prop.get("title" if prop["type"] == "title" else "rich_text", [])
            text = "".join(t["plain_text"] for t in parts)
            for pii_type, pattern in PII_PATTERNS:
                if pattern.search(text):
                    findings.append({"property": name, "type": pii_type})
    return findings
```

### Step 2: Redaction and Data Minimization

**Redact PII before logging or exporting:**

```typescript
function redactPageProperties(
  page: PageObjectResponse,
  sensitiveFields: string[] = ['Email', 'Phone', 'SSN']
): Record<string, unknown> {
  const redacted: Record<string, unknown> = { id: page.id };

  for (const [name, prop] of Object.entries(page.properties)) {
    // Always redact known sensitive property types
    if (prop.type === 'email') {
      redacted[name] = prop.email ? '[REDACTED_EMAIL]' : null;
      continue;
    }
    if (prop.type === 'phone_number') {
      redacted[name] = prop.phone_number ? '[REDACTED_PHONE]' : null;
      continue;
    }
    if (prop.type === 'people') {
      redacted[name] = `[${prop.people.length} users]`;
      continue;
    }

    // Redact explicitly marked sensitive fields
    if (sensitiveFields.includes(name)) {
      redacted[name] = '[REDACTED]';
      continue;
    }

    // Safe property types pass through
    switch (prop.type) {
      case 'title':
        redacted[name] = prop.title.map(t => t.plain_text).join('');
        break;
      case 'select':
        redacted[name] = prop.select?.name ?? null;
        break;
      case 'multi_select':
        redacted[name] = prop.multi_select.map(s => s.name);
        break;
      case 'number':
        redacted[name] = prop.number;
        break;
      case 'checkbox':
        redacted[name] = prop.checkbox;
        break;
      case 'date':
        redacted[name] = prop.date?.start ?? null;
        break;
      default:
        redacted[name] = `[${prop.type}]`;
    }
  }

  return redacted;
}

// Safe logging — never log raw page objects
console.log('Processing page:', JSON.stringify(redactPageProperties(page)));
// NEVER: console.log('Page:', JSON.stringify(page)); // LEAKS PII
```

**Data minimization — only request properties you need:**

```typescript
// filter_properties limits which properties are returned by the API
async function getTaskStatuses(dbId: string) {
  const response = await notion.databases.query({
    database_id: dbId,
    filter_properties: ['Status', 'Name', 'Due Date'],
    page_size: 100,
  });
  // Response only contains Status, Name, Due Date — no email, phone, etc.
  return response;
}
```

### Step 3: GDPR/CCPA Compliance Patterns

**Right of Access — export all data for a user:**

```typescript
async function exportUserData(userId: string, databaseIds: string[]) {
  const exportData: Record<string, unknown> = {
    exportedAt: new Date().toISOString(),
    requestType: 'GDPR Article 15 — Right of Access',
    source: 'Notion Integration',
    databases: {} as Record<string, unknown>,
  };

  for (const dbId of databaseIds) {
    const response = await notion.databases.query({
      database_id: dbId,
      filter: {
        property: 'Assignee',
        people: { contains: userId },
      },
    });

    (exportData.databases as Record<string, unknown>)[dbId] = response.results
      .filter((p): p is PageObjectResponse => 'properties' in p)
      .map(page => ({
        id: page.id,
        url: page.url,
        created: page.created_time,
        lastEdited: page.last_edited_time,
        properties: page.properties,
      }));
  }

  // Audit log the export
  console.log(JSON.stringify({
    event: 'gdpr_data_export',
    userId,
    databaseCount: databaseIds.length,
    timestamp: new Date().toISOString(),
  }));

  return exportData;
}
```

**Right of Deletion — archive pages or clear PII fields:**

```typescript
async function deleteUserData(
  userId: string,
  databaseIds: string[],
  strategy: 'archive' | 'clear_pii' = 'archive'
) {
  const deletionLog: { pageId: string; action: string; database: string }[] = [];

  for (const dbId of databaseIds) {
    const pages = await notion.databases.query({
      database_id: dbId,
      filter: {
        property: 'Assignee',
        people: { contains: userId },
      },
    });

    for (const page of pages.results) {
      if (strategy === 'archive') {
        // Soft delete — page moved to trash (recoverable for 30 days)
        await notion.pages.update({
          page_id: page.id,
          archived: true,
        });
        deletionLog.push({ pageId: page.id, action: 'archived', database: dbId });
      } else {
        // Clear PII fields but keep the record
        await notion.pages.update({
          page_id: page.id,
          properties: {
            Email: { email: null },
            Phone: { phone_number: null },
            Assignee: { people: [] },
            Notes: { rich_text: [{ text: { content: '[Data deleted per GDPR request]' } }] },
          },
        });
        deletionLog.push({ pageId: page.id, action: 'pii_cleared', database: dbId });
      }

      // Rate limit: 3 requests/second
      if (deletionLog.length % 3 === 0) {
        await new Promise(r => setTimeout(r, 1100));
      }
    }
  }

  // Audit log (REQUIRED for compliance — keep for minimum retention period)
  console.log(JSON.stringify({
    event: 'gdpr_data_deletion',
    userId,
    strategy,
    pagesAffected: deletionLog.length,
    timestamp: new Date().toISOString(),
    log: deletionLog,
  }));

  return deletionLog;
}
```

**Data retention — archive pages past retention window:**

```typescript
async function enforceRetention(dbId: string, retentionDays: number) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - retentionDays);

  let cursor: string | undefined;
  let archived = 0;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter: {
        timestamp: 'last_edited_time',
        last_edited_time: { before: cutoff.toISOString() },
      },
      page_size: 100,
      start_cursor: cursor,
    });

    for (const page of response.results) {
      await notion.pages.update({ page_id: page.id, archived: true });
      archived++;
      // Respect rate limits
      if (archived % 3 === 0) await new Promise(r => setTimeout(r, 1100));
    }

    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  console.log(JSON.stringify({
    event: 'retention_enforcement',
    database_id: dbId,
    retention_days: retentionDays,
    pages_archived: archived,
    cutoff_date: cutoff.toISOString(),
    timestamp: new Date().toISOString(),
  }));

  return { archived, cutoffDate: cutoff.toISOString() };
}
```

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
|-------|-------|----------|
| PII in application logs | Missing redaction layer | Use `redactPageProperties` for all logging |
| Deletion fails on pages | Integration lacks Update capability | Edit integration at notion.so/my-integrations |
| Export missing pages | Pagination not handled | Use `start_cursor` loop until `has_more` is false |
| Rate limit during bulk deletion | Too many update calls | Throttle to 3 requests/second with delays |
| Regex false positives | Overly broad patterns | Tune patterns for your data; consider allowlists |
| Audit log gaps | Async logging dropped events | Use synchronous logging for compliance events |

## Examples

### Quick PII Audit for a Database

```typescript
const findings = await auditDatabaseForPII(process.env.NOTION_DB_ID!);
console.log(`PII audit: ${findings.length} pages with PII detected`);
for (const f of findings) {
  console.log(`  Page "${f.pageTitle}": ${f.pii.map(p => p.piiType).join(', ')}`);
}
```

### Python Data Export

```python
def export_user_data(user_id: str, db_ids: list[str]) -> dict:
    export = {"exported_at": datetime.utcnow().isoformat(), "databases": {}}
    for db_id in db_ids:
        results = client.databases.query(
            database_id=db_id,
            filter={"property": "Assignee", "people": {"contains": user_id}},
        )
        export["databases"][db_id] = [
            {"id": p["id"], "properties": p["properties"]}
            for p in results["results"]
        ]
    return export
```

## Resources

- [GDPR Developer Guide](https://gdpr.eu/developers/) — key articles for data processors
- [Notion Page Properties Reference](https://developers.notion.com/reference/page-property-values) — all property types
- [Database Query with filter_properties](https://developers.notion.com/reference/post-database-query) — data minimization
- [CCPA Overview](https://oag.ca.gov/privacy/ccpa) — California Consumer Privacy Act requirements
- [Notion API Update Page](https://developers.notion.com/reference/patch-page) — archive and property updates

## Next Steps

For enterprise access control and multi-workspace permissions, see `notion-enterprise-rbac`.
