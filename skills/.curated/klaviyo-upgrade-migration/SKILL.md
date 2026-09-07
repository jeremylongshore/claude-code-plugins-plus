---
name: klaviyo-upgrade-migration
description: 'Upgrade Klaviyo SDK versions and migrate between API revisions.

  Use when upgrading the klaviyo-api package, migrating from v1/v2 legacy APIs
  to the current REST API, or handling breaking changes between revisions.
  Trigger with phrases like "upgrade klaviyo", "klaviyo migration",
  "klaviyo breaking changes", "update klaviyo SDK", "klaviyo API revision".

  '
allowed-tools: Read, Edit, Bash(npm:*), Bash(git:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Upgrade & Migration

## Overview

Guide for upgrading the `klaviyo-api` SDK, migrating from legacy v1/v2 APIs, and
handling breaking changes between Klaviyo API revisions. The workflow assesses the
current version, surfaces breaking changes with the TypeScript compiler, applies the
matching migration pattern, and ships behind a staging deploy with a clean rollback.

Deep before/after code and the full command sequence live in `references/` so this
file stays a scannable map of the workflow:

- [Migration patterns](references/migration-patterns.md) — legacy v1/v2 → current API, SDK major upgrade (`ConfigWrapper` → `ApiKeySession`), property casing.
- [Upgrade & rollback procedure](references/upgrade-procedure.md) — pinned install, tsc/test gates, staging deploy, rollback, migration checklist.

## Prerequisites

- The `klaviyo-api` package installed and a known current version (`npm list klaviyo-api`).
- Git available, with a clean working tree so the upgrade lands on its own branch.
- A working test suite (`npm test`), and ideally a staging integration test target.
- A Klaviyo private API key in the environment for integration verification.

## Klaviyo API Revision Timeline

Each revision is supported for **2 years** after release. Plan to move to the latest
every 12-18 months so you never fall inside the deprecation window.

| Revision | Released | Deprecated | Key Changes |
|----------|----------|------------|-------------|
| `2024-10-15` | Oct 2024 | Oct 2026 | Reporting API, campaign message updates |
| `2024-07-15` | Jul 2024 | Jul 2026 | Custom objects, tracking settings |
| `2024-02-15` | Feb 2024 | Feb 2026 | Bulk operations, segments V2 |
| `2023-12-15` | Dec 2023 | Dec 2025 | Profile subscription changes |
| `2023-07-15` | Jul 2023 | Jul 2025 | Relationship endpoint restructuring |

## Instructions

### Step 1: Assess the current state

Compare what is installed against what is published to size the jump. A single major
step is routine; skipping several majors means expect casing and import changes.

```bash
npm list klaviyo-api          # e.g. klaviyo-api@15.0.0
npm view klaviyo-api version  # latest, e.g. 21.0.0
```

### Step 2: Find affected usage

Read the [releases changelog](https://github.com/klaviyo/klaviyo-api-node/releases)
for the target major, then locate the call sites that will need edits.

```bash
grep -rn "from 'klaviyo-api'" src/
grep -rn "ApiKeySession\|ConfigWrapper\|ProfilesApi\|EventsApi" src/
```

### Step 3: Apply the matching migration pattern

Pick the pattern that fits the errors you see and edit each call site. Full
before/after code is in [migration patterns](references/migration-patterns.md):

- **Legacy v1/v2 → current API** — replace raw `/api/v2/...` HTTP calls with typed `EventsApi` / `ProfilesApi` resource classes.
- **SDK major upgrade** — swap the global `ConfigWrapper('pk_***')` for a per-instance `new ApiKeySession('pk_***')` passed to each `*Api`.
- **Property casing** — rename `snake_case` attributes (`first_name`) to `camelCase` (`firstName`).

### Step 4: Upgrade, verify, and ship

Install the target version pinned, let `tsc` and the test suite gate the change, and
deploy to staging before production. Full commands: [upgrade procedure](references/upgrade-procedure.md).

```bash
git checkout -b upgrade/klaviyo-api-v21
npm install klaviyo-api@21.0.0 --save-exact
npx tsc --noEmit 2>&1 | grep -i "klaviyo\|error TS"   # find breaking changes
npm test
```

### Step 5: Roll back if needed

If error rates rise after the upgrade, reinstall the previous exact version — see the
[rollback procedure](references/upgrade-procedure.md). Because Step 4 pinned versions,
rollback is a clean reinstall with no dependency guesswork.

## Output

Running this workflow produces:

- An `upgrade/klaviyo-api-vNN` branch with `package.json` + `package-lock.json` pinned to the target version via `--save-exact`.
- Edited call sites in `src/` using the current `ApiKeySession` pattern and `camelCase` attributes, with `npx tsc --noEmit` clean.
- A green `npm test` (and staging `test:integration`) run confirming the migration.
- A commit deployed to staging first, with a documented rollback commit ready if 24-hour error monitoring flags a regression.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TypeError: ConfigWrapper is not a function` | Old SDK pattern | Switch to `ApiKeySession` pattern |
| `Property 'first_name' does not exist` | Casing change | Use `firstName` (camelCase) |
| `response.data is undefined` | Access pattern change | Use `response.body.data` |
| `revision not supported` | Deprecated revision | Update `revision` header value |

## Examples

**Migrate a v2 identify call to the current SDK.** After `grep` finds a legacy
`/api/identify` call, replace it with `createOrUpdateProfile`:

```typescript
import { ApiKeySession, ProfilesApi, ProfileEnum } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: { email: 'user@example.com', firstName: 'Jane', properties: { plan: 'pro' } },
  },
});
```

The full set of before/after examples — event tracking, the `ConfigWrapper` →
`ApiKeySession` upgrade, and property casing — is in
[migration patterns](references/migration-patterns.md).

## Resources

- [API Versioning & Deprecation Policy](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)
- [v1/v2 Migration Guide](https://developers.klaviyo.com/en/v2024-10-15/docs/best_practices_v1v2_migration)
- [Relationship Migration](https://developers.klaviyo.com/en/v2024-10-15/docs/migrate_to_2023_07_15_relationships)
- [klaviyo-api-node Releases](https://github.com/klaviyo/klaviyo-api-node/releases)

## Next Steps

For wiring these upgrade checks into continuous integration, see the
`klaviyo-ci-integration` skill.
