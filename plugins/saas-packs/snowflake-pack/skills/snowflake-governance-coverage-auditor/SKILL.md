---
name: snowflake-governance-coverage-auditor
description: |
  Audit trusted Snowflake classification, tags, masking, row access, projection,
  join, aggregation, and privacy-policy evidence without reading customer data.
  Use when governance enforcement may be missing or ambiguous. Trigger with
  "Snowflake governance coverage", "policy precedence", "tag policy gaps",
  "classification failure", or "POLICY_CONTEXT verification".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[schema-2-evidence.json]"
model: inherit
effort: high
version: 3.16.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: "Model-neutral; requires Python 3.10+. Optional collection requires Snowflake CLI and an existing least-privilege profile."
tags: [saas, snowflake, governance, classification, masking, row-access, privacy]
---

# Snowflake Governance Coverage Auditor

## Purpose

Compare an owner-approved hashed denominator with trusted schema-2 current
receipts and separately trusted, sanitized `POLICY_CONTEXT` simulations. Missing,
stale, capped, privilege-filtered, unsupported, or context-mismatched evidence is
never a pass; the result distinguishes observable coverage from evidence gaps
without exposing governed data or claiming compliance.

Read [the input contract](references/input-contract.md) and
[the source notes](references/source-notes.md) before assembling evidence.

## Prerequisites

Use Python 3.10+, an owner-approved hashed denominator, and an existing Snowflake
CLI read-only profile. Establish independent evidence and policy trust boundaries
before analysis; do not accept credentials, raw identifiers, policy text, tag
values, customer rows, or ad hoc SQL.

## Workflow

1. Have the governance owner approve the exact asset and simulation denominator.
2. Collect one classification receipt per database and one tag plus one policy
   receipt per governed object. Use fixed unquoted selectors only:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface governance-classification-current --connection readonly-observer \
     --governance-database GOVERNED_DB --output ./classification.json

   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface governance-tags-current --connection readonly-observer \
     --governance-object GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE \
     --governance-domain TABLE --output ./tags.json

   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface governance-policies-current --connection readonly-observer \
     --governance-object GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE \
     --governance-domain TABLE --output ./policies.json
   ```

3. Independently verify the collection role's complete visibility over exactly
   those hashes and produce the scope receipt. Execute the approved
   `POLICY_CONTEXT` cases outside this collector; retain only the strict hash-only
   receipt contract. Never add `EXECUTE USING` to the shared collector.
4. Record evidence and policy digests at their independent trusted boundaries:

   ```bash
   # Record only at trusted local boundaries.
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_governance.py" evidence.json \
     --print-input-sha256
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_governance.py" evidence.json \
     --policy-file policy.json --print-policy-sha256
   ```

5. Analyze only with the previously recorded digests and policy-bound clock:

   ```bash
   # Replace the quoted placeholder with the owner-policy timestamp.
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_governance.py" evidence.json \
     --policy-file policy.json --evaluated-at "YYYY-MM-DDTHH:MM:SSZ" \
     --trusted-input-sha256 sha256:RECORDED_EVIDENCE_DIGEST \
     --trusted-policy-sha256 sha256:RECORDED_POLICY_DIGEST --pretty
   ```

Recomputing a digest from suspect evidence is not trust. Preserve every finding,
precedence observation, non-claim, and the dry-run remediation packet.

## Decision boundaries

- Unknown or Standard edition, unverified preview support, missing scope proof,
  role filtering, caps, duplicates, mixed contexts, or stale receipts suppress a
  positive bounded result.
- Account Usage classification is latency-bounded observation. A newer failed
  attempt, absent profile-scope proof, non-current status, or stale success is a
  gap. `CREATE OR REPLACE` profile operations can detach automatic
  classification and must be reviewed separately.
- Direct policy assignments take precedence over tag assignments. For aggregation
  policies, a direct assignment shadows a tag assignment only for the same entity
  keys; different entity-key sets remain cumulative.
- Any relevant non-`ACTIVE` provider status, including a missing conditional
  masking secondary argument, is a gap.
- Row access evaluates before masking. Projection applies to final output only;
  it is not proof against inner-query or `WHERE` exposure.
- Tag-based masking is generally available. Tag-based row access, projection,
  join, and aggregation require explicit owner-attested preview support.
- Privacy-policy combinations with masking, aggregation, or projection remain a
  blocked design review even when assignment succeeds.
- Every owner-approved sanitized simulation for each asset/control pair is
  cumulative; any mismatch or error blocks coverage. Each role, context,
  query-shape, expected outcome, account, and trusted input digest must match.

## Output

The collector uses reviewed `SELECT` statements only; it does not execute
`POLICY_CONTEXT`, mutation SQL, shell payloads, or network operations. Receipts and
reports contain only organization/account-scoped hashes, fixed enums, timestamps,
counts, and booleans. Never collect policy bodies, tag values, names, customer
rows, SQL text, errors, secrets, or query results. Exit `2` is a fixed generic
invalid-evidence error and never reflects rejected input.

Every remediation item has `mutation_sql: null` and
`requires_separate_authorization: true`. The skill never applies tags, policies,
profiles, grants, feature flags, or edition changes.

## Error Handling

Exit `2` means the evidence, policy, trust digest, freshness, context, cap, or
schema check failed. The fixed error intentionally omits rejected values. Recheck
the independent denominator and recollect; never infer health or escalate roles.

## Example

An inherited required tag plus one ACTIVE applicable policy and a matching
simulation can support bounded coverage. A missing secondary masking argument,
newer failed classification attempt, unverified preview, or missing scope receipt
produces a fixed hash-scoped gap and a non-executable remediation item.

## Resources

- [Current-state and trust boundary](references/current-state.md)
- [Input and receipt contract](references/input-contract.md)
- [Read-only boundaries](references/privilege-and-boundaries.md)
- [Primary-source notes](references/source-notes.md)
- [Snowflake POLICY_REFERENCES](https://docs.snowflake.com/en/sql-reference/functions/policy_references)
