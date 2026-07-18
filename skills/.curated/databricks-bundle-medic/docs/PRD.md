# PRD: databricks-bundle-medic

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Active

> Authored to the `templates/skill-docs/` submission standard at the Pack / flagship tier
> (this is a `databricks-pack` skill) as the design record for `databricks-bundle-medic`,
> per `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills"). Companion docs beside it: `ADR.md`, `ONE-PAGER.md`.

## Problem

Databricks Asset Bundles (DAB) are the GitOps deploy path for a workspace, and the tooling
is immature in exactly the places that block a promote-to-prod pipeline. Three deploy-time
failures recur, each a specific tracked `databricks/cli` issue with a specific workaround —
not a design flaw to argue about. Bringing an existing UC catalog or external location under
bundle management should be a `databricks bundle bind`, but the CLI does not recognize UC
resource types (bind was scoped to jobs and pipelines at GA), so the engineer either
hand-edits `terraform.tfstate` or lets the deploy try to *create* a resource whose name is
already taken and conflicts (D4, `databricks/cli#4842`, open through CLI v0.295.x). The
second `databricks bundle deploy` of any bundle can fail with `reading terraform.tfstate:
opening: unexpected EOF` — the remote state is valid 530-590 KB JSON, but the CLI's streaming
reader chokes on it, and the bundle is bricked until unblocked (D5, `databricks/cli#4986`,
reproduced v0.288.0 through v0.296.0). And a bundle that declares a schema, a GRANT on that
schema, and a pipeline that writes to it fails its first deploy with `User does not have
CREATE TABLE on Schema` because DAB's resource graph evaluates the pipeline before the grant
lands — the second deploy succeeds because the first one applied the grant before failing
(D6, `databricks/cli#4573`).

The same operators own the deploy-time infrastructure, and the v2 rebuild merged the CMK +
networking half of the retired `databricks-identity-secrets-ops` into this skill because it
shares their tooling (Terraform + the Account API), their blast radius (cluster downtime),
and their audience (platform engineers). Rotating a customer-managed KMS key is not a config
change — the key is wired into the disk / storage encryption envelope at compute-creation
time, so every cluster, pool, and SQL warehouse in the workspace must be terminated for the
rotation window, the new key version's `GET` / `WRAPKEY` / `UNWRAPKEY` grants must reach the
Databricks managed identity before the swap or clusters fail to launch with
`KeyVaultAccessForbidden`, and the old key must stay enabled 24+ hours or running clusters
brick (D8). And a team that enables PrivateLink assumes "all traffic is private now," but
PrivateLink covers only the control plane — S3, STS, and Kinesis still traverse the NAT
gateway at $0.045/GB processed until separate VPC endpoints are configured, a silent cost
leak discovered on the month-end bill or a reliability outage the day egress is locked down
(D9). The v1 skills described these operations; none guarded the deploy, decoded the exact
issue, or produced the runbook.

## Target users

Every user here is a platform / infrastructure engineer — the operator who owns the deploy
pipeline and the workspace's cloud wiring, not the application engineer who authors notebooks
and jobs.

| User | Context | Primary need |
| ---- | ------- | ------------ |
| Platform engineer running the promote-to-prod bundle pipeline | A `databricks bundle deploy` just failed and the stderr is opaque | The exact `databricks/cli` issue behind the failure and its specific workaround, not "retry the deploy" |
| Platform / DevOps engineer bringing existing UC resources under DAB | Has catalogs / external locations created in Terraform or the UI, wants them GitOps-managed without recreating | A safe import plan that never destroys a catalog with dependent tables |
| Security / platform engineer rotating a customer-managed KMS key | Annual / post-incident CMK rotation on a 24x7 workspace with no clean maintenance window | An end-to-end drain + rotation runbook with the 24-hour key overlap and the per-cloud Account API calls |
| Cloud / network engineer hardening a PrivateLink workspace | Enabled PrivateLink, then saw a NAT-gateway bill or an egress-lockdown outage | A VPC-endpoint audit that names the missing S3 / STS / Kinesis endpoints and emits the remediation |

## The foot-guns and the medic's response

| Foot-gun | Upstream signature | The medic's response |
| -------- | ------------------ | -------------------- |
| **D4** — `databricks bundle bind` rejects UC catalogs / external locations (`databricks/cli#4842`) | "does not recognise external_location as a supported resource type", or a create-conflict on an already-taken name | `bundle-bind-helper` subagent reads the live external locations + storage credentials and classifies each resource (already-bound / needs-import / safe-to-create / conflict-blocking); `import-uc-resource-to-bundle.py` runs the backup-first Terraform import — a self-deprecating workaround that removes itself when #4842 closes |
| **D5** — `terraform.tfstate` "unexpected EOF" on redeploy (`databricks/cli#4986`) | `Error: reading terraform.tfstate: opening: unexpected EOF` | The PreToolUse hook validates the remote state parses as JSON and canaries a size shrink before the deploy; `references/bundle-engine-tradeoffs.md` documents the `DATABRICKS_BUNDLE_ENGINE=direct` escape and what it trades away |
| **D6** — schema GRANT evaluated after pipeline creation (`databricks/cli#4573`) | `Error: cannot create pipeline: User does not have CREATE TABLE on Schema` | The PostToolUse hook auto-retries once on that exact stderr; `bundle-split-permissions.py` refactors the bundle into a permissions-first / workloads-second pair for teams that need a deterministic single pass |
| **D8** — CMK rotation terminates every cluster / pool / warehouse | `KeyVaultAccessForbidden` on launch; "all compute resources ... must be terminated" | `/cmk-rotation-plan` emits the drain-order runbook; `drain-workspace.py` pauses schedulers and terminates compute in dependency order; `references/cmk-rotation-by-cloud.md` carries the per-cloud API calls + the 24-hour overlap |
| **D9** — PrivateLink leaves S3 / STS / Kinesis on the NAT | No error — a NAT data-processing bill at $0.045/GB, or S3 timeouts once egress is locked down | `audit-vpc-endpoints.py` walks every workspace VPC and reports S3-gateway / STS / Kinesis / route-table coverage, emitting remediation Terraform |

## The two hooks contract

databricks-bundle-medic is the pack's **only two-hook skill**. The two hooks bracket a single
`databricks bundle deploy` — one guards the input state, one recovers from one specific
known-transient failure — and each carries a hard behavioral bound.

- **PreToolUse — the tfstate guard (D5).** Before every `databricks bundle deploy`, the hook
  fetches the remote `terraform.tfstate` via `databricks workspace export`, validates it
  parses as JSON, and warns if its size has shrunk versus the last known-good copy (a
  state-corruption canary for the `#4986` EOF class). It caches a known-good copy locally as a
  recovery escape hatch. It is a canary, not a gate: it warns and preserves recovery state, it
  never aborts a deploy the operator asked for.
- **PostToolUse — the D6-only retry (D6).** On a `databricks bundle deploy` that exits
  non-zero, the hook matches stderr against the exact `User does not have CREATE TABLE on
  Schema` signature (`databricks/cli#4573`). On a match, it auto-retries the deploy once, with
  a log line naming the grant-ordering bug so the retry is never silent. On no match, it does
  nothing.

**The no-masking guarantee** (the load-bearing constraint): the PostToolUse retry fires only
on that one exact stderr signature, retries at most once, and passes every other error class
through untouched — an auth failure, a vCPU-quota denial, the D5 tfstate EOF, or a bundle
syntax error all surface to the operator unmodified. The hook exists to absorb one
well-understood, self-healing race, not to paper over a real deploy failure. A broken deploy
must still look broken.

## Success criteria

Criteria below are the skill's eval contract — each is written to become a judge criterion in
the skill's `eval-spec.yaml`.

1. Triggers on bundle-deploy / DAB-infra questions ("bundle deploy fails", "unexpected EOF
   terraform.tfstate", "bundle bind won't take my catalog", "User does not have CREATE TABLE
   on Schema", "rotate the CMK", "PrivateLink S3 costs") and stays silent on unrelated
   Databricks prompts — eval criterion `triggers-on-bundle-medic-question` (blocker) plus
   should-not-trigger control cases.
2. The PreToolUse tfstate guard runs *before* the deploy, validates the state parses as JSON,
   canaries a size shrink versus the last known-good copy, and caches a known-good copy —
   without ever aborting a legitimate deploy — eval criterion
   `tfstate-guard-validates-before-deploy` (regression-critical).
3. The PostToolUse retry fires only on the exact `User does not have CREATE TABLE on Schema`
   signature, retries at most once, and passes every other error class through untouched —
   eval criterion `d6-retry-fires-only-on-grant-signature` (blocker).
4. Every diagnosis names the real upstream issue (`databricks/cli#4842` / `#4986` / `#4573`)
   or the exact cloud error (`KeyVaultAccessForbidden`) and its specific workaround, never a
   generic "retry the deploy" — eval criterion `names-issue-id-and-workaround` (blocker).
5. The skill plans and recommends; the destructive infra steps — CMK rotation, workspace
   drain, UC-resource import, VPC-endpoint changes — are emitted as operator-approved
   runbooks / Terraform, never executed autonomously — eval criterion
   `never-drains-or-rotates-without-approval` (regression-critical).

## Functional requirements

The spine is **guard the deploy → decode the failure by its issue ID → hand back the exact
workaround or runbook**. Five requirement threads, one per pain, plus the surface contract.

- **FR-1 (bundle-bind import, D4):** Read the live UC governance surface via
  `databricks-workspace-mcp` `external_locations_list` + `storage_credentials_list`, dispatch
  the `bundle-bind-helper` subagent to classify every proposed resource
  (already-bound / needs-import / safe-to-create / conflict-blocking), and run
  `scripts/import-uc-resource-to-bundle.py` to compute and execute the backup-first Terraform
  import — stopping before any destructive op and never dropping a catalog with dependent
  tables.
- **FR-2 (tfstate guard, D5):** The PreToolUse hook fetches, JSON-validates, and size-canaries
  the remote `terraform.tfstate` before each `databricks bundle deploy` and caches a
  known-good copy; `references/bundle-engine-tradeoffs.md` documents the
  `DATABRICKS_BUNDLE_ENGINE=direct` escape and the bug classes it trades into.
- **FR-3 (GRANT-order retry, D6):** The PostToolUse hook matches the exact `User does not have
  CREATE TABLE on Schema` stderr and auto-retries once with a clear log line;
  `scripts/bundle-split-permissions.py` refactors a `databricks.yml` into a permissions-first
  bundle + a workloads bundle with an ordered deploy script for teams that need a deterministic
  single pass.
- **FR-4 (CMK rotation, D8):** `/cmk-rotation-plan` produces the end-to-end runbook (drain
  order, expected duration, rollback, validation queries); `scripts/drain-workspace.py` pauses
  every Jobs scheduler, waits for in-flight completion, and terminates clusters / pools /
  warehouses in dependency order (idempotent, dry-run first); `references/cmk-rotation-by-cloud.md`
  carries the per-cloud Account API calls and the 24-hour old-key overlap requirement.
- **FR-5 (VPC-endpoint audit, D9):** `scripts/audit-vpc-endpoints.py` walks every VPC
  associated with the workspace and reports S3-gateway / STS / Kinesis / route-table coverage,
  emitting remediation Terraform; `references/cost-leak-map.md` maps each missing endpoint to
  the exact AWS bill line item (and the Azure private-endpoint equivalents).
- **FR-6 (dual-surface + advisory fallback):** Live diagnostics read the control-plane MCP for
  the D4 UC-resource inventory; when the MCP is absent, advisory mode accepts pasted
  `terraform.tfstate` / deploy stderr / `databricks.yml` / VPC describe output and still names
  the issue and hands back the workaround rather than failing.

## Out of scope

- SCIM / identity provisioning, nested-group sync, and SSO — that stayed in
  `databricks-uc-migration-pilot` when the rebuild split the retired identity-secrets skill;
  this skill took only the CMK + networking half.
- Ongoing cost / spend reporting (idle clusters, wrong-SKU jobs, DLT serverless spikes) —
  that is `databricks-cost-leak-hunter`; the D9 read here is the one-time
  networking-endpoint leak (S3 / STS / Kinesis on the NAT), a deploy-time config gap, not a
  dollar-ranked FinOps report.
- Cluster-lifecycle forensics (cold-start bucketing, termination-code decode, Photon
  fallback, DBR landmines) — that is `databricks-cluster-forensics`; a `KeyVaultAccessForbidden`
  here is scoped to the CMK-rotation cause, not general launch-failure decode.
- Executing the rotation / drain / import — the skill produces the runbook + Terraform; a
  human runs the destructive step in a maintenance window.
- Non-Databricks Terraform / IaC and networking specifics beyond the documented per-cloud
  playbooks (AWS VPC endpoints, Azure private endpoints).
