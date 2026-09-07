---
name: intercom-upgrade-migration
description: |
  Upgrade the intercom-client SDK across major versions and handle Intercom API
  version changes safely. Use when a project is pinned to an old intercom-client
  release, when the v5 CommonJS API must move to the v6 TypeScript rewrite, or
  when detecting breaking changes in a new Intercom release before shipping.
  Trigger with phrases like "upgrade intercom", "intercom migration",
  "intercom breaking changes", "update intercom SDK", "intercom API version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
argument-hint: "[current-version] [target-version]"
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Upgrade & Migration

## Overview

Upgrade the `intercom-client` npm package and handle Intercom API version
changes without breaking production traffic. The v6 TypeScript rewrite changed
the API surface — most notably unifying `users`/`leads` into a single `contacts`
API — so this skill drives a branch-based, type-checked upgrade that surfaces
every breaking change through the compiler and test suite before merge.

Deep material lives in `references/` so this file stays scannable:

- [Full v5 → v6 migration guide](references/migration-guide.md) — every changed
  operation with before/after code, API-version pinning, the upgrade procedure,
  type-import changes, and the method cheat sheet.
- [Worked examples](references/examples.md) — three end-to-end runs from version
  detection through a committed upgrade branch.

## Prerequisites

- A project with `intercom-client` already installed (`npm list intercom-client`
  shows the current version).
- Git available for branch-based upgrades and reviewable diffs.
- A working test suite, ideally including an integration suite that can run
  against a dev Intercom workspace.
- TypeScript (`tsc`) configured if migrating to v6+, since the compiler is the
  primary breaking-change detector.

## Authentication

Intercom API calls authenticate with a workspace access token passed as a Bearer
token. Read it from the `INTERCOM_ACCESS_TOKEN` environment variable — never
hardcode it. Version-detection curls and the integration test step both consume
this variable:

```bash
export INTERCOM_ACCESS_TOKEN="<workspace-access-token>"   # from Intercom > Developer Hub
```

Use a separate dev-workspace token (`$DEV_TOKEN`) for the integration test step
so the upgrade is validated without touching production data.

## Instructions

Follow the workflow at a high level here; drill into
[the migration guide](references/migration-guide.md) for the exact code diffs.

### Step 1: Check current versions

Read (with the `Read` tool or `npm list`) the installed version, the latest
published version, and the live API version to size the upgrade:

```bash
npm list intercom-client                  # installed SDK version
npm view intercom-client version          # latest available
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i intercom-version
```

If the installed major is < 6 and the target is ≥ 6, expect the TypeScript-rewrite
breaking changes.

### Step 2: Migrate the code (v5 → v6)

For a major crossing, apply the breaking-change diffs with the `Edit`/`Write`
tools: swap `new Intercom.Client()` for `new IntercomClient()`, move
`users`/`leads` calls to the unified `contacts` API, rename positional params
(`id` → `contactId`/`conversationId`), and update error handling to the
`IntercomError` instance check. The full before/after set and a one-line-per-method
cheat sheet are in [the migration guide](references/migration-guide.md).

### Step 3: Pin the API version if needed

The SDK sends a compatible `Intercom-Version` header automatically. Pin it
explicitly only when using raw `fetch` requests or when a response shape must be
frozen — see the API-version-pinning section of the migration guide.

### Step 4: Run the type-checked upgrade on a branch

Do the whole upgrade on a dedicated branch so TypeScript and the tests gate it:

```bash
git checkout -b upgrade/intercom-client-v6
npm install intercom-client@latest
npx tsc --noEmit 2>&1 | grep "intercom"    # surfaces every breaking change
npm test
```

Fix each error the compiler reports, re-run until clean, then validate against a
dev workspace and commit. The complete procedure is in the migration guide.

## Output

Running this skill produces:

- A dedicated upgrade branch (e.g. `upgrade/intercom-client-v6`) with
  `intercom-client` bumped in `package.json` / lockfile.
- Source edits that migrate every v5 call site to the v6 API surface.
- A clean `npx tsc --noEmit` run (no remaining `intercom-client` type errors) and
  a green `npm test` / integration run against a dev workspace.
- A commit ready for PR, e.g. `chore: upgrade intercom-client to v6`.

## Error Handling

| Issue | Detection | Solution |
|-------|-----------|----------|
| `Cannot find module 'intercom-client'` | Import fails | `npm install intercom-client` |
| `Property 'users' does not exist` | TypeScript error | Migrate `users`/`leads` to `contacts` |
| `Property 'id' does not exist` | Changed param names | Use `contactId`, `conversationId` |
| Response shape changed | Runtime errors | Check API version headers, pin `Intercom-Version` |
| `401 Unauthorized` | curl/test fails | Verify `INTERCOM_ACCESS_TOKEN` is set and valid |

## Examples

Quick skeleton — detect, then migrate one call:

```bash
npm list intercom-client        # e.g. 5.4.0
npm view intercom-client version # e.g. 6.4.0 → major upgrade
```

```typescript
// v5  → migrate to →  v6
// await client.users.create({ email });
await client.contacts.create({ role: "user", email });
```

Three full end-to-end runs — version detection, a single-call migration, and a
complete branch upgrade — are in [references/examples.md](references/examples.md).

## Resources

- [intercom-node GitHub](https://github.com/intercom/intercom-node)
- [SDK v6 Release Notes](https://github.com/intercom/intercom-node/discussions/416)
- [API Versioning](https://developers.intercom.com/docs/references/introduction)
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)

## Next Steps

After the upgrade branch is green, wire the version bump into CI so future
regressions are caught automatically — see the `intercom-ci-integration` skill
for the pipeline configuration.
