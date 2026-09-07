---
name: snowflake-access-guardian
description: |
  Audit Snowflake effective access and produce a safe least-privilege change packet.
  Trace account-role inheritance, primary and secondary roles, managed-access
  schemas, ownership, direct-to-user/PUBLIC grants, orphaned principals, and
  existing-versus-future-grant conflicts. Use when access is unexpectedly broad or
  denied, a role graph needs review, or an authorization cleanup needs evidence.
  Trigger with phrases like "Snowflake access audit", "trace Snowflake grants",
  "why can this user read", "Snowflake RBAC drift", or "future grants conflict".
allowed-tools: Read, Write, Bash(python3:*)
argument-hint: "[redacted-access-evidence.json]"
version: 3.16.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, security, rbac, governance, least-privilege]
---

# Snowflake Access Guardian

## Overview

Turn a sanitized Snowflake authorization inventory into an evidence-backed
effective-access trace and a dry-run remediation packet. This is the focused
Snowflake counterpart to a generic RBAC explainer: it catches the failure modes
that make enterprise reviews expensive—role inheritance that was not followed,
direct user and `PUBLIC` grants, abandoned grantees, ownership control, managed
access semantics, secondary-role assumptions, and future-grant precedence.

## Prerequisites

- Receipted, sanitized outputs from the bundled historical, session, role,
  user, database-role, and relevant database/schema future-grant collectors.
- A named principal/object/privilege question, account/role identity, UTC
  collection timestamp, observation window, and explicit freshness bound. Live
  Snowflake checks remain the operator's responsibility.
- Timestamped positive (allowed action) and negative (denied action) receipts
  captured under the same primary/secondary-role context; missing proof is
  `NOT_PROVEN`, never an inferred denial.
- Python 3.10+ for the bundled stdlib analyzer. No Snowflake driver or network
  access is required.

## Authentication

This skill's analyzer is offline and deliberately has no authentication flow.
If live Snowflake evidence is collected, use the organization's approved
Snowflake session/authentication process; never put its credentials in the
inventory or report. Use `Write` only to save a sanitized report or
approved local change packet; never to apply Snowflake mutations.

## Safety contract

- Read-only by default. The analyzer does not connect to Snowflake and never
  executes `GRANT`, `REVOKE`, `GRANT OWNERSHIP`, `ALTER USER`, or policy changes.
- Accept sanitized metadata only. Do not provide passwords, tokens, private keys,
  raw connection strings, or access-history payloads containing sensitive data.
- Do not infer denial from a missing historical row. Account Usage can lag by
  up to 120 minutes and has documented object/shared-role omissions.
- Never broaden to `ACCOUNTADMIN` or automatically grant `MANAGE GRANTS` to get
  a more complete snapshot. `MANAGE GRANTS` can administer grants and is not a
  read-only privilege, even when this collector executes only `SHOW` statements.
- Do not infer that a role is unused from one telemetry source. Name the review
  period, object coverage, and evidence gaps.
- Treat ownership as control-plane authority and future `OWNERSHIP` as a separate
  high-risk decision. Never auto-generate executable mutation SQL.

## Workflow

1. Establish the principal, target object, privilege, evidence timestamp, review
   period, and whether the question is about a primary-role or secondary-role
   session. Read [authorization-model.md](references/authorization-model.md) for
   path and evidence rules.
2. Collect the delayed account-wide baseline with a role holding Snowflake's
   `SNOWFLAKE.SECURITY_VIEWER` database role. Preserve the receipt unchanged:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access --connection <existing-readonly-profile> \
     --output ./snowflake-access-historical.json
   ```

3. Collect current evidence only for the declared review scope. Capture the
   session context without changing roles, then collect grants **to** and grants **of**
   each account role, target-user roles, involved database roles, and paired
   database/schema future grants:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access-session --connection <profile> --output ./session.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access-role-current --role DATA_READER \
     --connection <profile> --output ./role-current.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access-role-parents --role DATA_READER \
     --connection <profile> --output ./role-parents.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access-future-database --database ANALYTICS \
     --connection <profile> --output ./future-database.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface access-future-schema --schema ANALYTICS.CURATED \
     --connection <profile> --output ./future-schema.json
   ```

   Selectors accept only supported one-part or two-part unquoted identifiers;
   quoted/multipart identifiers need a separately reviewed collection path.
   Each scoped `SHOW` uses one Snowflake pipe statement that emits both the
   allowlisted rows and its execution context. Invocations may use different
   physical sessions; the analyzer requires equivalent account, user, primary
   role, role type, and secondary-role state. Saved/offline access JSON is not
   accepted as current evidence.
   Read [current-evidence-contract.md](references/current-evidence-contract.md)
   for every surface and the schema `2.0` bundle. Permission errors, missing
   declared selectors, a missing current `PUBLIC` role receipt, cap hits, or an
   unpaired schema receipt remain blockers.
4. At the controlled local collection boundary, assemble the bundle and record its
   canonical digest separately. Analyze the exact same bundle with that digest:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_access_evidence.py" \
     --input ./snowflake-access-bundle.json --print-input-sha256
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_access_evidence.py" \
     --input ./snowflake-access-bundle.json \
     --trusted-input-sha256 sha256:<separately-recorded-digest> \
     --out ./snowflake-access-report.json
   ```

   The receipt analyzer validates templates, selectors, sources, row counts,
   caps, Snowflake observation timestamps, request-derived coverage, equivalent
   authorization contexts, and the bundle digest before invoking the graph
   analyzer. The matching digest is an operator assertion of byte identity, not
   authentication; computing it from an untrusted copy creates no trust.
   `analyze_access.py` remains a diagnostic path for legacy sanitized
   inventories, but it cannot establish receipted completeness.
5. For each finding, distinguish **observed**, **not proven**, and **needs live
   verification**. Resolve managed-access, ownership, and future-grant findings
   with [managed-access-and-future-grants.md](references/managed-access-and-future-grants.md).
   The report must retain direct-user paths and every ownership path separately;
   ownership is control-plane authority, not routine access.
6. Produce a dry-run change packet: current path, intended path, exact proposed
   principal/privilege/object edge, approver, executor, precondition, reversal,
   and residual risk. Proposed SQL may be described as a review artifact, but it
   is not executed by this skill.
7. Require positive and negative verification before an authorized operator
   applies anything. Use [verification-and-rollback.md](references/verification-and-rollback.md)
   for receipt fields and rollback boundary. When database- and schema-level
   future grants overlap, report effective schema precedence and test a
   disposable object; do not summarize the conflict as a generic duplicate.

## What the report must answer

- Which paths prove the requested access, including inherited and secondary-role
  context? If no path is in the sanitized inventory, say `NOT_PROVEN`, not denied.
- Is access direct to a user, through `PUBLIC`, through an orphaned grantee, or
  through a role chain that should be reviewed?
- If access is direct to a user, was user-based access actually active through
  `USE SECONDARY ROLES ALL`? `NONE` or an explicit role list does not activate it.
- Is the object owned by a role whose control is broader than routine access?
- Is the schema managed access, and is the grantor evidence sufficient?
- Does any schema-level future grant suppress database-level definitions for the
  same object type in that schema—even for different grantees or privileges—or
  does a future `OWNERSHIP` grant need explicit approval?
- Which live checks remain necessary: container `USAGE`, policies, shares,
  `SHOW GRANTS`, current secondary-role mode, and a real allowed/denied operation?
- Is the evidence fresh for this decision, and do timestamped positive and
  negative access proofs exist for the requested role/object context?

## Output

Return a JSON report plus a human-readable change packet containing:

- deterministic input SHA-256 and inventory scope;
- object-privilege paths and `OBJECT_PRIVILEGE_PATH_PROVEN`/`NOT_PROVEN` status;
  this never certifies complete access without separate container/policy checks;
- separate `object_privilege_path_supported` and `positive_access_claim_supported`
  booleans; the latter also requires a matching positive behavior receipt;
- sorted findings with severity, evidence, and remediation decision;
- managed-access and secondary-role boundaries;
- evidence scope/freshness, direct-user and ownership paths, and explicit
  database-versus-schema future-grant precedence;
- per-receipt contract status, trusted-bundle status, declared-selector coverage,
  and current-versus-historical drift classifications;
- proposed change/reversal descriptions with no executed mutations; and
- positive and negative verification receipts with `PROVEN`/`NOT_PROVEN` status.

## Error Handling

| Condition | Response |
|---|---|
| Credential-bearing field appears | Stop; remove it and rerun with metadata only. |
| Role or user is absent from inventory | Mark path `NOT_PROVEN`; do not create or delete a principal. |
| Account Usage disagrees with `SHOW GRANTS` | Treat live/current evidence as a separate reconciliation; record lag and scope. |
| Current `SHOW` visibility is incomplete | Record the collector role and block absence claims; never grant `MANAGE GRANTS` automatically. |
| Receipt lacks a separate matching bundle digest | Report `UNTRUSTED`, suppress graph claims, and block completeness. |
| Any receipt lacks same-statement context or a fresh server observation | Suppress graph claims and recollect live. |
| Database future receipt lacks the target schema receipt | Block precedence and completeness claims. |
| Managed schema lacks grantor/owner evidence | Stop remediation proposal until `MANAGE GRANTS` and ownership are verified. |
| Future grants overlap | Reconcile schema precedence and test a disposable object before approval. |
| Ownership or PUBLIC access is involved | Require named security/data owner approval and an independent rollback path. |

## Examples

### Trace one path

Put `ALICE`, `ANALYTICS.CURATED.ORDERS`, and `SELECT` in the schema `2.0`
bundle's `request`, then run `analyze_access_evidence.py`. A result such as
`ALICE -> ANALYST -> DATA_READER` is a positively supported path; a missing path
never unblocks an absence or denial claim.

### Review a cleanup request

For “revoke everything suspicious,” report direct-user/PUBLIC/orphan findings,
future-grant precedence, and the required positive/negative tests. Keep changes
as a dry-run packet for the authorized operator.

## References

The four linked references contain the maintained decision detail and official
Snowflake primary sources; load only those relevant to the current finding.

## Resources

- [Authorization model](references/authorization-model.md)
- [Managed access and future grants](references/managed-access-and-future-grants.md)
- [Read-only audit queries](references/audit-queries.md)
- [Current evidence and receipt contract](references/current-evidence-contract.md)
- [Verification and rollback](references/verification-and-rollback.md)
