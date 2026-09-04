---
name: snowflake-strong-auth-migration-pilot
description: |
  Pilot a Snowflake authentication modernization without lockouts or credential
  exposure. Inventory PERSON, SERVICE, and LEGACY_SERVICE users; map named workloads
  to WIF, key pair, OAuth, or bounded PAT; and audit managed MCP/OAuth session controls.
  Use when replacing Snowflake passwords, reviewing service identities, planning
  workload identity federation, or scoping MCP OAuth. Trigger with phrases like
  "Snowflake auth migration", "service user password", "Snowflake WIF", "key pair
  rotation", or "MCP OAuth role scope".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[redacted-auth-evidence.json]"
version: 3.16.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, security, authentication, wif, oauth, mcp]
---

# Snowflake Strong-Auth Migration Pilot

## Overview

Convert an uncertain Snowflake identity estate into an owner-backed,
least-privilege authentication pilot. The useful unit is a named workload and
its runtime—not a blanket account-wide password deadline. The pilot classifies
PERSON, SERVICE, LEGACY_SERVICE, and SERVICE_AGENT principals, maps each bound
workload to a supported target, and checks that managed MCP/OAuth primary-role scopes,
client behavior, and secondary-role controls cannot silently broaden access.

## Prerequisites

- Three live schema-2 collector receipts: near-current `SHOW USERS`, delayed
  Account Usage `USERS`, and the latency-settled portion of a bounded trailing
  seven-day `LOGIN_HISTORY` horizon.
  Record the final bundle SHA-256 outside the bundle when it crosses the
  controlled local collection boundary; an embedded self-checksum is not provenance.
- Named identity/workload owner, security approver, executor, recovery identity,
  and approved canary/change window. The inventory must include a separately
  tested break-glass identity and a canary receipt with positive and negative
  outcomes. Keep those operational receipts outside this posture bundle; the
  analyzer intentionally rejects and never echoes embedded canary or recovery payloads.
- Python 3.10+ for the bundled stdlib analyzer. No Snowflake driver or network
  access is required.

## Authentication

This skill's analyzer is offline and intentionally has no credential or token
authentication flow. If live Snowflake evidence is collected, use the
organization's approved session/authentication process and record method names
only; never place credentials in the inventory or report. This skill has no
`Edit` authority and never edits local source or Snowflake objects. The Python
analyzer may write only the explicitly requested sanitized report path via
`--out`; never use that capability for credentials or mutation commands.

This package does not provide an MCP server, OAuth client, or token broker. Any
connector is configured separately. Supply only sanitized read-only evidence
and verify account, edition, connector, client behavior, and feature availability.

## Non-negotiable boundaries

- Read-only planning. This skill never disables users, rotates keys, creates or
  alters integrations, changes authentication/network policies, or handles
  passwords, PATs, tokens, private keys, or client secrets.
- Do not invent a universal retirement date. Dates depend on the account,
  connector, runtime, feature availability, owner, and approved change window.
- A service without a named workload is an ownership gap, not permission to
  disable it. A LEGACY_SERVICE must be bound and tested before retirement.
- Snowflake-managed `SNOWFLAKE_SERVICE` rows remain in receipt cap accounting
  but are excluded from the operator migration denominator. `SERVICE_AGENT`
  remains an operator-owned service classification.
- Prefer WIF only when the exact cloud runtime, Snowflake integration, and
  connector support it. Otherwise evaluate key pair, OAuth, or a bounded PAT
  using [workload-auth-options.md](references/workload-auth-options.md).
- Managed MCP/OAuth uses separate controls: advertised primary-role scopes,
  client scope behavior, the user's `DEFAULT_ROLE`, allowed/blocked roles, and
  `OAUTH_USE_SECONDARY_ROLES`. Never collapse those into one invented role list.

## Workflow

1. Read [current-evidence-contract.md](references/current-evidence-contract.md),
   then collect all three independent read-only surfaces under the same account,
   collector identity, primary role, secondary-role configuration, and CLI profile:

   ```bash
   AUTH_PROFILE="replace-with-approved-readonly-profile"
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface auth-current --connection "${AUTH_PROFILE}" \
     --output snowflake-auth-current.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface auth --connection "${AUTH_PROFILE}" \
     --output snowflake-auth-history.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface auth-login-history --connection "${AUTH_PROFILE}" \
     --output snowflake-auth-login-history.json
   ```

   Do not use `--input-json`: offline normalization cannot bind live posture or
   execution context. A cap hit, collector error, stale receipt, context mismatch,
   privilege-filtered SHOW row, or user-hash drift blocks scoped completeness.
2. Build one schema-2 bundle containing those receipts, the exact expected
   hashed organization-plus-account/user/role authorization context, an explicit digest
   coverage denominator, owner-backed users/workloads, and one approved bounded
   enforcement window per workload. Operator type and current authentication
   method declarations must match receipted posture. Include method names and
   booleans only; omit credential values and all canary/break-glass payloads.
   Workload names must be unique. MFA posture is a separate factor observation,
   not a primary `auth_methods` value.
   The reference defines the exact envelope.
3. At the controlled local boundary, compute and separately record the final
   canonical bundle digest:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_auth_evidence.py" \
     --input snowflake-auth-bundle.json --print-input-sha256
   ```

   The digest is an operator assertion of byte identity, not a signature or
   collector identity proof. Never place it inside the bundle it authenticates.
4. Run the evidence-gated analyzer with that out-of-band digest:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_auth_evidence.py" \
     --input snowflake-auth-bundle.json \
     --trusted-input-sha256 sha256:<recorded-digest> \
     --out snowflake-auth-pilot.json
   ```

   The wrapper validates exact reviewed SQL hashes, sources, dataset fields,
   row counts/caps, live mode, wall-clock freshness, declared authorization context, coverage, and
   current/history reconciliation before allowing receipt rows into analysis.
   `analyze_auth.py` remains the metadata-only planning engine; it cannot certify evidence.
5. Load [mcp-oauth-role-scoping.md](references/mcp-oauth-role-scoping.md) when
   an MCP/OAuth integration appears. Verify feature support and live role
   mapping; the report is not evidence that an integration is enabled.
6. Produce the dry-run cutover packet. For each workload include owner, current
   path, selected target, capability evidence, role scope, canary, rollback,
   and the exact authorized operator/change window. Read [cutover-and-recovery.md](references/cutover-and-recovery.md).
7. Require both positive and negative receipts: target login and allowed action;
   old-path rejection only after replacement/recovery; out-of-scope role/object
   denial; and independent recovery. Keep the current path until receipts are
   accepted.

## Mapping rules

- PERSON with SSO/OAuth evidence: retain interactive design and verify the IdP
  path; do not silently convert a human to a service identity.
- PERSON with password only: high-priority review, not an automatic disable.
- SERVICE/LEGACY_SERVICE with password/basic: high-priority modernization;
  choose WIF → key pair → OAuth → PAT only from declared supported options.
- SERVICE without workload: ownership/inventory finding.
- Unknown user, runtime, driver, or target capability: `MANUAL_REVIEW`, not a
  guessed migration.
- Missing or untested break-glass identity or canary: block the pilot; do not
  disable the current path.
- PAT: bounded fallback only; record owner, audience, revocation/expiration
  process, and why stronger options are unavailable.

## Output

Return a JSON report plus a human-readable packet containing:

- deterministic input SHA-256 and evidence scope;
- per-surface trust, freshness, exact-template, cap, and context assessments;
- current/historical pseudonymous user reconciliation and drift;
- latency-settled LOGIN_HISTORY observations, explicitly separated from proof;
- counts and findings for PERSON/SERVICE/LEGACY_SERVICE/SERVICE_AGENT;
- workload-to-identity-to-auth target mapping and rationale;
- managed MCP/OAuth integration state, advertised scopes, client/default-role
  behavior, scope-setting location/object, allowed/blocked roles, secondary-role
  controls, and mismatches;
- no-credential safety statement plus narrow analyzer/collector operation boundaries;
- read-only inventory receipt, explicit `edit_authority: false`, and separately
  tested break-glass/canary evidence;
- positive/negative verification receipts and a recovery plan; and
- residual unknowns with named owners rather than fabricated certainty.

## Error Handling

| Condition | Response |
|---|---|
| Missing/mismatched out-of-band digest | Quarantine receipt rows and return `UNTRUSTED`, `INVALID_TRUST_ANCHOR`, or `DIGEST_MISMATCH`. |
| SHOW-only, stale, capped, errored, or context-mismatched evidence | Block scoped completeness and cutover approval; recollect all required surfaces. |
| Raw username, email, IP, event ID, factor ID, connection ID, or free-form error appears in receipt rows | Reject the receipt; use only the reviewed pseudonymous projection. |
| Credential-bearing field appears | Stop; remove it and rerun with metadata only. |
| Service has no workload/owner | Do not disable it; open ownership discovery. |
| WIF support is not proven | Treat `supported_auth` as an unverified operator declaration; verify the exact runtime, driver, connector, integration, and target login before approval. |
| MCP OAuth controls are missing or broad | Stop; capture scopes, client behavior, default role/warehouse, allow/block lists, and secondary-role mode. |
| Canary or recovery test fails | Preserve the current path, use the approved recovery route, and record the failure. |
| User requests mass disable/rotation | Convert to a staged, owner-approved packet; this skill does not execute mutations. |

## Examples

### Password-backed ETL service

Declare a password-backed `ETL_SVC` as `LEGACY_SERVICE`, bind it to `etl-prod`, and list only supported
target methods such as `["WIF", "KEY_PAIR"]`. The analyzer selects WIF first,
then requires canary login, allowed-action, denied-old-path, and recovery receipts.

### Managed MCP/OAuth

Declare `OAUTH_SCOPES_SUPPORTED`, whether the client requests a named role or
`session:role:all`, the user's `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE`, the
integration allow/block lists, and `OAUTH_USE_SECONDARY_ROLES`. A missing or
overbroad control stops the packet; the analyzer never broadens it.

## Resources

- [Identity types and inventory](references/identity-types-and-inventory.md)
- [Current and historical evidence contract](references/current-evidence-contract.md)
- [Workload authentication options](references/workload-auth-options.md)
- [Managed MCP/OAuth role scoping](references/mcp-oauth-role-scoping.md)
- [Cutover and recovery](references/cutover-and-recovery.md)
