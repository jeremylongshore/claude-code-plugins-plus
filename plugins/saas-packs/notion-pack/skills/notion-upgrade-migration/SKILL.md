---
name: notion-upgrade-migration
description: |
  Upgrade @notionhq/client SDK versions and migrate between Notion API versions.
  Use when updating SDK packages, handling breaking changes between API versions,
  adopting new SDK features like comments API or status properties, or migrating Python notion-client.
  Trigger with phrases like "upgrade notion SDK", "notion migration", "notion breaking changes",
  "update notionhq client", "notion API version upgrade", "notion deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Upgrade & Migration

## Overview

Step-by-step guide for upgrading `@notionhq/client` (Node.js) and `notion-client` (Python) SDK versions, migrating between Notion API versions, handling breaking changes, and adopting newly released features. Covers the current stable API version `2022-06-28` and the SDK feature timeline through v2.x.

## Prerequisites

- Existing project with `@notionhq/client` or `notion-client` installed
- Git repository with clean working tree (no uncommitted changes)
- Test suite covering Notion API calls (or willingness to add verification tests)
- `NOTION_TOKEN` environment variable configured

## Instructions

### Step 1: Audit Current Versions and API Surface

Determine what you are running today before changing anything.

```bash
# Node.js — check installed SDK version
npm ls @notionhq/client

# Node.js — check latest available
npm view @notionhq/client version

# Python — check installed SDK version
pip show notion-client 2>/dev/null | grep Version

# Python — check latest available
pip index versions notion-client 2>/dev/null | head -1

# Find which API version your code specifies
grep -rn "notionVersion\|Notion-Version\|notion_version" src/ lib/ app/ 2>/dev/null
```

Record the current SDK version and API version before proceeding. If no `notionVersion` is set explicitly, the SDK uses its built-in default (typically `2022-06-28` for current releases).

**SDK version history — key milestones:**

| SDK Version | Notable Additions |
|-------------|-------------------|
| `2.2.0` | Comments API support (`notion.comments.create`, `notion.comments.list`) |
| `2.2.3` | Status property type in database schemas |
| `2.2.4` | Unique ID property, verification property |
| `2.2.13` | Improved TypeScript discriminated unions for block types |
| `2.2.15` | Current stable — bug fixes, dependency updates |

**API version timeline:**

| API Version | Key Changes |
|-------------|-------------|
| `2022-02-22` | Rich text standardization, consistent pagination |
| `2022-06-28` | **Current stable** — most tutorials and production apps use this |

### Step 2: Perform the Upgrade

Create an isolated branch, upgrade the package, and address breaking changes before merging.

**Node.js upgrade:**
```bash
# Create upgrade branch
git checkout -b upgrade/notionhq-client-$(npm view @notionhq/client version)

# Upgrade to latest
npm install @notionhq/client@latest

# Review what changed
npm ls @notionhq/client
git diff package.json package-lock.json
```

**Python upgrade:**
```bash
git checkout -b upgrade/notion-client-$(pip show notion-client 2>/dev/null | grep Version | awk '{print $2}')

pip install --upgrade notion-client

# Verify
pip show notion-client | grep Version
```

**Breaking changes to check after any major version bump:**

```typescript
// 1. Import paths — endpoint types moved in some releases
// OLD (pre-2.2.x):
import type { QueryDatabaseResponse } from '@notionhq/client/build/src/api-endpoints';
// CURRENT (2.2.x):
import type {
  PageObjectResponse,
  DatabaseObjectResponse,
  BlockObjectResponse,
  QueryDatabaseResponse,
} from '@notionhq/client/build/src/api-endpoints';

// 2. Error handling imports are stable across all 2.x versions
import { Client, isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

// 3. New property types — code must handle unknown types gracefully
function extractProperty(prop: any): string {
  switch (prop.type) {
    case 'title': return prop.title.map((t: any) => t.plain_text).join('');
    case 'rich_text': return prop.rich_text.map((t: any) => t.plain_text).join('');
    case 'status': return prop.status?.name ?? '';       // Added in 2.2.3
    case 'unique_id': return String(prop.unique_id?.number ?? ''); // Added in 2.2.4
    default: return `[unhandled: ${prop.type}]`;
  }
}

// 4. Pin API version explicitly for reproducible behavior
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28',  // Always pin — do not rely on SDK default
});
```

**Python breaking changes:**
```python
from notion_client import Client, APIResponseError

# Pin API version explicitly
notion = Client(
    auth=os.environ["NOTION_TOKEN"],
    notion_version="2022-06-28",  # Explicit pin
)

# New in recent versions: comments API
comments = notion.comments.list(block_id=page_id)

# Status property (requires SDK that supports it)
# Returns: {"type": "status", "status": {"name": "In Progress", "color": "blue"}}
```

### Step 3: Verify and Test the Upgrade

Run targeted verification tests to confirm nothing broke. Test each API surface your application uses.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28',
});

// Test 1: Authentication and user listing
async function verifyAuth(): Promise<void> {
  const { results } = await notion.users.list({});
  console.log(`Auth OK — ${results.length} users found`);
}

// Test 2: Database query (most common operation)
async function verifyDatabaseQuery(databaseId: string): Promise<void> {
  const response = await notion.databases.query({
    database_id: databaseId,
    page_size: 5,
  });
  console.log(`Query OK — ${response.results.length} pages, has_more=${response.has_more}`);

  // Verify property types are still parsed correctly
  for (const page of response.results) {
    if ('properties' in page) {
      const types = Object.values(page.properties).map(p => p.type);
      console.log(`  Property types: ${[...new Set(types)].join(', ')}`);
    }
  }
}

// Test 3: Page creation and archival (write path)
async function verifyPageLifecycle(databaseId: string): Promise<void> {
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: { title: [{ text: { content: `Upgrade test ${Date.now()}` } }] },
    },
  });
  console.log(`Create OK — page ${page.id}`);
  await notion.pages.update({ page_id: page.id, archived: true });
  console.log('Archive OK');
}

// Test 4: Block operations (read + append)
async function verifyBlocks(pageId: string): Promise<void> {
  const { results } = await notion.blocks.children.list({ block_id: pageId });
  console.log(`Block list OK — ${results.length} blocks`);
  await notion.blocks.children.append({
    block_id: pageId,
    children: [{
      paragraph: { rich_text: [{ text: { content: 'Upgrade verification block' } }] },
    }],
  });
  console.log('Block append OK');
}

// Test 5: Comments API (available since SDK 2.2.0)
async function verifyComments(pageId: string): Promise<void> {
  try {
    const { results } = await notion.comments.list({ block_id: pageId });
    console.log(`Comments OK — ${results.length} comments`);
  } catch (err) {
    console.log('Comments API not available in this SDK version');
  }
}

// Run all verification
await verifyAuth();
await verifyDatabaseQuery(process.env.TEST_DB_ID!);
await verifyPageLifecycle(process.env.TEST_DB_ID!);
await verifyBlocks(process.env.TEST_PAGE_ID!);
await verifyComments(process.env.TEST_PAGE_ID!);
```

After all tests pass, merge the upgrade branch:
```bash
npm test                  # Run project test suite
git add -A
git commit -m "chore: upgrade @notionhq/client to $(npm ls @notionhq/client --depth=0 | grep @notionhq)"
git checkout main && git merge -
```

## Output

- SDK upgraded to the latest stable release with exact version pinned in `package.json`
- API version explicitly set in client initialization (not relying on SDK default)
- New property types (status, unique_id) handled in extraction logic
- All existing API calls verified — database queries, page CRUD, block operations
- Upgrade branch merged with clean test run

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TypeError: Cannot read properties of undefined` | New property type returned by API that code does not handle | Add a default case to property type switch — see Step 2 |
| `APIResponseError: Could not find ...` | Stale page/database ID after workspace migration | Re-share pages with the integration at notion.so/my-integrations |
| `notionVersion is not a valid API version` | Typo or unsupported version string | Use `2022-06-28` — confirm at developers.notion.com/reference/versioning |
| Type errors on `api-endpoints` imports | Import path changed between SDK major versions | Check `node_modules/@notionhq/client/build/src/api-endpoints.d.ts` for current exports |
| `ENOTFOUND api.notion.com` | Network or proxy blocking Notion API | Verify DNS, check corporate proxy, test with `curl https://api.notion.com/v1/users/me` |
| `pip install` fails for `notion-client` | Python version incompatible | Requires Python 3.7+; use `pip install --upgrade pip` first |

## Examples

### Rollback After Failed Upgrade

```bash
# Revert to exact previous version
npm install @notionhq/client@2.2.14 --save-exact

# Restore any source changes
git checkout -- src/

# Verify rollback
npm test
npm ls @notionhq/client
```

### Adopting Comments API After Upgrade

```typescript
// Available since @notionhq/client 2.2.0
// Add a comment to a page
await notion.comments.create({
  parent: { page_id: pageId },
  rich_text: [{ text: { content: 'Automated review comment from CI' } }],
});

// List all comments on a page
const { results: comments } = await notion.comments.list({
  block_id: pageId,
});
for (const comment of comments) {
  const text = comment.rich_text.map(rt => rt.plain_text).join('');
  console.log(`${comment.created_by.id}: ${text}`);
}
```

### Detecting New Property Types in Existing Databases

```typescript
// After upgrade, scan databases for new property types your code may not handle
async function auditPropertyTypes(databaseId: string): Promise<void> {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const knownTypes = new Set([
    'title', 'rich_text', 'number', 'select', 'multi_select',
    'date', 'checkbox', 'url', 'email', 'phone_number',
    'formula', 'relation', 'rollup', 'people', 'files',
    'created_time', 'last_edited_time', 'created_by', 'last_edited_by',
    'status', 'unique_id',  // Newer types
  ]);

  for (const [name, prop] of Object.entries(db.properties)) {
    if (!knownTypes.has(prop.type)) {
      console.warn(`Unknown property type "${prop.type}" on "${name}" — add handler`);
    }
  }
}
```

### Deprecation Monitoring Script

```bash
#!/usr/bin/env bash
# Check for known deprecated patterns in your codebase
echo "=== Notion SDK Deprecation Audit ==="

# Check for deprecated header format
grep -rn "Notion-Version" --include="*.ts" --include="*.js" src/ 2>/dev/null && \
  echo "WARN: Raw Notion-Version header found — use client notionVersion option instead"

# Check for untyped page responses
grep -rn "as any" --include="*.ts" src/ 2>/dev/null | grep -i notion && \
  echo "WARN: Type assertions on Notion responses — use PageObjectResponse type"

# Check SDK version against latest
CURRENT=$(npm ls @notionhq/client --depth=0 2>/dev/null | grep @notionhq | sed 's/.*@//')
LATEST=$(npm view @notionhq/client version 2>/dev/null)
if [ "$CURRENT" != "$LATEST" ]; then
  echo "UPDATE: Running $CURRENT, latest is $LATEST"
else
  echo "OK: Running latest ($CURRENT)"
fi
```

## Resources

- [Notion SDK Releases](https://github.com/makenotion/notion-sdk-js/releases) — changelog for every `@notionhq/client` version
- [API Versioning](https://developers.notion.com/reference/versioning) — version lifecycle and header format
- [API Changelog](https://developers.notion.com/changelog) — new endpoints, properties, and breaking changes
- [Python notion-client](https://pypi.org/project/notion-client/) — PyPI page with version history
- [API Status](https://status.notion.so/) — check for ongoing incidents before debugging upgrade issues

## Next Steps

After upgrading, apply production patterns from `notion-sdk-patterns` and verify rate limit handling with `notion-rate-limits`.
