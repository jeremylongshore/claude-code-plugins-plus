---
name: snowflake-data-quality-sentinel
description: |
  Assess trusted Snowflake data metric function coverage and expectation evidence
  without reading customer rows. Use when evaluations, definitions, schedules,
  notifications, anomaly state, or monitoring coverage may be incomplete or
  unhealthy. Trigger with "Snowflake data quality", "DMF expectation",
  "definition drift", "missing evaluation", or "notification gap".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[schema-2-evidence.json]"
model: inherit
effort: high
version: 3.16.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: "Model-neutral; requires Python 3.10+. Optional collection requires Snowflake CLI with an existing read-only profile."
tags: [saas, snowflake, data-quality, governance, observability, incident-response]
---

# Snowflake Data Quality Sentinel

## Purpose

Produce separate configuration, history-observation, and history-completeness
verdicts from an owner-approved requirement denominator and trusted schema-2
collector receipts. Missing or untrusted evidence never becomes a pass, and this
history surface never supports an unqualified present-tense quality pass.

Read [the input contract](references/input-contract.md) before assembly and consult
[the source notes](references/source-notes.md) when interpreting provider semantics.

## Prerequisites

Use Python 3.10+, an owner-approved policy, and Snowflake CLI with an existing
least-privilege profile. Never accept credentials or request customer rows,
failed-row payloads, metric values, or SQL text.

## Workflow

1. Collect the exact per-object receipt set.
2. Record independently trusted evidence and owner-policy digests.
3. Analyze at the policy-bound time and preserve every non-claim.

### Step 1: Collect evidence

Collect one bounded history receipt. For every distinct governed object, collect
one selector-bound live association receipt and one selector-bound live
expectation receipt. Also collect one notification receipt for every distinct
governed object whose `notification_required` is true:

```bash
# Example fixed UTC window; replace with the audited interval.
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface data-quality --connection readonly-observer \
  --window-start 2026-09-01T00:00:00Z --window-end 2026-09-02T00:00:00Z \
  --output ./dq-history.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface data-quality-associations-current --connection readonly-observer \
  --data-quality-object GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE \
  --data-quality-domain TABLE \
  --output ./dq-associations.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface data-quality-expectations-current --connection readonly-observer \
  --data-quality-object GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE \
  --data-quality-domain TABLE \
  --output ./dq-expectations.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface data-quality-notification-current --connection readonly-observer \
  --data-quality-object GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE \
  --data-quality-domain TABLE --output ./dq-notification.json
```

The object selector is used only in reviewed local SQL. The receipt retains its
scoped object hash and domain, never the raw selector. Do not escalate roles when
a source is permission-blocked.

### Step 2: Establish trust and analyze

Maintain the owner-approved policy as a separate `policy.json`. Assemble exactly
`schema_version`, the byte-equivalent parsed policy, and `collector_receipts` in
the evidence wrapper. Record the evidence and policy digests independently when
each crosses its trusted local boundary. The embedded receipt checksums are not
trust anchors.

```bash
# Record these at their independent trusted local boundaries.
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_data_quality.py" evidence.json \
  --print-input-sha256
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_data_quality.py" \
  --policy-file policy.json --print-policy-sha256

python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_data_quality.py" evidence.json \
  --policy-file policy.json \
  --evaluated-at 2026-09-03T12:00:00Z \
  --trusted-input-sha256 sha256:RECORD_FROM_EVIDENCE_BOUNDARY \
  --trusted-policy-sha256 sha256:RECORD_FROM_POLICY_BOUNDARY --pretty
```

Supplying digests recomputed from an already suspect file does not establish
trust. The policy's `analysis_as_of_utc` must equal `--evaluated-at`, preventing a
trusted old policy from being replayed against a shifted clock.

### Step 3: Interpret the result

Preserve `configuration_status`, `history_observation_status`,
`history_completeness_status`, every finding code and hashed scope, evidence
integrity and coverage, the evaluated denominator, receipt hashes, and fixed
non-claims. Do not convert an inconclusive result or satisfied observation into
operational approval. If remediation would mutate Snowflake, produce a dry-run
proposal and obtain separate authorization.

## Decision boundaries

- `EXPECTATION_VIOLATED=false` is `SATISFIED_OBSERVATION`, never quality `PASS`.
  Snowflake publishes no finality SLA for the history surface, so
  `history_completeness_status` remains `UNPROVEN_NO_PROVIDER_SLA`,
  `pass_supported` remains false, and `settled_through_utc` remains null.
- No matching result is `DQ_NO_EVALUATION`, not a pass. `true` is a violation;
  null is an evaluation failure.
- Definition, schedule, role, filter, object-domain, grouping, or group-limit drift
  blocks a healthy verdict.
- Trigger-on-change freshness and grouped-result completeness remain inconclusive
  until separately reviewed evidence proves them.
- Anomaly objectives remain inconclusive until a separate trusted anomaly surface
  exists. Do not infer anomaly health from association configuration.
- Notification `ENABLED` proves configuration only. Delivery always remains
  `NOT_OBSERVED`; missing visibility differs from disabled configuration.
- One association-surface receipt and one expectation-surface receipt must cover
  every distinct governed object exactly. Multiple expectations may share an association, but the
  `(association_key_sha256, expectation_key_sha256)` policy key is unique.
- Missing surfaces, stale or mixed contexts, caps, truncation, invalid schemas,
  duplicates, offline receipts, or either trust mismatch suppress classification.

## Output

The report includes the three status axes, `pass_supported`,
`settled_through_utc`, integrity and coverage, denominator counts, deterministic
findings, safe provenance, fixed non-claims, and `report_sha256`. Findings contain
fixed text and validated requirement hashes only.

## Error Handling

- Exit `2` is a fixed generic malformed-input error and never reflects rejected input.
- `evidence_integrity_status=INVALID` means a trust or receipt check failed; recollect.
- `evidence_complete` remains false because history completeness is not provider-proven.
- Permission-filtered notification evidence is a visibility gap, not proof of disabled configuration.
- Edition or privilege failures do not authorize automatic role escalation.

## Example

False produces `SATISFIED_OBSERVATION`, while a missing row produces
`DQ_NO_EVALUATION`; neither produces quality `PASS`. A true row produces
`VIOLATION_OBSERVED` and quality `FAIL`.

## Safety

The analyzer and collector are read-only. A remediation request ends at a dry-run
change proposal unless the caller separately authorizes mutation. Findings use
validated requirement hashes as scopes and fixed text, so rejected receipt fields
or values are never reflected into output.

## Resources

- [Schema-2 input contract](references/input-contract.md)
- [Primary-source semantics and latency](references/source-notes.md)
- [Snowflake data-quality monitoring](https://docs.snowflake.com/en/user-guide/data-quality-intro)
