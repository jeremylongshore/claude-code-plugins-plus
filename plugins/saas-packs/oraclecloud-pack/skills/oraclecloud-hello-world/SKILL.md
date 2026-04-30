---
name: oraclecloud-hello-world
description: 'Launch your first OCI compute instance with capacity retry logic.

  Use when creating a new compute instance, testing OCI connectivity, or hitting "Out
  of host capacity" errors on Always Free ARM shapes.

  Trigger with "oraclecloud hello world", "launch oci instance", "oci compute example",
  "out of capacity oci".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(oci:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Hello World

## Overview

Launch, list, and manage your first OCI compute instance. The most common blocker for new OCI users is the `Out of host capacity` error when launching Always Free ARM shapes (VM.Standard.A1.Flex). This error means the data center has no available hosts — it is **not** a permissions issue. The solution is a retry loop that polls until capacity becomes available.

**Purpose:** Get a running compute instance on OCI, including the capacity retry pattern that makes Always Free ARM shapes actually usable.

## Prerequisites

- **Completed `oraclecloud-install-auth`** — valid `~/.oci/config` with API key authentication
- **Python 3.8+** with `pip install oci` installed
- A **subnet OCID** in your tenancy (VCN > Subnets in the Console, or use the default VCN)
- An **image OCID** for your region (Compute > Custom Images, or list platform images via API)
- An **SSH public key** at `~/.ssh/id_rsa.pub` (for instance access)

## Instructions

### Step 1: List Existing Instances

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

instances = compute.list_instances(compartment_id=config["tenancy"])
for inst in instances.data:
    print(f"{inst.display_name:<30} {inst.lifecycle_state:<12} {inst.shape}")
```

### Step 2: List Available Shapes and Images

```python
# List shapes available in your tenancy
shapes = compute.list_shapes(compartment_id=config["tenancy"])
for s in shapes.data:
    ocpus = getattr(s, "ocpus", "fixed")
    print(f"{s.shape:<35} OCPUs: {ocpus}")

# List platform images (Oracle Linux)
images = compute.list_images(
    compartment_id=config["tenancy"],
    operating_system="Oracle Linux",
    sort_by="TIMECREATED",
    sort_order="DESC",
    limit=5
)
for img in images.data:
    print(f"{img.display_name:<60} {img.id[:40]}...")
```

### Step 3: Launch an Instance (Standard)

```python
import os

launch_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=config["tenancy"],
    availability_domain="Uocm:US-ASHBURN-AD-1",  # Change for your region
    display_name="hello-oci",
    shape="VM.Standard.E4.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=1, memory_in_gbs=8
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id="ocid1.image.oc1.iad.aaaa...",  # Your image OCID
        boot_volume_size_in_gbs=50
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id="ocid1.subnet.oc1.iad.aaaa..."  # Your subnet OCID
    ),
    metadata={
        "ssh_authorized_keys": open(
            os.path.expanduser("~/.ssh/id_rsa.pub")
        ).read()
    }
)

response = compute.launch_instance(launch_details)
instance_id = response.data.id
print(f"Launching: {instance_id}")
print(f"State: {response.data.lifecycle_state}")
```

### Step 4: Wait for Instance to Be Running

```python
# Poll until RUNNING (typically 30-90 seconds)
get_instance = oci.core.ComputeClient(config)
waiter = get_instance.get_instance(instance_id)
result = oci.wait_until(
    get_instance,
    waiter,
    "lifecycle_state",
    "RUNNING",
    max_wait_seconds=300
)
print(f"Instance is RUNNING: {result.data.display_name}")
```

### Step 5: Launch with Capacity Retry (Always Free ARM)

This is the pattern you need for `VM.Standard.A1.Flex` shapes. OCI returns `Out of host capacity` intermittently — retry until a host becomes available:

```python
import time
import random

def launch_with_retry(compute_client, launch_details, max_retries=720, interval=60):
    """Retry instance launch until capacity is available.

    Default: retry every 60s for up to 12 hours (720 attempts).
    Always Free ARM shapes have intermittent capacity.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = compute_client.launch_instance(launch_details)
            print(f"Attempt {attempt}: SUCCESS — {response.data.id}")
            return response
        except oci.exceptions.ServiceError as e:
            if e.status == 500 and "Out of host capacity" in str(e.message):
                jitter = random.uniform(0, 15)
                print(f"Attempt {attempt}: Out of capacity. Retrying in {interval + jitter:.0f}s...")
                time.sleep(interval + jitter)
            else:
                raise  # Re-raise non-capacity errors
    raise RuntimeError(f"Failed after {max_retries} attempts — no capacity available")

# ARM Always Free shape
arm_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=config["tenancy"],
    availability_domain="Uocm:US-ASHBURN-AD-1",
    display_name="hello-arm",
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=4, memory_in_gbs=24  # Always Free max: 4 OCPUs, 24 GB
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id="ocid1.image.oc1.iad.aaaa...",
        boot_volume_size_in_gbs=100  # Always Free: up to 200 GB total
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id="ocid1.subnet.oc1.iad.aaaa..."
    ),
    metadata={
        "ssh_authorized_keys": open(
            os.path.expanduser("~/.ssh/id_rsa.pub")
        ).read()
    }
)

launch_with_retry(compute, arm_details)
```

### Step 6: Instance Lifecycle Operations

```python
# Stop an instance (preserves boot volume)
compute.instance_action(instance_id=instance_id, action="STOP")

# Start a stopped instance
compute.instance_action(instance_id=instance_id, action="START")

# Reboot
compute.instance_action(instance_id=instance_id, action="RESET")

# Terminate (deletes instance, boot volume preserved by default)
compute.terminate_instance(instance_id=instance_id)
```

### Step 7: OCI CLI Equivalent

```bash
# List instances
oci compute instance list --compartment-id <TENANCY_OCID> --output table

# Launch (CLI)
oci compute instance launch \
  --compartment-id <TENANCY_OCID> \
  --availability-domain "Uocm:US-ASHBURN-AD-1" \
  --shape "VM.Standard.E4.Flex" \
  --shape-config '{"ocpus": 1, "memoryInGBs": 8}' \
  --display-name "hello-cli" \
  --image-id <IMAGE_OCID> \
  --subnet-id <SUBNET_OCID> \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub

# Stop / start / terminate
oci compute instance action --instance-id <INSTANCE_OCID> --action STOP
oci compute instance action --instance-id <INSTANCE_OCID> --action START
oci compute instance terminate --instance-id <INSTANCE_OCID>
```

## Output

Successful completion produces:
- A list of existing compute instances in your tenancy
- A newly launched compute instance (standard or ARM Always Free) in RUNNING state
- The instance OCID for use in subsequent lifecycle operations
- SSH connectivity to the instance via its public IP

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Out of host capacity | 500 | No ARM hosts available in the AD | Use the retry loop in Step 5; try a different AD or region |
| NotAuthenticated | 401 | Invalid config or key mismatch | Run `oraclecloud-install-auth` to fix config |
| NotAuthorizedOrNotFound | 404 | Wrong compartment OCID or missing IAM policy | Verify compartment OCID; add policy: `allow group <grp> to manage instances in compartment <comp>` |
| InvalidParameter | 400 | Bad shape, image, or subnet OCID | List valid shapes/images with Step 2; verify subnet is in same AD |
| LimitExceeded | 400 | Tenancy service limit reached | Check Governance > Limits in Console; request increase |
| TooManyRequests | 429 | API rate limit (no Retry-After header) | Add exponential backoff; see `oraclecloud-sdk-patterns` |

## Examples

**Quick instance count with CLI:**

```bash
oci compute instance list --compartment-id <TENANCY_OCID> \
  --lifecycle-state RUNNING --query 'data | length(@)'
```

**Get public IP of a running instance:**

```python
network = oci.core.VirtualNetworkClient(config)
vnic_attachments = compute.list_vnic_attachments(
    compartment_id=config["tenancy"],
    instance_id=instance_id
).data
for att in vnic_attachments:
    vnic = network.get_vnic(att.vnic_id).data
    if vnic.public_ip:
        print(f"Public IP: {vnic.public_ip}")
```

## Resources

- [OCI Compute Documentation](https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm) — instance shapes, images, and lifecycle
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — ComputeClient API
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line usage
- [Always Free Resources](https://www.oracle.com/cloud/free/) — ARM shape limits (4 OCPU, 24 GB RAM, 200 GB boot)
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — capacity and service issues
- [OCI Status](https://ocistatus.oraclecloud.com) — real-time service health

## Next Steps

After launching your first instance, proceed to `oraclecloud-local-dev-loop` to set up a productive CLI-based workflow, or see `oraclecloud-sdk-patterns` for production-grade client lifecycle patterns.
