# GDPR/CCPA Compliance Patterns

Three data-subject workflows, each with mandatory audit logging: right of access
(export), right of deletion (archive or field clearing), and retention-based archival.
Every one emits a structured audit event — keep those events for your minimum retention
period, they are the evidence that the request was honored.

## Right of Access — export all data for a user

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

## Right of Deletion — archive pages or clear PII fields

Two strategies, chosen with the `strategy` parameter:

- `archive` — soft-delete the whole page (moved to trash, recoverable ~30 days). Use when
  the record itself is the user's data.
- `clear_pii` — keep the record for referential integrity but null out PII fields and
  overwrite notes. Use when other records depend on the row existing.

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

## Data retention — archive pages past the retention window

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

All three functions throttle bulk `pages.update` calls to Notion's ~3 requests/second
limit and continue through pagination until `has_more` is false.
