---
name: algolia-upgrade-migration
description: |
  Upgrade algoliasearch from v4 to v5 with breaking change detection and codemod.
  Use when upgrading SDK versions, detecting deprecations, or migrating initIndex patterns.
  Trigger: "upgrade algolia", "algolia migration v5", "algolia breaking changes",
  "update algolia SDK", "algolia v4 to v5".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Upgrade & Migration (v4 to v5)

## Overview

Guide for upgrading `algoliasearch` from v4 to v5. The v5 release is a major rewrite: `initIndex()` is removed, all methods move to the client, and the import style changes.

## Prerequisites

- Current `algoliasearch` v4 installed
- Git for version control (work in a branch)
- Test suite passing on current version

## Breaking Changes Summary

| v4 Pattern | v5 Replacement |
|-----------|----------------|
| `const client = algoliasearch(appId, key)` | `import { algoliasearch } from 'algoliasearch'; const client = algoliasearch(appId, key);` |
| `const index = client.initIndex('name')` | Removed — pass `indexName` to every method |
| `index.search('query')` | `client.searchSingleIndex({ indexName, searchParams: { query } })` |
| `index.saveObjects(records)` | `client.saveObjects({ indexName, objects })` |
| `index.saveObject(record)` | `client.saveObject({ indexName, body: record })` |
| `index.partialUpdateObject(data)` | `client.partialUpdateObject({ indexName, objectID, attributesToUpdate })` |
| `index.deleteObject('id')` | `client.deleteObject({ indexName, objectID })` |
| `index.setSettings(settings)` | `client.setSettings({ indexName, indexSettings })` |
| `index.getSettings()` | `client.getSettings({ indexName })` |
| `index.browse()` | `client.browse({ indexName, browseParams })` |
| `index.findObject(cb)` | `client.findObject({ indexName, ... })` |
| `index.replaceAllObjects(records)` | `client.replaceAllObjects({ indexName, objects })` |
| `index.saveSynonyms(syns)` | `client.saveSynonyms({ indexName, synonymHit })` |
| `index.saveRule(rule)` | `client.saveRule({ indexName, objectID, rule })` |
| `index.waitTask(taskID)` | `client.waitForTask({ indexName, taskID })` |

## Instructions

### Step 1: Create Upgrade Branch and Install v5

```bash
git checkout -b upgrade/algoliasearch-v5
npm install algoliasearch@latest
npm list algoliasearch  # Verify v5.x.x
```

### Step 2: Update Imports

```typescript
// v4
import algoliasearch from 'algoliasearch';
const client = algoliasearch('APP_ID', 'API_KEY');

// v5
import { algoliasearch } from 'algoliasearch';
const client = algoliasearch('APP_ID', 'API_KEY');

// v5 lite client (search-only, frontend)
import { liteClient } from 'algoliasearch/lite';
const searchClient = liteClient('APP_ID', 'SEARCH_KEY');

// v5 individual API client (if you only need one)
import { searchClient } from '@algolia/client-search';
```

### Step 3: Remove initIndex and Update Method Calls

```typescript
// v4: index-based API
const index = client.initIndex('products');
const { hits } = await index.search('laptop');
await index.saveObjects(records);
await index.setSettings({ searchableAttributes: ['name'] });

// v5: client-based API with indexName parameter
const { hits } = await client.searchSingleIndex({
  indexName: 'products',
  searchParams: { query: 'laptop' },
});
await client.saveObjects({ indexName: 'products', objects: records });
await client.setSettings({
  indexName: 'products',
  indexSettings: { searchableAttributes: ['name'] },
});
```

### Step 4: Update waitTask

```typescript
// v4
const { taskID } = await index.saveObjects(records);
await index.waitTask(taskID);

// v5
const { taskID } = await client.saveObjects({ indexName: 'products', objects: records });
await client.waitForTask({ indexName: 'products', taskID });
```

### Step 5: Update Error Handling

```typescript
// v4: error classes from algoliasearch
import { AlgoliaError } from 'algoliasearch';

// v5: error classes
import { ApiError } from 'algoliasearch';

try {
  await client.searchSingleIndex({ indexName: 'products', searchParams: { query: 'test' } });
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`HTTP ${error.status}: ${error.message}`);
  }
}
```

### Step 6: Find All Usage and Verify

```bash
# Find all files using Algolia v4 patterns
grep -rn "initIndex\|\.search(\|\.saveObjects\|\.setSettings\|\.deleteObject\|\.waitTask" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/

# Run tests
npm test

# Type-check
npx tsc --noEmit
```

## Rollback Procedure

```bash
# If v5 breaks things, revert to v4
npm install algoliasearch@4
git checkout -- src/  # Restore v4 code
npm test              # Verify v4 still works
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `initIndex is not a function` | v5 installed but v4 code | Remove `initIndex`, pass `indexName` to methods |
| `searchSingleIndex is not a function` | v4 installed but v5 code | Run `npm install algoliasearch@latest` |
| Type errors after upgrade | Changed type signatures | Update to new parameter objects |
| `default import` error | v5 uses named exports | Change `import algoliasearch` to `import { algoliasearch }` |

## Resources

- [Official v4 to v5 Migration Guide](https://www.algolia.com/doc/libraries/javascript/v5/upgrade/)
- [v5 Method Reference](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/)
- [algoliasearch npm](https://www.npmjs.com/package/algoliasearch)

## Next Steps

For CI integration during upgrades, see `algolia-ci-integration`.
