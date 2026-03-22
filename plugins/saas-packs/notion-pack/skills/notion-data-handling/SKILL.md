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
Handle sensitive data correctly when integrating with Notion: PII detection in page content, data redaction for logging, and GDPR/CCPA compliance patterns.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- `@notionhq/client` installed
- Audit logging infrastructure

## Instructions

### Step 1: Identify Sensitive Data in Notion
Notion pages and databases can contain PII in any property type:

```typescript
import { Client } from '@notionhq/client';
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Scan page properties for PII
function scanPageForPII(page: PageObjectResponse): string[] {
  const findings: string[] = [];

  for (const [name, prop] of Object.entries(page.properties)) {
    // Email properties directly contain PII
    if (prop.type === 'email' && prop.email) {
      findings.push(`PII: email in property "${name}"`);
    }

    // Phone properties
    if (prop.type === 'phone_number' && prop.phone_number) {
      findings.push(`PII: phone in property "${name}"`);
    }

    // People properties contain user info
    if (prop.type === 'people' && prop.people.length > 0) {
      findings.push(`PII: user references in property "${name}"`);
    }

    // Rich text and title may contain embedded PII
    if (prop.type === 'rich_text' || prop.type === 'title') {
      const text = (prop.type === 'title' ? prop.title : prop.rich_text)
        .map(t => t.plain_text).join('');
      if (containsPII(text)) {
        findings.push(`PII: detected in text property "${name}"`);
      }
    }
  }

  return findings;
}

// Pattern-based PII detection
const PII_PATTERNS = [
  { type: 'email', pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', pattern: /\b\d{3}-\d{2}-\d{4}\b/g },
];

function containsPII(text: string): boolean {
  return PII_PATTERNS.some(p => p.pattern.test(text));
}
```

### Step 2: Redact PII from Logs and Exports
```typescript
// Redact sensitive property values before logging
function redactPageProperties(page: PageObjectResponse): Record<string, any> {
  const redacted: Record<string, any> = { id: page.id };

  for (const [name, prop] of Object.entries(page.properties)) {
    switch (prop.type) {
      case 'email':
        redacted[name] = prop.email ? '[REDACTED_EMAIL]' : null;
        break;
      case 'phone_number':
        redacted[name] = prop.phone_number ? '[REDACTED_PHONE]' : null;
        break;
      case 'people':
        redacted[name] = `[${prop.people.length} users]`;
        break;
      case 'title':
        redacted[name] = prop.title.map(t => t.plain_text).join('');
        break;
      case 'select':
        redacted[name] = prop.select?.name ?? null;
        break;
      case 'number':
        redacted[name] = prop.number;
        break;
      case 'checkbox':
        redacted[name] = prop.checkbox;
        break;
      default:
        redacted[name] = `[${prop.type}]`;
    }
  }

  return redacted;
}

// Safe logging
console.log('Processing page:', JSON.stringify(redactPageProperties(page)));
// Instead of: console.log('Page:', JSON.stringify(page)); // LEAKS PII
```

### Step 3: Data Minimization in API Calls
```typescript
// Only request properties you need via filter_properties
// (Available on pages.retrieve and databases.query)

async function getTaskStatuses(dbId: string) {
  const response = await notion.databases.query({
    database_id: dbId,
    // filter_properties limits which properties are returned
    filter_properties: ['Status', 'Name'],
    page_size: 100,
  });
  // Response only contains Status and Name — no email, phone, etc.
  return response;
}
```

### Step 4: GDPR Right of Access (Data Export)
```typescript
async function exportUserData(userId: string, databaseIds: string[]) {
  const export_: Record<string, any> = {
    exportedAt: new Date().toISOString(),
    source: 'Notion Integration',
    databases: {},
  };

  for (const dbId of databaseIds) {
    // Find all pages where the user is referenced
    const response = await notion.databases.query({
      database_id: dbId,
      filter: {
        property: 'Assignee',
        people: { contains: userId },
      },
    });

    export_.databases[dbId] = response.results
      .filter((p): p is PageObjectResponse => 'properties' in p)
      .map(page => ({
        id: page.id,
        created: page.created_time,
        lastEdited: page.last_edited_time,
        properties: page.properties,
      }));
  }

  return export_;
}
```

### Step 5: GDPR Right of Deletion
```typescript
async function deleteUserData(userId: string, databaseIds: string[]) {
  const deletionLog: { pageId: string; action: string }[] = [];

  for (const dbId of databaseIds) {
    const pages = await notion.databases.query({
      database_id: dbId,
      filter: {
        property: 'Assignee',
        people: { contains: userId },
      },
    });

    for (const page of pages.results) {
      // Option 1: Archive the page (soft delete — recoverable)
      await notion.pages.update({
        page_id: page.id,
        archived: true,
      });
      deletionLog.push({ pageId: page.id, action: 'archived' });

      // Option 2: Clear PII fields (if keeping the record)
      // await notion.pages.update({
      //   page_id: page.id,
      //   properties: {
      //     Email: { email: null },
      //     Phone: { phone_number: null },
      //     Assignee: { people: [] },
      //   },
      // });
    }
  }

  // Audit log the deletion (required for compliance)
  console.log(JSON.stringify({
    event: 'gdpr_deletion',
    userId,
    pagesAffected: deletionLog.length,
    timestamp: new Date().toISOString(),
    log: deletionLog,
  }));

  return deletionLog;
}
```

### Step 6: Data Retention Cleanup
```typescript
async function archiveOldPages(dbId: string, retentionDays: number) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - retentionDays);

  const oldPages = await notion.databases.query({
    database_id: dbId,
    filter: {
      timestamp: 'last_edited_time',
      last_edited_time: { before: cutoff.toISOString() },
    },
  });

  let archived = 0;
  for (const page of oldPages.results) {
    await notion.pages.update({ page_id: page.id, archived: true });
    archived++;
    // Respect rate limits
    if (archived % 3 === 0) await new Promise(r => setTimeout(r, 1000));
  }

  console.log(`Archived ${archived} pages older than ${retentionDays} days`);
}
```

## Output
- PII detection scanning page properties and content
- Redacted logging preventing PII leakage
- Data minimization via `filter_properties`
- GDPR export and deletion endpoints
- Retention-based archival

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in logs | Missing redaction | Use `redactPageProperties` wrapper |
| Deletion fails on some pages | Permission issue | Verify integration has Update capability |
| Export incomplete | Pagination needed | Use pagination for large datasets |
| Audit gap | Async logging failed | Use synchronous audit logging |

## Examples

### Quick PII Scan
```typescript
const pages = await notion.databases.query({ database_id: dbId });
for (const page of pages.results) {
  if ('properties' in page) {
    const pii = scanPageForPII(page as PageObjectResponse);
    if (pii.length > 0) {
      console.warn(`Page ${page.id}: ${pii.join(', ')}`);
    }
  }
}
```

## Resources
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [Notion API Page Properties](https://developers.notion.com/reference/page-property-values)
- [Query Databases with filter_properties](https://developers.notion.com/reference/post-database-query)

## Next Steps
For enterprise access control, see `notion-enterprise-rbac`.
