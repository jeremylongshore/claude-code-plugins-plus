# Customer-managed key (CMK) rotation — the full-drain, per-cloud playbook

Rotating a workspace's customer-managed key is the rare Databricks operation whose blast
radius is the **entire workspace**, not one cluster or one job. The load-bearing fact under
every playbook below: **a running cluster binds its disk-encryption key reference once, at
boot, and never re-reads it.** There is no live re-key of an in-flight VM. So the only safe
path to move a workspace onto a new key version is _terminate every compute resource, swap
the key, bring everything back_ — a hard maintenance window that a multi-team, 24x7 workspace
cannot casually absorb. This reference is the per-cloud mechanics (AWS KMS, Azure Key Vault,
GCP Cloud KMS), the account-level API surface each rotation is driven from, and the
drain-then-resume discipline the skill's `scripts/drain-workspace.py` automates.

Two things trip teams up on this operation, repeatedly:

- **Not every key a workspace holds forces the drain.** The managed-services key rotates
  live; only the storage/disk key needs the outage. Conflating the two turns a zero-downtime
  change into an unnecessary maintenance window (or, worse, plans a maintenance window and
  then discovers mid-flight that the disk key needs a _second_ one).
- **The rotation is driven from the account level, not the workspace.** A workspace-scoped
  personal access token (PAT) is the wrong credential and fails with a permission error that
  reads like a bug rather than "you used the wrong token type."

## The three key types a workspace can have — and which one forces the drain

A Databricks workspace can be wired to as many as three distinct customer-managed keys, and
they sit at different layers of the stack. Only one of them requires the outage.

- **Managed-services key** (`use_cases: ["MANAGED_SERVICES"]`) — encrypts control-plane
  secrets: notebook source and results, the secret store, Databricks SQL query text and query
  history, personal access tokens, and Git credentials. It lives entirely in the **control
  plane**; no cluster ever holds a reference to it. **Rotating or updating this key does NOT
  require terminating compute** — the control plane re-wraps against the new key version in
  place, and running clusters never notice.
- **Workspace-storage / DBFS-root key** (`use_cases: ["STORAGE"]`) — encrypts the workspace
  root bucket: the DBFS root, cluster and job logs, and any Delta tables written to the root.
  The reference is established when the workspace storage is provisioned. On Azure the
  DBFS-root CMK is fixed at **workspace creation** and is effectively immutable afterward; on
  AWS/GCP adding or changing the storage key on an existing workspace is constrained (see the
  per-cloud sections and the anchors below).
- **Cluster-volume / managed-disk key** — encrypts the local disks attached to compute: **EBS
  volumes on AWS, managed disks on Azure, persistent disks on GCP**. On AWS this is the same
  `STORAGE` key when `reuse_key_for_cluster_volumes: true`; on Azure it is a separate
  managed-disk CMK. **This is the key that forces the full drain.** A cluster reads the
  disk-key reference at launch and encrypts its scratch/spill volumes against that version for
  the life of the VM. It cannot re-point mid-life, so the workspace update that swaps the key
  is rejected while any compute is running.

The rotation-requirement matrix, condensed:

| Key type | Encrypts | Set / rotated via | Requires full drain? |
| --- | --- | --- | --- |
| Managed services | Notebooks, secrets, SQL query history, PATs, Git creds | Account API workspace `PATCH` (live) | No — control-plane re-wrap |
| Workspace storage / DBFS root | Root bucket, DBFS root, cluster + job logs | Provisioning time; AWS/GCP add/update constrained, Azure immutable after create | Partial — see per-cloud notes |
| Cluster volumes / managed disks | EBS (AWS) / managed disks (Azure) / PDs (GCP) | Account API (AWS/GCP) · ARM (Azure) | **Yes — every cluster, pool, warehouse terminated** |

The mental model: **managed-services = control plane = live rotate. Disk/EBS = data plane =
boot-time binding = drain.** When someone says "we just need to rotate our Databricks CMK,"
the first question is always _which key_ — because the answer decides whether you need a
change window at all.

## Account API surface and identity — why a workspace PAT is the wrong key

On AWS and GCP the CMK configuration is an **account-level** object, so it is created and
attached through the Databricks **Account API** (`accounts.cloud.databricks.com` for AWS,
`accounts.gcp.databricks.com` for GCP _(verify)_), never the per-workspace REST API. That has
a hard identity consequence: **a workspace-scoped PAT cannot call these endpoints.** You need
an **account admin** identity, and the supported non-interactive path is **OAuth
machine-to-machine (M2M)** — an account-level service principal with a client ID + secret,
granted account admin, exchanging its credentials for a short-lived OAuth token:

```bash
# OAuth M2M token exchange (AWS account host shown; swap host for GCP)
curl --request POST \
  "https://accounts.cloud.databricks.com/oidc/accounts/${ACCOUNT_ID}/v1/token" \
  --user "${CLIENT_ID}:${CLIENT_SECRET}" \
  --data 'grant_type=client_credentials&scope=all-apis'
```

The customer-managed-keys surface on the Account API:

```text
POST   /api/2.0/accounts/{account_id}/customer-managed-keys
GET    /api/2.0/accounts/{account_id}/customer-managed-keys
GET    /api/2.0/accounts/{account_id}/customer-managed-keys/{customer_managed_key_id}
DELETE /api/2.0/accounts/{account_id}/customer-managed-keys/{customer_managed_key_id}
```

Attaching a key to a workspace — the step the drain exists to protect — is a workspace update,
setting the `storage_customer_managed_key_id` and/or `managed_services_customer_managed_key_id`
fields:

```text
PATCH  /api/2.0/accounts/{account_id}/workspaces/{workspace_id}
GET    /api/2.0/accounts/{account_id}/workspaces/{workspace_id}
```

The Databricks CLI wraps the same surface as `databricks account encryption-keys
{create,list,get,delete}` and `databricks account workspaces update` _(verify)_ — same OAuth
M2M identity, same account host. **Azure is the exception to everything in this section**: its
CMK is an ARM operation, not an Account API call — see its section below.

## AWS — KMS

On AWS the storage key and the cluster-EBS key are the same `STORAGE`-use-case CMK config when
`reuse_key_for_cluster_volumes: true`. Because the EBS side binds at cluster boot, an EBS/root
key change is the classic full-drain rotation. Sequence:

- **Prepare the key.** Create the new AWS KMS key (or roll to a new version) in the **same
  region** as the workspace. Grant the Databricks cross-account IAM role the KMS actions it
  needs — `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey*`, `kms:DescribeKey`, and the
  grant-creation actions EBS requires (`kms:CreateGrant`, `kms:ListGrants`,
  `kms:RevokeGrant`) _(verify the exact EBS grant set against current docs)_. **Leave the old
  key enabled.**
- **Register the CMK config.** `POST .../customer-managed-keys` with an `aws_key_info` block
  (`key_arn`, `key_alias` _(verify)_, `key_region`, `reuse_key_for_cluster_volumes`) and
  `use_cases: ["STORAGE"]`:

```json
{
  "use_cases": ["STORAGE"],
  "aws_key_info": {
    "key_arn": "arn:aws:kms:us-east-1:111122223333:key/NEW-KEY-ID",
    "key_region": "us-east-1",
    "reuse_key_for_cluster_volumes": true
  }
}
```

- **Drain the workspace.** Run `scripts/drain-workspace.py` (below). Every cluster, pool, and
  SQL warehouse must be terminated before the update will succeed.
- **Swap the key.** `PATCH .../workspaces/{workspace_id}` with
  `storage_customer_managed_key_id` set to the new config's ID. The API **rejects** this while
  any compute is live — that rejection is the platform enforcing the drain, not a transient
  error to retry.
- **Keep the old key enabled ≥24 hours.** In-flight envelope references may still resolve
  against the old key material during the cutover; deleting or disabling it too early bricks
  clusters mid-restart. Only schedule the old key for deletion after a full clean cycle.
- **Resume.** Restart pools/warehouses and un-pause schedulers (drain script `--resume`).

Note the storage-CMK constraint the research surfaced: once a workspace's storage CMK is set,
the AWS **master-key material rotates automatically** underneath it, but swapping to an
entirely different key config on an existing workspace is limited — treat a storage-key change
as a create-then-attach with the drain, and confirm current add/update support in the anchors.

## Azure — Key Vault (ARM, not the Account API)

**Azure Databricks does not use the multi-cloud Account API for CMK.** The workspace is an
Azure Resource Manager (ARM) resource (`Microsoft.Databricks/workspaces`), and its CMK settings
are ARM properties. Identity is a **Microsoft Entra ID** service principal with Contributor (or
Owner) on the workspace resource — plus the Databricks managed identity must hold **get,
wrap, and unwrap** on the Key Vault key. Grant that access **before** the update, or clusters
fail at boot with `Cloud Provider Launch Failure: KeyVaultAccessForbidden`.

Two distinct Azure CMKs, mapped to the earlier taxonomy:

- **Managed-services CMK** (control plane) — a Key Vault key referenced in the workspace
  `properties.encryption` block. Updatable **without** draining compute.
- **Managed-disk CMK** (data plane) — the one carrying the exact documented constraint: _"To
  update a workspace with a customer-managed key for managed disks, all compute resources
  (clusters, pools, and SQL warehouses) in your workspace must be terminated."_ This is the
  Azure full-drain rotation.

The DBFS-root CMK is a third case and is **fixed at workspace creation** — it cannot be added
or rotated afterward, so it is out of scope for a rotation runbook (a change means a new
workspace and a data migration).

Managed-disk rotation, in order: grant the workspace managed identity wrap/unwrap on the new
Key Vault key version → drain the workspace → update the managed-disk CMK on the ARM resource →
keep the old key version enabled ≥24h → resume. The update via CLI:

```bash
# Update the managed-disk CMK (flag names — verify against current az CLI)
az databricks workspace update \
  --resource-group "${RG}" \
  --name "${WORKSPACE_NAME}" \
  --disk-key-name "${KEY_NAME}" \
  --disk-key-vault "${VAULT_URI}" \
  --disk-key-version "${KEY_VERSION}" \
  --disk-key-auto-rotation true
```

Key Vault **auto-rotation** can generate new key versions on a schedule, but flipping managed
disks onto a newly-generated version **still requires the compute drain** — auto-rotation
schedules the material, it does not remove the boot-time binding. Do not treat "auto-rotation
is on" as "rotation is zero-downtime for disks."

## GCP — Cloud KMS (CMEK)

On GCP the CMK is a Cloud KMS CMEK key, configured through the Account API on the GCP account
host (`accounts.gcp.databricks.com` _(verify)_) with a `gcp_key_info` block carrying the KMS
key resource ID (`kms_key_id` _(verify)_). The Databricks GCP service account must hold
`roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key **before** the workspace update, or
compute launch fails on the KMS permission check.

GCP is the thinnest-documented of the three (smallest install base), so verify the exact
`gcp_key_info` field names and the account host against current docs before running. The
sequence mirrors AWS: create/rotate the Cloud KMS key → grant the Databricks service account
encrypt/decrypt → register the CMK config via `POST .../customer-managed-keys` with
`use_cases: ["STORAGE"]` → drain → `PATCH .../workspaces/{workspace_id}` with the new
`storage_customer_managed_key_id` → hold the old key ≥24h → resume. The same identity rule
applies: account-admin OAuth M2M, never a workspace PAT.

## The drain, in operational terms — `scripts/drain-workspace.py`

"Drain" is not "stop the running jobs and hope." It is a specific, ordered teardown of
**everything that holds a disk-key reference or would auto-restart into the old key**:

- **Pause every Jobs scheduler** so cron/continuous jobs do not spin up a fresh cluster
  mid-drain and re-pin the old key.
- **Wait for in-flight runs to complete** up to a configurable max wait, so you drain on a
  clean boundary instead of killing live work (or force-terminate past the deadline if the
  window is hard).
- **Terminate all compute in dependency order** — interactive and job clusters, then instance
  pools (idle pool instances also carry EBS/managed disks), then SQL warehouses. Nothing that
  holds an encrypted volume may survive into the key swap.

`scripts/drain-workspace.py` does exactly this and is **idempotent** (re-running on a
half-drained workspace converges to fully drained rather than erroring) with a **`--dry-run`**
mode that reports what _would_ be paused/terminated without touching anything — always run
`--dry-run` first against a 24x7 workspace so operators see the full blast list before the
window opens. It also drives **`--resume`**: un-pause the schedulers and restart the pools and
warehouses it stopped, so the workspace comes back in a known state instead of a partial one.
Run order for a rotation is: `--dry-run` → (open window) → drain → attach the new key via the
per-cloud step above → `--resume`.

## Maintenance-window reality for 24x7 workspaces

A shared, always-on workspace has no natural quiet moment, so the drain window is a coordination
problem more than a technical one:

- **Blast radius is total, not partial.** Every team on the workspace loses interactive
  clusters, scheduled jobs, and SQL/BI dashboards simultaneously — a CMK rotation cannot be
  scoped to one team's compute. Socialize it as a workspace-wide outage, not a background op.
- **Batch by workspace, and prefer a per-environment / per-team workspace topology.** The
  cleanest mitigation is architectural: if Dev/Test/Prod (or per-team) live in **separate
  workspaces**, each has an independent, smaller drain window instead of one estate-wide
  outage. Rotate the least-critical workspace first as a rehearsal.
- **Communicate against the estimated duration, not a guess.** Window length is dominated by
  the in-flight-drain wait plus warehouse/pool cold-start on resume, not the key swap itself
  (the `PATCH` is seconds). The `/cmk-rotation-plan` command produces the per-cluster duration
  estimate and rollback plan the announcement should quote.
- **Keep the old key alive through the whole window and 24h past it.** The single most common
  self-inflicted outage is disabling the old key immediately after the swap; hold it until a
  full clean restart cycle has been observed.

## Version-accuracy anchors

Endpoint _paths_ and _identity_ requirements are stable; the flagged items below are the exact
field/flag/host names to confirm against current docs before running — do not invent Account
API paths.

- **Account hosts** — AWS `accounts.cloud.databricks.com` (confident); GCP
  `accounts.gcp.databricks.com` _(verify)_.
- **CMK endpoints** — `/api/2.0/accounts/{account_id}/customer-managed-keys` (`POST` / `GET` /
  `GET {id}` / `DELETE {id}`) — path shape confident; confirm the `{customer_managed_key_id}`
  path parameter name.
- **Workspace attach** — `PATCH /api/2.0/accounts/{account_id}/workspaces/{workspace_id}` with
  `storage_customer_managed_key_id` and `managed_services_customer_managed_key_id` — confident
  on field names; confirm no additional required body fields on `PATCH`.
- **AWS key info** — `aws_key_info.key_arn` / `key_region` / `reuse_key_for_cluster_volumes`
  confident; `key_alias` _(verify)_; exact KMS EBS grant action set _(verify)_.
- **GCP key info** — `gcp_key_info.kms_key_id` _(verify)_; the required GCP service-account KMS
  role `roles/cloudkms.cryptoKeyEncrypterDecrypter` (confident).
- **Azure CLI** — `az databricks workspace update` disk-key flags
  (`--disk-key-name/--disk-key-vault/--disk-key-version/--disk-key-auto-rotation`) _(verify)_;
  Azure managed-disk CMK is ARM, **not** the Account API (confident).
- **CLI account wrappers** — `databricks account encryption-keys {create,list,get,delete}` and
  `databricks account workspaces update` _(verify command group spelling)_.
- **OAuth token endpoint** — `POST /oidc/accounts/{account_id}/v1/token` with
  `grant_type=client_credentials&scope=all-apis` (confident); account-admin M2M is required,
  workspace PAT is insufficient (confident).
- **24-hour overlap** — the "keep the old key enabled ≥24h" figure is per Databricks docs;
  confirm the current stated minimum before shortening any window.

## Sources

- Databricks — Configure customer-managed keys (AWS): use cases, `aws_key_info`, `reuse_key_for_cluster_volumes`, storage-vs-managed-services keys — https://docs.databricks.com/aws/en/security/keys/configure-customer-managed-keys
- Databricks Account API — customer-managed-keys + workspaces endpoints (`customer_managed_key_id`, `storage_customer_managed_key_id`, `managed_services_customer_managed_key_id`) — https://docs.databricks.com/api/account/customermanagedkeys
- Databricks — OAuth machine-to-machine (M2M) for account-level service principals — https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m
- Azure Databricks — Customer-managed keys for managed disks (the "all compute must be terminated" constraint) — https://learn.microsoft.com/en-us/azure/databricks/security/keys/cmk-managed-disks-azure/cmk-managed-disks-azure
- Azure Databricks — Customer-managed keys overview (managed services vs managed disks vs DBFS root) — https://learn.microsoft.com/en-us/azure/databricks/security/keys/
- Databricks — Configure customer-managed keys (GCP / CMEK), `gcp_key_info`, Cloud KMS role — https://docs.databricks.com/gcp/en/security/keys/customer-managed-keys
- Databricks KB — Cluster restart fails: `KeyVaultAccessForbidden` / KMS launch failure after key change — https://kb.databricks.com/clusters/cluster-restart-fails
- Databricks Community — Key rotation process for storage customer-managed keys (24-hour overlap, storage-key immutability) — https://community.databricks.com/t5/community-discussions/need-guidance-on-key-rotation-process-for-storage-customer/td-p/64863
