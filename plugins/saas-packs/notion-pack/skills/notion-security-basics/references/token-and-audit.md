# Token Storage, Secret Scanning, and Access Auditing

Full walkthrough for Step 1 (secure token storage) and Step 2 (least-privilege
capabilities + access auditing). All examples use `@notionhq/client` v2.x and
target the `2022-06-28` API version.

## Step 1: Secure Token Storage and `.env` Management

Integration tokens are secrets with the same sensitivity as database passwords.
Notion tokens use the `ntn_` prefix (current) or `secret_` prefix (legacy). Both
grant full access to every page shared with the integration.

```bash
# .gitignore — add these patterns BEFORE creating .env
.env
.env.local
.env.*.local
.env.production
.env.staging

# .env.example — commit this template (no real values)
NOTION_TOKEN=ntn_your_internal_integration_token_here
NOTION_OAUTH_CLIENT_ID=
NOTION_OAUTH_CLIENT_SECRET=
NOTION_OAUTH_REDIRECT_URI=http://localhost:3000/auth/notion/callback
```

```typescript
import { Client } from '@notionhq/client';

// Always load tokens from environment — never hardcode
const token = process.env.NOTION_TOKEN;

if (!token) {
  throw new Error(
    'NOTION_TOKEN is required. ' +
    'Create an integration at https://www.notion.so/my-integrations ' +
    'and set the token in your .env file.'
  );
}

// Validate token format before using it
if (!token.startsWith('ntn_') && !token.startsWith('secret_')) {
  throw new Error(
    'NOTION_TOKEN has an unexpected format. ' +
    'Internal integration tokens start with ntn_ (or legacy secret_).'
  );
}

const notion = new Client({ auth: token });
```

**Git secret scanning** to catch accidental commits:

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for Notion tokens
        run: |
          # Scan for internal integration tokens
          if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --include="*.yaml" --include="*.yml" --include="*.env" .; then
            echo "::error::Notion token found in source code! Rotate immediately."
            exit 1
          fi
```

## Step 2: Least-Privilege Capabilities and Access Auditing

Configure integration capabilities at the [integration dashboard](https://www.notion.so/my-integrations).
Each integration should request only the capabilities it actually uses.

| Capability | Grant when... | Do NOT grant for... |
| ------------ | --------------- | --------------------- |
| Read content | Reading pages, databases, blocks | Write-only bots (form submissions) |
| Update content | Modifying existing page properties/blocks | Read-only dashboards |
| Insert content | Creating new pages, appending blocks | Analytics/reporting tools |
| Read comments | Listing and reading page comments | Data sync pipelines |
| Create comments | Adding comments to discussions | Read-only integrations |
| Read user info (with email) | User lookup by email address | Most integrations |
| Read user info (without email) | Resolving user references in properties | None (safe default) |

**Separate integrations by responsibility:**

```typescript
// Create distinct integrations with different capabilities:
// "acme-reader" — Read content only
// "acme-writer" — Read + Update + Insert content

const readerNotion = new Client({ auth: process.env.NOTION_READ_TOKEN });
const writerNotion = new Client({ auth: process.env.NOTION_WRITE_TOKEN });

// Dashboards and reporting use the reader
const results = await readerNotion.databases.query({
  database_id: process.env.NOTION_DATABASE_ID!,
  filter: {
    property: 'Status',
    select: { equals: 'Published' },
  },
});

// Mutations use the writer only when needed
await writerNotion.pages.update({
  page_id: pageId,
  properties: {
    'Last Synced': {
      date: { start: new Date().toISOString() },
    },
  },
});
```

**Audit which pages are shared with an integration:**

```typescript
async function auditIntegrationAccess(notion: Client): Promise<void> {
  // Search with empty query returns all pages the integration can access
  let hasMore = true;
  let startCursor: string | undefined;
  const accessiblePages: Array<{ id: string; title: string; type: string }> = [];

  while (hasMore) {
    const response = await notion.search({
      start_cursor: startCursor,
      page_size: 100,
    });

    for (const result of response.results) {
      if (result.object === 'page') {
        const titleProp = Object.values((result as any).properties || {})
          .find((p: any) => p.type === 'title') as any;
        const title = titleProp?.title?.[0]?.plain_text || '(untitled)';
        accessiblePages.push({ id: result.id, title, type: 'page' });
      } else if (result.object === 'database') {
        const title = (result as any).title?.[0]?.plain_text || '(untitled)';
        accessiblePages.push({ id: result.id, title, type: 'database' });
      }
    }

    hasMore = response.has_more;
    startCursor = response.next_cursor ?? undefined;
  }

  console.log(`Integration has access to ${accessiblePages.length} objects:`);
  for (const page of accessiblePages) {
    console.log(`  [${page.type}] ${page.title} (${page.id})`);
  }
}
```

**Page sharing hierarchy rules:**

- Sharing a parent page grants access to all child pages and databases
- Sharing a child page alone does NOT grant access to its parent
- Removing integration access from a parent cascades to all children
- The API returns `object_not_found` for both non-existent pages and unshared pages — this is intentional to prevent information leakage
