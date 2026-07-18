---
name: clickhouse-upgrade-migration
description: |
  Use when upgrading ClickHouse server versions or the @clickhouse/client SDK,
  handling breaking changes between versions, or migrating from older client
  libraries — covers version checks, changelog review, staged upgrade, post-upgrade
  validation, and rollback.
  Trigger with phrases like "upgrade clickhouse", "clickhouse version upgrade",
  "update clickhouse client", "clickhouse breaking changes", "new clickhouse version".
allowed-tools: Read, Edit, Bash(npm:*), Bash(git:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Upgrade & Migration

## Overview

Safely upgrade ClickHouse server and the `@clickhouse/client` Node.js SDK, with
rollback procedures and breaking-change detection. The workflow is check versions
→ review changelogs → upgrade the client → upgrade the server → validate →
rollback if needed. Full command sequences live in
[references/implementation.md](references/implementation.md); the runnable
migration, validation, and rollback code lives in
[references/examples.md](references/examples.md).

## Prerequisites

- Current ClickHouse version known (`SELECT version()`)
- Git for version control (client changes land on an `upgrade/` branch)
- Test suite for integration validation (`npm test`)
- Staging environment for pre-production testing
- `CLICKHOUSE_HOST` set (and credentials — see Authentication)

## Authentication

The client and validation scripts read the server URL from the
`CLICKHOUSE_HOST` environment variable (e.g. `http://localhost:8123` locally, or
your ClickHouse Cloud endpoint). Keep credentials in the environment, never
hardcoded: pass `username` / `password` to `createClient` from
`process.env.CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD`, and for raw `curl` send
them via the `X-ClickHouse-User` / `X-ClickHouse-Key` headers. ClickHouse Cloud
endpoints require TLS (`https://`) and a password; self-hosted default installs
often run open on `8123` (the HTTP port) in dev only.

## Instructions

Work the steps in order — the client upgrade and the server upgrade are separate,
independently reversible changes. Read
[references/implementation.md](references/implementation.md) for the full command
sequence of each step.

### Step 1: Check Current Versions

Capture the server version, the installed client version, and the latest
published client before changing anything — this is your rollback target.

```bash
curl 'http://localhost:8123/?query=SELECT+version()'   # server
npm list @clickhouse/client                            # installed client
npm view @clickhouse/client version                    # latest available
```

### Step 2: Review Changelog

Read the client and server changelogs and note breaking changes: `createClient`
option renames, default setting changes (compression, timeouts), query
result-format behavior, removed SQL functions, and renamed MergeTree settings.
Full checklist and links: implementation.md Step 2.

### Step 3: Upgrade the Node.js Client

Isolate the client bump on a branch so it is reversible independent of the server.

```bash
git checkout -b upgrade/clickhouse-client
npm install @clickhouse/client@latest
npm test
```

Then apply the code-migration patterns (the `host` → `url` option rename and the
`rs.json()` result-shape change) — full before/after in
[references/examples.md](references/examples.md) under "Common migration patterns".
Edit the client-initialization and result-handling code to match.

### Step 4: Upgrade ClickHouse Server

ClickHouse Cloud upgrades automatically — just read the console release notes.
Self-hosted follows a fixed sequence: **backup → check changed settings → stop →
`apt-get install` → start → verify version → scan schema**. Full command block:
implementation.md Step 4.

### Step 5: Validate After Upgrade

Run the post-upgrade validation script — ping, version, schema, insert, and query
checks, each reporting PASS/FAIL. Full script:
[references/examples.md](references/examples.md) under "Post-upgrade validation script".

### Step 6: Rollback Procedure

If validation fails, roll back the client (`npm install` the previous version
with `--save-exact`), the server package, and — if data is affected — `RESTORE` from the
pre-upgrade backup. Full commands:
[references/examples.md](references/examples.md) under "Rollback commands".

## Version Compatibility Matrix

| Client Version | Min Server Version | Node.js | Key Changes |
|---------------|-------------------|---------|-------------|
| 1.x | 22.6+ | 18+ | Stable API, `url` option |
| 0.3.x | 22.6+ | 16+ | `host` option, different JSON result shape |
| 0.2.x | 21.8+ | 14+ | Initial release |

## Output

- Current and target versions recorded (server + client) as the rollback baseline
- Client upgraded on an isolated `upgrade/` branch with `npm test` green
- Code migrated for known breaking changes (`host` → `url`, `rs.json()` shape)
- Server upgraded via the backup → stop → install → verify sequence
- Post-upgrade validation run: ping, version, schema, insert, and query all PASS
- Documented rollback path for both client and server if any check fails

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Unknown setting` | New default in config | Remove deprecated setting |
| `Cannot parse datetime` | Format change | Update date format strings |
| `Method not found` | Client API changed | Check migration guide |
| `Checksum mismatch` | Corrupted upgrade | Rollback and re-download |

## Examples

Two ready-to-run starting points live in
[references/examples.md](references/examples.md):

- **Common migration patterns** — before/after for the `createClient` option
  rename and the `rs.json()` result-shape change between v0.x and v1.x.
- **Post-upgrade validation script** — a self-contained check runner that
  exercises ping → version → schema → insert → query.

```typescript
// Validation entry point — full runner in references/examples.md
const client = createClient({ url: process.env.CLICKHOUSE_HOST! });
await client.ping();                                          // 1. reachable
await client.query({ query: 'SELECT version()', format: 'JSONEachRow' }); // 2. new version live
// 3. schema, insert, and query checks follow in the full script
```

## Resources

- [Client Releases](https://github.com/ClickHouse/clickhouse-js/releases)
- [Server Changelog](https://github.com/ClickHouse/ClickHouse/blob/master/CHANGELOG.md)
- [ClickHouse Cloud Upgrades](https://clickhouse.com/docs/en/manage/updates)

## Next Steps

For CI/CD integration of the upgraded client, see `clickhouse-ci-integration`.
For pre-production release gating, see `clickhouse-prod-checklist`.
