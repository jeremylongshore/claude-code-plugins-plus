# Databricks Pain Catalog — Domain 3: Unity Catalog, Asset Bundles, Identity, Workspace Ops, Secrets, Networking

**Research date:** 2026-05-27
**Author:** Research pass for Claude Code skill plugin pack rebuild
**Scope:** Six domains — Unity Catalog (UC), Asset Bundles (DAB), SCIM/SSO, workspace ops, secret scopes + KMS, networking (PrivateLink/VPC).
**Method:** Mined Databricks docs/KB, Databricks Community forum, `gh api repos/databricks/{cli,terraform-provider-databricks}/issues`, Microsoft Learn Q&A, Medium/blog write-ups. Cited verbatim source URLs per entry.

**Key cross-cutting findings up front:**

- **September 30, 2026 forcing function.** All new workspaces will be provisioned UC-only — no DBFS root, no DBFS mounts, no Hive metastore, no no-isolation shared clusters. Migration pain is at peak right now. ([databricks docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/migrate))
- **Asset Bundles are immature tooling, not bad design.** The pain pattern in the `databricks/cli` repo is panics, state-file corruption, and resource-binding gaps, not architectural mistakes. Many issues opened in 2026 are still open. The recently-introduced "direct" deployment engine (env `DATABRICKS_BUNDLE_ENGINE=direct`) is the unofficial workaround for terraform-state bugs.
- **Identity is the Azure-AD-shaped hole.** Nested groups don't sync, external groups are immutable, and the SCIM provisioner has 20-40 minute sync windows with no way to confirm completion programmatically. Reddit/community posts on this dwarf all other identity complaints.
- **The single-metastore-per-region rule is a load-bearing constraint** that org-design and naming conventions have to be built around, and is repeatedly hit late.

---

## D1 — Hive metastore → UC migration: `wasbs://` / DBFS-root tables silently skipped

**Domain:** unity-catalog
**Trigger:** Engineer runs UCX assessment or Databricks Migration Assistant to lift legacy `hive_metastore.*` tables into a UC catalog, expects all tables to come over, runs the workflow, gets a green checkmark, and finds half the tables missing in UC.
**Symptom:**

- Assessment marks external tables "ready" but managed tables "not ready" with no surfaced reason.
- Workflow "completes successfully, but neither the external nor the managed tables appear in Unity Catalog."
- For Azure: `Table is not eligible for an upgrade from Hive Metastore to Unity Catalog. Reason: Unsupported file system scheme wasbs` (or `adl`).
- For AWS/Azure: managed tables backed by `dbfs:/user/hive/warehouse/...` are skipped entirely because "Unity Catalog cannot govern DBFS root, as it lacks cloud-native URIs (s3://, abfss://)."
- LEGACY_TABLE_ACL clusters cause migration to skip tables silently because their DENY-based permissive model cannot be auto-mapped to UC's strict allow-only model.
- `CREATE TABLE CLONE` does not migrate Delta history — time-travel + change-data-feed silently break post-migration.

**Root cause:** UC requires (a) cloud-native object-storage URIs (`s3://`, `abfss://`, `gs://`), (b) UC-compatible cluster modes (single-user or shared with UC), and (c) no DBFS root or DBFS-mount-only data. UCX is "diagnostic-first, not destructive" — it silently skips violating tables instead of erroring loudly.
**Blast radius:** Catalog-wide for the targeted hive_metastore; potentially every workload that reads the un-migrated tables continues to work against the legacy HMS while the org believes migration is complete. False-confidence pattern.
**Current workaround (manual):**

1. Run UCX (or `system.information_schema` queries) to inventory `STORAGE_LOCATION` of every HMS table.
2. For each `wasbs://` / `adl://` / `dbfs:/` table: physically copy data to `abfss://` / `s3://` / `gs://` first using `DEEP CLONE` or a Spark `INSERT INTO ... SELECT *` against a new path.
3. Recreate tables in UC against the new path.
4. Manually copy ACLs (HMS table ACL → UC `GRANT SELECT` etc.).
5. Validate row counts catalog-by-catalog with a reconciliation notebook.
6. Plan for the Delta-history loss: archive the old table read-only, document the cutover date as the new "time-travel zero."

**Citations:**

- https://docs.databricks.com/aws/en/data-governance/unity-catalog/migrate
- https://community.databricks.com/t5/get-started-discussions/issues-migrating-hive-metastore-tables-to-unity-catalog/td-p/90836
- https://community.databricks.com/t5/technical-blog/from-hms-to-unity-catalog-a-self-service-migration-playbook/ba-p/155116
- https://www.databricks.com/blog/migrating-tables-hive-metastore-unity-catalog-metastore

**Response architecture recommendation:**
SKILL.md + references/ + scripts/ + Subagent.

- **`references/`**: full taxonomy of un-migratable conditions (`wasbs`, `adl`, `dbfs:/user/hive`, LEGACY_TABLE_ACL, view-on-view depth limits, non-Delta external tables). Per-cloud playbooks for the physical-relocation step.
- **`scripts/audit-hms-readiness.py`**: queries `system.information_schema` and HMS, emits a CSV: `table_name, storage_uri, scheme, migration_blocker, suggested_action`.
- **`scripts/reconcile.py`**: post-migration row-count + schema diff between HMS source and UC target.
- **Subagent (`migration-planner`)**: takes the readiness CSV and produces a per-table migration plan (clone vs deep-clone vs rewrite), respecting the org's catalog naming convention.
- **WHY**: Migration is a multi-week sequenced operation with strong invariants (don't drop the source until reconciliation passes). A subagent keeps the main context clean while it grinds through hundreds of tables; deterministic scripts catch the silent-skip class.

---

## D2 — UC external-location AccessDenied after IAM-role recreation

**Domain:** unity-catalog
**Trigger:** Platform engineer deletes and recreates the IAM role used by a UC storage credential (e.g., during a cross-account refactor, naming standardization, or Terraform `taint` + apply).
**Symptom:** Every query against tables in that external location starts failing with:

```
java.nio.file.AccessDeniedException: s3://<bucket>.<region>.amazonaws.com/path/to/object
com.amazonaws.services.s3.model.AmazonS3Exception: Forbidden
```

The Databricks UI shows the storage credential and external location both "healthy." The IAM role exists with the same name and the same trust policy. SQL warehouses, jobs, and notebooks all fail simultaneously.
**Root cause:** AWS S3 bucket policies that reference an IAM role by ARN store the *role's unique ID* (`AROAXXXXXXXXXXXXXXXX`) internally, not the ARN string. When the role is deleted, AWS substitutes the unique-ID placeholder. Recreating the role with the same name generates a *new* unique ID — the bucket policy now points at the dead ID, so all requests are denied. The bucket policy looks textually identical in the AWS console but semantically references a tombstone.
**Blast radius:** All UC external tables/volumes that resolve through that storage credential — typically a whole catalog or schema. Often production critical.
**Current workaround (manual):**

1. Open S3 bucket policy in the AWS console — JSON form, not the visual editor.
2. Identify any `Principal` block showing `AROAXXX...` rather than the role ARN.
3. Replace with the current role ARN.
4. (Belt-and-suspenders) Recreate the storage credential in UC pointing at the new role, then recreate the external location.

**Citations:**

- https://kb.databricks.com/unity-catalog/accessdenied-error-on-unity-catalog-when-querying-external-locations
- https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/manage-storage-credentials
- https://learn.microsoft.com/en-us/answers/questions/5590979/azure-databricks-permission-denied-on-adls-contain

**Response architecture recommendation:**
SKILL.md + Hook (PreToolUse on `aws iam delete-role` / `aws iam create-role`) + scripts/.

- **Hook**: blocks any `aws iam delete-role` that targets a role currently referenced by a UC storage credential unless the operator passes `--force` *and* has a recovery plan filed. Prevents the most common cause.
- **`scripts/scan-bucket-policies.sh`**: walks every UC storage credential, fetches the bucket policy, flags any `AROA*` placeholders. Run in CI weekly.
- **`scripts/repair-bucket-policy.py`**: takes a credential name, computes the live role's ARN, rewrites the bucket policy in place.
- **WHY**: This is a *prevention-first* problem — once it bites it's loud and recoverable, but the prevention has to live at the moment of the destructive action. PreToolUse hook is the right primitive.

---

## D3 — UC: single metastore per region forces SDLC namespace gymnastics

**Domain:** unity-catalog
**Trigger:** Team designs Dev/Test/Prod isolation for UC and wants three separate metastores in the same region so promotion is a metadata operation, not a rename. Discovers the one-metastore-per-region rule late.
**Symptom:** Cannot create a second metastore in the same region. Forces every catalog name to encode the environment (`bronze_dev`, `bronze_test`, `bronze_prod`), which then has to be substituted into views, DLT pipelines, jobs, dashboards, and every external BI tool's connection string. Cross-environment lineage gets polluted because UC sees `bronze_dev.silver.foo` and `bronze_prod.silver.foo` as siblings.
**Root cause:** Hard product constraint, documented but easy to miss until late in design. Databricks recommends Delta Sharing for cross-metastore/region sharing, which is a different cost and operational model than the multi-metastore design teams expected.
**Blast radius:** Account-wide. Sets the catalog naming convention for the lifetime of the deployment. Refactoring it later requires renaming every table reference in every notebook, view, pipeline, and downstream tool.
**Current workaround (manual):**

1. Adopt environment-suffixed catalogs (`bronze_<env>`) and parameterize every SQL/notebook with a `${env}` substitution.
2. Use DAB targets to inject `var.env` into every catalog reference.
3. File a request with the Databricks account team — the one-per-region limit is "soft" and can be lifted by the account team for some customers (undocumented exception).
4. For true isolation: deploy each environment to a different *region* and accept the cross-region egress cost / lineage gap, or use a separate Databricks account per environment (cost: separate billing, separate principals, separate SSO).

**Citations:**

- https://community.databricks.com/t5/data-governance/metastore-one-per-account-region-limitation/td-p/41097
- https://community.databricks.com/t5/data-governance/unity-catalog-multiple-metastore-in-same-region/td-p/28513
- https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices

**Response architecture recommendation:**
SKILL.md + references/ + Slash command.

- **`references/uc-environment-isolation-patterns.md`**: four named patterns (single-metastore-catalog-per-env, multi-region, multi-account, soft-quota-bump), with concrete cost/operational tradeoffs.
- **Slash command `/uc-env-pattern-picker`**: interactive decision tree (compliance reqs → cost tolerance → BI-tool count → naming flexibility) that recommends the pattern and emits the matching DAB target stub.
- **WHY**: This is a *design-time* decision with permanent consequences. The skill's job is to surface the constraint before the design freezes, not to fix a runtime symptom. A slash command at the right moment in the project flow is the highest-leverage primitive.

---

## D4 — Asset Bundle `bundle bind` does not support UC resources (catalogs, external locations)

**Domain:** asset-bundles
**Trigger:** Team has existing UC catalogs and external locations (created via Terraform, UI, or earlier scripts) and wants to bring them under DAB management without recreating them. Runs `databricks bundle bind external_location <key> <existing-name>`.
**Symptom:** CLI rejects with "does not recognise external_location (or catalog) as a supported resource type." If the engineer just adds the resource block to `databricks.yml` and deploys, DAB tries to *create* the resource and conflicts with the existing one — deploy fails because the catalog/external-location name is already taken.
**Root cause:** Immature tooling. `bundle bind` was scoped to jobs and pipelines at GA; UC resource binding was deferred. Open issue [databricks/cli#4842](https://github.com/databricks/cli/issues/4842) tracks it, no fix as of CLI v0.295.x.
**Blast radius:** Per-resource; blocks GitOps-driven UC governance until manual workaround applied.
**Current workaround (manual):**

1. Manually edit `terraform.tfstate` to import the resource (hostile, undocumented surface area).
2. Or: destroy + recreate the catalog/external-location via DAB — *only* possible if no dependent tables exist (managed tables die with the catalog).
3. Or: skip DAB for these resources and keep managing them in Terraform, which defeats the unified-pipeline goal of DAB.

**Citations:**

- https://github.com/databricks/cli/issues/4842
- https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands
- https://docs.databricks.com/aws/en/dev-tools/bundles/resources

**Response architecture recommendation:**
SKILL.md + scripts/ + Subagent.

- **`scripts/import-uc-resource-to-bundle.py`**: takes an existing catalog or external-location name, computes the Terraform import command + state-file mutation, runs it under a backup-first guardrail. Tracks support gaps so when CLI lands native support the script can deprecate cleanly.
- **Subagent (`bundle-bind-helper`)**: walks the existing UC inventory + the proposed `databricks.yml`, produces a per-resource plan (`already-bound` / `needs-import` / `safe-to-create` / `conflict-blocking`) and stops before any destructive op.
- **WHY**: This is an *upstream bug we can't fix* — the response is a workaround tool that's correct, safe, and self-deprecating once Databricks ships the feature. Subagent keeps the multi-step import flow out of the main context.

---

## D5 — Asset Bundle: `terraform.tfstate` "unexpected EOF" on every deploy after the first

**Domain:** asset-bundles
**Trigger:** Team deploys a bundle for the first time (succeeds), commits, runs `databricks bundle deploy` a second time in CI or locally.
**Symptom:**

```
Error: reading terraform.tfstate: opening: unexpected EOF
```

The remote state file is valid JSON (530-590 KB), downloadable via `databricks workspace export`, but the CLI's streaming reader fails. Reproducible on macOS and Linux, CLI v0.288.0 through v0.296.0. Effectively bricks the bundle until manually unblocked.
**Root cause:** Bug in the CLI's `workspace-files` streaming-read path when fetching `terraform.tfstate`. Issue [databricks/cli#4986](https://github.com/databricks/cli/issues/4986) — open at time of writing.
**Blast radius:** Per-bundle; every subsequent deploy of the affected bundle fails until the workaround is applied. Blocks promote-to-prod pipelines.
**Current workaround (manual):** Switch to the "direct" deployment engine, which bypasses Terraform state entirely:

```bash
export DATABRICKS_BUNDLE_ENGINE=direct
databricks bundle deploy --profile <profile>
```

This is officially a preview feature; teams adopt it as a permanent workaround because the underlying terraform-state path keeps breaking in other ways too. There are *other* open issues against the direct-engine path (cluster restart on every deploy, catalog "always recreate" drift) — switching engines trades one class of bug for another, and is not a clean fix.

**Citations:**

- https://github.com/databricks/cli/issues/4986
- https://github.com/databricks/cli/issues/4933
- https://github.com/databricks/cli/issues/4625
- https://github.com/databricks/cli/issues/5179
- https://community.databricks.com/t5/data-engineering/databricks-assets-bundles-no-deployment-state/td-p/67918

**Response architecture recommendation:**
SKILL.md + Hook (PreToolUse on `databricks bundle deploy`) + references/.

- **PreToolUse hook**: before every `bundle deploy`, downloads the remote `terraform.tfstate` via the workspace API, validates it parses as JSON, and warns if size has shrunk vs. the last good copy (state corruption canary). Caches a known-good copy locally as a recovery escape hatch.
- **`references/bundle-engine-tradeoffs.md`**: side-by-side of `terraform` vs `direct` engine, listing the known-open bug IDs against each. Updated as issues close.
- **WHY**: Tooling is in flux — the right response is to detect breakage early (hook), preserve recovery state (hook side-effect), and document the unstable choice (reference) so the team doesn't waste a sprint rediscovering the workaround. The skill itself can't fix the upstream bug.

---

## D6 — Asset Bundle: schema GRANTs evaluated after pipeline creation, deploy fails on cold runs

**Domain:** asset-bundles
**Trigger:** Team defines a UC schema, a GRANT on that schema (e.g., `CREATE TABLE` to a service principal), and a DLT pipeline that writes to the schema — all in the same `databricks.yml`. Runs `databricks bundle deploy` on a fresh workspace or after a schema rebuild.
**Symptom:** Deploy fails with:

```
Error: cannot create pipeline: User does not have CREATE TABLE on Schema 'CATALOG_NAME.*'.
```

The grant *is* in the bundle, but the resource graph evaluates the pipeline before the grant takes effect. Reissuing `databricks bundle deploy` immediately afterward succeeds because the grant landed on the first (failed) pass.
**Root cause:** DAB's resource graph does not encode the implicit ordering "GRANTs that supply privileges needed at resource-creation time must apply *before* the resources that exercise those privileges." Open issue [databricks/cli#4573](https://github.com/databricks/cli/issues/4573).
**Blast radius:** Per-bundle, per-fresh-deploy. Particularly painful in disaster-recovery / multi-environment promotion where the first deploy to a new workspace fails non-deterministically.
**Current workaround (manual):**

1. Run `databricks bundle deploy` twice (the second attempt succeeds because the first one applied the grants before failing).
2. Or split the bundle into two: a "permissions" bundle that's deployed first, then the workload bundle.
3. Or pre-create schemas + grants via Terraform outside the bundle and only put pipelines in DAB.

**Citations:**

- https://github.com/databricks/cli/issues/4573
- https://docs.databricks.com/aws/en/dev-tools/bundles/resources
- https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/

**Response architecture recommendation:**
SKILL.md + Hook (PostToolUse on `databricks bundle deploy` failure) + scripts/.

- **PostToolUse hook**: on a `bundle deploy` failure, parse stderr for the `User does not have CREATE TABLE on Schema` pattern; if matched, auto-retry once (exit-code-2 with a clear message). Only fires on this exact known transient failure — does not mask other errors.
- **`scripts/bundle-split-permissions.py`**: takes a `databricks.yml` and refactors it into a `permissions.yml` (catalogs, schemas, grants, volumes) + `workloads.yml` (jobs, pipelines), emits an updated deploy script that runs them in order. Permanent fix for teams that don't want to depend on retry behavior.
- **WHY**: The retry-on-known-error pattern is exactly what a hook is for; the refactor script handles teams that need deterministic single-pass deploys. Both layers are useful; either alone leaves a gap.

---

## D7 — Azure AD SCIM: nested groups don't sync, "external" group membership is immutable in Databricks

**Domain:** scim-sso
**Trigger:** Org standardizes Databricks group membership in Azure AD (Entra ID). Either (a) adds a nested AD group to an explicitly-assigned Databricks group, or (b) tries to add a user to a synced group from inside Databricks via the SCIM API or admin UI.
**Symptom:**

- Nested-group case: the parent group syncs, but its child-group members never appear in Databricks. No error, just missing users. Hours wasted before discovering the docs note.
- Membership-modification case:

```
InternalError: None Error in performing the patch operation on group resource.
```

when calling `w.groups.patch(...)` from the SDK, the SCIM REST API, the account console UI, or the workspace admin settings. All four surfaces fail the same way.

- Sync windows are 20-40 minutes; no programmatic way to confirm a specific change has landed. Workflow: change AD → wait → grep → re-wait.

**Root cause:**

- Microsoft Entra ID's Databricks SCIM Provisioning Connector only enumerates *direct* members of an explicitly-assigned group; it does not flatten nested groups. Hard architectural limit of the connector.
- Groups synced from an IdP are flagged "External" in Databricks; membership is locked to the IdP as the source of truth. Documented design choice, not a bug.

**Blast radius:** Account-wide identity hygiene. Affects every catalog GRANT, cluster policy, workspace ACL — every access decision flows through these groups.
**Current workaround (manual):**

1. Flatten group structure in AD so every Databricks-assigned group has only user members (eliminate nesting on the Databricks side).
2. Or: bypass the Entra SCIM connector entirely — use the Databricks Terraform provider against the SCIM API, walk nested groups in code, and sync membership on a cron. Loses the IdP-as-source-of-truth invariant.
3. Or: create Databricks-native account groups (not synced) for the few cases that need in-Databricks management.
4. For sync-timing visibility: poll the SCIM API after a known-good change with exponential backoff until the user appears.

**Citations:**

- https://docs.databricks.com/aws/en/admin/users-groups/scim/aad
- https://community.databricks.com/t5/administration-architecture/unable-to-add-users-to-azure-ad-synced-databricks-group-via-scim/td-p/147917
- https://community.databricks.com/t5/technical-blog/how-to-sync-nested-azure-ad-groups-to-databricks/ba-p/44007
- https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/scim/

**Response architecture recommendation:**
SKILL.md + MCP server + scripts/.

- **MCP server (`databricks-scim-bridge`)**: exposes tools `list_group_members(group_name)`, `flatten_ad_group(ad_group_id)`, `force_scim_sync()`, `wait_for_user(email, max_seconds)`. Wraps Microsoft Graph + Databricks SCIM APIs. Encapsulates the auth glue so the agent doesn't have to.
- **`scripts/sync-nested-ad-groups.py`**: cron-driven flattener that walks nested AD groups via Microsoft Graph and syncs membership via the Databricks SCIM API, idempotent. Owned by platform team.
- **WHY**: SCIM operations span two APIs (Microsoft Graph + Databricks SCIM) with different auth flows, both polled over long windows. An MCP server is the right primitive when the agent needs to interactively query both surfaces with consistent auth; the cron script handles the steady-state mismatch nested-group bug.

---

## D8 — Customer-managed KMS key rotation requires terminating every cluster / pool / warehouse in the workspace

**Domain:** secrets-networking
**Trigger:** Security team rotates the customer-managed KMS key for managed disks (annual rotation, post-incident, compliance requirement). Or AWS automatic key rotation flips the underlying KMS material.
**Symptom:**

- Cluster start fails: `Cloud Provider Launch Failure: KeyVaultAccessForbidden` if the new key version doesn't have GET/WRAPKEY/UNWRAPKEY granted to the Databricks managed identity.
- For Azure managed-disk CMK: "To update a workspace with a customer-managed key for managed disks, all compute resources (clusters, pools, and SQL warehouses) in your workspace must be terminated." Translates to a hard maintenance window on every workspace using the key.
- For storage CMK on AWS: cannot rotate the key at all once configured — only the master-key material under it rotates automatically.
- Old key must remain available for at least 24 hours after rotation; deleting too early bricks running clusters.

**Root cause:** CMK is wired into the disk/storage encryption envelope at compute-creation time. Compute can't pick up a new key reference mid-life — the only safe path is termination + recreation. Storage CMK has an even stricter constraint: the key reference is set at workspace creation and is immutable.
**Blast radius:** Workspace-wide. Every running notebook, job, and SQL warehouse on every cluster in the workspace must be stopped during the rotation window. Multi-team / 24x7 workspaces have no clean maintenance window.
**Current workaround (manual):**

1. Schedule a maintenance window communicated to every team using the workspace.
2. Drain jobs (pause schedulers, wait for in-flight to complete).
3. Terminate every cluster, pool, and SQL warehouse manually.
4. Rotate the key in the cloud KMS; grant the new key version's permissions to the Databricks managed identity *before* the rotation completes.
5. Update the workspace via the Account API to point at the new key.
6. Keep the old key enabled for 24+ hours.
7. Recreate / restart everything.

**Citations:**

- https://docs.databricks.com/aws/en/security/keys/configure-customer-managed-keys
- https://learn.microsoft.com/en-us/azure/databricks/security/keys/cmk-managed-disks-azure/cmk-managed-disks-azure
- https://kb.databricks.com/clusters/cluster-restart-fails
- https://community.databricks.com/t5/community-discussions/need-guidance-on-key-rotation-process-for-storage-customer/td-p/64863

**Response architecture recommendation:**
SKILL.md + Slash command + scripts/ + references/.

- **Slash command `/cmk-rotation-plan`**: takes a workspace ID + target key version, produces an end-to-end runbook: drain order, expected duration per cluster type, rollback plan, validation queries. Outputs a markdown checklist the operator runs against.
- **`scripts/drain-workspace.py`**: pauses every Jobs scheduler, waits for in-flight to complete with a configurable max wait, terminates clusters/pools/warehouses in dependency order. Idempotent. Has a dry-run mode.
- **`references/cmk-rotation-by-cloud.md`**: per-cloud (AWS managed disks vs storage, Azure Key Vault, GCP CMEK) playbook with exact API calls and the 24-hour overlap requirement.
- **WHY**: This is a rare, high-blast-radius, multi-step operation where checklist discipline matters more than automation. A slash command produces the runbook artifact; a drain script handles the mechanical part safely. Hooks would be wrong (no recurring trigger); MCP would be overkill (no agent dialog needed).

---

## D9 — PrivateLink without S3/STS/Kinesis VPC endpoints silently routes through NAT and racks up egress

**Domain:** secrets-networking
**Trigger:** Team enables Databricks PrivateLink for the control-plane connection (front-end + back-end), assumes "all traffic is private now," but does not separately configure VPC endpoints for AWS services (S3, STS, Kinesis).
**Symptom:** No errors. Jobs run normally. Then the AWS bill arrives showing massive NAT-gateway data-processing charges and cross-AZ data-transfer charges. Or, after locking down egress per security policy, jobs start failing with S3 timeouts because the NAT was the only path out and egress is now blocked.
**Root cause:** Databricks PrivateLink covers the *control-plane* (workspace web app, REST API, compute-plane → control-plane) and optionally the *secure cluster connectivity* relay. It does *not* automatically route data-plane traffic to S3/STS/Kinesis privately — those need their own VPC endpoints. Without them, S3 reads/writes traverse the NAT, costing $0.045/GB processed in addition to per-GB egress. Many teams discover this only on month-end billing review.
**Blast radius:** Account-wide cost; workspace-wide reliability if egress later restricted.
**Current workaround (manual):**

1. Add VPC endpoints for **S3 (gateway endpoint — free)**, **STS (interface endpoint)**, **Kinesis (interface endpoint)** in every VPC that runs a Databricks compute plane.
2. Update VPC route tables to send S3 traffic to the gateway endpoint.
3. Validate by checking VPC Flow Logs that S3 traffic is no longer hitting the NAT.
4. For Azure: equivalent is private endpoints for ADLS Gen2 + KeyVault + the relevant data services.
5. Document the endpoint inventory because it's not obvious from the Databricks console.

**Citations:**

- https://docs.databricks.com/aws/en/security/network/classic/privatelink
- https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management
- https://www.databricks.com/blog/optimizing-aws-s3-access-databricks
- https://docs.databricks.com/aws/en/security/network/deployment-architecture/hardened-connectivity

**Response architecture recommendation:**
SKILL.md + scripts/ + references/.

- **`scripts/audit-vpc-endpoints.py`**: walks every VPC associated with a Databricks workspace (via the Account API + AWS Describe APIs), produces a checklist: S3 gateway ✓/✗, STS interface ✓/✗, Kinesis interface ✓/✗, route-table coverage ✓/✗. Emits remediation Terraform.
- **`references/cost-leak-map.md`**: itemizes every known networking-cost-leak pattern (NAT data processing, cross-AZ DTO, IGW egress) with the AWS bill line item each maps to. Cross-cloud (Azure NAT Gateway pricing, GCP NAT) included.
- **WHY**: This is a static, deterministic check; the right primitive is a script + a reference doc, not a hook (it's not action-triggered) or an MCP (no interactive dialog needed).

---

## D10 — `system.billing.usage` invisible to anyone without metastore-admin role

**Domain:** workspace-ops
**Trigger:** Finance / FinOps / platform team gets the request "tell us our Databricks spend by job by team this month." They grant themselves Account Admin in the account console, open a notebook, and try to `SELECT * FROM system.billing.usage`.
**Symptom:**

- Query fails with `SCHEMA_NOT_FOUND` or `Table or view not found: system.billing.usage`, even though the account console clearly shows the user as Account Admin.
- `SHOW CATALOGS` does not list `system` at all.
- After much searching, docs reveal the user *also* needs the **metastore admin** role (a separate role at the UC metastore level), and the metastore admin has to explicitly enable the `system.billing` schema (it's gated per-schema).

**Root cause:** Two layered access controls. (1) Account Admin gives org-level account API access but does *not* grant UC privileges. (2) System tables are gated *per schema* — each one (billing, access, lineage, compute) has to be enabled by a metastore admin before any user can be granted access. (3) Even after enabling, end users need `USE CATALOG system` + `USE SCHEMA system.billing` + `SELECT` on the relevant tables — all of which only a metastore admin can grant.
**Blast radius:** Workspace-wide visibility blind spot. FinOps cannot do its job without involving a metastore admin for every new query consumer.
**Current workaround (manual):**

1. Identify the metastore admin (often a different person from the account admin in mature orgs).
2. Metastore admin enables the system schemas via the Account API (`PUT /api/2.0/accounts/<id>/metastores/<id>/systemschemas/<schema>`).
3. Metastore admin grants `USE CATALOG system`, `USE SCHEMA system.billing`, `SELECT ON system.billing.usage` to a dedicated FinOps group.
4. Add FinOps users to the group via the IdP (per D7, can't add them directly if it's an external group).
5. Document the audit trail because the org will get this request again.

**Citations:**

- https://docs.databricks.com/aws/en/admin/system-tables/
- https://docs.databricks.com/aws/en/admin/system-tables/billing
- https://community.databricks.com/t5/administration-architecture/access-to-system-billing-usage-tables/td-p/100955
- https://docs.databricks.com/aws/en/admin/usage/system-tables

**Response architecture recommendation:**
SKILL.md + scripts/ + Subagent.

- **`scripts/enable-system-schemas.py`**: account-admin-runnable, enables every system schema (or a chosen subset), grants `SELECT` on the expected tables to a configurable group, emits the audit log.
- **Subagent (`uc-permission-tracer`)**: given a user + an error message, walks the two-level access model (account role → metastore role → catalog/schema/table grant chain) and produces a remediation diff: "user X needs Y group membership AND grant Z run by metastore admin W." Replaces 90 minutes of doc-spelunking per support ticket.
- **WHY**: Layered access control is exactly the surface where an agent dialog outperforms a static reference — the question is always "why does *this user* not see *this thing*," and the answer is a graph traversal. Subagent keeps that traversal out of the main context.

---

# Source gaps and follow-on research notes

1. **Reddit r/databricks was thin on indexed results** for direct pain-point queries (web-search engine didn't surface them well). Worth a manual pass through the subreddit's "top" sort for the last 12 months — likely 5-10 more entries hiding there, especially on DAB and SCIM.
2. **Azure-specific KMS rotation incidents** are documented in Microsoft Q&A more than Databricks docs; the Microsoft Learn Q&A search engine isn't indexed in standard web search well. Direct browsing would surface more.
3. **GCP-specific pain** is under-represented vs. AWS/Azure — Databricks on GCP has the smallest install base and the thinnest community. If the skill pack targets GCP equally, a dedicated GCP-only pass is warranted.
4. **Stack Overflow `[databricks-unity-catalog]` tag** has ~600 questions; only the top ~20 got direct attention here. A bulk pull + classification (similar to what UCX does for tables) would surface long-tail patterns.
5. **DAIS 2024-2025 video talks** were not transcribed in this pass — operator war stories from those decks are not captured. Cost: 4-6 hours of transcript scraping.
6. **`databricks/databricks-sdk-py` issues** were not pulled in this pass; that repo has a different shape of pain (Python ergonomics, async issues) that may merit its own domain entry if the skill pack covers SDK consumers as a persona.
7. **Bundle "direct" engine known-bug inventory** (referenced in D5) deserves its own entry as the engine matures; right now it's a moving target — the bug list will be different in 90 days.
