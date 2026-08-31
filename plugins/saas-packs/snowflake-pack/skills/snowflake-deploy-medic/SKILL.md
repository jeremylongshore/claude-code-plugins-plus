---
name: snowflake-deploy-medic
description: |
  Review and safely diagnose Snowflake infrastructure and database deployments
  across the snowflakedb/snowflake Terraform 2.x provider, grants/state/imports,
  schemachange versioned and repeatable migrations, Snowflake CLI/drivers, and
  behavior-change releases. Use before a production deploy, when a plan wants
  to replace or revoke grants, state is unreadable, a migration checksum drifts,
  or a CLI/driver upgrade changes behavior. Produces a zero-change/plan verdict,
  ordered remediation, and tested rollback requirements. It never applies,
  destroys, deploys, runs mutating SQL, or edits state/history automatically.
  Trigger with "Snowflake Terraform plan", "grant import", "terraform state",
  "schemachange checksum", "repeatable migration", "Snowflake CLI upgrade",
  "driver BCR", or "rollback Snowflake deploy". Use when a production change
  needs a current plan, migration-integrity, toolchain, or rollback gate.
allowed-tools: Read, Bash(python3:*), Bash(terraform:plan*)
argument-hint: "[redacted-deploy-evidence.json]"
version: 2.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, terraform, schemachange, deploy, migrations, bcr]
---

# Snowflake Deploy Medic

## Overview

Snowflake deployment failures hide in the seams: a grant resource is declared as
new although the remote grant already exists; provider state is truncated; a
versioned migration was edited after application; a repeatable checksum change
reruns unexpectedly; or a current CLI/driver behavior change is mistaken for a
database defect. This skill creates one evidence-backed gate across those seams.

The deterministic classifier is
[`scripts/analyze_deploy_evidence.py`](scripts/analyze_deploy_evidence.py). It
accepts redacted plan/state/history/toolchain evidence and emits findings,
zero-change status, ordered read-only checks, and post-deploy invariants. Read
[`references/terraform-provider-2x.md`](references/terraform-provider-2x.md),
[`references/schemachange-integrity.md`](references/schemachange-integrity.md),
and [`references/zero-change-rollback.md`](references/zero-change-rollback.md)
for the relevant surface. Always verify current primary docs and release notes;
the versions in a local receipt are observations, not timeless recommendations.

## Hard boundaries

- Never run `terraform apply`, `terraform destroy`, state editing, `schemachange
  deploy`, mutating `snow sql`, or Snowflake DDL/DML automatically.
- Never hand-edit `terraform.tfstate` or `CHANGE_HISTORY` to make a plan green.
- Never treat a valid plan with changes as a zero-change adoption; inspect every
  grant, ownership, replacement, destroy, and preview feature.
- Never edit an applied versioned migration in place. A checksum mismatch is a
  release-blocking integrity signal; choose a new version, restore the exact
  applied content, or explicitly review a compensating path.
- Never treat a repeatable checksum change as either an error or a free rerun:
  verify idempotence, intended scope, and current schemachange behavior.
- Never freeze provider, CLI, driver, or BCR guidance to a version copied from
  this skill. Record current versions and check live release notes for the target
  account release window.
- Redact backend credentials, tokens, private keys, passphrases, passwords,
  sensitive plan values, customer data, and presigned URLs from receipts.

## Prerequisites

Collect a timestamped receipt from the exact account, role, backend, and CI
commit. It should include:

1. A preflight record with operator, UTC timestamp, account/backend/workspace
   identity, state lock/backup, affected-object inventory, plan, BCR, and
   rollback checks. A green plan does not waive this gate.
2. Terraform source and locked provider version, Terraform/runtime version,
   backend/workspace identity (without secrets), and parseable state status.
3. Saved `terraform plan -detailed-exitcode` output: exit code, change count,
   resource actions, replacements/destroys, grant/ownership changes, and preview
   features.
4. For existing grants/objects, the intended resource address, remote identity,
   import evidence, and post-import plan result.
5. An itemized BCR inventory for the account release window: each ID/source,
   affected surface, owner, and verified/mitigated/not-applicable disposition.
6. An affected-object inventory reconciled to plan addresses (empty and
   explicitly verified for a zero-change plan), plus a verified point-in-time
   state backup receipt with location, capture time, and SHA-256.
7. Schemachange version, migration commit, script type/path/version, stored and
   current checksums, change-history status, dry-run/verify output, and out-of-
   order policy if relevant.
8. Snowflake CLI, connector/driver, Terraform, schemachange, and runtime versions
   plus current release-note/BCR sources reviewed.
9. A zero-change receipt when exit code is `0` and changes are `0`, tied to the
   saved plan hash and verified affected-object count. Otherwise, a rollback or
   forward-fix test against this exact plan/migration set, including
   owner, preconditions, validation, and stop condition.

Missing evidence is an explicit finding. A successful command from a different
role, account, or environment is not a deployment receipt.

## Instructions

### Step 1: Establish current toolchain and account identity

Record the installed versions and lockfiles. Read the live provider registry,
Snowflake CLI/client-driver release notes, and current behavior-change notes for
the target account release window. Do not rely on a cached blog post or a generic
“latest” label. Keep auth read-only and least-privileged; use key pair/OAuth/
workload identity/external-browser mechanisms without exposing secrets.

For live metadata, use the pack's shared bounded collector (never pass
credentials on its command line):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface query --connection <existing-readonly-profile> \
  --output ./snowflake-deploy-live-evidence.json
```

Treat the collector's `collected_at`, SQL hash, source views, row count, and
non-claims as provenance. It does not replace Terraform state/plan, BCR, or
backup receipts. A receipt with `truncation_possible: true` cannot prove a
complete affected-object or dependency inventory.

### Step 2: Gate Terraform state and preview

Validate that state parses and belongs to the intended backend/workspace. Preserve
a backend version/lock receipt before refreshing. Run only the reviewed read-only
plan with detailed exit status:

- exit `0` and `changes=0`: candidate zero-change receipt;
- exit `2`: valid preview with changes, requiring review;
- any other non-zero value: plan failed, not a safe preview.

For a grant adoption, declare the intended address and use the current provider's
documented import identity. Refresh and require a zero-change plan. Inspect grant
scope, future grants, role/object ownership, managed access, privilege removals,
and provider normalization. Never destroy a live dependency graph to avoid an
import.

For provider 2.x preview resources/features, read the exact current support
boundary and release notes. A green plan does not make preview behavior stable.
See [`references/terraform-provider-2x.md`](references/terraform-provider-2x.md).

### Step 3: Gate schemachange integrity

Separate migration types:

- `V...__...sql`: versioned, tracked once; checksum drift blocks deployment until
  the applied content is reconciled.
- `R__...sql`: repeatable; checksum changes intentionally cause a rerun, so prove
  idempotence and scope before approval.
- `A__...sql`: always-run; review side effects and cost on every deploy.

Compare repository content to the actual `CHANGE_HISTORY` row. Check duplicate
version names and branch ordering. Use current `verify`/dry-run behavior and
review upgrade notes for checksum normalization regressions before changing the
tool version. Never alter history by hand. See
[`references/schemachange-integrity.md`](references/schemachange-integrity.md).

### Step 4: Run the deterministic evidence classifier

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_deploy_evidence.py" \
  --input ./snowflake-deploy-evidence.json
```

Expected findings include:

- `GRANT_IMPORT_REQUIRED`, `TERRAFORM_STATE_UNREADABLE`,
  `DESTRUCTIVE_PLAN_CHANGE`, `PLAN_FAILED`, `PLAN_NOT_VERIFIED`;
- `VERSIONED_CHECKSUM_DRIFT`, `REPEATABLE_CHANGE_DETECTED`,
  `VERSION_COLLISION`;
- `PROVIDER_PRE_2`, `PROVIDER_PREVIEW_FEATURE`, `TOOLCHAIN_UNVERIFIED`,
  `BCR_NOT_CHECKED`, `BCR_INVENTORY_MISSING`;
- `PREFLIGHT_INCOMPLETE`, `STATE_BACKUP_MISSING`,
  `AFFECTED_OBJECTS_UNVERIFIED`, `ZERO_CHANGE_RECEIPT_MISSING`;
- `ROLLBACK_UNTESTED`.

The script is pure and connector-neutral. It reports findings from supplied
evidence; it does not call Terraform, schemachange, Snowflake CLI, or Snowflake.

### Step 5: Produce the release decision

Return a receipt containing scope/identity, current toolchain sources, zero-change
or plan verdict, grant/import/state findings, migration checksum findings, BCR
review, and rollback status. For each finding distinguish observed, derived,
unknown, and hypothesis. Name the exact next read-only check and the approval
boundary for any later mutation.

### Step 6: Verify post-deploy invariants

After a separately approved deployment, collect fresh evidence. Do not call a
release complete from process exit status alone. The saved state/plan, grant
addresses, migration history, toolchain/BCR receipt, and rollback/forward-fix
validation must all reconcile.

## Output format

- **Identity:** account, role, backend/workspace, repository commit, collection
  timestamp, and explicit UTC observation window.
- **Toolchain:** exact observed versions and links/dates for current docs/BCRs.
- **Terraform:** state parseability, detailed exit code, zero-change status,
  grant/import/ownership/replacement risks.
- **Preflight:** operator/timestamp, BCR inventory, affected objects, and state
  backup receipt reconciled to the same account and saved plan.
- **Migrations:** V/R/A classification, checksum/history comparison, collision or
  out-of-order risk, and idempotence evidence.
- **Decision:** block, review, or ready-for-explicit-approval; explain why.
- **Rollback:** tested strategy for this exact change set and stop condition.
- **Zero-change receipt:** saved-plan hash, verified object count, issuance time,
  and explicit `issued` status when the plan is truly zero-change.
- **Invariants:** checks required after the approved deployment.

## Error Handling

If the JSON receipt is malformed, the classifier exits with code 2; correct the
receipt instead of reading a partial verdict. If state, plan, change history,
toolchain, or BCR evidence is missing, emit an explicit unknown/blocking finding.
If the account, backend, role, or repository commit cannot be established, stop
at identity verification. If a user asks to auto-apply, destroy, deploy, mutate
SQL, or edit state/history, return the reviewed read-only checks and approval
boundary instead. A successful CLI command from another environment is not proof
of this deployment.

## Examples

### Existing grant adoption

When Terraform wants to create a grant that already exists, classify
`GRANT_IMPORT_REQUIRED`. Declare the intended address, use the current provider's
documented import identity, refresh, and require a zero-change plan. Do not hand-
edit `terraform.tfstate` or destroy the database to force adoption.

### Versioned drift plus repeatable change

When a `V...` checksum differs from `CHANGE_HISTORY`, block the release and restore
the applied content or create a new migration. When an `R__...` checksum changes,
review the intentional rerun and idempotence separately. Never update the history
table by hand to silence either finding.

## References

- [`references/terraform-provider-2x.md`](references/terraform-provider-2x.md) —
  provider support, state/plan, grant import, ownership, and preview review.
- [`references/schemachange-integrity.md`](references/schemachange-integrity.md) —
  versioned/repeatable/always scripts, checksums, history, and upgrade risk.
- [`references/toolchain-bcr.md`](references/toolchain-bcr.md) — current CLI,
  driver, authentication, and behavior-change review.
- [`references/zero-change-rollback.md`](references/zero-change-rollback.md) —
  detailed plan semantics and change-specific rollback boundaries.
- [`references/source-notes.md`](references/source-notes.md) — primary research
  routes; verify live pages at execution time.
