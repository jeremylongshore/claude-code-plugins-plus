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
allowed-tools: Read
argument-hint: "[redacted-deploy-evidence.json]"
version: 3.16.0
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
accepts a bounded schema-v2 projection plus its digest from an independent CI or
artifact channel. It emits privacy-safe findings, a point-in-time zero-change
status, ordered read-only checks, and post-deploy invariants. Nested receipt
hashes detect internal inconsistency; they never substitute for trusted origin.
Read
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
- Never execute Terraform, Snowflake, schemachange, a network client, or a shell
  from the classifier. It is a pure JSON reader and report writer.
- Never treat a generic query-history receipt as deployment proof. It cannot
  establish a complete plan, state, migration, BCR, or affected-object denominator.

## Prerequisites

Collect a timestamped receipt from the exact account, role, backend, and CI
commit. Hash account, role, backend, workspace, object, address, operator, and
owner identities before they enter the packet. Obtain the canonical packet
SHA-256 independently from the trusted CI/artifact channel. The packet must include:

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
   immutable source snapshot hash, externally established item count, affected
   surface, owner, and verified/mitigated/not-applicable disposition.
6. An affected-object inventory reconciled to plan addresses (empty and
   explicitly verified for a zero-change plan), plus a verified point-in-time
   state backup receipt with location, capture time, and SHA-256.
7. Schemachange version, migration commit, exact script filename/type/version,
   stored and current checksums, change-history status, dry-run/verify output,
   and out-of-order policy if relevant. Bind a nonempty repository-script denominator, a
   current observed projection of the relevant rows, and the append-only
   `CHANGE_HISTORY` count/hash; repeated R/A executions make those counts differ.
8. Snowflake CLI, connector/driver, Terraform, schemachange, and runtime versions
   plus current release-note/BCR sources reviewed.
9. A zero-change receipt when exit code is `0` and changes are `0`, tied to the
   saved plan hash and verified affected-object count. Otherwise, a rollback or
   forward-fix test against this exact plan/migration set, including
   owner, preconditions, validation, and stop condition.
10. A hash-bound provider migration-segment inventory and a verified denominator
    for affected dbt Project objects, including the 2026_06 live-version BCR when
    applicable.
11. Exactly one account/plan-bound post-change invariant per changed plan
    resource; process exit status is never the verification result.

Missing evidence is an explicit finding. A successful command from a different
role, account, or environment is not a deployment receipt.

## Instructions

### Step 1: Establish current toolchain and account identity

Record the installed versions and lockfiles. Read the live provider registry,
Snowflake CLI/client-driver release notes, and current behavior-change notes for
the target account release window. Do not rely on a cached blog post or a generic
“latest” label. Keep auth read-only and least-privileged; use key pair/OAuth/
workload identity/external-browser mechanisms without exposing secrets.

The pack's generic query collector may support diagnosis, but it is not positive
evidence for this gate. A raw query receipt, a self-asserted hash, or a receipt
with `truncation_possible: true` cannot prove a complete affected-object or
dependency inventory. Build the schema-v2 projection in trusted CI from sanitized
`terraform show -json`, backend metadata, lock-file selection, repository migration
inventory, `CHANGE_HISTORY`, official BCR status/items, and exact tool versions.

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
Record every migration-guide segment between the locked source and target provider
versions. Each segment receipt must bind its source, versions, affected addresses,
immutable source snapshot, state-move boundary, disposition, and canonical SHA-256.
Segments must advance monotonically without gaps, cycles, or synthetic multi-minor
leaps. Empty means explicitly
verified not applicable, not “not checked.”

If dbt Project objects are in scope, inventory their deployed/staged code hashes,
current and target version model, supported runtime, behavior-change disposition,
and rollback artifact. The pending live-version behavior changes the rollback model;
see [`references/dbt-project-and-provider-migrations.md`](references/dbt-project-and-provider-migrations.md).

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
  --input ./snowflake-deploy-evidence.json \
  --as-of '<current-utc-evaluation-timestamp>' \
  --trusted-bundle-sha256 'sha256:<digest-from-trusted-ci-or-artifact-channel>'
```

The explicit `--as-of` value prevents wall-clock-dependent output. A clean
verdict is `PASS_AS_OF`, expires at that exact timestamp, and is never permission
to apply. Expected findings include:

- `TRUSTED_BUNDLE_DIGEST_MISSING_OR_MISMATCHED`,
  `EVIDENCE_CONTEXT_INVALID_OR_STALE`, `PLAN_RECEIPT_UNVERIFIABLE`,
  `PLAN_EXIT_ACTION_CONTRADICTION`, `TERRAFORM_STATE_UNREADABLE_OR_UNBOUND`;
- `GRANT_IMPORT_REQUIRED`, `DESTRUCTIVE_PLAN_CHANGE`,
  `AFFECTED_OBJECT_DENOMINATOR_UNVERIFIED`;
- `VERSIONED_CHECKSUM_DRIFT`, `REPEATABLE_CHANGE_DETECTED`,
  `ALWAYS_MIGRATION_UNREVIEWED`, `MIGRATION_DENOMINATOR_UNVERIFIED`;
- `PROVIDER_PREVIEW_FEATURE`, `PROVIDER_PREVIEW_DENOMINATOR_UNVERIFIED`,
  `PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED`, `DEPLOY_TOOLCHAIN_UNVERIFIED`;
- `BCR_INVENTORY_UNVERIFIED`, `DBT_PROJECT_DENOMINATOR_UNVERIFIED`,
  `PREFLIGHT_DENOMINATOR_UNVERIFIED`, `STATE_BACKUP_RECEIPT_UNVERIFIABLE`;
- `ROLLBACK_RECEIPT_UNVERIFIABLE`, `POST_CHANGE_INVARIANTS_UNVERIFIED`,
  `ZERO_CHANGE_RECEIPT_UNVERIFIABLE`.

The script is pure and connector-neutral. It reports findings from supplied
evidence; it does not call Terraform, schemachange, Snowflake CLI, or Snowflake.

### Step 5: Produce the release decision

Return a receipt containing scope/identity, current toolchain sources, zero-change
or plan verdict, grant/import/state findings, migration checksum findings, BCR
review, and rollback status. For each finding distinguish observed, derived,
unknown, and hypothesis. Name the exact next read-only check and the approval
boundary for any later mutation.

### Step 6: Verify post-deploy invariants

After a separately approved deployment, collect fresh evidence. The preflight
classifier validates only the invariant plan; it does not claim to execute or
verify post-deploy checks. Reconcile the saved state/plan, grant addresses,
migration history, toolchain/BCR receipt, observed invariant results, and
rollback/forward-fix validation in a separate operator-reviewed receipt.

## Output format

- **Identity:** hashed account, role, backend/workspace, repository commit,
  collection timestamp, and explicit UTC observation window.
- **Toolchain:** exact observed versions and links/dates for current docs/BCRs.
- **Terraform:** state parseability, detailed exit code, zero-change status,
  grant/import/ownership/replacement risks.
- **Preflight:** operator/timestamp, BCR inventory, affected objects, and state
  backup receipt reconciled to the same account and saved plan.
- **Migrations:** V/R/A classification, checksum/history comparison, collision or
  out-of-order risk, and idempotence evidence.
- **Decision:** `BLOCKED` or `PASS_AS_OF`; neither authorizes apply.
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
- [`references/dbt-project-and-provider-migrations.md`](references/dbt-project-and-provider-migrations.md)
  — provider migration segments and dbt Project live-version preflight.
