---
name: snowflake-failover-readiness-drill
description: |
  Analyze Snowflake failover-group RPO/RTO readiness from independently trusted,
  privacy-preserving live receipts without executing refresh, failover, failback,
  redirect, cancellation, resume, or session changes. Use when an owner needs a
  Business Critical disaster-recovery preflight, replication failure diagnosis,
  dangling-reference check, or operator-executed drill proof. Trigger with "Snowflake
  failover drill", "replication RPO", "failback proof", or "secondary refresh".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[schema-2-evidence.json]"
version: 3.16.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, disaster-recovery, failover, replication, rpo, rto]
---

# Snowflake Failover Readiness Drill

## Purpose

Produces a deterministic readiness or attestation result from exact,
independently trusted evidence. It observes and verifies but never performs or
authorizes a Snowflake control-plane change.

## Prerequisites

- Python 3.10+ and this complete skill directory, including its reviewed SQL.
- An owner-approved scope and separately retained digests for policy, collection,
  and operator/validation evidence.
- Existing least-privilege Snowflake CLI profiles in source and target accounts
  when live collection is required. Profiles used for Information Schema history,
  progress, or dangling functions must select an approved current database; the
  skill does not configure authentication or session state.
- Business Critical Edition or higher for failover groups.

## Workflow

1. Have the recovery owner approve an exact policy containing every in-scope
   group, dependency, validation, RPO, and RTO. Record its digest at a trusted
   boundary before evidence is transported.
2. Collect `replication-current` in both source and target accounts. Collect
   `replication` and `replication-progress` in each target account over the same
   current, explicit half-open UTC window. A full failback drill also requires
   both surfaces in the original source account to prove the reverse refresh leg.
   Collect `replication-dangling` in both accounts for every in-scope local group.
3. Build the exact schema-2 wrapper in
   [`references/evidence-contract.md`](references/evidence-contract.md). Record
   independent digests for the collector bundle, policy, and operator/validation
   receipts. A digest recomputed from the delivered file is not independent.
4. Run the analyzer; it writes only to stdout:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_failover_readiness.py" \
     --input ./snowflake-failover-evidence.json \
     --evaluated-at "$EVALUATED_AT_UTC" \
     --trusted-input-sha256 sha256:... \
     --trusted-policy-sha256 sha256:... \
     --trusted-operator-sha256 sha256:... \
     > ./snowflake-failover-report.json
   ```

An `INCONCLUSIVE` or `NOT_READY` exit is `1`; malformed input exits `2`.

## Collection pattern

Use an existing least-privilege Snowflake CLI profile. Never pass credentials to
the collector and never switch to `ACCOUNTADMIN` because evidence is missing.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface replication-current --connection source-observer \
  --output ./source-current.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface replication --connection target-observer \
  --window-start "$WINDOW_START_UTC" --window-end "$WINDOW_END_UTC" \
  --output ./target-history.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface replication-progress --connection target-observer \
  --window-start "$WINDOW_START_UTC" --window-end "$WINDOW_END_UTC" \
  --output ./target-progress.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface replication-dangling --connection source-observer \
  --replication-group DR_CORE --output ./source-dangling.json
```

The group selector is validated locally and hashed inside Snowflake. Raw account,
group, role, owner, object, and dependency identifiers are not emitted. Every
receipt is live-only schema 2, no older than 15 minutes at evaluation, capped at
5,000 rows, and invalid if the cap is reached. History/progress window ends must
be at or before and within 60 seconds of collection start, no more than 15
minutes behind evaluation, and identical for the paired receipts in an account.

## Modes and proof

- `PREFLIGHT`: one current snapshot per source and target account, no operator
  events, and passing `PRE_FAILOVER` validations. A clean result is only
  `READY_FOR_OPERATOR_DRILL_AS_OF`.
- `FAILOVER_ATTESTATION`: before/after current snapshots, one successful scoped
  failover receipt per group, and passing pre/post validations. A clean result is
  `FAILOVER_ATTESTED_AS_OF`.
- `FULL_DRILL_ATTESTATION`: before/middle/after current snapshots, ordered
  successful failover then failback receipts, and passing validations at all
  three stages. A clean result is `FULL_DRILL_ATTESTED_AS_OF`.

RPO age is `evaluated_at - PRIMARY_SNAPSHOT_TIMESTAMP` from the latest refresh
job for preflight, or `transition_started_at - PRIMARY_SNAPSHOT_TIMESTAMP` for
each directional drill leg, only when that job has exactly one `COMPLETED`
terminal phase and exactly one snapshot timestamp. Refresh end time, schedule
time, and login success are never substitutes. RTO comes only from trusted
operator event start/completion times.

## Non-negotiable safety boundary

- Never run refresh, promotion, failover, failback, redirect, suspend/resume,
  cancel/abort, role switching, or session mutation.
- Never treat a self-checksum as provenance. Require all three separately
  supplied trusted digests.
- Never shrink a denominator after collection. Exact group, dependency, and
  validation counts are part of policy.
- Never treat missing, stale, permission-filtered, malformed, duplicated, or
  capped evidence as healthy.
- Never echo attacker-controlled raw identifiers or provider messages. Findings
  expose finite codes and hashed scopes only.
- Keep every actual transition in a separately approved human change window.

## References

- [`references/evidence-contract.md`](references/evidence-contract.md) — exact
  wrapper, policy, receipt coverage, trust, and verdict rules.
- [`references/source-notes.md`](references/source-notes.md) — official Snowflake
  semantics and operational caveats.

Use the `Read` tool to inspect both references before evaluating production
evidence; they are part of the contract, not optional background.

## Output

The analyzer emits one JSON report to stdout with the overall status, integrity
and coverage states, finite findings, RPO results, the three computed trust
digests, admitted receipt hashes, conservative non-claims, and a deterministic
report digest. It never copies collector, operator, or validation rows into the
report.

## Error handling

Stop and recollect on schema, digest, freshness, source, query-template, row,
count, cap, selector, or authorization-context errors. Stop on a failed/canceled
latest refresh, incomplete progress, RPO/RTO breach, suspended/unconfigured
secondary schedule, blocking dangling reference, missing dependency ordering
proof, stale validation, failed validation, unrestored final-secondary schedule,
or unproved transition. A warning-only nonblocking
dangling reference yields `AT_RISK`; it is never silently accepted.

## Examples

- A snapshot exactly 3,600 seconds old against a 3,600-second RPO passes; one
  second older yields `RPO_BREACH` and `NOT_READY`.
- A recent successful refresh does not override a newer failed job or incomplete
  progress; the latest refresh remains unproved.
- A caller-authored `SUCCEEDED` event with a recomputed self-hash cannot produce
  an attested result when the independent operator digest does not match.
- A complete preflight produces `READY_FOR_OPERATOR_DRILL_AS_OF`, never
  `FULL_DRILL_ATTESTED_AS_OF`; that requires ordered operator failover and failback
  receipts plus before/middle/after state observations and passing validations.
