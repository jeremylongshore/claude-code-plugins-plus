---
name: oraclecloud-incident-runbook
description: "Self-service incident runbook for OCI outages \u2014 health probes,\
  \ instance recovery, cross-AD/region failover.\nUse when OCI instances go down,\
  \ the status page is silent, or you need automated recovery without waiting for\
  \ support.\nTrigger with \"oraclecloud incident\", \"oci outage runbook\", \"oci\
  \ failover\", \"oci instance recovery\".\n"
allowed-tools: Read, Write, Edit, Bash(oci:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Incident Runbook

## Overview

Self-service runbook for when OCI instances go down and the status page stays green. OCI's status page has a history of not acknowledging outages in real time (London Jan 2026 — 502s and instances disappearing for 10 minutes with no status update). OCI Support response times average 4+ hours for Sev-1 tickets. This runbook gives you health probes, automated instance recovery, cross-AD failover, and cross-region failover — all executable without waiting on Oracle.

**Purpose:** Detect OCI service degradation independently, recover instances automatically, and fail over to alternate availability domains or regions when the primary is impacted.

## Prerequisites

- **OCI CLI installed and configured** — `~/.oci/config` validated (see `oraclecloud-install-auth`)
- **Python 3.8+** with the OCI SDK — `pip install oci`
- **Pre-configured resources**: at least one compute instance, a VCN with subnets in multiple ADs
- **IAM policies**: `manage instances`, `manage volumes`, `inspect work-requests` in the target compartment
- **Boot volume backups** enabled (recovery depends on having a recent backup)

## Instructions

### Step 1: Independent Health Probes

Do not trust the OCI status page alone. Run your own health checks against the OCI API:

```python
import oci
import time

config = oci.config.from_file("~/.oci/config")

def probe_oci_health(config):
    """Probe OCI API endpoints independently of the status page."""
    results = {}

    # Probe 1: Identity service (lightest call)
    try:
        start = time.time()
        identity = oci.identity.IdentityClient(config)
        identity.list_regions()
        results["identity"] = {"status": "healthy", "latency_ms": int((time.time() - start) * 1000)}
    except oci.exceptions.ServiceError as e:
        results["identity"] = {"status": "degraded", "error": str(e.status)}

    # Probe 2: Compute service
    try:
        start = time.time()
        compute = oci.core.ComputeClient(config)
        compute.list_instances(compartment_id=config["tenancy"], limit=1)
        results["compute"] = {"status": "healthy", "latency_ms": int((time.time() - start) * 1000)}
    except oci.exceptions.ServiceError as e:
        results["compute"] = {"status": "degraded", "error": str(e.status)}

    # Probe 3: Networking service
    try:
        start = time.time()
        network = oci.core.VirtualNetworkClient(config)
        network.list_vcns(compartment_id=config["tenancy"], limit=1)
        results["networking"] = {"status": "healthy", "latency_ms": int((time.time() - start) * 1000)}
    except oci.exceptions.ServiceError as e:
        results["networking"] = {"status": "degraded", "error": str(e.status)}

    return results

health = probe_oci_health(config)
for service, status in health.items():
    print(f"  {service}: {status['status']} ({status.get('latency_ms', 'N/A')}ms)")
```

### Step 2: Severity Classification

| Level | Condition | Detection | Response Time |
|-------|-----------|-----------|---------------|
| **P1 — Total Outage** | All API probes fail, instances unreachable | All 3 probes return `degraded` | Immediate — trigger cross-region failover |
| **P2 — Partial Degradation** | Some APIs slow (>2s latency), instance agent unresponsive | Latency >2000ms on any probe | 15 min — attempt instance recovery, prepare failover |
| **P3 — Intermittent** | Sporadic 429/500 errors, some requests succeed | Occasional probe failures | 1 hour — enable retries, monitor trend |

### Step 3: Instance Recovery Actions

```bash
# Check current instance state
oci compute instance get --instance-id "$INSTANCE_OCID" \
  --query 'data."lifecycle-state"' --raw-output

# Action: Reset (hard reboot) — fastest recovery for hung instances
oci compute instance action --instance-id "$INSTANCE_OCID" \
  --action RESET

# Action: Reboot (graceful) — for instances still responding to ACPI
oci compute instance action --instance-id "$INSTANCE_OCID" \
  --action SOFTRESET

# Action: Stop then Start — forces reallocation to new host hardware
oci compute instance action --instance-id "$INSTANCE_OCID" \
  --action STOP
# Wait for STOPPED state
oci compute instance action --instance-id "$INSTANCE_OCID" \
  --action START
```

### Step 4: Cross-AD Failover

When an entire availability domain is impacted, launch a replacement instance in a different AD using the latest boot volume backup:

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)
blockstorage = oci.core.BlockstorageClient(config)

# Find latest boot volume backup
backups = blockstorage.list_boot_volume_backups(
    compartment_id="COMPARTMENT_OCID",
    boot_volume_id="BOOT_VOLUME_OCID",
    sort_by="TIMECREATED",
    sort_order="DESC",
    limit=1,
).data

if not backups:
    raise RuntimeError("No boot volume backups found — cannot failover")

latest_backup = backups[0]
print(f"Using backup: {latest_backup.id} from {latest_backup.time_created}")

# Launch replacement instance in alternate AD
launch_details = oci.core.models.LaunchInstanceDetails(
    availability_domain="AD-2",  # Different from the impacted AD
    compartment_id="COMPARTMENT_OCID",
    shape="VM.Standard.E4.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=2, memory_in_gbs=16),
    display_name="failover-instance",
    source_details=oci.core.models.InstanceSourceViaBootVolumeDetails(
        source_type="bootVolume",
        boot_volume_id=latest_backup.id,
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id="SUBNET_OCID_IN_AD2",
    ),
)

response = compute.launch_instance(launch_details)
print(f"Failover instance launching: {response.data.id}")
```

### Step 5: Cross-Region Failover

For region-wide outages, use a pre-replicated boot volume in the DR region:

```bash
# List available boot volume replicas in DR region
oci bv boot-volume-backup list \
  --compartment-id "$COMPARTMENT_OCID" \
  --query 'data[0].id' --raw-output \
  --region us-phoenix-1

# Launch instance in DR region
oci compute instance launch \
  --compartment-id "$COMPARTMENT_OCID" \
  --availability-domain "AD-1" \
  --shape "VM.Standard.E4.Flex" \
  --shape-config '{"ocpus":2,"memoryInGBs":16}' \
  --display-name "dr-failover-instance" \
  --source-boot-volume-id "$DR_BACKUP_OCID" \
  --subnet-id "$DR_SUBNET_OCID" \
  --region us-phoenix-1
```

### Step 6: Status Monitoring Script

Run this in a loop during an incident to detect recovery:

```bash
#!/bin/bash
while true; do
  STATUS=$(oci compute instance get --instance-id "$INSTANCE_OCID" \
    --query 'data."lifecycle-state"' --raw-output 2>&1)
  TIMESTAMP=$(date -u +%H:%M:%S)
  echo "$TIMESTAMP | Instance: $STATUS"
  if [ "$STATUS" = "RUNNING" ]; then
    echo "$TIMESTAMP | Instance recovered."
    break
  fi
  sleep 30
done
```

## Output

Successful execution produces:
- Independent health probe results for Identity, Compute, and Networking services
- Severity classification (P1/P2/P3) based on probe results
- Instance recovery action (reset, reboot, or stop/start) applied to the impacted instance
- Cross-AD failover instance launched from the latest boot volume backup (if AD-level failure)
- Cross-region failover instance launched in the DR region (if region-level failure)
- Continuous monitoring log tracking instance lifecycle state until recovery

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | API key expired during incident | Use `oci session authenticate` for token-based short-term auth |
| NotAuthorizedOrNotFound | 404 | IAM policy missing for recovery actions | Pre-create policy: `allow group sre to manage instances in compartment prod` |
| TooManyRequests | 429 | Rate limited during mass recovery | OCI has no Retry-After header — back off 30 seconds between calls |
| InternalError | 500 | OCI service itself is degraded | This confirms the outage — proceed to cross-region failover |
| No boot volume backups | — | Backups not configured | Cannot failover without backups — enable in Block Storage > Boot Volumes > Backup Policies |
| ServiceError status -1 | — | API timeout (region unreachable) | Switch to DR region immediately: `--region us-phoenix-1` |

## Examples

**Quick health check (CLI one-liner):**

```bash
# Test if OCI API is responsive
oci iam region list --output table && echo "OCI API: OK" || echo "OCI API: UNREACHABLE"
```

**Automated recovery wrapper:**

```bash
#!/bin/bash
set -euo pipefail
INSTANCE_OCID="${1:?Usage: recover.sh <instance-ocid>}"
STATE=$(oci compute instance get --instance-id "$INSTANCE_OCID" \
  --query 'data."lifecycle-state"' --raw-output)
case "$STATE" in
  RUNNING) echo "Instance is healthy" ;;
  STOPPED) oci compute instance action --instance-id "$INSTANCE_OCID" --action START ;;
  *)       oci compute instance action --instance-id "$INSTANCE_OCID" --action RESET ;;
esac
```

## Resources

- [OCI Instance Recovery](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/restartinginstance.htm) — stop, start, reboot, and reset actions
- [OCI Status Page](https://ocistatus.oraclecloud.com) — official service health (may lag actual incidents)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line interface documentation
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — ComputeClient, BlockstorageClient APIs
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — platform-known issues and workarounds
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — connectivity and timeout debugging

## Next Steps

After stabilizing the incident, run `oraclecloud-debug-bundle` to collect forensic data for the postmortem, or review `oraclecloud-prod-checklist` to harden your environment against future outages.
