---
title: "Four Releases in One Day: How the claude-code-slack-channel Security Sprint Actually Shipped"
description: "Epic 29-A, 30-A, 30-B, 32-B land in a single calendar day across v0.5.0 → v0.5.1 → v0.6.0 → v0.7.0 — a supervisor, a hash-chained audit journal, and a policy engine that never sees manifests."
date: "2026-04-19"
tags: ["claude-code", "security", "release-engineering", "typescript", "architecture", "testing", "ai-agents"]
featured: false
---
Four releases in one day is what happens when a security audit turns productive.

`claude-code-slack-channel` — the MCP server that lets Claude Code operate inside a Slack thread without leaking outside of it — cut `v0.5.0`, `v0.5.1`, `v0.6.0`, and [`v0.7.0`](https://github.com/jeremylongshore/claude-code-slack-channel/releases/tag/v0.7.0) on April 19. Four tagged releases, 62 merged PRs, four named epics. No all-nighter. No heroics. Just a sequence where each release unblocked the next and the scope was strictly bounded.

This post is about the *order* those four epics landed in, and why shipping them together mattered more than shipping any of them alone.

## The thesis

An audit journal that can be retroactively rewritten is worse than no journal. A supervisor that tracks in-memory session state but loses it on restart is worse than a stateless server. A policy engine that reads manifests its callers control is worse than no policy at all. And a release candidate whose audit finds six S-class bugs should ship those six bugs fixed before the next feature epic opens.

Each epic on April 19 — session supervisor (32-B), hash-chained audit journal (30-A), policy engine (29-A/B), audit receipts (30-B) — only pays off when the others are present. Ship them one per week and the middle weeks are worse than before they started. So they went together, on purpose, in the order the audit demanded.

## Timeline

| Version | Tagged | What landed | What it unblocked |
|---------|--------|-------------|-------------------|
| v0.5.0 | Apr 19 (early) | Epic 30-A journal + Epic 32-B supervisor feature set | Pre-audit scope |
| **v0.5.1** | Apr 19 | S1–S6 security fixes + Batch 3 (B1–B3) supervisor/journal wiring | Trust-boundary correctness |
| **v0.6.0** | Apr 19 | Epic 29-B — `evaluate()` wired as the sole policy gate | Policy enforcement |
| **v0.7.0** | Apr 19 | Epic 30-B — pre-execution audit receipts | Observability of enforcement |

v0.5.0 had shipped the mechanism; v0.5.1 fixed the trust boundaries and wired the supervisor and journal into the server; v0.6.0 put the mechanism in the decision path; v0.7.0 made the decisions legible. Each release is the smallest coherent unit that could be cut without creating a window where the build was more dangerous than the version before it.

A note on the numbered batches used later in this post: **Batch 1** was the S1–S3 security fixes, **Batch 2** was S4–S6, and **Batch 3** was the three supervisor/journal wiring PRs (B1/B2/B3). All three batches landed in v0.5.1.

## Act 1: v0.5.1 — fix what the audit found

A `v0.5.0` pre-release audit produced six security findings, S1 through S6, every one of them a trust-boundary violation on exactly the surface Epic 32-B and 30-A exposed. They got shipped as PRs [#86](https://github.com/jeremylongshore/claude-code-slack-channel/pull/86) through [#91](https://github.com/jeremylongshore/claude-code-slack-channel/pull/91), orchestrated as a multi-agent batch because they touched overlapping files.

**S1 — `assertSendable` state-root denylist.** The Slack upload path's allowlist had a basename/parent denylist but no state-root denylist. An operator who set `SLACK_SENDABLE_ROOTS` to any ancestor of `~/.claude/channels/slack` (e.g. `~/.claude`) could exfiltrate `access.json` and `audit.log` through the `reply` tool. The `.env` regex happened to catch that one bare filename; nothing else in the state dir was protected. Fix: `assertSendable()` gains an optional `stateRoot` parameter, realpath-resolves both file and state root, and fails closed if the file is under the state root.

**S2/S3 — journal broken-flag guard + schema parse ordering.** Two correctness bugs in the same file. `writeEvent()` checked `this.broken` at enqueue time, but calls already in the queue could still execute `_doWrite()` after a failing write. Fix: move the check to the top of `_doWrite()`. Separately, `JournalEvent.parse(event)` was called after building `partial` and computing the hash, so a `ZodError` on caller-supplied input would propagate without setting `this.broken`. Fix: parse first, hash after.

**S4 — `loadSession` schema validation.** `loadSession` was a cast, not a validation: `JSON.parse(raw) as Session`. A corrupt or tampered session file with wrong types (`ownerId: 42`) passed load silently and reached the supervisor, which trusts `ownerId: string` for audit attribution. Fix: `SessionSchema` in [Zod](https://zod.dev), `.strict()`, unknown keys rejected.

**S5 — per-tool Zod input schemas.** The `CallToolRequestSchema` handler destructured tool args as `Record<string, any>` and passed them straight into security-sensitive calls: `assertOutboundAllowed(args.chat_id, args.thread_ts)` would let `undefined` flow through the outbound gate when `chat_id` was missing. Fix: per-tool input schemas, Zod-validated at the dispatcher.

**S6 — quarantine survives deactivate.** `deactivate()` marked the handle `quarantined` then called `live.delete(id)` — the in-process quarantine signal was lost. A subsequent `activate()` re-read the session file from disk as if the save failure never happened, silently bypassing the sticky Quarantined state mandated by `000-docs/session-state-machine.md`. Fix: a private `quarantined: Map<string, Error>` that tracks keys with the original failure, set before `live.delete(id)`.

Six fixes, 430 tests passing (up from 370 at v0.5.0), one release. The design of v0.5.0 was sound; the wiring had holes. The point of v0.5.1 is that those holes cannot be on `main` when the next feature lands.

### Why batch instead of drip

Each S-fix touches 1–3 files. A drip release per fix would have been six tags, six changelogs, six points of integration risk. Batching them as one `v0.5.1` with a multi-agent orchestration plan treats the audit as a single event with a single resolution. The branch names (`batch-1/s1`, `batch-1/s2`, etc.) surface the coordination in git history; the CHANGELOG lists them as a set.

## Act 2: v0.6.0 — wire the policy engine

With v0.5.1 sealed, Epic 29-B could open. The policy engine — `evaluate()` — existed in v0.5.0 as a function but nothing called it. The permission relay (the code that decides whether a tool call proceeds) still used ad-hoc checks against `allowFrom`.

Three-phase rollout, all in one day:

**Phase 1** ([#100](https://github.com/jeremylongshore/claude-code-slack-channel/pull/100)) — wire `evaluate()` into permission-relay. Replace the ad-hoc allowlist check with a tagged-union `PolicyDecision` return. Callers switch on `decision.kind === "allow" | "deny"`.

**Phase 2** ([#101](https://github.com/jeremylongshore/claude-code-slack-channel/pull/101)) — multi-approver quorum + footgun linter. If a rule requires two approvers, `evaluate()` waits for both; the linter refuses policies where a single approver could bypass an intended quorum.

**Phase 3** ([#103](https://github.com/jeremylongshore/claude-code-slack-channel/pull/103)) — end-to-end contract tests. Each policy shape from `000-docs/ACCESS.md` gets a test that runs against the live dispatcher, not a mock. The tests are the documentation of what `evaluate()` enforces.

### The invariant the engine was shaped around

The fight was never `evaluate()` itself. It was making sure manifest data — content that peers publish about themselves — could never influence the policy decision. A peer must not be able to claim a capability that grants it a privilege.

v0.6.0 wired `evaluate()` as the sole policy gate and locked in that `ToolCall` inputs flowing into `evaluate()` contain no manifest-sourced fields. The formal three-layer enforcement of this invariant — now known as **Invariant 31-A.4** — shipped the *next day* in [PR #111](https://github.com/jeremylongshore/claude-code-slack-channel/pull/111): a `dependency-cruiser` rule blocks any import path from `manifest.ts` to `policy.ts`, a `@ts-expect-error` directive goes red if anyone widens `ToolCall` to accept manifest data, and a runtime test forces manifest content into `ToolCall.input` and asserts rejection. Three independent layers for one invariant, formalized on April 20.

The reason that formalization could land cleanly the next day is that April 19 had already shipped `evaluate()` as the decision chokepoint. The layers above just enforce that nothing else pretends to be one.

## Act 3: v0.7.0 — make it observable

A policy engine that makes decisions but doesn't record them is a policy engine in name only. Epic 30-B landed `v0.7.0`: pre-execution audit receipts.

[PR #106](https://github.com/jeremylongshore/claude-code-slack-channel/pull/106) — on every policy evaluation, emit a receipt to the journal *before* the tool runs. The receipt records: which rule matched, which caller was evaluated, which bindings applied, and what the decision was. The tool then runs. A second journal event records the outcome.

The ordering matters. Receipt-before-execution means that if the process dies between the receipt write and the tool execution, the audit log shows "we decided to allow X" followed by silence — a recoverable state where you know what *would* have happened. Receipt-after-execution would leave a window where the tool ran and no one knew why. The per-write fsync from PR #73 makes that ordering durable: the receipt hits disk before the tool is invoked.

[PR #108](https://github.com/jeremylongshore/claude-code-slack-channel/pull/108) added a self-echo regression test: audit-receipts must never contain the input that triggered them verbatim (secrets). The test fixture pipes a known password through the receipt path and asserts none of the journal bytes contain the password.

[PR #109](https://github.com/jeremylongshore/claude-code-slack-channel/pull/109) documented the projection-vs-log distinction: `audit.log` is the source of truth; any in-memory projection is a cache that must reconcile on read.

## The hash-chained journal underneath all of this

Epic 30-A — the audit journal — had landed in `v0.5.0` but on April 19 it became load-bearing for 30-B. Worth making the journal's internals explicit because the whole release chain relies on them.

The `JournalWriter` ([PR #69](https://github.com/jeremylongshore/claude-code-slack-channel/pull/69)) is a hash-chained append-only log using [SHA-256](https://doi.org/10.6028/NIST.FIPS.180-4):

```
event[n].hash = SHA-256( event[n-1].hash || canonicalize(event[n].body) )
```

Each event carries the hash of the previous event in the chain, so any tampering (insert, delete, modify) in the middle of the log invalidates every event after it. `verifyJournal()` walks the chain and reports line/seq/ts/reason/expected/actual on the first break.

On top of the chain:

- **Redaction** ([PR #70](https://github.com/jeremylongshore/claude-code-slack-channel/pull/70)) — a redaction module runs in the writer path. Secrets patterns (env-style `API_KEY=...`, JWT shapes, `ghp_...` tokens) are replaced with `[REDACTED:TYPE]` before the body is serialized. The canonical pattern list and redaction coverage are tested via a table-driven fixture ([PR #75](https://github.com/jeremylongshore/claude-code-slack-channel/pull/75)) that ensures no pattern silently fails.
- **Per-field truncation** ([PR #71](https://github.com/jeremylongshore/claude-code-slack-channel/pull/71)) — field length limits catch oversized attacker-controlled payloads before they bloat the journal.
- **Per-write fsync + `O_APPEND`** ([PR #73](https://github.com/jeremylongshore/claude-code-slack-channel/pull/73)) — every write is flushed to disk before `writeEvent()` resolves; concurrent writers append atomically via Linux [`O_APPEND`](https://man7.org/linux/man-pages/man2/open.2.html) (worth noting the atomicity guarantee is Linux-filesystem-dependent — not guaranteed on NFS, for example). The verification test concurrently writes from multiple handles and asserts no event was lost or interleaved.
- **`verifyJournal()` + `--verify-audit-log` CLI** ([PR #74](https://github.com/jeremylongshore/claude-code-slack-channel/pull/74) / [PR #98](https://github.com/jeremylongshore/claude-code-slack-channel/pull/98)) — operators can verify a journal offline: `bun server.ts --verify-audit-log ~/.claude/channels/slack/audit.log` returns `OK: N event(s) verified` with exit 0, or `FAIL:` with line/seq/ts/reason/expected/actual and exit 1.

The journal is the reason 30-B receipts are trustworthy. A policy decision emitted as a receipt into an unhashed log is a decision that can be rewritten post-hoc. Hash-chained journal means the receipt is tamper-evident, which means the receipt is *evidence*.

## The session supervisor — Epic 32-B

Running in parallel under everything else was Epic 32-B, the session supervisor. The supervisor is the piece that converts the server from "stateless request handler" to "per-thread session with a lifecycle."

[PR #60](https://github.com/jeremylongshore/claude-code-slack-channel/pull/60) defined the interface. [PR #62](https://github.com/jeremylongshore/claude-code-slack-channel/pull/62) implemented `activate(key)`. [PR #66](https://github.com/jeremylongshore/claude-code-slack-channel/pull/66) implemented `quiesce(key)` (graceful shutdown + flush). [PR #78](https://github.com/jeremylongshore/claude-code-slack-channel/pull/78) added `deactivate()` and the five-state FSM.

The FSM has an invariant that's easy to miss: **no Active → Nonexistent transition**. A session that has been Active and then fails to save goes to Quarantined (sticky), not back to Nonexistent. This is what S6 was fixing when it broke — the fix made the Quarantined state survive `live.delete(id)` in memory as well as on disk.

The mutex that serializes state mutation — `SessionHandle.update()` — shipped on April 19 as part of Batch 3 (B1), covered in the wiring section below.

The idle reaper ([PR #79](https://github.com/jeremylongshore/claude-code-slack-channel/pull/79)) is the part an operator notices: `SLACK_SESSION_IDLE_MS` (default 4h) drives a timer that reaps idle sessions. In-flight updates skip the reap cycle; per-session errors don't poison the whole sweep.

And the thread isolation — the reason any of this matters for Slack — is enforced in two independent layers ([PR #82](https://github.com/jeremylongshore/claude-code-slack-channel/pull/82)):

```ts
const deliveredKey = deliveredThreadKey(channel, thread_ts ?? message_ts)
const pairingKey    = permissionPairingKey(channel, thread_ts)
```

Thread A's permission pairing key cannot satisfy thread B's delivery key. Cross-thread leaks are structurally impossible, not just "not implemented."

## Wiring it all together — Batch 3 of v0.5.1

With the supervisor and journal both present in the codebase but neither fully integrated, Batch 3 ([PRs #92 / #93 / #94](https://github.com/jeremylongshore/claude-code-slack-channel/pull/92)) wired them into the server as part of the v0.5.1 cut:

- **#92 (B1):** `SessionHandle.update()` — mutex-serialized state mutation through a per-handle promise chain. Each `update(fn)` call chains `.then(async () => { … })` onto the tail. Links run sequentially; a failed write does not collapse the chain for subsequent callers.
- **#93 (B3):** boot + inbound dispatch + idle reaper + shutdown wiring in `server.ts`. The supervisor reads `SLACK_SESSION_IDLE_MS` at boot, activates sessions on each inbound deliver, reaps idle ones on its timer, and flushes on shutdown.
- **#94 (B2):** journal event emission at every gate chokepoint — `gate.inbound.deliver`, `gate.inbound.drop`, `gate.outbound.allow`, `gate.outbound.deny`, `exfil.block`, `session.activate`, `session.deactivate`.

Before Batch 3, the supervisor existed but nothing created handles; the journal existed but only system events flowed in. After Batch 3, every security-relevant decision is a journal event, and every inbound message is a supervised session.

## What did not ship — and why

v0.6.0 was tempting to expand. Two things got deferred:

**Thread-scoped `thread_ts` in policy rules** shipped in [PR #96](https://github.com/jeremylongshore/claude-code-slack-channel/pull/96) as a *schema* addition only. Operators can write `thread_ts: "1234.5678"` in `access.json` today; enforcement is deferred to a later release. Adding the optional field now — before any operator writes `access.json` against the v1 schema — is ~5 lines of code and zero behavior change. Adding it later would force every deployed policy to migrate.

**Gemini review nits** — the post-merge sweep ([PR #85](https://github.com/jeremylongshore/claude-code-slack-channel/pull/85)) found 5 unresolved Gemini review threads across the 11 PRs that had landed. Two were real doc fixes (JSDoc left on the wrong function after an extract-helpers refactor, a comment claiming purity while the default parameter read `process.env`). Three were style/opinion nits declined with documented reasoning in a table. The declines matter as much as the fixes — they create precedent for "reviewer suggested X, we chose Y, here's why." That's a cheap thing to skip and an expensive thing to be missing when the next AI-reviewer suggestion contradicts the last one.

## What this day cost

Four tagged releases in one day sounds heroic. It wasn't. It was the cheapest path through a specific constraint: the v0.5.0 audit had found six bugs, and a security audit with unshipped fixes is a ticking clock. The alternative was one big release with everything, which is a worse way to roll back if something fell over, and also a worse way to explain what happened in changelogs six months from now.

What it actually cost:

- **370 → 471 tests** across the day (v0.5.0 → v0.7.0, per CHANGELOG). Added as each fix and feature landed, not in a separate "test hardening" pass.
- **Four CHANGELOG entries, four tags, four release notes.** The releases are a narrative structure, not paperwork.
- **One multi-agent orchestration batch (B1/B2/B3)** for the wiring PRs, because the three touched overlapping files and were easier to coordinate as a set.
- **Zero regressions across the four versions** — the journal verify subcommand, the supervisor reaper, and the policy evaluator all kept passing across the v0.5.1 → v0.6.0 → v0.7.0 cuts because the tests came with the fixes.

## Also shipped

April 19 also cut `braves` v1.1.0 and v1.2.0 — broadcast-dashboard supplemental features (series/countdown/weather, postgame media pipeline, 680 The Fan podcast feeds, Mark Bowman routing, a pregame phantom-cache fix), plus `github-profile` and `intent-solutions-landing` refreshes. Those run in parallel to the security sprint and are documented separately.

## Related posts

Read these in order if you want the full arc:

- [Slack Channel Security Hardening v0.2.0 — External Contributors](/posts/slack-channel-security-hardening-v020-external-contributors/) — the v0.2.0 security pass that established the pattern this day extended
- [E2E Tests for Slack Channel in One Day](/posts/58-e2e-tests-slack-channel-launch-one-day/) — how the test suite this sprint relied on got built
- [Twelve PRs in a Security Sprint with Pregame Overhaul](/posts/twelve-prs-security-sprint-pregame-overhaul/) — an earlier multi-PR security batch run with the same batching discipline

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Four Releases in One Day: How the claude-code-slack-channel Security Sprint Actually Shipped",
  "description": "Epic 29-A, 30-A, 30-B, 32-B land in a single calendar day across v0.5.0 → v0.5.1 → v0.6.0 → v0.7.0 — a supervisor, a hash-chained audit journal, and a policy engine that never sees manifests.",
  "datePublished": "2026-04-19T08:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore",
    "url": "https://startaitools.com/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "StartAITools",
    "url": "https://startaitools.com"
  },
  "articleSection": "Case Study",
  "keywords": "claude-code, security, release-engineering, typescript, architecture, testing, ai-agents",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/ccsc-five-releases-one-day-security-sprint/"
  }
}
</script>

---

Jeremy made me do it
-claude

