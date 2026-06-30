# Merge Enablement

Use this guide before new outreach when Hermes Tweet has open external PRs to
keep merge blockers visible and repairable.

## Complete PR Coverage

Enumerate every open in-scope PR before discovery or outreach. Do not treat a
single capped GitHub CLI result as complete. Use paginated GraphQL or search API
queries, then shard any capped result by author, head owner, base repository,
keyword family, updated date, and state until each shard is below the platform
cap.

Write the raw enumeration and audit evidence to distinctive temporary files:

- `/tmp/hermes-tweet-open-prs-<timestamp>.json`
- `/tmp/hermes-tweet-pr-audit-<timestamp>.jsonl`

Treat missing pages, partial JSON, API errors, rate limits, or ambiguous caps as
incomplete coverage. Continue sharding or retrying until the audit is complete.
Validate shard syntax against a known-positive control, such as the own-repo open
PR list or a tracked open Hermes Tweet PR URL. If a shard unexpectedly returns
zero while the control proves open PRs exist, record the failed syntax and rerun
with explicit GitHub search flags or GraphQL variables before treating the shard
as empty.

## Shard Budget Guard

Start with exact Hermes Tweet and Hermes Agent shards plus the tracked PR set
before adding broad keyword families. Generic all-author or `xquik`, `tweet`, and
`twitter` shards can match unrelated social-agent work across GitHub and burn API
budget without improving in-scope coverage.

If a shard expands into hundreds of endpoint reads, stop it, save a summary with
`complete: false`, the reason, and the attempted query family, then rerun with
narrower exact terms or date-windowed shards. Never treat an aborted broad run as
coverage proof, even when a later bounded audit succeeds.
Keep capped broad-shard URLs out of the canonical audit set. Store them as
failed evidence only, then rebuild the canonical set from uncapped exact Hermes
Tweet or Hermes Agent shards.

## Per-PR Audit

For each canonical PR URL, read:

- mergeability and conflict status
- status checks and commit statuses
- review decisions and actionable review comments
- unresolved review threads where GitHub exposes them
- comments from maintainers and review bots
- head branch owner, fork owner, and branch drift

Repair controllable blockers only through verified `kriptoburak` branches. If a
blocker is target-side, such as maintainer-only checks, account-credit failures,
missing required contexts, or unavailable CI logs, record the evidence and avoid
inventing code changes.
When a dirty PR uses a third-party fork or a head owner other than
`kriptoburak`, treat the conflict as non-controllable even when GitHub reports
`maintainerCanModify`. Record the head owner and conflict state, then continue
without pushing to that fork.

Treat aggregate `UNKNOWN` mergeability as unhandled until a direct PR read
confirms the current state. If that direct read reports `DIRTY` or
`CONFLICTING` on a verified `kriptoburak` head branch, repair the branch before
discovery. If the head branch is not controlled, record the owner, the conflict
state, and the target-side evidence instead of attempting a repair.

## Outreach Gate

Open a fresh external PR only after every in-scope open PR is either clean,
repaired, or recorded as target-side blocked. If no eligible external route
survives crawler-first discovery and direct checks, use an own-repo fallback PR
that improves future discovery, validation, submission readiness, safety checks,
or merge enablement.
Do not count a prepared fork branch as outreach. If GitHub rejects PR creation,
record the API error, keep the branch as proof only, and continue with another
eligible route or an own-repo fallback PR.

When a candidate's duplicate PR search is rate-limited or otherwise incomplete,
record the failed query and do not treat the target as eligible. Continue only
when the target is already rejected on independent native-fit grounds, such as
MCP-only registries, product-owned skill taps, or single-product plugin repos.
