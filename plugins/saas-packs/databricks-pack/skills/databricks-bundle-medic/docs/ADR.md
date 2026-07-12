# ADR: databricks-bundle-medic — a two-hook deploy guard, a self-deprecating bind workaround, a script-vs-LLM infra split, and a merged CMK + networking half

> Filed at `docs/ADR.md` beside the rest of the submission set, per
> `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills") — keeping the four docs atomic and inside the
> markdownlint-gated `plugins/**` tree. The ADR template's `000-docs/`-filing note
> (`NNN-AT-DECR-<slug>.md`) is the known alternative reading; the divergence is intentional
> and called out here.

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Accepted

## Context

A deploy-time medic is only worth shipping if a platform engineer mid-incident can trust the
named cause and act on the exact workaround. Four forces shaped the design. (1) DAB is the
GitOps deploy path, but the tooling breaks at the promote-to-prod boundary — the bind gap
(`databricks/cli#4842`), the `terraform.tfstate` EOF (`#4986`), the schema GRANT-ordering
race (`#4573`) — and each break is a specific, tracked issue with a specific workaround, not a
design flaw to reason from first principles at 2 AM. (2) Two of these have a moment-of-action
shape: the tfstate EOF is best caught *before* the deploy runs, while a known-good copy can
still be cached as a recovery escape hatch, and the grant-ordering failure is self-healing on
a single retry — both are hook-shaped, not prompt-shaped. (3) The destructive infrastructure
operations — CMK rotation, workspace drain, VPC-endpoint changes, UC-resource import — are
deterministic, auditable, high-blast-radius mechanics, while the reasoning about *whether and
when* to run them is genuinely LLM-shaped; conflating the two would either freeze the model
out of a real decision or hand it a live production lever. (4) The v2 rebuild had to place the
CMK + networking work somewhere: it shares tooling (Terraform + the Account API), failure mode
(cluster downtime / deploy blast radius), and audience (platform engineers) with the DAB
deploy work — but shares none of that with the SCIM / identity work.

## Decision

We ship **two hooks** bracketing a single `databricks bundle deploy` — making this the pack's
only two-hook skill. A **PreToolUse tfstate guard** downloads the remote `terraform.tfstate`
via `databricks workspace export`, validates it parses as JSON, warns on a size shrink versus
the last known-good copy, and caches a known-good copy as a recovery escape hatch (D5). A
**PostToolUse D6-only retry** matches deploy stderr against the exact `User does not have
CREATE TABLE on Schema` signature (`databricks/cli#4573`) and auto-retries once with a clear
log line — and is **bound so it can never mask any other error class**: one exact signature,
at most one retry, everything else passes through untouched. We enforce a **script-vs-LLM
split**: the VPC-endpoint audit (`audit-vpc-endpoints.py`), the workspace drain
(`drain-workspace.py`), the UC-resource import (`import-uc-resource-to-bundle.py`), and the
permissions/workloads refactor (`bundle-split-permissions.py`) are deterministic scripts,
while the "should we rotate the CMK now / is this VPC safe to change" reasoning is LLM-side and
`/cmk-rotation-plan` produces a runbook a **human** executes. The D4 bind workaround is
deliberately **self-deprecating** — `import-uc-resource-to-bundle.py` carries a "remove when
`databricks/cli#4842` closes" lifecycle marker. We **merge the CMK + networking half of the
retired `databricks-identity-secrets-ops` into this skill** and leave the SCIM / identity half
in `databricks-uc-migration-pilot`. Evidence comes from the **control-plane
`databricks-workspace-mcp`** (`external_locations_list` + `storage_credentials_list`) for the
D4 inventory, degrading to **advisory mode** on pasted input when the MCP is absent. Deep
knowledge (bundle-engine tradeoffs, per-cloud CMK rotation, the networking-cost-leak map) loads
from `references/*.md` on demand.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| One hook that retries *any* `bundle deploy` failure | A blanket retry masks real failures — a vCPU-quota denial or the D5 tfstate EOF is not self-healing, and a second green-looking pass hides a broken deploy. The retry is bound to the one exact `User does not have CREATE TABLE on Schema` signature precisely so a broken deploy still looks broken. |
| No hooks — diagnose the tfstate EOF and the grant race in the prompt, after the fact | The tfstate corruption is best caught *before* the deploy, when a known-good copy can still be cached as a recovery escape hatch; and the grant race resolves on a single retry the operator should not have to run by hand. Post-hoc prose can neither preserve pre-deploy state nor auto-recover a self-healing race. |
| Keep `databricks-identity-secrets-ops` whole (CMK + networking + SCIM in one skill) | CMK rotation and VPC-endpoint work share Terraform, the Account API, cluster-downtime blast radius, and the platform-engineer audience with the DAB deploy flow; SCIM / identity shares none of that and belongs with the UC governance work. Splitting the retired skill along the tooling / blast-radius seam put each half where its operator already is. |
| Let the LLM run the drain / rotation / import directly | These are high-blast-radius, auditable mechanics — terminate every warehouse, mutate `terraform.tfstate`, rewrite a bucket route table. A bundled script produces the same steps every run and is reviewable line-by-line; the model does the whether/when reasoning and never the load-bearing destructive action — the pack's "the model does NOT do the load-bearing operation" invariant. |
| Hard-require the workspace MCP registered | A platform engineer mid-incident rarely has the full toolchain wired. Advisory mode accepts pasted `terraform.tfstate` / deploy stderr / `databricks.yml` / VPC describe output and still names the issue and the workaround — weaker evidence, clearly labeled, still actionable — rather than refusing to run. |
| Ship the D4 bind workaround as a permanent supported feature | `bundle bind` for UC resources is an upstream gap Databricks is expected to close (`databricks/cli#4842`). A permanent tool would rot into a competing, unmaintained code path once native support lands. The import script is marked self-deprecating so it is deleted cleanly when the issue closes, not left to drift. |

A further rejection is baked into the output contract: a generic "your deploy failed — retry
it." Every diagnosis must name the *actual* upstream issue (`databricks/cli#4842` / `#4986` /
`#4573`) or the exact cloud error (`KeyVaultAccessForbidden`) and its specific workaround,
enforced by the blocker eval criterion `names-issue-id-and-workaround`.

## Consequences

**Positive:**

- Two known-transient DAB failures are handled at the moment of action: the tfstate EOF is
  caught before the deploy with a cached recovery copy, and the grant-ordering race self-heals
  on one bounded retry — no sprint spent rediscovering either workaround.
- The D6 retry can never mask a real failure — bound to one exact stderr signature, capped at
  one retry, every other error class passing straight through to the operator.
- The D4 bind workaround is safe (backup-first import, never drops a catalog with dependent
  tables) and self-deprecating (removes itself when `#4842` closes), so it cannot rot into a
  competing path.
- The high-blast-radius infra steps are deterministic scripts plus human-run runbooks, not
  autonomous model actions — reviewable, idempotent, dry-run-first.
- Merging CMK + networking put the deploy-time infra work with the deploy work: one skill, one
  platform-engineer audience, shared Terraform + Account API tooling.

**Negative / accepted tradeoffs:**

- Two hooks are more moving parts than a hookless skill, and a mis-scoped hook is a real risk —
  mitigated by binding the retry to one exact stderr signature and capping it at a single
  retry, and by keeping the PreToolUse guard non-blocking.
- The self-deprecating bind script is deliberately temporary tech debt tracking an upstream
  bug; it needs a cleanup pass when `#4842` lands. Accepted — the lifecycle marker is in-file
  so the debt is visible, not silent.
- The `DATABRICKS_BUNDLE_ENGINE=direct` escape trades the terraform-state bug class for the
  direct-engine bug class (cluster restart on every deploy, catalog "always recreate" drift);
  the skill documents the trade in `references/bundle-engine-tradeoffs.md` rather than
  pretending it is a clean fix.
- Merging CMK + networking makes this a broader skill spanning deploy + infra. Accepted —
  progressive disclosure keeps the CMK / VPC knowledge in `references/*.md`, loaded only when a
  run hits that case.
- Without the workspace MCP, advisory mode leans on pasted `terraform.tfstate` / stderr /
  bundle YAML: weaker evidence, clearly labeled, still names the issue.

## Tool-permission scope

No bare `Bash`: shell is scoped to a few binaries. The MCP calls are read-only
`external_locations` / `storage_credentials` list reads. The destructive mechanics live in
bundled scripts that emit runbooks + Terraform for a human to run — nothing in the tool set
autonomously rotates a key, drains a workspace, or mutates production state without an operator
executing the emitted artifact. The two hooks are configured separately in `hooks/` and
bracket `databricks bundle deploy`.

| Tool | Why it's needed |
| ---- | --------------- |
| `Read` | Load the on-demand `references/*.md` knowledge (bundle-engine tradeoffs, per-cloud CMK rotation, the networking-cost-leak map) and the per-resource result artifacts. |
| `Write` | Write the rendered runbooks, import plans, and audit reports to the runtime working dir (`$OUT`), plus the PreToolUse hook's known-good `terraform.tfstate` cache — never into the skill package. |
| `Edit` | Rescope a plan when the operator narrows to one resource, one cloud, or one pain. |
| `Bash(databricks:*)` | CLI: `databricks workspace export` for the tfstate fetch (D5 guard), `databricks bundle deploy` interactions, and Account API calls for CMK rotation (D8) and workspace-VPC association lookups (D9). |
| `Bash(terraform:*)` | Compute and run the backup-first UC-resource import (D4) and emit the D9 remediation Terraform. |
| `Bash(python3:*)` | Run the bundled scripts — `import-uc-resource-to-bundle.py`, `bundle-split-permissions.py`, `drain-workspace.py`, `audit-vpc-endpoints.py` (the last using the cloud SDK for the VPC / route-table describe reads). The scripts own the mechanics; the LLM never hand-edits state. |
| `Bash(jq:*)` | Parse `terraform.tfstate` JSON and the Account API / cloud describe JSON the scripts and hooks consume. |
| `mcp__databricks-workspace-mcp__external_locations_list` | Enumerate the existing external locations to classify each for bind / import (D4). |
| `mcp__databricks-workspace-mcp__storage_credentials_list` | Enumerate the existing storage credentials the external locations resolve through, for the same bind / import plan (D4). |
