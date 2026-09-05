---
title: "Claude Code Subagents Load at Session Start, Not at Commit"
description: "Claude Code registers project subagents at session start, so committed agents aren't available until restart. A human caught it, not the system."
date: "2026-09-04"
tags: ["claude-code", "ai-agents", "debugging", "automation", "architecture"]
featured: false
canonical: "https://startaitools.com/posts/project-subagents-load-at-session-start/"
---
Claude Code registers project subagents at session start, not at commit time. On 2026-09-04 that cost nothing and hid everything for most of a day.

On 2026-09-03, eight subagents went into intent-longbox `.claude/agents/`. Intent-longbox is a greenfield multi-tenant comic and trading-card consignment platform, built epic by epic against numbered decision records. The subagent roster was purpose-built:

- longbox-domain-builder, epics E02 and E04, opus
- longbox-security-tenancy-builder, epic E03, opus
- longbox-mobile-builder, epic E05, sonnet
- longbox-resolution-ai-builder, epics E06 and E07, opus
- longbox-valuation-commerce-builder, epics E08 through E11, opus
- longbox-platform-delivery-builder, epics E12 through E15, opus
- longbox-invariant-reviewer, read-only, runs before any code close, opus
- longbox-gate-auditor, read-only, runs before any decision close, opus

Each one carried a model assignment, an effort level, its own doc citations, and a never-close rule. The two auditors carried read-only tool restrictions. The session that built the whole system started before those files were committed. Claude Code's spawnable-types list at session start contained none of the eight. So every dispatch that wanted a project agent spawned `general-purpose` and handed it the project agent's definition to adopt verbatim. Same prompt text, same read-only restrictions on the two auditors, same never-close rule. The behavior was correct. The label was stale. That happened 156 times.

The E00 governance epic closed at 00:41 with a signed `g0-truth-lock` tag and a restorable manifest. Build work on E02, E03 and E04 then ran until 23:31 on Claude Fable 5 1: 108 commits, 42 merged pull requests. A representative slice of what merged:

- **#59** expand-contract migrations, indexes, locking, compatibility, rollback and an architecture gate
- **#60** the outbox runtime: append-only outbox and attempt tables, a poller, a `draft_requested` consumer with a fail-closed guard, and a reconciliation seam
- **#57** the migration-runner role separated from the server role, so no application connection can disable a trigger
- **#54** every append-only trigger hardened to `ENABLE ALWAYS`, read back from `pg_trigger`
- **#66** the public uploads mount deleted, photo previews served through the tenant-scoped API instead
- **#70** every uploaded photo validated, sanitised and metered before it becomes a file
- **#71** the identity substrate: two session chains, a device-bound PIN, one authentication hook
- **#74** a credential's life made a fact: rotation, deletion by refusal, a cost ledger naming who paid
- **#82** TOTP and recovery codes for owner and support roles, AEAD-encrypted secrets, a `key_version` column
- **#87** connector OAuth with least scopes, token lifecycle, consent, uninstall and revocation

Twenty numbered decision-record documents were ratified alongside the code.

The invariant reviewer ran before PR #75 closed and returned a by-tool PASS: typecheck ok, lint ok, depcruise across 83 modules with 0 violations, an architecture gate over 70 files and 8 rules, 1065 of 1065 unit tests at 87.37% lines, 465 integration tests passing with 1 skipped by design, and 11 of 11 required CI checks green on the reviewed commit. That is the agent definition doing its job.

Nothing in the system flagged the naming, because from inside there is nothing to flag. The agent read the right prompt, ran under the right tool limits, and returned the right verdict. The only place the mismatch was visible was the log, and only to someone reading it from outside. An operator did, at 21:45:

"why are we using so lamy general agents dont i have over 400 availble"

"didnt we create specific subagents foe this repo"

The answer was yes to both. The fix was a session restart. No code changed.

The secondary thread that day was claude-code-plugins around 21:41 via Codex on GPT-5.6 Sol. Three bulk Dependabot pull requests got closed (82 version bumps between them, all failing CI), and rather than deleting Dependabot it was reconfigured to security-only. That surfaced the reason the dependency picture had looked quiet: GitHub vulnerability alerts and automated security fixes were disabled on the repository. Re-enabling them read 16 open alerts. Minutes later the inventory finished populating and the settled count was 104: 4 critical, 43 high, 47 medium, 10 low. The first reading was a mid-scan snapshot, wrong by a factor of roughly 6.5. A real high-severity js-yaml denial-of-service fix arrived minutes later as pull request #1446 and was correctly kept, which is the security-only policy behaving as designed. Also in that pass: three human contributors were waiting on replies to earlier maintainer review comments on pull requests #1125, #1380 and #1103. Credit for Steve Harlow's diagnosis was preserved deliberately by inviting him to open the pull request rather than implementing over him.

Session failure arcs also got exercise. A git worktree collision on branch feat/e01-b02-observation-batch (already checked out at a stale `.claude/worktrees/agent-a21f4013acfa1f0e5`). Two exit-128 git failures on stale state (recovered with stash, pull, stash-pop). Several pnpm ELIFECYCLE failures. All contained and resolved. A Buzz verification run confirmed the relay path around 18:15. Intent-os got a debug session around 22:17 on a scorecardecho.com TypeError reading "terminated: other side closed", chased onto the VPS. One comehomealabama journal post landed.

The registry is a snapshot taken at process start. Commit an agent into a running session and the session keeps the list it booted with. That is a checkpoint, not a bug, and the workaround costs nothing because the definition can be pasted into a generic agent and behaves identically. What it costs is the log: for twenty hours the record of who did the work named the wrong thing, and the only detector was a person reading it.

## Related Posts

- [Every Verdict Carries the Scope It Actually Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [When a Gate Should Re-Run the Step Instead of Trusting Its Receipt](https://startaitools.com/posts/stop-trusting-the-stored-claim/)
- [A Path Is Not Proof of Identity](https://startaitools.com/posts/a-path-is-not-proof-of-identity/)
