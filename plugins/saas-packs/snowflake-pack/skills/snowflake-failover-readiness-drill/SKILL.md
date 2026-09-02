---
name: snowflake-failover-readiness-drill
description: |
  Assess Snowflake replication and failover-group readiness without performing
  a refresh, promotion, redirect, cancellation, resume, failover, or failback.
  Use when defining RPO/RTO, preparing or reviewing a Business Critical disaster-
  recovery exercise, diagnosing replication history, checking cross-group object
  dependencies, or verifying an operator-executed failover/failback receipt.
  Produces a deterministic readiness verdict, evidence gaps, abort gates, and an
  operator runbook boundary. Trigger with "Snowflake failover drill", "replication
  group RPO", "secondary refresh failed", "account failover", "failback proof",
  or "client redirect validation".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[redacted-evidence.json]"
version: 3.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, disaster-recovery, failover, replication, rpo, rto]
---

# Snowflake Failover Readiness Drill

## Purpose

Turn a declared recovery objective and redacted Snowflake evidence into a
reproducible readiness decision. The skill evaluates what is observable; it never
performs a control-plane change, and it treats database/share replication as
distinct from Business Critical account failover/failback.

## Safety boundary

- Never run `ALTER ... REFRESH`, `PRIMARY`, `FAILOVER`, `FAILBACK`, redirect,
  suspend/resume, cancellation, or any other mutating command.
- Never infer readiness from a successful login or one green refresh.
- Never collect credentials, SQL text, customer rows, presigned URLs, or secrets.
- Treat Account Usage as historical evidence that can lag by three hours. Use
  approved near-live Information Schema evidence at the operator decision point.
- Keep promotion and failback as explicit human-controlled change windows with
  named owners, abort conditions, and rollback/forward-fix steps.

## Prerequisites

- Python 3.10+ and a redacted JSON evidence file matching the contract below.
- Explicit account/region scope, in-scope failover groups and applications,
  objective owners, positive RPO/RTO values, and a timezone-aware `as_of`.
- For live collection, an existing least-privilege Snowflake CLI profile. The
  skill neither accepts nor configures credentials.
- Business Critical Edition or higher for account-object failover/failback. A
  lower or unknown edition yields a bounded blocker rather than an upgrade action.

## Workflow

1. Declare `as_of`, mode, edition, target RPO/RTO, in-scope groups, applications,
   and required object classes. No denominator means no readiness claim.
2. Collect historical replication evidence with the model-neutral collector:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface replication --connection readonly-observer \
     --output ./snowflake-replication-evidence.json
   ```

   A receipt with `truncation_possible: true` cannot prove complete refresh
   history; narrow or partition the window before a readiness verdict. The
   receipt must match the exact vendored SQL hash and contain history for every
   in-scope group; an absent group remains `INCONCLUSIVE`, never healthy.

3. Add operator-reviewed near-live group state, membership, dependencies, object
   checks, target validation, privileges, client redirect proof, and drill events
   to the input contract in
   [`references/evidence-contract.md`](references/evidence-contract.md).
4. Run the deterministic classifier:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_failover_readiness.py" \
     --input ./snowflake-failover-readiness.json \
     --output ./snowflake-failover-readiness-report.json
   ```

5. Stop on `NOT_READY` or `INCONCLUSIVE`. Resolve the named evidence gap or
   readiness defect and collect a new receipt. `READY_FOR_OPERATOR_DRILL` permits
   planning an approved exercise; it does not authorize one.
6. `FAILOVER_VERIFIED` requires a separately operator-executed failover plus
   successful target validations. `DRILL_VERIFIED` additionally requires an
   operator-executed failback and post-failback validation.

## Required review surfaces

- Edition and group capability; primary/secondary membership and suspension.
- Refresh phase/error, last successful refresh, RPO, scheduled interval, and
  detailed-history retention.
- RTO objective and measured operator drill duration.
- Cross-group/dangling dependencies; task/stream split and task ownership;
  stale, duplicate, or time-travel stream risk; dynamic-table reinitialization.
- Target data/application invariants, client redirection, and least-privilege
  evidence for both source and target accounts.

## Output

Report `status`, `mode`, objective summary, sorted findings, `non_claims`, and a
SHA-256 receipt. Classify evidence as observed, derived, or missing. Never turn a
missing row, permission failure, stale Account Usage result, or login success into
a positive readiness claim.

## References

- [`references/evidence-contract.md`](references/evidence-contract.md) — strict
  input schema, status logic, and operator boundary.
- [`references/source-notes.md`](references/source-notes.md) — primary Snowflake
  sources and freshness/edition constraints to re-check at execution time.
- `scripts/collect_snowflake_evidence.py` — bundled read-only collector and
  receipt implementation; each installed skill carries the executable code.

## Error Handling

Malformed JSON, invalid modes, naive timestamps, future evidence, non-positive
objectives, secret-bearing fields, raw rows, SQL text, PII, or presigned URLs exit
with code 2 and no partial report. A missing group denominator, stale history,
missing target invariants, or insufficient visibility stays in the report as
`INCONCLUSIVE`; correct the evidence and rerun. A Snowflake permission failure is
not authorization to escalate to `ACCOUNTADMIN`.

## Examples

If the last successful refresh is 95 minutes old against a 60-minute RPO, report
`RPO_BREACH` and `NOT_READY`; do not propose an automatic refresh. If a clean
preflight has current history and passing target invariants, report only
`READY_FOR_OPERATOR_DRILL`. After an approved operator supplies successful
failover and failback events plus passing validations within RTO, the report may
be `DRILL_VERIFIED`; successful login alone cannot produce that verdict.
