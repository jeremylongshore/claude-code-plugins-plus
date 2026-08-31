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
allowed-tools: Read, Write, Edit, Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
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

- Read-only, sanitized exports from `SHOW ROLES`, `SHOW GRANTS`, and relevant
  `SHOW FUTURE GRANTS` queries.
- A named principal/object/privilege question, evidence timestamp, and review
  period. Live Snowflake checks remain the operator's responsibility.
- Python 3.10+ for the bundled stdlib analyzer. No Snowflake driver or network
  access is required.

## Authentication

This skill's analyzer is offline and deliberately has no authentication flow.
If live Snowflake evidence is collected, use the organization's approved
Snowflake session/authentication process; never put its credentials in the
inventory or report. Use `Write`/`Edit` only to save a sanitized report or
approved local change packet; never to apply Snowflake mutations.

## Safety contract

- Read-only by default. The analyzer does not connect to Snowflake and never
  executes `GRANT`, `REVOKE`, `GRANT OWNERSHIP`, `ALTER USER`, or policy changes.
- Accept sanitized metadata only. Do not provide passwords, tokens, private keys,
  raw connection strings, or access-history payloads containing sensitive data.
- Do not infer denial from a missing historical row. Account Usage can lag and
  does not replace current `SHOW GRANTS`, policy, share, and session-context checks.
- Do not infer that a role is unused from one telemetry source. Name the review
  period, object coverage, and evidence gaps.
- Treat ownership as control-plane authority and future `OWNERSHIP` as a separate
  high-risk decision. Never auto-generate executable mutation SQL.

## Workflow

1. Establish the principal, target object, privilege, evidence timestamp, review
   period, and whether the question is about a primary-role or secondary-role
   session. Read [authorization-model.md](references/authorization-model.md) for
   path and evidence rules.
2. Collect the narrowest read-only `SHOW ROLES`, `SHOW GRANTS`, and `SHOW FUTURE
   GRANTS` exports needed. Read [audit-queries.md](references/audit-queries.md)
   for the sanitized input shape. Record the role that ran each query.
3. Run the deterministic analyzer:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_access.py" \
     --input ./snowflake-access-inventory.json \
     --principal ALICE \
     --object ANALYTICS.CURATED.ORDERS \
     --privilege SELECT \
     --out ./snowflake-access-report.json
   ```

   The script owns graph traversal and finding classification. Do not replace
   its path output with an eyeballed role diagram.
4. For each finding, distinguish **observed**, **not proven**, and **needs live
   verification**. Resolve managed-access, ownership, and future-grant findings
   with [managed-access-and-future-grants.md](references/managed-access-and-future-grants.md).
5. Produce a dry-run change packet: current path, intended path, exact proposed
   principal/privilege/object edge, approver, executor, precondition, reversal,
   and residual risk. Proposed SQL may be described as a review artifact, but it
   is not executed by this skill.
6. Require positive and negative verification before an authorized operator
   applies anything. Use [verification-and-rollback.md](references/verification-and-rollback.md)
   for the receipt fields and rollback boundary.

## What the report must answer

- Which paths prove the requested access, including inherited and secondary-role
  context? If no path is in the sanitized inventory, say `NOT_PROVEN`, not denied.
- Is access direct to a user, through `PUBLIC`, through an orphaned grantee, or
  through a role chain that should be reviewed?
- Is the object owned by a role whose control is broader than routine access?
- Is the schema managed access, and is the grantor evidence sufficient?
- Do database- and schema-level future grants overlap for the same grantee/object
  type, or does a future `OWNERSHIP` grant need explicit approval?
- Which live checks remain necessary: container `USAGE`, policies, shares,
  `SHOW GRANTS`, current secondary-role mode, and a real allowed/denied operation?

## Output

Return a JSON report plus a human-readable change packet containing:

- deterministic input SHA-256 and inventory scope;
- object-privilege paths and `OBJECT_PRIVILEGE_PATH_PROVEN`/`NOT_PROVEN` status;
  this never certifies complete access without separate container/policy checks;
- sorted findings with severity, evidence, and remediation decision;
- managed-access and secondary-role boundaries;
- proposed change/reversal descriptions with no executed mutations; and
- positive and negative verification receipts.

## Error Handling

| Condition | Response |
|---|---|
| Credential-bearing field appears | Stop; remove it and rerun with metadata only. |
| Role or user is absent from inventory | Mark path `NOT_PROVEN`; do not create or delete a principal. |
| Account Usage disagrees with `SHOW GRANTS` | Treat live/current evidence as a separate reconciliation; record lag and scope. |
| Managed schema lacks grantor/owner evidence | Stop remediation proposal until `MANAGE GRANTS` and ownership are verified. |
| Future grants overlap | Reconcile schema precedence and test a disposable object before approval. |
| Ownership or PUBLIC access is involved | Require named security/data owner approval and an independent rollback path. |

## Examples

### Trace one path

Run the analyzer with `--principal ALICE --object ANALYTICS.CURATED.ORDERS
--privilege SELECT`. A result such as `ALICE -> ANALYST -> DATA_READER` is an
observed path; a missing path is `NOT_PROVEN`, not proof of denial.

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
- [Verification and rollback](references/verification-and-rollback.md)
