---
name: oraclecloud-core-workflow-a
description: |
  Execute Oracle Cloud primary workflow: Compute Instance Management.
  Trigger: "oraclecloud compute instance management", "primary oraclecloud workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud — Compute Instance Management

## Overview
Primary workflow for Oracle Cloud integration.

## Instructions

### Step 1: List Instances
```python
import oci

config = oci.config.from_file()
compute = oci.core.ComputeClient(config)

instances = compute.list_instances(compartment_id=config['tenancy'])
for inst in instances.data:
    print(f"{inst.display_name} | {inst.lifecycle_state} | {inst.shape}")
```

### Step 2: Launch an Instance
```python
launch_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=config['tenancy'],
    availability_domain='Uocm:US-ASHBURN-AD-1',
    display_name='my-instance',
    shape='VM.Standard.E4.Flex',
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=2, memory_in_gbs=16
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id='ocid1.image.oc1...',
        boot_volume_size_in_gbs=50
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id='ocid1.subnet.oc1...'
    ),
    metadata={'ssh_authorized_keys': open(os.path.expanduser('~/.ssh/id_rsa.pub')).read()}
)

response = compute.launch_instance(launch_details)
print(f"Launching: {response.data.id} | Status: {response.data.lifecycle_state}")
```

### Step 3: Stop/Start Instance
```python
# Stop
compute.instance_action(instance_id='ocid1.instance...', action='STOP')

# Start
compute.instance_action(instance_id='ocid1.instance...', action='START')

# Terminate
compute.terminate_instance(instance_id='ocid1.instance...')
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-core-workflow-b`.
