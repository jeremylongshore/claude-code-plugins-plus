---
name: apify-upgrade-migration
description: |
  Upgrade Apify SDK, apify-client, and Crawlee versions safely.
  Use when migrating between SDK versions, handling breaking changes,
  or updating from Apify SDK v2 to v3 (Crawlee split).
  Trigger with "upgrade apify", "apify migration", "apify breaking changes",
  "update apify SDK", "crawlee upgrade", "apify v2 to v3".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(git:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Upgrade & Migration

## Overview

Guide for upgrading `apify`, `apify-client`, and `crawlee` packages. The biggest
migration in Apify's history was SDK v2 to v3, which split crawling functionality
into the `crawlee` package. This skill covers that migration plus general upgrade
procedures. Read and edit source files with `Grep`/`Read`/`Edit` to apply the
rename-heavy changes, then verify with the packaged script.

## Prerequisites

Before starting, confirm the working tree is in a recoverable state:

- A dedicated git branch for the upgrade, so a bad bump can be reverted cleanly.
- A runnable test suite (`npm test`) plus a build step (`npm run build`) to catch
  TypeScript interface changes.
- The current installed versions recorded (`npm list apify apify-client crawlee`)
  so rollback targets are known.
- `APIFY_TOKEN` in the environment if the verification script's API-connection
  check will run.

## Instructions

### Step 1: Check Current Versions

```bash
# Check installed versions
npm list apify apify-client crawlee 2>/dev/null

# Check latest available versions
npm view apify version
npm view apify-client version
npm view crawlee version

# Check for outdated packages
npm outdated apify apify-client crawlee
```

### Step 2: Create Upgrade Branch

```bash
git checkout -b upgrade/apify-packages
```

### Step 3: Upgrade Packages

```bash
# Upgrade to latest
npm install apify@latest crawlee@latest apify-client@latest

# Or upgrade to specific version
npm install apify@3.2.0 crawlee@3.11.0

# Check for peer dependency issues
npm ls 2>&1 | grep "ERESOLVE\|peer dep"
```

### Step 4: Apply Code Changes

If crossing the v2→v3 boundary, use `Grep` to find every `Apify.` reference and
`Edit` each call site. The full before/after set — imports, `Actor.main`, crawler
option renames (`handlePageFunction` → `requestHandler`), proxy config, request
queues, and the new router pattern — is in
[the v2-to-v3 migration guide](references/v2-to-v3-migration.md). Minimal shape:

```typescript
// v2
import Apify from 'apify';
const { CheerioCrawler } = Apify;
// v3
import { Actor } from 'apify';
import { CheerioCrawler } from 'crawlee';
```

### Step 5: Verify and Test

```bash
npm test
npm run build  # Catch TypeScript errors
```

Then run the packaged verification script from
[verify-and-rollback.md](references/verify-and-rollback.md), which checks imports
resolve, the client connects, and a crawler instantiates.

## Output

A successful upgrade produces:

- Updated `package.json` / `package-lock.json` with the new `apify`, `crawlee`,
  and `apify-client` versions on the `upgrade/apify-packages` branch.
- Migrated source files with all `Apify.*` call sites converted to `Actor.*` /
  `crawlee` imports (only when crossing v2→v3).
- A passing verification run, e.g.:

```text
=== Upgrade Verification ===
  [PASS] Actor import
  [PASS] CheerioCrawler import
  [PASS] ApifyClient import
  [PASS] API connection
  [PASS] Crawler instantiation

All checks passed.
```

If any check fails, follow the [rollback procedure](references/verify-and-rollback.md)
to restore the previous versions before investigating.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `handlePageFunction is not valid` | Using v2 option names in v3 | Rename to `requestHandler` |
| `Apify.main is not a function` | v2 default export removed | Import `{ Actor }` from `apify` |
| `Cannot find module 'crawlee'` | Crawlee not installed | `npm install crawlee` |
| Type errors after upgrade | Changed interfaces | Check release notes for type changes |
| `ERESOLVE` peer conflict on install | Mismatched `apify`/`crawlee` majors | Pin both to matching majors, e.g. `apify@3 crawlee@3` |

## Examples

**Example 1 — Straight version bump (no major boundary).** Update within v3 and
confirm nothing broke:

```bash
git checkout -b upgrade/apify-packages
npm install apify@latest crawlee@latest apify-client@latest
npm test && npm run build
```

**Example 2 — v2 → v3 crawler migration.** Rename the removed option names in a
crawler config:

```typescript
// BEFORE (v2)
const crawler = new Apify.CheerioCrawler({
  handlePageFunction: async ({ request, $ }) => { /* ... */ },
});
// AFTER (v3 / Crawlee)
const crawler = new CheerioCrawler({
  requestHandler: async ({ request, $ }) => { /* ... */ },
});
```

**Example 3 — apify-client constructor change.** Drop the removed `userId`:

```typescript
// v1.x
const client = new ApifyClient({ userId: 'xxx', token: 'yyy' });
// v2+
const client = new ApifyClient({ token: 'yyy' });
```

Deeper walkthroughs — the complete v2→v3 rename set and the full verification
script — live in [references/](references/v2-to-v3-migration.md).

## Resources

- [v2-to-v3 migration guide](references/v2-to-v3-migration.md) — every import,
  initialization, crawler, proxy, request-queue, and router change plus
  apify-client notes.
- [Verification & rollback](references/verify-and-rollback.md) — the post-upgrade
  check script and version-revert procedure.
- [SDK v2 to v3 Migration Guide](https://docs.apify.com/sdk/js/docs/upgrading/upgrading-to-v3)
- [Crawlee Changelog](https://crawlee.dev/js/api/core/changelog)
- [apify-client Releases](https://github.com/apify/apify-client-js/releases)

## Next Steps

For CI integration during upgrades, see `apify-ci-integration`.
