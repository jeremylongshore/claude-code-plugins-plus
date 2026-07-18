# Databricks Cluster Termination-Reason Codebook

When a cluster dies, the console rarely explains why in English — it shows a
short `termination_reason.code` and a `type`, and the operator is left to
translate. This is that translation table: for each real code, what it means,
the likely underlying cause(s), and the concrete next diagnostic step or fix.

**Where the code appears.** Every cluster terminates with a `TERMINATING` event
in the cluster event log. Read it three ways:

- **UI:** cluster page → *Event log*, or the "Termination reason" banner on a
  stopped cluster; a failed job run shows the same block under its run detail.
- **REST:** `POST /api/2.1/clusters/events` with `event_types: ["TERMINATING"]`
  — each event carries `details.reason` with `code`, `type`, and `parameters`.
- **Jobs:** the run's `cluster_instance` → the same `termination_reason` object.

A representative reason object looks like this:

```json
{
  "code": "CLOUD_PROVIDER_LAUNCH_FAILURE",
  "type": "CLOUD_FAILURE",
  "parameters": {
    "databricks_error_message": "Error: not enough IP addresses in subnet ...",
    "azure_error_code": "SubnetIsFull"
  }
}
```

## Reading a termination reason

Two fields disambiguate faster than the `code` itself:

- **`type`** buckets the fault by owner: `SUCCESS` (expected/clean),
  `CLIENT_ERROR` (your config — non-retryable until you fix it), `CLOUD_FAILURE`
  (the cloud provider rejected or reclaimed capacity), `SERVICE_FAULT`
  (Databricks-side). A `SUCCESS` termination is never an incident.
- **`parameters.databricks_error_message`** is the free-text detail the platform
  captured from the cloud API. On the two umbrella codes below it is the single
  most load-bearing field — the `code` is generic, the message names the actual
  cause (`SubnetIsFull`, `QuotaExceeded`, DNS name, blocked port). Always read it
  before touching infrastructure. Cloud-specific keys (`azure_error_code`,
  `aws_api_error_code`, `gcp_error_code`) frequently ride alongside it.

Rule of thumb: `SUCCESS` → not a failure, stop here. `CLIENT_ERROR` → your VNet /
init script / spec, and it will recur until fixed. `CLOUD_FAILURE` → capacity or
provider event, often transient and retryable. `SERVICE_FAULT` → open a support
case with the event JSON.

Error strings below marked *(representative)* are accurate paraphrases — exact
wording drifts across DBR versions and clouds; do not quote them as literals.
Codes marked *(representative)* are real families whose exact spelling varies by
cloud/version — verify against the live event before scripting on them.

## User / expected terminations (`type: SUCCESS`)

These are not failures. If an alert fired on one, the alert is wrong.

| Code | Meaning | Disambiguating check | Fix |
| --- | --- | --- | --- |
| `USER_REQUEST` | A human or API call stopped the cluster. | `parameters.user` / the audit log `deleteCluster` action names who. | None. Expected. If unexpected, find the caller in the audit log. |
| `INACTIVITY` | Auto-termination fired after the idle window elapsed. | `parameters.inactivity_duration_min` shows the idle minutes; matches the cluster's `autotermination_minutes`. | None — this is the feature working. Raise `autotermination_minutes` only if restarts hurt. |
| `JOB_FINISHED` *(representative)* | A job cluster shut down after its run completed. | Present only on ephemeral job clusters; the run status is `SUCCESS`/`FAILED` independently. | None. Job-cluster lifecycle. |

## Cloud-provider terminations (`type: CLOUD_FAILURE`)

The VM layer, not Databricks, ended or refused the instances.

| Code | Meaning | Disambiguating check | Fix |
| --- | --- | --- | --- |
| `CLOUD_PROVIDER_SHUTDOWN` | The cloud provider stopped a running VM out from under the cluster (host maintenance, hardware fault, underlying VM deallocated). | Cross-reference the cloud's service-health / maintenance events for that VM at the timestamp; distinct from spot reclaim (that has its own code). | Usually transient — restart. If chronic on one instance type/region, switch type or AZ. On-demand VMs should not see this often. |
| `SPOT_INSTANCE_TERMINATION` | Spot / preemptible capacity was reclaimed by the provider (price/capacity). | The cluster used spot workers (`aws_attributes.availability` spot, Azure spot, GCP preemptible); often only workers die, not the driver. | Expected with spot. Put the driver on-demand, use spot for workers only, or fall back to on-demand. Retry is fine. |
| `CLOUD_PROVIDER_LAUNCH_FAILURE` | The provider refused to launch the requested instances at start-up. **Umbrella — five distinct causes.** | Read `databricks_error_message` + `azure_error_code` / `aws_api_error_code` / `gcp_error_code`. See the umbrella section. | Depends entirely on the sub-cause — see below. Do not blind-retry. |
| `INSTANCE_POOL_CLUSTER_FAILURE` | The cluster draws from an instance pool and the pool could not supply instances. | Inspect the pool's own event log; `INSTANCE_POOL_MAX_CAPACITY_FAILURE` *(representative)* means the pool `max_capacity` was hit, vs the pool itself failing to expand against the cloud. | Raise pool `max_capacity`, widen instance types, or check the pool's cloud errors (same causes as launch failure). |

## Network / NPIP terminations

The cluster could not establish or keep its control-plane connection. In a
secure-cluster-connectivity (NPIP / "no public IP") workspace, every worker VM
opens a reverse tunnel to the SCC relay in the control plane; if that tunnel
never comes up, the cluster is torn down.

| Code | Meaning | Disambiguating check | Fix |
| --- | --- | --- | --- |
| `NPIP_TUNNEL_SETUP_FAILURE` | The SCC reverse tunnel from the VMs to the control-plane relay never established at start-up. **Umbrella — five distinct causes.** | Read `databricks_error_message`; the cause is almost always egress/DNS/route, not the cluster. See the umbrella section. | Depends on sub-cause — DNS, NSG/SG egress, route/NAT, subnet. See below. |
| `NPIP_TUNNEL_TOKEN_FAILURE` *(representative)* | The tunnel auth token could not be obtained/validated — a narrower NPIP failure than setup. | Usually a control-plane reachability or clock/identity issue distinct from raw egress; check egress to the relay + token endpoint. | Same network remediation as tunnel-setup; if egress is clean, open a support case. |
| `COMMUNICATION_LOST` | The control plane lost contact with an already-running driver for long enough to declare it dead. | Was the cluster healthy first, then lost (network flap / NAT idle-timeout / driver hang) vs never connected (that is a tunnel/bootstrap code)? Check node timeline for the last heartbeat. | Investigate NAT gateway idle timeout, firewall session limits, or a driver OOM that froze heartbeats (overlaps with driver codes). |

## Driver, bootstrap, and internal faults

The instances launched, but the Spark driver / runtime never became healthy.

| Code | Meaning | Disambiguating check | Fix |
| --- | --- | --- | --- |
| `DRIVER_UNRESPONSIVE` | The driver stopped responding to health checks (commonly driver OOM or a full GC pause). | Driver logs (`log4j`, `stdout`) + node timeline: look for OOM kill, GC thrash, or a runaway `collect()`/`toPandas()` pulling data to the driver. | Right-size the driver, stop collecting large results to the driver, fix the OOM. Not a retry. |
| `DRIVER_UNAVAILABLE` *(representative)* | The driver process/host became unavailable (crashed or the driver VM was lost). | Distinguish a host loss (see cloud events) from a process crash (driver logs). Pairs closely with `DRIVER_UNRESPONSIVE`. | If host loss → restart; if process crash → treat like the unresponsive case (memory/workload). |
| `BOOTSTRAP_TIMEOUT` | The cluster did not reach a ready state within the bootstrap window (VMs up but Spark never fully started). | Read `databricks_error_message`: slow VM provisioning (capacity), a hanging global/named init script, or slow metastore/DBFS mounts. Overlaps with init-script + capacity. | Speed up or fix init scripts, use a pool for warm instances, check region capacity; retry if it was a transient slow launch. |
| `INTERNAL_ERROR` | A Databricks-side error terminated the cluster (`type: SERVICE_FAULT`). | Nothing in your config to read — capture the full event JSON and timestamp. | Retry once; if it recurs, open a support case with the event payload. Do not chase it as a config bug. |

## Init-script failures

| Code | Meaning | Disambiguating check | Fix |
| --- | --- | --- | --- |
| `INIT_SCRIPT_FAILURE` | A cluster-scoped or global init script exited non-zero, so the node failed to start. | The event `parameters` name the failing script path; read that script's output under the cluster log-delivery destination (`dbfs:/cluster-logs/<id>/init_scripts/` or the configured path). | Fix the script (a failing `apt-get`/`pip install`, a bad download URL, a missing secret). Test on one node before rolling out. |
| `GLOBAL_INIT_SCRIPT_FAILURE` *(representative)* | A workspace-global init script failed — blast radius is every cluster, not one. | Same log path, but the culprit is an admin-owned global script; correlate with a recent global-init-script change. | Fix or disable the offending global init script in Admin Settings; it is breaking all clusters, so treat as a workspace incident. |

## The `CLOUD_PROVIDER_LAUNCH_FAILURE` / `NPIP_TUNNEL_SETUP_FAILURE` umbrella

These two codes are where most real cluster-launch incidents land, and both are
deceptively generic — the same networking mistake surfaces as a *launch* failure
if it blocks the VM from starting, or a *tunnel* failure if the VM starts but
cannot reach the control-plane relay. Five distinct root causes hide under them.
**Always read `parameters.databricks_error_message` first** — it names which one.

Rough split: IP exhaustion, a deleted subnet, and capacity/quota tend to surface
as `CLOUD_PROVIDER_LAUNCH_FAILURE` (the VM never comes up); custom-DNS and
NSG/route egress blocks tend to surface as `NPIP_TUNNEL_SETUP_FAILURE` (the VM
came up but cannot phone home). Any of the five can appear under either code, so
disambiguate by the message and the checks below, not by the code name.

Cloud terminology map: Azure *VNet / subnet / NSG*; AWS *VPC / subnet / security
group + NACL*; GCP *VPC / subnetwork / firewall rule*.

### Cause 1 — Subnet / IP-address exhaustion

The VNet/VPC subnet the workspace launches into ran out of free private IPs, so
no new worker (or driver) can get an address.

- **Message fragment** *(representative)*: `not enough available IP addresses in subnet`; `azure_error_code: SubnetIsFull`; GCP `IP_SPACE_EXHAUSTED`.
- **Disambiguating check.** Read the subnet's free-IP count directly: Azure portal subnet blade *Available IPs*; AWS `aws ec2 describe-subnets --subnet-ids <id> --query 'Subnets[].AvailableIpAddressCount'`; GCP check the subnetwork range utilization. Databricks reserves ~2 IPs per node (plus overhead) — a `/26` caps you far below what operators expect. Correlate the failure timestamp with a scale-up.
- **Fix.** Move the workspace to a larger subnet (Azure requires this for the host/container subnets), or cap `max_workers`/pool size to fit. There is no in-place subnet resize on Azure Databricks-managed VNets — plan the CIDR up front.

### Cause 2 — Custom DNS resolution failure

The VNet uses custom DNS servers that cannot resolve the Databricks control-plane
/ SCC-relay / managed-storage hostnames, so the tunnel target never resolves.

- **Message fragment** *(representative)*: `could not resolve host` / `name resolution failed` for a `*.databricks.com` / relay / storage FQDN — classic `NPIP_TUNNEL_SETUP_FAILURE`.
- **Disambiguating check.** From a VM in the same subnet (or a diagnostic instance), resolve the region's control-plane, SCC-relay, and workspace-storage FQDNs. If the VNet points at on-prem/custom DNS, confirm that resolver forwards the required zones (and Azure Private DNS / PrivateLink zones when using Private Link). A launch that fails only after custom DNS was introduced is the tell.
- **Fix.** Add conditional forwarders (or the required Private DNS zone links) so the custom resolver answers the Databricks control-plane and PrivateLink names; or fall back to Azure/AWS-provided DNS for those zones.

### Cause 3 — NSG / security-group rule blocking required traffic

A network security group, security group + NACL, or firewall rule blocks the
outbound 443 (and PrivateLink relay ports) the tunnel needs, or the inbound
intra-subnet traffic the nodes need.

- **Message fragment** *(representative)*: tunnel setup timed out / connection refused to the relay endpoint — `NPIP_TUNNEL_SETUP_FAILURE` with no DNS error.
- **Disambiguating check.** Verify egress `443` to the control-plane + SCC relay is allowed (Azure: the `AzureDatabricks` service tag / relay addresses; AWS PrivateLink SCC also needs the relay VPC-endpoint reachable, typically port `6666`; GCP: egress firewall to the control-plane range). Confirm the Databricks-required intra-subnet allow rules were not overwritten by a custom deny-all. A `curl -v https://<relay-endpoint>:443` from a same-subnet VM that hangs pins it.
- **Fix.** Restore the required NSG/SG/firewall allow rules (do not delete the Databricks-managed rules); for PrivateLink workspaces confirm the relay + workspace VPC endpoints are healthy and their SG allows the relay port.

### Cause 4 — Deleted / dangling VNet or subnet reference

The workspace config still points at a VNet/subnet (or route table) that was
deleted or renamed, so the launch request references infrastructure that no
longer exists.

- **Message fragment** *(representative)*: `subnet not found` / `referenced resource ... does not exist` / `InvalidSubnetID.NotFound` — surfaces as `CLOUD_PROVIDER_LAUNCH_FAILURE`.
- **Disambiguating check.** Compare the workspace's configured host/container subnet IDs (VNet-injection config) against what actually exists in the cloud (`az network vnet subnet show`, `aws ec2 describe-subnets`, `gcloud compute networks subnets describe`). A recent Terraform/IaC apply that recreated the VNet with a new ID is the usual trigger.
- **Fix.** Re-point the workspace to the current subnet IDs (or restore the referenced resource). Treat VNet/subnet as immutable dependencies of the workspace; never let IaC recreate them under a live workspace.

### Cause 5 — Cloud-provider capacity throttling / quota

The provider had no capacity for the requested instance type in the region/AZ, or
the subscription/account hit a vCPU or API-rate quota.

- **Message fragment** *(representative)*: Azure `QuotaExceeded` / `AZURE_QUOTA_EXCEEDED_EXCEPTION`, `SkuNotAvailable`; AWS `InsufficientInstanceCapacity` / `AWS_INSUFFICIENT_INSTANCE_CAPACITY_FAILURE`, `RequestLimitExceeded`; GCP `QUOTA_EXCEEDED` / `ZONE_RESOURCE_POOL_EXHAUSTED`. All surface as `CLOUD_PROVIDER_LAUNCH_FAILURE` (`type: CLOUD_FAILURE`).
- **Disambiguating check.** Distinguish *quota* (raiseable via a support/quota request — the account limit is the wall) from *capacity* (the region/AZ is simply out — a quota bump won't help). The error family names which: `QuotaExceeded` vs `InsufficientCapacity`/`SkuNotAvailable`.
- **Fix.** Quota → file a limit increase for that VM family. Capacity → switch instance type, region, or AZ; use an instance pool to hold warm capacity; or retry (capacity is transient). Do not tight-loop retry on a quota error — it will never clear on its own.

## Other codes you may encounter

Real but rarer — verify the exact spelling against the live event before
scripting on any tagged *(representative)*.

| Code | Meaning | First check |
| --- | --- | --- |
| `TRIAL_EXPIRED` | The Databricks trial/subscription lapsed; clusters will not launch. | Billing/subscription state, not infrastructure. |
| `CONTAINER_LAUNCH_FAILURE` *(representative)* | A Databricks Container Services custom image failed to pull/launch. | The image ref + registry auth; the init/bootstrap logs. |
| `METASTORE_COMPONENT_UNHEALTHY` *(representative)* | The workspace's built-in Hive metastore backend was unreachable at start-up. | Usually a transient service fault — retry; if chronic, support case. |
| `SELF_BOOTSTRAP_FAILURE` *(representative)* | A node's own bootstrap failed before Spark started. | Node/bootstrap logs; overlaps with init-script + capacity. |
| `REQUEST_REJECTED` *(representative)* | Databricks rejected the launch request (control-plane throttle or workspace state). | Workspace status + any concurrent bulk launch; retry after backoff. |
| `SECURITY_DAEMON_REGISTRATION_EXCEPTION` *(representative)* | The node's security daemon failed to register (secure-connectivity path). | Same egress/DNS checks as the NPIP umbrella. |

## Sources

- Databricks — *Cluster termination reasons* / `TerminationReason` codes and
  `TerminationType` (`SUCCESS`/`CLIENT_ERROR`/`CLOUD_FAILURE`/`SERVICE_FAULT`),
  docs.databricks.com clusters reference.
- Databricks — *Clusters API 2.1* `clusters/events` (`TERMINATING` event,
  `details.reason.code` / `type` / `parameters.databricks_error_message`).
- Databricks — *Secure cluster connectivity (no public IP / NPIP)* and *Enable
  secure cluster connectivity* — SCC relay, tunnel setup, required egress.
- Databricks — *Troubleshoot cluster launch* / *Cluster failures* KB: subnet IP
  exhaustion, custom DNS, NSG/egress, deleted subnet references.
- Azure Databricks — *VNet injection*, *NSG rules for Databricks*, and quota /
  `SubnetIsFull` / `SkuNotAvailable` guidance, learn.microsoft.com.
- AWS / GCP Databricks — customer-managed VPC networking + capacity/quota error
  families (`InsufficientInstanceCapacity`, `QUOTA_EXCEEDED`), docs.databricks.com.
- community.databricks.com — `CLOUD_PROVIDER_LAUNCH_FAILURE` and
  `NPIP_TUNNEL_SETUP_FAILURE` diagnosis threads (IP exhaustion, DNS, NSG, deleted
  subnet, capacity).
