---
name: snowflake-governance-coverage-auditor
description: |
  Audit whether a declared Snowflake sensitive-asset denominator has effective
  classification, tags, and masking, row-access, projection, join, or aggregation
  policy coverage. Resolve direct-versus-tag precedence, classification failures,
  evidence visibility, edition/preview limits, and POLICY_CONTEXT dry-run proof.
  Use when a governance dashboard's coverage claim needs independent evidence or
  sensitive Snowflake assets may be unprotected. Trigger with phrases like
  "Snowflake governance coverage", "find unprotected sensitive columns",
  "audit Snowflake policies", or "verify tag-based policy coverage".
allowed-tools: Read, Write, Bash(python3:*)
argument-hint: "[sanitized-governance-evidence.json]"
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake session for operator-run read-only evidence collection
tags: [saas, snowflake, governance, security, privacy, policy-audit]
---

# Snowflake Governance Coverage Auditor

## Overview

Measure protection against an explicit sensitive-asset denominator. The
deterministic analyzer distinguishes effective coverage from merely present
metadata, emits a dry-run remediation packet, and never connects to Snowflake,
inspects data values, or mutates tags, policies, tables, or views.

This is not an RBAC audit. Use `snowflake-access-guardian` for role and grant
paths. Use this skill when the question is whether known sensitive assets are
classified and protected by the expected data-governance controls.

## Prerequisites

- A sanitized denominator whose asset identities are opaque keys, not database,
  schema, table, column, tag-value, or policy names.
- Bounded receipts for the denominator, `TAG_REFERENCES`, `POLICY_REFERENCES`,
  and `DATA_CLASSIFICATION_LATEST`, including freshness, truncation, query hash,
  and visibility scope.
- Account edition and explicit preview-feature state. Absence of that evidence
  blocks support claims.
- Python 3.10+. The offline analyzer uses only the standard library.

Read [evidence-contract.md](references/evidence-contract.md) before constructing
the bundle. Read [precedence-and-platform-bounds.md](references/precedence-and-platform-bounds.md)
when direct and tag-based assignments coexist or preview/privilege limits apply.

## Authentication

The analyzer has no network or authentication flow. If an operator collects
Snowflake evidence, use an existing organization-approved read-only session.
Do not put passwords, tokens, keys, connection strings, raw tag values, policy
bodies, object names, or data samples in the bundle. A role with partial
metadata visibility produces a partial receipt, not a clean bill of health.

## Safety contract

- Run only the bundled offline analyzer. The SQL files are read-only collection
  templates for an authorized operator; validate every substitution token before use.
- Never execute or emit `ALTER`, `CREATE`, `DROP`, `SET TAG`, or policy-assignment
  SQL. The remediation packet describes gaps and prechecks, with `mutation_sql`
  fixed to null.
- Never equate no row with no protection. `TAG_REFERENCES` and
  `POLICY_REFERENCES` can be privilege-filtered; Account Usage is delayed.
- Never label classification pending, failed, stale, or absent as current.
- Never treat a tag as a policy. Coverage requires an active effective policy
  of each control type declared by the denominator.

## Workflow

1. Define the denominator and required controls per opaque asset key. Do not
   infer the denominator from already-tagged objects; doing so makes missing
   coverage invisible.
2. Collect only bounded metadata with the deterministic collector and the rules
   in [collection-and-dry-run.md](references/collection-and-dry-run.md). It
   renders the bundled template, executes it through an existing Snowflake CLI
   profile, normalizes opaque rows, and seals the dataset-bound receipt. Resolve
   `snowflake_skill_dir` to the directory containing this `SKILL.md`:

   ```bash
   # Example per-query cap; partition larger inventories.
   snowflake_skill_dir=/path/to/snowflake-governance-coverage-auditor
   python3 "${snowflake_skill_dir}/scripts/collect_governance_evidence.py" \
     --surface tag_references --database ANALYTICS --row-limit 1000 \
     --connection readonly --privilege-scope COMPLETE \
     --output ./snowflake-tags-envelope.json
   ```

   Use `--input-json` to normalize saved Snowflake CLI `JSON_EXT` instead of
   connecting. Denominator collection requires a sanitized `--requirements`
   file. Complete join-policy evidence requires the restricted
   `--object-manifest` current-policy path. Record `COMPLETE`, `PARTIAL`, or
   `UNKNOWN` visibility honestly.
3. Merge each collector envelope's `dataset` into its matching analyzer array
   and its `receipt` under the matching receipt key. Do not edit either after
   collection; row count, dataset hash, template hash, rendered SQL hash,
   source, safe selector fingerprint, and canonical receipt hash are verified.
   `TAG_REFERENCES` Account Usage rows are direct assignments only; inherited
   resolution needs separately bounded Information Schema evidence.
4. Run the analyzer:

   ```bash
   snowflake_skill_dir=/path/to/snowflake-governance-coverage-auditor
   python3 "${snowflake_skill_dir}/scripts/analyze_governance_coverage.py" \
     --input ./snowflake-governance-evidence.json \
     --out ./snowflake-governance-coverage-report.json
   ```

   Use `Read` to inspect the JSON evidence and report. Use `Write` only to save
   a sanitized report or approved dry-run packet.
5. Review `precedence`, `coverage`, and `receipts`. For the same policy type, a
   direct assignment takes precedence over a tag-based assignment. Aggregation
   policies are the exception: assignments with different entity-key sets are
   cumulative; an equal entity-key set is shadowed by the direct assignment.
6. Under an approved Snowflake session, design a minimal `POLICY_CONTEXT`
   simulation for each affected role/context and record only its sanitized
   pass/fail receipt. The function is diagnostic, but its query can expose data
   if poorly designed. Follow the privilege and output rules in the dry-run guide.
7. Hand the dry-run packet to the policy owner. Any actual classification, tag,
   or policy change is a separate authorized workflow with its own rollback.

## Decision rules

- `VERIFIED` requires all core receipts to be fresh, untruncated, integrity
  checked, and marked with complete privilege scope; every denominator asset
  must pass required tag/classification/control checks; each controlled asset
  must also have a fresh passing `POLICY_CONTEXT` scenario.
- A non-`ACTIVE` `POLICY_STATUS` is misconfiguration, not protection.
- A direct policy shadows same-type tag policies, except aggregation policies
  with different entity-key sets, which are both enforced.
- Tag-based row-access, projection, join, and aggregation policies are preview
  capabilities and require explicit enabled-feature evidence. Enterprise-or-
  higher bounds are enforced for governance coverage claims.
- Missing, stale, truncated, privilege-filtered, unsupported, or preview-unknown
  evidence yields `NOT_PROVEN`.

## Output

The JSON report contains a canonical input SHA-256, denominator counts,
per-asset tag/classification/control states, effective and shadowed policies,
aggregation entity-key exceptions, POLICY_CONTEXT status, receipt assessments,
sorted findings, platform boundaries, and a non-executable remediation packet.

No output field contains supplied Snowflake object names or tag values because
the input contract rejects them in identity fields and the SQL templates hash
identities before export.

## Examples

For “certify every sensitive column is masked,” require a column denominator,
current classification/tag evidence, an active effective masking association,
complete receipts, and a sanitized POLICY_CONTEXT scenario. A tag by itself is
not masking coverage.

For “no policy rows means we are clean,” return `NOT_PROVEN` when the collection
role has partial visibility or the Account Usage receipt is stale. Request a
bounded current reconciliation; do not escalate the collector role automatically.

## Error handling

| Condition | Response |
|---|---|
| Empty or duplicate denominator | Stop; fix the denominator before measuring coverage. |
| Raw object identity or credential material | Reject the bundle and sanitize at collection. |
| Receipt is stale, partial, truncated, or tampered | Block completeness and refresh the bounded surface. |
| Classification last attempt follows last success with an error | Report `FAILED`, even if the stored status says classified/reviewed. |
| Policy status is not `ACTIVE` | Report `MISCONFIGURED`; do not count the assignment. |
| Preview or edition evidence is missing | Report the platform boundary and do not pass coverage. |
| POLICY_CONTEXT errors or lacks required privileges | Record `NOT_PROVEN`; do not escalate privileges automatically. |

## Resources

- [Evidence contract](references/evidence-contract.md)
- [Precedence and platform bounds](references/precedence-and-platform-bounds.md)
- [Collection and POLICY_CONTEXT dry-run](references/collection-and-dry-run.md)
- [Official Snowflake sources](references/sources.md)
