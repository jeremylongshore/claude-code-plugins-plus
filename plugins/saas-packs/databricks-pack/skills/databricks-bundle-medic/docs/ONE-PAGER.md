# Databricks Bundle Medic

**The deploy + infrastructure spine of the Databricks pack — the pack's only two-hook skill: a PreToolUse guard that validates `terraform.tfstate` before every `databricks bundle deploy` and a PostToolUse retry that self-heals the one known grant-ordering race and never masks any other error, plus deterministic runbooks for CMK rotation and PrivateLink VPC-endpoint gaps — each failure named by its real `databricks/cli` issue and exact workaround.**

## Problem

Databricks Asset Bundles are the GitOps deploy path, and the tooling breaks at the
promote-to-prod boundary. `databricks bundle bind` won't take UC catalogs or external
locations (`databricks/cli#4842`), so bringing existing resources under DAB means hand-editing
`terraform.tfstate` or hitting a create-conflict. The second deploy of any bundle can die on
`reading terraform.tfstate: opening: unexpected EOF` (`#4986`), bricking the pipeline. A bundle
with a schema, a GRANT, and a pipeline fails its first deploy with `User does not have CREATE
TABLE on Schema` because the grant lands after the pipeline is evaluated — the second deploy
succeeds (`#4573`). And the same operators own the infra: rotating a customer-managed KMS key
forces terminating every cluster, pool, and warehouse in the workspace, and a PrivateLink
workspace still leaks S3 / STS / Kinesis traffic through the NAT at $0.045/GB until separate
VPC endpoints exist. The v1 skills described these; none guarded the deploy or decoded the
exact issue.

## Solution

A **guard → decode → hand back the workaround** flow. Two hooks bracket `databricks bundle
deploy`: a PreToolUse guard downloads and JSON-validates the remote `terraform.tfstate`,
canaries a size shrink, and caches a known-good recovery copy (D5); a PostToolUse hook
auto-retries once — and only once — on the exact `User does not have CREATE TABLE on Schema`
stderr, passing every other error through untouched (D6). A `bundle-bind-helper` subagent plus
a self-deprecating `import-uc-resource-to-bundle.py` bring existing UC resources under DAB
safely (D4); `bundle-split-permissions.py` refactors a bundle for a deterministic single pass;
`/cmk-rotation-plan` + `drain-workspace.py` produce the CMK maintenance-window runbook (D8);
and `audit-vpc-endpoints.py` names the missing S3 / STS / Kinesis endpoints and emits
remediation Terraform (D9). Live UC reads come from the `databricks-workspace-mcp` control
plane, with an advisory-mode fallback on pasted input. It plans and recommends; the destructive
steps are operator-run.

## W5

|           |                                                                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Platform / infrastructure engineers who own the bundle deploy pipeline and the workspace's cloud wiring — not application engineers      |
| **What**  | Guards `databricks bundle deploy`, decodes the failure by its real `databricks/cli` issue, and hands back the exact workaround or runbook for the bind gap, tfstate EOF, GRANT-ordering race, CMK rotation, or PrivateLink NAT leak |
| **When**  | A bundle deploy just failed; a `bundle bind` won't take a catalog; before a customer-managed-key rotation; after a PrivateLink NAT bill  |
| **Where** | Claude Code (also Codex-compatible), against a Databricks workspace with the workspace MCP registered, or advisory mode on pasted state  |
| **Why**   | Two known-transient DAB failures are handled at the moment of action and the destructive infra steps are deterministic runbooks — the retry self-heals one race and never masks a real error |

## Stack

| Layer | Choice |
| ----- | ------ |
| Skill runtime | Claude Code `SKILL.md` (compatibility: Codex) |
| Deploy guard | PreToolUse hook — `terraform.tfstate` JSON-validate + size canary + known-good cache (D5) |
| Deploy recovery | PostToolUse hook — D6-only single retry on the exact GRANT-ordering stderr, no-masking bound (D6) |
| Control-plane evidence | `databricks-workspace-mcp` — `external_locations_list` / `storage_credentials_list` (D4), advisory-mode fallback on pasted input |
| Deterministic scripts | `import-uc-resource-to-bundle.py` (self-deprecating, D4), `bundle-split-permissions.py` (D6), `drain-workspace.py` (D8), `audit-vpc-endpoints.py` (D9) |
| Runbook surface | `/cmk-rotation-plan` slash command + `bundle-bind-helper` subagent |
| Knowledge | `references/*.md` on demand — bundle-engine tradeoffs, per-cloud CMK rotation, networking-cost-leak map |

## Differentiators

1. **The deploy spine — the only two-hook skill, and the retry never masks a real error.** A
   PreToolUse guard validates `terraform.tfstate` before every `databricks bundle deploy` and
   caches a recovery copy; a PostToolUse hook auto-retries once on the exact `User does not
   have CREATE TABLE on Schema` signature and passes every other error class — auth, quota,
   tfstate EOF, syntax — straight through, so a broken deploy still looks broken.
2. **Names the issue, not the symptom.** Every failure is decoded to its real `databricks/cli`
   issue (`#4842` / `#4986` / `#4573`) or exact cloud error (`KeyVaultAccessForbidden`) with
   the specific workaround — the self-deprecating bind import, the `DATABRICKS_BUNDLE_ENGINE=direct`
   escape, the permissions/workloads split — where the v1 skills only described the operation.
3. **The model reasons; the scripts do the load-bearing work.** CMK rotation, workspace drain,
   VPC-endpoint remediation, and UC-resource import are deterministic scripts and human-run
   runbooks — the LLM decides whether and when to rotate, never terminates a warehouse or
   mutates production state on its own.
