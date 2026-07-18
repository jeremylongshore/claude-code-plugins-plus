---
name: notion-upgrade-migration
description: 'Upgrade @notionhq/client SDK versions and migrate between Notion API
  versions.

  Use when updating SDK packages, handling breaking changes between API versions,

  adopting new SDK features like comments API or status properties, or migrating Python
  notion-client.

  Trigger with phrases like "upgrade notion SDK", "notion migration", "notion breaking
  changes",

  "update notionhq client", "notion API version upgrade", "notion deprecation".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*), Glob, Grep
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Upgrade & Migration

## Overview

Step-by-step guide for upgrading `@notionhq/client` (Node.js) and `notion-client` (Python) SDK versions, migrating between Notion API versions, handling breaking changes, and adopting newly released features. Covers the current stable API version `2022-06-28` and the SDK feature timeline through v2.x.

The workflow is three phases — **audit** what you run today, **upgrade** on an isolated branch while fixing breaking changes, then **verify** every API surface before merging. Deep code (the full breaking-change catalog, the verification suite, and worked recipes) lives in `references/` so this file stays a scannable playbook.

## Prerequisites

- Existing project with `@notionhq/client` or `notion-client` installed
- Git repository with clean working tree (no uncommitted changes)
- Test suite covering Notion API calls (or willingness to add verification tests)
- `NOTION_TOKEN` environment variable configured

## Instructions

### Step 1: Audit Current Versions and API Surface

Determine what you are running today before changing anything.

```bash
# Node.js — installed vs latest SDK version
npm ls @notionhq/client
npm view @notionhq/client version

# Python — installed vs latest SDK version
pip show notion-client 2>/dev/null | grep Version
pip index versions notion-client 2>/dev/null | head -1

# Find which API version your code specifies
grep -rn "notionVersion\|Notion-Version\|notion_version" src/ lib/ app/ 2>/dev/null
```

Record the current SDK version and API version before proceeding. If no `notionVersion` is set explicitly, the SDK uses its built-in default (typically `2022-06-28` for current releases).

**SDK version history — key milestones:**

| SDK Version | Notable Additions |
| ------------- | ------------------- |
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

```bash
# Node.js
git checkout -b upgrade/notionhq-client-$(npm view @notionhq/client version)
npm install @notionhq/client@latest
git diff package.json package-lock.json

# Python
git checkout -b upgrade/notion-client-$(pip show notion-client 2>/dev/null | grep Version | awk '{print $2}')
pip install --upgrade notion-client
pip show notion-client | grep Version
```

After any major version bump, check four things: endpoint-type **import paths** (they moved in some releases), **error-handling imports** (stable across 2.x), **new property types** your extraction logic must handle gracefully (`status` added in 2.2.3, `unique_id` in 2.2.4), and an **explicitly pinned `notionVersion`** so behavior is reproducible instead of tracking the SDK default. The complete before/after code for Node.js and Python is in [breaking-changes.md](references/breaking-changes.md).

### Step 3: Verify and Test the Upgrade

Run targeted verification tests to confirm nothing broke — test each API surface your application uses (auth, database query, page create/archive, block read/append, comments), then run the project suite and merge. Skeleton:

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN, notionVersion: '2022-06-28' });

async function verifyDatabaseQuery(databaseId: string) {
  const res = await notion.databases.query({ database_id: databaseId, page_size: 5 });
  console.log(`Query OK — ${res.results.length} pages, has_more=${res.has_more}`);
}
```

The full five-test verification suite plus the merge commands are in [verification.md](references/verification.md).

## Output

- SDK upgraded to the latest stable release with exact version pinned in `package.json`
- API version explicitly set in client initialization (not relying on SDK default)
- New property types (status, unique_id) handled in extraction logic
- All existing API calls verified — database queries, page CRUD, block operations
- Upgrade branch merged with clean test run

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `TypeError: Cannot read properties of undefined` | New property type returned by API that code does not handle | Add a default case to property type switch — see Step 2 |
| `APIResponseError: Could not find ...` | Stale page/database ID after workspace migration | Re-share pages with the integration at notion.so/my-integrations |
| `notionVersion is not a valid API version` | Typo or unsupported version string | Use `2022-06-28` — confirm at developers.notion.com/reference/versioning |
| Type errors on `api-endpoints` imports | Import path changed between SDK major versions | Check `node_modules/@notionhq/client/build/src/api-endpoints.d.ts` for current exports |
| `ENOTFOUND api.notion.com` | Network or proxy blocking Notion API | Verify DNS, check corporate proxy, test with `curl https://api.notion.com/v1/users/me` |
| `pip install` fails for `notion-client` | Python version incompatible | Requires Python 3.7+; use `pip install --upgrade pip` first |

## Examples

Common follow-ons — each is a full recipe in [examples.md](references/examples.md):

- **Rollback after a failed upgrade** — pin the exact previous SDK version, restore source, re-test.
- **Adopting the Comments API** (SDK 2.2.0+) — create and list comments on a page.
- **Detecting new property types** — scan existing databases for types your extraction code does not yet handle.
- **Deprecation monitoring** — a bash audit for raw `Notion-Version` headers, untyped responses, and SDK version drift.

## Resources

- [Notion SDK Releases](https://github.com/makenotion/notion-sdk-js/releases) — changelog for every `@notionhq/client` version
- [API Versioning](https://developers.notion.com/reference/versioning) — version lifecycle and header format
- [Python notion-client](https://pypi.org/project/notion-client/) — PyPI page with version history
- [API Status](https://status.notion.so/) — check for ongoing incidents before debugging upgrade issues

## Next Steps

After upgrading, apply production patterns from `notion-sdk-patterns` and verify rate limit handling with `notion-rate-limits`.
