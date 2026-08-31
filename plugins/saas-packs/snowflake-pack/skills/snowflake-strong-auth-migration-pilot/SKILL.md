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
version: 2.1.0
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
PERSON, SERVICE, and LEGACY_SERVICE principals, maps each bound workload to a
  supported target, and checks that managed MCP/OAuth primary-role scopes,
  client behavior, and secondary-role controls cannot silently broaden access.

## Prerequisites

- A sanitized user/workload/integration inventory with evidence timestamps,
  freshness bounds, and source scope. The collection and observation window
  must be ordered and no later than the current clock; proof timestamps cannot
  be future-dated or later than the collection receipt.
- Named identity/workload owner, security approver, executor, recovery identity,
  and approved canary/change window. The inventory must include a separately
  tested break-glass identity and a canary receipt with positive and negative
  outcomes.
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
- Prefer WIF only when the exact cloud runtime, Snowflake integration, and
  connector support it. Otherwise evaluate key pair, OAuth, or a bounded PAT
  using [workload-auth-options.md](references/workload-auth-options.md).
- Managed MCP/OAuth uses separate controls: advertised primary-role scopes,
  client scope behavior, the user's `DEFAULT_ROLE`, allowed/blocked roles, and
  `OAUTH_USE_SECONDARY_ROLES`. Never collapse those into one invented role list.

## Workflow

1. Capture account/cloud/edition, evidence timestamp, user type, default role,
   observed auth method names, workload binding, runtime/driver, integration,
   target options, role scope, a separately owned break-glass identity, and a
   target-auth canary receipt. Read [identity-types-and-inventory.md](references/identity-types-and-inventory.md).
   For live identity posture, collect account-level rows through the pack's
   shared read-only evidence collector:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
     --surface auth --connection <existing-readonly-profile> \
     --output ./snowflake-auth-live-evidence.json
   ```

   Preserve its source views, SQL hash, row count, timestamp, and non-claims;
   supplement it with an owner-approved workload inventory because the shared
   auth query intentionally does not discover runtime ownership or credentials.
   If `truncation_possible` is true, partition the inventory before making a
   migration-denominator or absence claim.
2. Create a sanitized JSON inventory. Include method names and booleans only;
   omit all credential values. A minimal shape is:

   ```json
   {
     "users": [{"name": "ETL_SVC", "type": "SERVICE", "auth_methods": ["PASSWORD"]}],
     "workloads": [{"name": "etl-prod", "identity": "ETL_SVC", "current_auth": "PASSWORD", "supported_auth": ["WIF", "KEY_PAIR"], "roles": ["ETL_ROLE"]}],
     "integrations": [{"name": "MCP_MANAGED", "type": "SNOWFLAKE_MANAGED_MCP_OAUTH", "source_control_type": "SNOWFLAKE_OAUTH", "oauth_scopes_supported": ["session:role:MCP_READER"], "scope_location": "ACCOUNT", "allowed_roles": ["MCP_READER"], "blocked_roles": ["ACCOUNTADMIN"], "oauth_use_secondary_roles": "NONE", "client_scope_behavior": "SESSION_ROLE_ALL", "enabled": true}]
   }
   ```

3. Run the deterministic analyzer:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_auth.py" \
     --input ./snowflake-auth-inventory.json \
     --out ./snowflake-auth-pilot.json
   ```

   The analyzer owns user classification, target selection, identity/workload
   binding, MCP scope checks, and stable report ordering.
4. Load [mcp-oauth-role-scoping.md](references/mcp-oauth-role-scoping.md) when
   an MCP/OAuth integration appears. Verify feature support and live role
   mapping; the report is not evidence that an integration is enabled.
5. Produce the dry-run cutover packet. For each workload include owner, current
   path, selected target, capability evidence, role scope, canary, rollback,
   and the exact authorized operator/change window. Read [cutover-and-recovery.md](references/cutover-and-recovery.md).
6. Require both positive and negative receipts: target login and allowed action;
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
- counts and findings for PERSON/SERVICE/LEGACY_SERVICE;
- workload-to-identity-to-auth target mapping and rationale;
- managed MCP/OAuth integration state, advertised scopes, client/default-role
  behavior, scope-setting location/object, allowed/blocked roles, secondary-role
  controls, and mismatches;
- no-credential/no-mutation safety statement;
- read-only inventory receipt, explicit `edit_authority: false`, and separately
  tested break-glass/canary evidence;
- positive/negative verification receipts and a recovery plan; and
- residual unknowns with named owners rather than fabricated certainty.

## Error Handling

| Condition | Response |
|---|---|
| Credential-bearing field appears | Stop; remove it and rerun with metadata only. |
| Service has no workload/owner | Do not disable it; open ownership discovery. |
| WIF support is not proven | Do not assume it; evaluate key pair/OAuth from declared capability evidence. |
| MCP OAuth controls are missing or broad | Stop; capture scopes, client behavior, default role/warehouse, allow/block lists, and secondary-role mode. |
| Canary or recovery test fails | Preserve the current path, use the approved recovery route, and record the failure. |
| User requests mass disable/rotation | Convert to a staged, owner-approved packet; this skill does not execute mutations. |

## Examples

### Password-backed ETL service

Declare `ETL_SVC` as `SERVICE`, bind it to `etl-prod`, and list only supported
target methods such as `["WIF", "KEY_PAIR"]`. The analyzer selects WIF first,
then requires canary login, allowed-action, denied-old-path, and recovery receipts.

### Managed MCP/OAuth

Declare `OAUTH_SCOPES_SUPPORTED`, whether the client requests a named role or
`session:role:all`, the user's `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE`, the
integration allow/block lists, and `OAUTH_USE_SECONDARY_ROLES`. A missing or
overbroad control stops the packet; the analyzer never broadens it.

## Resources

- [Identity types and inventory](references/identity-types-and-inventory.md)
- [Workload authentication options](references/workload-auth-options.md)
- [Managed MCP/OAuth role scoping](references/mcp-oauth-role-scoping.md)
- [Cutover and recovery](references/cutover-and-recovery.md)
