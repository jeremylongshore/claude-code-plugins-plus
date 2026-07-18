# Notion Advanced Troubleshooting — Examples

Copy-paste starting points for isolating a failing Notion API call and for
escalating an unresolved issue to Notion support.

## Minimal Reproduction Script

Strip the problem to its smallest form. This script walks auth → search →
resource retrieve → the failing call, so you learn exactly which layer breaks.

```typescript
// Strip to bare minimum to isolate the issue
async function minimalRepro() {
  const notion = new Client({
    auth: process.env.NOTION_TOKEN,
    logLevel: LogLevel.DEBUG,
  });

  // 1. Auth check
  const me = await notion.users.me({});
  console.log('Auth OK:', me.name);

  // 2. Search check (proves token works)
  const search = await notion.search({ page_size: 1 });
  console.log('Search OK:', search.results.length, 'results');

  // 3. Specific resource check
  const db = await notion.databases.retrieve({
    database_id: process.env.NOTION_DB_ID!,
  });
  console.log('DB OK:', Object.keys(db.properties).join(', '));

  // 4. The failing operation — insert exact failing call here
}

minimalRepro().catch(console.error);
```

## Support Escalation Template

When the problem is on Notion's side (intermittent 500s, unexpected
`validation_error`), open a ticket with the captured `x-request-id`. Notion
support can trace a request by ID far faster than by description.

```
Subject: [Request ID: abc123] validation_error on pages.create
Environment: Node.js 20, @notionhq/client 2.2.15, API 2022-06-28
Integration ID: [from notion.so/profile/integrations]
Request ID: [from x-request-id header or error body]
Timestamp: 2026-03-22T14:30:00Z

Steps: POST /v1/pages with body: { ... }
Expected: 200 with page object
Actual: 400 validation_error "..."
Frequency: Every time / Intermittent since [date]
```
