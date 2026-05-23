---
title: "The Two Postgres Bugs the Tests Caught: A Real-DB Integration Test Case Study"
description: "A no-mocks testcontainers policy caught two production-fatal Postgres bugs in one test run — PG 15's schema USAGE removal and an asymmetric SELECT grant for a state-machine-driving sink."
date: "2026-05-05"
tags: ["postgres", "testing", "testcontainers", "architecture", "ci-cd", "authentication", "typescript"]
featured: false
---
## Thesis

A "no mocks" testcontainers policy caught two production-fatal Postgres bugs in one test run. The first would have shipped silently and failed at runtime on every fresh tenant. The second would have shipped to staging and waited there for a real human approver to exercise it — late integration at best, production runtime at worst, depending on how strict the pre-deploy soak is.

The artifact is PR #92 in the Guidewire MCP repo: +1581 lines, -2 lines, 11 new testcontainer cases against a real Postgres 16 image. The tests failed on the first run, surfaced two distinct migration bugs, got the fixes, and now report 51/51 pass at the package level (40 existing + 11 new) and 115/115 across all 8 workspaces.

The post is about the bugs and the methodology that exposed them. The bigger argument: role boundaries belong in tests, not in staging environments. A migration that compiles, applies clean, and grants what it claims to grant can still be wrong in two different ways — and only a test that drives a real Postgres role through a real state machine will tell you so.

## What got built

The harness pattern (plan → policy → approval → execute → audit → rollback) needs a place to put approvals. The previous sink was in-memory: fine for unit tests, useless the moment a CLI session dies mid-`wait()`, the host restarts, or a network partition drops the harness off the audit bus.

The replacement is a Postgres-backed `ApprovalSink`. Per the PRD it must survive restart, network partition, and CLI session death. The pool's connection identity must hold the `audit_writer` Postgres role — the same role used by the audit-chain writer, by design, so a single connection identity covers both tables in one transaction when needed.

The sink does not enforce state-machine legality at the DDL level. The application does. Every UPDATE carries a state precondition in its WHERE clause:

```typescript
UPDATE approvals SET state = $new
 WHERE approval_id = $id AND state = 'pending'
```

That precondition does three things at once:

- **Race-safe.** Two concurrent `decide()` calls cannot both flip the row. The first to acquire the row write lock wins; the second sees `rowCount === 0` and reads the actual state back.
- **Idempotent for the loser.** No throw. The losing call returns the current state. A retry that arrives after a successful approval just gets the approval.
- **Hard-error on illegal user-driven transitions.** A `decide()` call against an already-terminal row returns `rowCount === 0`, the sink reads the current state, sees it is terminal, and throws. The application layer is the one source of truth for legal transitions.

There is no `RETURNING` clause in the UPDATE. The sink does a separate SELECT to read the post-state. That SELECT is what triggered Bug 2 — covered below.

## The first failure: GRANTs that grant nothing

The migration declared the role and table grants the way every Postgres tutorial since 9.x has shown:

```sql
CREATE ROLE audit_writer NOLOGIN;
CREATE ROLE audit_reader NOLOGIN;

-- ... table DDL ...

GRANT INSERT, SELECT ON audit_entries TO audit_writer;
GRANT SELECT          ON audit_entries TO audit_reader;

GRANT INSERT (...), UPDATE (state, approvers, updated_at)
                  ON approvals TO audit_writer;
```

The migration applied clean against the testcontainers `postgres:16` image. No errors. `\dp approvals` showed the privileges exactly as written. Nothing in the SQL surface said anything was wrong.

The first test then failed:

```
error: permission denied for table approvals
    at Parser.parseErrorMessage
    at PgApprovalSink.request (.../packages/harness/src/approvals/pg.ts:74:18)
```

The role had INSERT on the table. `\dp` confirmed it. The pool was authenticating as the right role. The test was inserting through the documented path. Permission denied.

The line in the [Postgres 15 release notes](https://www.postgresql.org/docs/15/release-15.html) that explains this is buried under a heading most people scroll past:

> Remove PUBLIC creation permission on the public schema (Noah Misch). The new default is one of the secure schema usage patterns that we have been recommending since the security release for CVE-2018-1058.

That entry undersells the practical effect. PG 15 tightened the default permissions on the `public` schema in **newly created databases**: the schema is now owned by `pg_database_owner`, and `PUBLIC` lost its `CREATE` privilege. New roles created inside such a database — including the `NOLOGIN` roles this migration declares — cannot exercise any table grant in `public` until somebody hands them schema-level `USAGE` explicitly. Existing PG 13 / 14 databases that get upgraded in place are unaffected; only fresh databases inherit the new posture.

Without `USAGE`, a `GRANT INSERT ON public.approvals TO audit_writer` is a no-op the database cheerfully accepts and silently ignores at runtime — the role has no schema visibility, so the table grant never resolves.

Three lines of SQL fixed it:

```sql
-- PG 15+ removed implicit USAGE on the public schema for new roles.
-- Without this, the table-level GRANTs above are no-ops because the
-- role cannot see the schema. This would have failed any fresh prod
-- deploy on PG 15+. See PG 15 release notes.
GRANT USAGE ON SCHEMA public TO audit_writer, audit_reader;
```

The detail that matters for the case-study argument: this would not have failed in a long-running staging environment. Most staging databases were created on PG 13 or 14 and got upgraded in place. Existing roles kept their `USAGE` from before the change. The bug shows up only on **fresh** deploys to PG 15+ — every new tenant, every disaster-recovery rebuild, every Kubernetes-native ephemeral test environment. The class of bug that bites once and then goes quiet for a year and bites again on a customer that you didn't know was a customer yet.

testcontainers is the inverse of that environment. Every test run is a fresh deploy. `postgres:16` image, no rows, no migrations, full migration replayed top-to-bottom against a freshly created database with freshly created roles. Bug 1 cannot hide there.

## The second failure: a writer that has to read

Tests progressed past Bug 1. The INSERT in `request()` worked. The UPDATE in `decide()` worked. Then the `wait()` test failed:

```
error: permission denied for table approvals
    at PgApprovalSink.wait (.../packages/harness/src/approvals/pg.ts:178:24)
```

The `wait()` method polls. The query is a one-line SELECT against the row by `approval_id`:

```sql
SELECT state, approvers, expires_at, updated_at
  FROM approvals
 WHERE approval_id = $1 AND tenant_id = $2;
```

`wait()` runs that statement at every poll interval, checks if the state is terminal, sleeps, repeats. The poll runs as the same role that did the INSERT. And `audit_writer` had INSERT and column-restricted UPDATE on `approvals` — but no SELECT.

The migration had been written by analogy to `audit_entries`, where the asymmetry is correct: the audit table is append-only from the writer's perspective. Verification (`verifyChain()`) runs under `audit_reader`, a different connection identity by design decision D-019, so the writer never needs to see what it just wrote. The hash chain is what provides tamper-evidence; the writer's lack of read privilege is part of that.

That model breaks for `approvals`. The same identity that INSERTs the `pending` row has to wait for an external actor (a human approver, a sibling service, a partner system) to call `decide()`, then observe the new state. Forcing a separate reader pool for that polling path means dragging a second set of connection credentials, a second pool config, and a second observability surface around for zero security benefit. The provenance for an approval lives in the `audit_entries` rows that reference `approval_id` — not in whether the writer can read the approval row itself.

The fix is one line. The comment that justifies it is fourteen:

```sql
-- The audit_writer ALSO gets SELECT on `approvals` (but NOT on
-- `audit_entries`). This is the asymmetry between the two tables:
--   • `audit_entries` is append-only from the writer's perspective —
--     the writer NEVER reads its own log entries; verifyChain() runs
--     as `audit_reader` (a separate operational identity per D-019).
--   • `approvals` is state-machine-driven by the harness. The same
--     identity that INSERTs the pending row must also wait()-poll it
--     to observe external decisions. Forcing a separate reader pool
--     for that polling path adds connection-management complexity
--     for zero tamper-evidence benefit — provenance comes from the
--     audit_entries rows that reference approval_id, not from
--     approvals row visibility. The defense-in-depth on the
--     approval table is the column-restricted UPDATE + denied DELETE
--     below — both intact under this SELECT grant.
GRANT SELECT ON approvals TO audit_writer;
```

The defense-in-depth properties survive. `audit_writer` still cannot mutate any column except the three the state machine touches (`state`, `approvers`, `updated_at`). It still cannot DELETE from `approvals` at all — forensic retention is non-negotiable. The seven immutable columns (`tenant_id`, `plan_id`, `decision_id`, `requested_at`, `expires_at`, `created_at`, `approval_id`) are still locked down at the column-grant level. A test asserts that explicitly.

The bug class: an asymmetric privilege model that was right for one table got copy-pasted onto a second table where it was wrong. The pattern is correct in both places — the audit table needs a tamper-evidence boundary, the approvals table needs a state-machine boundary. The grants need to express two different invariants.

## Why testcontainers is the only test type that catches this

A mock-based test of `PgApprovalSink` would have passed both bugs.

Bug 1 would have passed because mocks do not have schemas. There is no `public` to lack `USAGE` on. The mock returns whatever you tell it to.

Bug 2 would have passed because mocks do not enforce row-level grants. The mock would have responded to the SELECT in `wait()` with whatever the test fixture said. The actual privilege boundary lives in the database; a mock substitutes for the database; the boundary is not in the test.

A staging-environment integration test would have caught Bug 1 only on the first deploy to a fresh PG 15+ tenant. Most staging databases at most companies were created on PG 13 or PG 14 and upgraded in place; existing roles kept their `USAGE` privilege from the upgrade. Bug 1 shows up on a **new** tenant — exactly the scenario that staging-environment tests rarely cover, because staging databases live for years.

Staging would have caught Bug 2, but only after a `wait()` actually fired against a real approval — meaning after a real human approver decided a real plan, in a real CLI session, against a database the writer role had been bound to for the first time. Most synthetic staging traffic short-circuits the wait-loop with pre-set test fixtures rather than running the polling path end-to-end. The bug surfaces on the first end-to-end approval cycle, which by definition is on the boundary between "caught it in staging" and "shipped it to prod" — and which one of those two the team gets depends on how disciplined the pre-deploy soak is, not on the design of the test.

testcontainers per the repo's CLAUDE.md hard rule #2 — `NO MOCKS, NO STUBS, NO FAKES for any I/O dependency` — is what makes both bugs visible inside a developer's commit cycle. Bug 1 surfaced on the first test that hit `request()`. Bug 2 surfaced on the first test that exercised `wait()` after a `decide()`. Neither bug needed a code review to find. Neither needed a customer.

## Tradeoffs

The bill for this approach is real and itemized.

- **+934 lines of `pnpm-lock.yaml`** out of the +1581 PR total. The new dev dependencies are `pg` (the node Postgres driver) and `testcontainers` (the orchestrator). Their transitive footprint is what it is. Lockfile churn on a `pnpm install` is the headline visual diff in PR #92. The other +647 lines split roughly: +252 sink implementation (`pg.ts`), +357 testcontainer test cases (`approvals.pg.test.ts`), +29 SQL migration deltas, +9 across `package.json` and the harness `index.ts` export.
- **First-run latency.** The `postgres:16` image is ~451 MB. CI pulls it once per runner; locally the developer pulls it once per machine. After that the image is cached.
- **Per-test-file startup.** Each test file spins up its own container, runs migrations, tears down. About 3 seconds of overhead per file. Eleven test cases in one file means 3 seconds amortized, not 33.

The team accepts these costs because the alternative — finding Bug 1 in a Sev 1 customer ticket six months from now during a tenant rebuild, or finding Bug 2 the first time a human approver actually approves something through a real production CLI session — is more expensive in every dimension that matters.

## What this means for the Guidewire MCP architecture

Approvals are the pivot for E3, the write-tools epic. Without a durable approval record, every write tool — `bind-this-quote-with-these-changes`, `submit-payment`, `cancel-policy-with-effective-date` — has nowhere to anchor its proof-of-consent. The audit chain references `approval_id`. The `idempotency.pruned` field in audit entries (PR #85) references `approval_id`. The BAA-carve enforcement at boot for `lob_class:health` (PR #87) gates the approval workflow on a tenant attribute.

Approvals are load-bearing. Approvals must outlive the harness process that requested them. Approvals must survive a CLI session ending mid-`wait()`. Approvals must be readable across audit-chain verification windows that may span weeks (long-tail compliance review, partner reconciliation, dispute resolution).

A Postgres-backed sink is the cheapest way to get all of those properties at once. Postgres gives durability, role-based access control, the column-restricted UPDATE primitive, the per-table DELETE-denied stance, and the SQL we already use everywhere else for tenancy, indexing, and audit. The state-machine guard in the WHERE clause is a Postgres feature being used as a Postgres feature.

The audit chain references `approval_id`. The approval row must therefore exist for at least as long as the audit log that cites it. Forensic retention on `approvals` is permanent. DELETE is denied to every role. That stance is the precondition for the `audit_writer` SELECT grant being safe — the writer can read approvals, but it cannot make approvals disappear.

## Also shipped today

The same day produced eight more PRs across two repos and started a third.

- **PR #91 / #90 (governance):** corrected the OWNER-bypass documentation and recorded the main-branch ruleset that's now actually enforced. Bypass requires explicit `bypass_actors`.
- **PR #89 (lint cleanup):** dropped the biome baseline from 43 ignored issues to 0. Karate JS files now have a targeted ignore; the harness package got auto-fixes applied.
- **PR #88 (CI):** unbroke `ci.yml` workflow startup. The previous startup race meant the very first job in a fresh runner couldn't find a peer dependency.
- **PR #87 (BAA carve):** enforce the carve at boot when `lob_class:health` is set on a tenant. Maps to safeguards SA-6 and MS-6.
- **PR #86 (E3):** approvals table + grants in `0001_init.sql` (the table this sink targets — HR-4).
- **PR #85 (audit chain):** plumb `oauthScope` and `idempotency.pruned` through audit chain (GA-3, HR-3).
- **PR #82 (GW-1.9 closure):** filed re-pass memos and applied 6 findings — sealing blueprint v1.0.

Plus: `partner-portals` shipped its initial Hugo site with the Kobiton portal, a Download-PDF action, and a deploy workflow (5 commits). The Kobiton exp-06 work added 16 tests (78 → 94) and reproduced Plane bug `makeplane/plane#8909` via a browser-log interceptor + click-driver.

## Recap

Two production-fatal bugs surfaced in one test run. Both were in a migration that looked correct under static review. Both required a real Postgres database, exercising real role boundaries, against the actual state machine the sink drives. Mocks would have hidden both. Staging would have caught one of them, on the first new tenant, sometime later, in a place that wasn't a developer's IDE.

The case-study argument: when a privilege boundary is load-bearing, the test that proves it has to be the same kind of database the production runs on. testcontainers makes that affordable. The +934 lines of lockfile is the price of being able to delete the phrase "should work in prod" from the team vocabulary.

## Related Posts

- [Guidewire MCP v0.1.0: The Foundation Ship](/posts/guidewire-mcp-v0-1-0-foundation-ship/) — yesterday's post on the v0.1.0 ship that this sink continues
- [Anti-Slop Framework Found Three Bugs Inside Itself](/posts/anti-slop-framework-found-three-bugs-inside-itself/) — earlier dogfooding case study on quality gates catching their own author
- [Audit Harness v0.1.0: Enforcement Travels With the Code](/posts/audit-harness-v010-enforcement-travels-with-code/) — the harness package the test methodology depends on
