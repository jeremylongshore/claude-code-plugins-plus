---
name: notion-upgrade-migration
description: |
  Upgrade @notionhq/client SDK versions and migrate to new Notion API versions.
  Use when upgrading SDK versions, handling breaking changes in Notion API,
  or migrating to the 2025-09-03 data source model.
  Trigger with phrases like "upgrade notion", "notion migration",
  "notion breaking changes", "update notion SDK", "notion API version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Upgrade & Migration

## Overview
Guide for upgrading `@notionhq/client` SDK versions and migrating between Notion API versions, including the 2025-09-03 data source model changes.

## Prerequisites
- Current `@notionhq/client` installed
- Git for version control
- Test suite covering Notion API calls

## Instructions

### Step 1: Check Current Versions
```bash
# SDK version
npm list @notionhq/client

# Latest available
npm view @notionhq/client version

# Current API version used
grep -r "notionVersion\|Notion-Version" src/
```

### Step 2: Review Changelog
```bash
# View SDK changelog
npx changelog @notionhq/client
# Or check: https://github.com/makenotion/notion-sdk-js/releases

# View API changelog
# https://developers.notion.com/changelog
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/notionhq-client-v$(npm view @notionhq/client version)
npm install @notionhq/client@latest
npm test
```

### Step 4: Notion API Version History

| API Version | Key Changes |
|-------------|-------------|
| `2022-06-28` | Stable baseline, most tutorials use this |
| `2022-02-22` | Rich text standardization |
| `2025-09-03` | **Breaking:** Database object restructured to data sources model |

### Step 5: Migrating to API Version 2025-09-03

The 2025-09-03 version introduces multi-source databases. Key changes:

```typescript
// BEFORE (2022-06-28): Properties on database object
const db = await notion.databases.retrieve({ database_id: dbId });
const schema = db.properties; // Properties directly on database

// AFTER (2025-09-03): Properties on data_sources
const db = await notion.databases.retrieve({ database_id: dbId });
const dataSource = db.data_sources[0]; // Array of data sources
const schema = dataSource.properties; // Properties on data source

// Query endpoint changed:
// BEFORE: POST /v1/databases/{id}/query
// AFTER: POST /v1/data_sources/{id}/query
```

**Migration steps:**
1. Pin your current API version explicitly in the client
2. Run full test suite against current version
3. Update to new version and fix breaking changes
4. Test all database operations
5. Deploy to staging first

```typescript
// Step 1: Pin current version
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28', // Pin until ready to migrate
});

// Step 3: After updating to 2025-09-03
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2025-09-03',
});
```

### Step 6: SDK Major Version Changes

**@notionhq/client v2.x to v3.x (if applicable):**
```typescript
// Import path is stable
import { Client } from '@notionhq/client';

// Error handling imports are stable
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

// Type imports may change — check API endpoint types
import type {
  PageObjectResponse,
  DatabaseObjectResponse,
  BlockObjectResponse,
} from '@notionhq/client/build/src/api-endpoints';
```

### Step 7: Test Migration
```typescript
// Run targeted tests against each API feature
describe('Post-Upgrade Verification', () => {
  it('should list users', async () => {
    const { results } = await notion.users.list({});
    expect(results.length).toBeGreaterThan(0);
  });

  it('should query database', async () => {
    const response = await notion.databases.query({
      database_id: testDbId,
      page_size: 1,
    });
    expect(response.results).toBeDefined();
  });

  it('should create and archive page', async () => {
    const page = await notion.pages.create({
      parent: { database_id: testDbId },
      properties: {
        Name: { title: [{ text: { content: 'Upgrade test' } }] },
      },
    });
    expect(page.id).toBeTruthy();
    await notion.pages.update({ page_id: page.id, archived: true });
  });

  it('should append and list blocks', async () => {
    const { results } = await notion.blocks.children.list({
      block_id: testPageId,
    });
    expect(Array.isArray(results)).toBe(true);
  });
});
```

## Output
- Updated SDK version
- API version pinned or migrated
- Breaking changes identified and fixed
- Test suite passing on new version

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Type errors after upgrade | API types changed | Update imports from `api-endpoints` |
| `validation_error` | API version mismatch | Set `notionVersion` explicitly |
| Missing `data_sources` | Using old API version | Upgrade to `2025-09-03` |
| Deprecation warnings | Old SDK patterns | Follow migration guide |

## Examples

### Rollback
```bash
# If upgrade fails, revert
npm install @notionhq/client@2.2.15 --save-exact
git checkout -- src/  # Restore source changes
npm test              # Verify rollback works
```

### Version Detection
```typescript
// Check which API version is in use
const notion = new Client({ auth: process.env.NOTION_TOKEN });
// The client sends Notion-Version header automatically
// Check your configured version:
console.log('API Version:', notion.notionVersion ?? '2022-06-28 (default)');
```

## Resources
- [Notion SDK Releases](https://github.com/makenotion/notion-sdk-js/releases)
- [API Versioning](https://developers.notion.com/reference/versioning)
- [API Changelog](https://developers.notion.com/changelog)
- [2025-09-03 Upgrade Guide](https://developers.notion.com/docs/upgrade-guide-2025-09-03)

## Next Steps
For CI integration during upgrades, see `notion-ci-integration`.
