---
title: "Guidewire MCP: v0.1.0 → v0.1.1 in 76 minutes"
description: "v0.1.0 shipped at 19:14 Mountain, surfaced an install-path defect at 20:30, patched in v0.1.1. The architectural insight: dual Postgres pools for tamper-resistant audit logs."
date: "2026-05-06"
tags: ["mcp", "guidewire", "release-engineering", "postgres-audit", "case-study"]
featured: false
---
Insurance carriers run on Guidewire InsuranceSuite — PolicyCenter, ClaimCenter, BillingCenter. Underwriters and claims adjusters spend hours navigating the UI to answer questions like *"what submissions are waiting on me?"* or *"why isn't the Acme account active anymore?"*. The Cloud API exists, but it speaks REST verbs (`GET /job/v1/jobs?subtype=Submission&status=Quoted&assignedTo=alice`). LLMs route well on operator language and badly on REST verbs. So the tools are named like the question an operator would actually ask:

```
find-submissions-waiting-on-me
show-policies-for-this-insured
summarize-this-submission
did-we-lose-this-account
pull-this-submission
```

That's the v0.1.0 catalog — five read-only PolicyCenter tools, shipped this week as `@intentsolutions/policycenter-mcp` (the MCP server package, one of several under the `@intentsolutions/guidewire-*` workspace scope — `guidewire-schemas`, `guidewire-observability`, `guidewire-auth`, `guidewire-audit`, `guidewire-client`, `guidewire-mcp-runtime`, plus the harness, all published from one monorepo). One-line install:

```
/plugin install jeremylongshore/guidewire-mcp-for-claude
```

That `/plugin install` command pulls the GitHub repo `jeremylongshore/guidewire-mcp-for-claude`, which boots the `policycenter-mcp` server from the `@intentsolutions/guidewire-*` published packages. Set four env vars, restart Claude Code, ask carrier questions in a session. The tool's *implementation* hits real Guidewire endpoints; the carrier's profile translates Guidewire's raw field names back to operator-speak before the response returns. Outside layer = operator speech; inside layer = Guidewire schema. The translation step is the load-bearing piece — that's where the operator-question framing actually pays off, because the model is doing the linguistic work it's good at and the profile is doing the schema mapping it's bad at.

What follows is the actual ship narrative — v0.1.0 cut at 19:14 Mountain, v0.1.1 published at 20:30 after an install-path defect surfaced, and a same-evening cleanup commit at 21:29 to reconcile a lint cascade caused by the v0.1.1 version bump. One day, two releases, one cleanup. Every patch surfaced a real defect that would have hit the next end-user, every patch shipped with a CHANGELOG entry, the v0.1.0 ship shipped with an AAR. That sequence is the case the rest of the post makes.

## The day, in commits

The 2026-05-06 commit log on `guidewire-mcp-for-claude` reads cleanly in retrospect, but it didn't feel clean while it was happening. The shape of the day:

| Commit | What landed |
|---|---|
| `a43a9d2` | E1/AR-7: testcontainers role-separation test + pg-store TIMESTAMPTZ fix |
| `838c2ab` | E3 boot-path error translator + CLI wiring (closes BAA carve loop) |
| `173def8` | TECH-SPEC § 8.2.0 + § 8.2.1 sync to shipped migration |
| `3015209` | **chore(release): v0.1.0 — E1 foundation + E2 read-only tools + E3 harness** |
| `578fde0` | .gist-id added for release gist tracking |
| `3264335` | v0.1.0 AAR |
| `a9fcd48` | **fix(install): prepare hook propagates build failures (drop `\|\| true`)** |
| `38124dc` | **chore(release): v0.1.1 — same-day install-path patch (#96 fix)** |
| `aee7653` | feat(E3/obp): end-to-end approved-write test through full harness pipeline |
| `bf38afc` | docs: blog draft for v0.1.0/v0.1.1/v0.1.2 ship narrative |
| `0170574` | docs(README): use real `@intentsolutions/guidewire-*` package names |
| `049e83f` | docs: bump test count 133 → 135 (e2e harness pipeline added 2 tests) |
| `4f7c97b` | chore(deps): bump vitest 2→3 + pnpm overrides for vite 6.4.2 + ip-address 10.1.1 |
| `8acf130` | chore(beads): close guidewire-3x1 (vitest CVE bump landed in PR #101) |
| `6e9e3fd` | **fix(ops/lint): biome format — collapse `files` arrays in 8 package.json** |
| `2f59afb` | docs(CLAUDE.md): /init refresh — drift fixes + new architectural insights |

15 commits. Two tagged releases (v0.1.0, v0.1.1) plus a same-evening biome cleanup that didn't need its own version bump. One architectural insight that will outlast all three.

## Why "carrier vocabulary" instead of "API verbs"

This was the hardest design call to defend in front of the staffed audit panel. The lazy MCP wrapper would expose `search_policies`, `get_account`, `list_submissions` — direct passthroughs to the Cloud API. That's the default pattern across most wrap-an-API MCP servers on GitHub. The principle the Guidewire MCP server is built around — and which is mine, not lifted from any published MCP guidance — is that tool names which ask the LLM to translate from natural language *into* the API's vocabulary force the model to do work it's bad at.

Operator language is what the LLM is good at. So the tool names are operator questions, never API verbs. PR review rejects `search_*`, `list_*`, `get_*` on sight.

The translation layer lives in the customer's profile — specifically `profiles/<tenant>/field-aliases.yaml`. Default install uses an in-memory profile that covers all 5 v0.1.0 tools with sensible defaults; carriers with custom LOB codes, typelists, or role mappings copy `profiles/_template/` into `profiles/<their-tenant>/` and edit. **Zero YAML editing required for the 80% case** — that was the bar for "plug-and-play."

The naming discipline is the difference between an MCP server that demos well and an MCP server an underwriter actually opens before lunch. The five tools above are the ones that survived three rounds of vocabulary review.

## What didn't ship — and why I'm comfortable with that

Three execution modes are in the schema: `read_only`, `draft_only`, `approved_execute`. v0.1.0 ships only `read_only`. The other two are gated behind the harness — a library + CLI (not an MCP server, recursion + tool-selection problem) that wraps every write in `plan → policy → approval → execute → audit → rollback`.

Why the harness gets its own engineering quarter — and why the answer keeps coming back to dual Postgres pools backing a hash-chained audit log, not just "we have a logger":

- **No write without audit, policy, idempotency.** Hash-chained Postgres rows; tamper-resistant via three-role separation (`audit_writer` INSERT-only, `audit_reader` SELECT-only, `audit_owner` for DDL only). The migration grants are tested with testcontainers — `audit_writer` literally cannot `UPDATE` or `DELETE`, caught at build time, not at audit time.
- **Approval flow is human, not Claude.** The harness's `approve()` waits for an external human to click "approve" via the CLI, web UI, or API. The harness side effect (the actual Cloud API write) only fires after an approver decision lands. Tested end-to-end with testcontainers Postgres in the e2e bead that closed E3 — see below.
- **Rollback is a forensic hint, not auto-revert.** The harness produces a `humanInstruction` string ("To roll back: open ClaimCenter → CLM-2026-001 → Reserves tab → set reserve back to prior value"). Carriers do not want their AI assistant auto-reverting writes; they want a paper trail of what happened and a clear instruction for a human to undo it.

That's why drafting tools (`draft-referral-note`, `draft-endorsement`) ship in E5, ClaimCenter MCP in E7, BillingCenter + Payments in E8 (separate dual-control `payments-mcp` because money). All blocked by E3 — and that's the right ordering. The harness moat exists or none of those ship safely.

## The hash-chained audit moat

Every harness call writes a row into `audit_entries` with `prev_hash` referencing the previous row's `entry_hash`. The hash is over the canonical serialization of the row (with `recordedAt` coerced through `toIsoString()` because `pg` returns `TIMESTAMPTZ` as `Date` by default and the canonical hash was computed over the ISO string — caught by the AR-7 testcontainers test, commit `a43a9d2`).

### Six event types in the happy path

A successful approved_execute pipeline run writes these six entries (in order):

1. **plan.created** — idempotency key derived, plan content-addressed
2. **policy.decided** — rule set version stamped onto decision
3. **approval.requested** — human approver gets the row in their queue
4. **approval.decided** — approver vote captured + reason
5. **execute.started** — effect about to fire
6. **execute.completed** — effect returned a value

The full schema includes additional types for failure paths (`execute.failed`, `execute.replayed`) and lifecycle events (`rollback.hint.issued`, `idempotency.pruned`) — ten in total — but these six are what a clean run leaves in the chain. (For the real-world Postgres test that uncovered role-separation bugs, see [The Two Postgres Bugs the Tests Caught](/blog/postgres-approval-sink-bugs-the-tests-caught/).)

### Verification via read-only role

`evidence(traceId)` reconstructs the bundle across all six entries and returns `chainVerification.valid: true` only if every `prev_hash` matches and every `entry_hash` recomputes correctly. A compromised harness can write a row with a wrong hash, but `evidence()` (binding via `audit_reader`, NOT the writer role) will catch it.

The strongest claim I'm willing to make: **tamper-resistant against an outsider; tamper-evident against an unprivileged operator; defense-in-depth via role separation against a privileged DBA — NOT cryptographic tamper-evidence against the schema-owner role.** KMS-signed external commitment is E3+ work.

## The architectural insight that surfaced this week

Writing the end-to-end harness pipeline test (the close criterion for E3, commit `aee7653`) caught a real production-wiring gap: **the harness needs both Postgres pools — writer for `audit.append()`, reader for `evidence.build()`.** The in-memory tests never caught this because the memory store has no role separation; the unit tests passed cleanly. Only when wiring real `PgAuditStore` for both audit + evidence did Postgres throw `permission denied for table audit_entries` — because `audit_writer` is INSERT-only, and `evidence.build()` needs `SELECT`.

This is the kind of bug that's invisible in unit tests, invisible in mock-based integration tests, and only catchable when you wire **real infrastructure with real role separation against the actual production architecture**. CLAUDE.md's `NO MOCKS` hard rule is what surfaced it.

The fix is two lines:

```diff
- const evidence = createEvidenceExporter({ audit: writerAudit, tenantId });
+ const evidence = createEvidenceExporter({ audit: readerAudit, tenantId });
```

The doc note is one comment block in the bootstrap. But without the test, future server bootstrap that wires the harness into `approved_execute` mode would have hit this in production — and the failure mode would have been a confusing `permission denied` at evidence-export time, not at write time. The write would succeed; the proof-of-write would be the thing that failed. That's the worst kind of audit-log bug.

The deeper point: **a hash chain only gives you tamper-evidence if the verification path is bound to a role that physically cannot write.** If `evidence.build()` ran via `audit_writer`, a compromised harness could rewrite a row, recompute the chain, and the verification would happily return `valid: true`. The role separation isn't a defense-in-depth nice-to-have — it is what makes the chain mean anything at all. The dual-pool wiring is the implementation of that property in the harness's bootstrap layer.

For anyone building MCP servers that touch regulated data: this is the design pattern worth lifting. Two pools. One role each. Verification binds via the read-only role, period.

## v0.1.0 → v0.1.1: the install-path defect

v0.1.0 went out at commit `3015209` at 19:14 Mountain. The npm publish ran clean, the GitHub release got created, the gist landed, the `.gist-id` was committed for tracking, the AAR landed three minutes later at 19:17. By the post-release checklist, every gate was green.

About an hour later, an early adopter ran:

```
/plugin install jeremylongshore/guidewire-mcp-for-claude
```

The install reported success. The MCP server failed to register. No error visible to the user — just a "tool not found" when they tried to invoke `find-submissions-waiting-on-me`.

Root cause, found in the root monorepo `package.json`:

```json
"scripts": {
  "prepare": "pnpm -r build || true"
}
```

The `prepare` hook at the workspace root ran `pnpm -r build` (recursive, all workspaces) with `|| true` swallowing any non-zero exit. During the install path, pnpm runs `prepare` to compile the workspaces' TypeScript into each package's `dist/`. If the recursive build failed for any reason — missing peer dep, TS error in a transitive workspace, anything — the `|| true` masked the failure and the postinstall completed "successfully" without producing `policycenter-mcp/dist/cli.js`. The MCP server's entrypoint pointed at `dist/cli.js`. The file didn't exist. The server failed to register, silently.

The fix (commit `a9fcd48`):

```diff
"scripts": {
-  "prepare": "pnpm -r build || true"
+  "prepare": "pnpm -r build"
}
```

One line. Drop the `|| true`. Let install fail loudly when build fails.

I committed the fix at 20:28, ran the release sweep, and v0.1.1 (commit `38124dc`) was on npm two minutes later at 20:30. Total time from v0.1.0 publish to v0.1.1 publish: 76 minutes. The CHANGELOG entry calls out the defect by name; the AAR for v0.1.0 got an addendum noting that this should have been caught by an install-path smoke test in CI, which is now on the E2.5 punch list.

The lesson generalizes beyond this repo. **Any `|| true` in a release-path shell command is a bug.** It is hiding a failure mode that you will discover in production. If you genuinely want to tolerate a non-zero exit, write `|| echo "build failed but continuing"` or set an explicit fallback — never silent-swallow.

## The lint cascade after v0.1.1

The version bump in v0.1.1 ran through `jq` to update 8 `package.json` files across the monorepo workspaces. `jq` does what `jq` does: it parses JSON, pretty-prints it back out, and the pretty-print expanded short string arrays from compact form into multi-line form. The diff looked like:

```diff
-  "files": ["dist", "README.md"]
+  "files": [
+    "dist",
+    "README.md"
+  ]
```

Functionally identical JSON. Visually different. Biome's formatter, configured for the repo's style, wanted the compact form. CI lint failed. Release CI failed. The v0.1.1 publish to npm had already succeeded (the publish runs before the lint gate in this repo's CI), but the next push to main would be blocked until the formatting was reconciled.

The fix (commit `6e9e3fd`):

```bash
npx biome check --write .
git add .
git commit -m "fix(ops/lint): biome format — collapse files arrays in 8 package.json"
```

That's it. Biome rewrote all 8 files back to the compact form, the diff was committed at 21:29, CI went green. No v0.1.2 was cut — the cleanup was a behavior no-op, so cutting another version would have been ceremony for ceremony's sake. The next ship will roll the formatting fix in transparently.

The discipline note for the next release ceremony is the takeaway most engineers will tweet:

> **Always run `npx biome check --write .` as the LAST step of any release-prep diff and re-add the formatted files. Don't trust `jq` to preserve formatting biome cares about.**

That's now an auto-memory feedback rule that travels with me into every Intent Solutions release. The cost of the rule: 5 seconds per release. The cost of not having it: an extra cleanup commit on the day-of, plus the cognitive overhead of rebuilding the mental model for "did this fail because of behavior or because of formatting" the next time CI goes red on a release sweep.

## What v0.1.0 actually contains

Stat block, for the engineers who want to size the surface. For the full v0.1.0 design rationale, see [Guidewire MCP v0.1.0: Carrier-Native Server Blueprint](/blog/guidewire-mcp-v0-1-0-foundation-ship/) (shipped the same week).

| Metric | Value |
|--------|-------|
| Commits in v0.1.0 cut | 63 |
| Files changed | 245 |
| Tests passing | 133 (135 after E3 e2e tests) |
| pnpm workspaces | 8 |
| Days since v0.0.1 | 2 |
| Tools shipped | 5 (read-only) |
| Execution modes available | 1 of 3 (`read_only`) |

The 8 workspaces map to the package layout: `schemas`, `observability`, `auth`, `audit`, `client`, `mcp-runtime`, `harness`, `policycenter-mcp`. v0.1.0 publishes 5 of those to npm under the `@intentsolutions/guidewire-*` scope; the harness ships its own publish in the next release after the e2e test suite is green for a full week.

The 133 tests cover unit (vitest) and integration (testcontainers Postgres for the audit role-separation tests). The two new tests added in commit `aee7653` are end-to-end harness pipeline tests that drive a full `plan → policy → approval → execute → audit → rollback` cycle through real Postgres with both writer and reader pools wired. Those are the tests that surfaced the dual-pool wiring requirement.

## What carriers and MCP authors can take from this week

Three things, ordered by how broadly they apply.

### 1. Name tools after the question, not the API

If you are building an MCP server that wraps an existing API — Salesforce, ServiceNow, Jira, Guidewire, anything — resist the urge to expose `search_*`, `list_*`, `get_*`. Force yourself to write down the question the operator would ask out loud, then make the tool name the slug of that question. The LLM routes on language, not on REST. Your users will thank you, your integration tests will read better, and your tools will survive vocabulary review.

### 2. Bind verification to a role that cannot write

This applies to anyone building audit logs, event sourcing, or any kind of "trust me, here is the proof" surface. The hash chain or the cryptographic signature is necessary but not sufficient. The verification path must be unable to forge the data it verifies. In Postgres, that means a separate role with `SELECT` only. In other systems it means a separate IAM principal, a separate KMS key, a separate process boundary. The dual-pool wiring is the cheapest implementation of this property I know of for a Postgres-backed log.

### 3. Treat every shell command in your release path as a load-bearing assertion

`|| true` is the symptom; the disease is "I want this step to be tolerant of failure." If the step legitimately needs to tolerate failure, write the explicit failure-handling logic. If it doesn't, let it fail loud. The 76-minute round-trip from v0.1.0 publish to v0.1.1 publish is genuinely fast — but the install-path smoke test in CI that should have caught it in the v0.1.0 release sweep was a known gap. The cost of skipping the smoke test was visible to me before the ship; I shipped anyway because the tool list was clean. That was the wrong call. The discipline note: gate releases on install-path smoke tests, not on tool-list cleanliness.

## What's next

- **E3 npm publish** — the harness has the test infra now (135 tests, dual-pool wiring proven); npm publish is the bundle for the marketplace push (E11+).
- **E2.5 aggregate-query tools** — UW manager tranche per architecture decision D-017. Same vocabulary discipline; different access pattern.
- **Karate contract recordings** — gating risk for v0.2.0. The 5 v0.1.0 tools have been validated against a profile-mocked endpoint, not yet against a real Guidewire dev-tier sandbox. Sandbox application is in flight.
- **E5 drafting tools** — `draft-referral-note`, `draft-endorsement`. First writes, gated by harness in `draft_only` mode (no real write — produces a draft artifact for human review).
- **Install-path smoke test in CI** — the explicit gap surfaced by the v0.1.0 → v0.1.1 round trip. Will run `npm install` against the published tarball in a clean container and verify `dist/cli.js` exists before any tag gets pushed.

If you work in carrier IT, build agent tooling, or care about the API-verb-vs-operator-language MCP design question: the [GitHub repo](https://github.com/jeremylongshore/guidewire-mcp-for-claude) is the thing to read. The [live architecture diagram](https://guidewire-mcp.intentsolutions.io/) is the visual companion. Comments and issues welcome.

The discipline IS the product. v0.1.0 shipped, v0.1.1 patched the install path 76 minutes later, the biome cleanup reconciled the lint cascade an hour after that — and the audit log of those changes is itself the evidence that the harness pattern this server enforces in code is the same pattern its maintainer enforces on himself. That symmetry is the point.

---

*Jeremy Longshore is the author and sole maintainer of `@intentsolutions/guidewire-mcp-for-claude`. He runs Intent Solutions, a consulting and tooling practice focused on AI integration for regulated industries.*
