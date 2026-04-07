---
name: glean-data-handling
description: |
  PII filtering: strip emails, phone numbers, SSNs from document body before indexing.
  Trigger: "glean data handling", "data-handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Data Handling

## Overview

Glean enterprise search ingests documents from dozens of connectors (Google Drive, Confluence, Slack, Jira, Salesforce, etc.) and builds a unified search index with permission-aware access control. Data types include indexed document content, connector metadata, user permission maps, query logs, and search analytics. All document content must be PII-filtered before indexing, permission boundaries must be preserved to prevent data leakage across teams, and retention policies must be enforced to comply with corporate governance and GDPR/CCPA obligations.

## Data Classification

| Data Type | Sensitivity | Retention | Encryption |
|-----------|-------------|-----------|------------|
| Indexed document content | High (may contain PII) | Per source retention policy | AES-256 at rest |
| User permission maps | High (access control) | Sync lifecycle | TLS + at rest |
| Connector metadata | Medium | Until connector removed | AES-256 at rest |
| Search query logs | Medium (reveals intent) | 90 days default | AES-256 at rest |
| Search analytics/aggregates | Low | 1 year | TLS in transit |

## Data Import

```typescript
interface GleanDocument {
  id: string; datasource: string; title: string;
  body: string; permissions: { allowedUsers?: string[]; allowAnonymousAccess?: boolean };
  updatedAt: string; url: string;
}

async function indexDocuments(docs: GleanDocument[], datasource: string) {
  // PII strip before indexing
  const sanitized = docs.map(doc => ({
    ...doc,
    body: stripPII(doc.body),
  }));
  // Batch upload with pagination (max 100 per request)
  for (let i = 0; i < sanitized.length; i += 100) {
    const batch = sanitized.slice(i, i + 100);
    await fetch(`https://customer-be.glean.com/api/index/v1/bulkindexdocuments`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.GLEAN_INDEXING_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ datasource, documents: batch }),
    });
  }
}

function stripPII(text: string): string {
  return text
    .replace(/\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, '[EMAIL_REDACTED]')
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE_REDACTED]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]');
}
```

## Data Export

```typescript
async function exportSearchAnalytics(startDate: string, endDate: string) {
  const res = await fetch(`https://customer-be.glean.com/api/v1/analytics`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.GLEAN_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ startDate, endDate, metrics: ['query_count', 'click_through', 'zero_results'] }),
  });
  const data = await res.json();
  // Redact user identifiers from analytics export
  return data.results.map((r: any) => ({ ...r, userId: undefined, query: r.query?.length > 3 ? r.query : '[SHORT_QUERY_REDACTED]' }));
}
```

## Data Validation

```typescript
function validateDocument(doc: GleanDocument): string[] {
  const errors: string[] = [];
  if (!doc.id || doc.id.length > 512) errors.push('Invalid document ID');
  if (!doc.datasource) errors.push('Missing datasource identifier');
  if (!doc.title || doc.title.length > 1000) errors.push('Title missing or exceeds 1000 chars');
  if (!doc.body || doc.body.length === 0) errors.push('Empty document body');
  if (!doc.permissions) errors.push('Missing permissions — defaults to deny-all');
  if (doc.updatedAt && isNaN(Date.parse(doc.updatedAt))) errors.push('Invalid updatedAt timestamp');
  return errors;
}
```

## Compliance

- [ ] PII stripped from document body before indexing (emails, phones, SSNs)
- [ ] Permission boundaries enforced: allowedUsers scope matches source system ACLs
- [ ] Connector credentials stored in secret manager, rotated quarterly
- [ ] Search query logs retained max 90 days, purged via automated job
- [ ] GDPR right-to-erasure: delete all indexed content referencing a specific user on request
- [ ] CCPA: honor do-not-sell signals for search analytics data
- [ ] SOC 2 Type II audit trail for all indexing and deletion operations

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 403 on bulk index | Expired or insufficient indexing token | Rotate token, verify datasource permissions |
| Permission mismatch in search | Stale ACL sync from connector | Force re-sync connector permissions via admin API |
| PII detected in indexed content | New PII pattern not in strip regex | Add pattern to `stripPII`, re-index affected datasource |
| Zero-result queries spike | Connector sync failure, stale index | Check connector health dashboard, trigger manual re-crawl |
| Rate limit 429 on indexing | Batch size too large or too frequent | Reduce batch to 50 docs, add 500ms delay between batches |

## Resources

- [Glean Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Glean Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-security-basics`.
