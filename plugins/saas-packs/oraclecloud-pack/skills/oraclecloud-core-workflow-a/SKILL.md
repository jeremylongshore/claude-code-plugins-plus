---
name: oraclecloud-core-workflow-a
description: 'Launch, manage, and scale OCI compute instances with capacity retry
  logic.

  Use when provisioning VMs, selecting instance shapes, or handling "out of capacity"
  errors.

  Trigger with "oci compute", "launch instance", "out of capacity", "instance shapes".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# OCI Compute — Launch, Manage & Scale

## Overview

Provision and manage OCI compute instances using the Python SDK. Compute is the entry point for most OCI workloads, but "out of host capacity" errors, shape selection confusion (Flex vs Standard, AMD vs ARM vs Intel), and boot volume management make it harder than AWS EC2. This skill covers shape selection, launch with capacity retry across availability domains, instance lifecycle actions, and boot volume management.

**Purpose:** Launch reliable compute instances with retry logic that survives capacity shortages.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **Config file** at `~/.oci/config` with fields: `user`, `fingerprint`, `tenancy`, `region`, `key_file`
- **IAM policy** — `Allow group Developers to manage instances in compartment <name>`
- **Python 3.8+**
- A VCN with at least one subnet (see `oraclecloud-core-workflow-b`)

## Instructions

### Step 1: Understand Shape Options

| Shape | Arch | Flex? | OCPUs | Use Case |
|-------|------|-------|-------|----------|
| VM.Standard.A1.Flex | ARM (Ampere) | Yes | 1-80 | Always Free eligible, best price/perf |
| VM.Standard.E5.Flex | AMD | Yes | 1-94 | General purpose, broadest availability |
| VM.Standard3.Flex | Intel | Yes | 1-32 | Intel-specific workloads |
| VM.Standard.E4.Flex | AMD | Yes | 1-64 | Previous gen, still available |

**Key rule:** Always use Flex shapes. They let you set exact OCPU and memory. Standard (non-Flex) shapes have fixed sizes and are being phased out.

### Step 2: List Available Shapes and Images

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)
identity = oci.identity.IdentityClient(config)

# Get availability domains
ads = identity.list_availability_domains(compartment_id=config["tenancy"]).data

# List shapes in each AD
for ad in ads:
    shapes = compute.list_shapes(
        compartment_id=config["tenancy"],
        availability_domain=ad.name
    ).data
    flex_shapes = [s for s in shapes if "Flex" in s.shape]
    print(f"\n{ad.name}:")
    for s in flex_shapes:
        print(f"  {s.shape} | OCPUs: {s.ocpu_options.min}-{s.ocpu_options.max}")
```

### Step 3: Launch with Capacity Retry

The most common OCI error is `500 InternalError` with message "Out of host capacity." The fix is to retry across availability domains.

```python
import oci
import time

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)
identity = oci.identity.IdentityClient(config)

ads = identity.list_availability_domains(compartment_id=config["tenancy"]).data

launch_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=config["tenancy"],
    display_name="my-app-server",
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=2, memory_in_gbs=12
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id="ocid1.image.oc1...",  # Oracle Linux 8 image OCID
        boot_volume_size_in_gbs=50
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id="ocid1.subnet.oc1..."
    ),
    metadata={"ssh_authorized_keys": open("/home/user/.ssh/id_rsa.pub").read()},
)

# Retry across all ADs on capacity errors
for ad in ads:
    launch_details.availability_domain = ad.name
    try:
        response = compute.launch_instance(launch_details)
        print(f"Launched in {ad.name}: {response.data.id}")
        break
    except oci.exceptions.ServiceError as e:
        if e.status == 500 and "capacity" in str(e.message).lower():
            print(f"No capacity in {ad.name}, trying next AD...")
            time.sleep(2)
            continue
        raise
else:
    print("ERROR: No capacity in any AD. Try a different shape or region.")
```

### Step 4: Instance Lifecycle Actions

```python
instance_id = "ocid1.instance.oc1..."

# Stop (SOFTSTOP sends ACPI shutdown, STOP is hard power-off)
compute.instance_action(instance_id=instance_id, action="SOFTSTOP")

# Start
compute.instance_action(instance_id=instance_id, action="START")

# Reboot
compute.instance_action(instance_id=instance_id, action="SOFTRESET")

# Terminate (preserves boot volume by default)
compute.terminate_instance(
    instance_id=instance_id,
    preserve_boot_volume=True
)
```

### Step 5: Get Instance Metadata and Public IP

```python
# Get instance details
instance = compute.get_instance(instance_id=instance_id).data
print(f"State: {instance.lifecycle_state}")
print(f"Shape: {instance.shape}")

# Get VNIC attachments to find public IP
network = oci.core.VirtualNetworkClient(config)
vnic_attachments = compute.list_vnic_attachments(
    compartment_id=config["tenancy"],
    instance_id=instance_id
).data

for attachment in vnic_attachments:
    vnic = network.get_vnic(vnic_id=attachment.vnic_id).data
    print(f"Public IP: {vnic.public_ip}")
    print(f"Private IP: {vnic.private_ip}")
```

## Output

Successful completion produces:
- A running compute instance in the best available AD
- Capacity retry logic that falls back across availability domains
- Instance lifecycle management (stop, start, reboot, terminate)
- Public and private IP addresses retrieved via VNIC attachment

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Out of host capacity | 500 InternalError | AD has no available hosts for shape | Retry across ADs (Step 3), try different shape, or different region |
| Not authenticated | 401 NotAuthenticated | Bad API key or config | Verify `~/.oci/config` key_file path and fingerprint |
| Not authorized | 404 NotAuthorizedOrNotFound | IAM policy missing or wrong OCID | Add IAM policy: `Allow group X to manage instances in compartment Y` |
| Shape not found | 400 InvalidParameter | Shape not available in region | List shapes first (Step 2) to confirm availability |
| Rate limited | 429 TooManyRequests | Too many API calls | Add exponential backoff; OCI does not return Retry-After header |
| Limit exceeded | 400 LimitExceeded | Service limit for shape reached | Request limit increase in Console > Governance > Limits |

## Examples

**Quick instance list via CLI:**

```bash
# List all running instances
oci compute instance list \
  --compartment-id <OCID> \
  --lifecycle-state RUNNING \
  --query "data[*].{Name:\"display-name\",Shape:shape,State:\"lifecycle-state\"}" \
  --output table
```

**Find Oracle Linux images:**

```python
images = compute.list_images(
    compartment_id=config["tenancy"],
    operating_system="Oracle Linux",
    shape="VM.Standard.A1.Flex",
    sort_by="TIMECREATED",
    sort_order="DESC",
).data
latest = images[0]
print(f"Latest image: {latest.display_name} ({latest.id})")
```

## Resources

- [Compute Service Overview](https://docs.oracle.com/en-us/iaas/Content/) — launching and managing instances
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — ComputeClient API
- [CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — `oci compute` commands
- [Always Free Tier](https://www.oracle.com/cloud/free/) — ARM A1 Flex instances included
- [Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — current service issues

## Next Steps

After launching instances, proceed to `oraclecloud-core-workflow-b` to build the networking layer (VCN, subnets, security rules), or see `oraclecloud-data-handling` for Object Storage operations.
