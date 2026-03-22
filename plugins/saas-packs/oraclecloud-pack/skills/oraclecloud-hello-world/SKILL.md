---
name: oraclecloud-hello-world
description: |
  Create a minimal working Oracle Cloud example.
  Trigger: "oraclecloud hello world", "oraclecloud example", "test oraclecloud".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Hello World

## Overview
Minimal working examples demonstrating core Oracle Cloud API functionality.

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

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Auth error | Invalid credentials | Check OCI_CONFIG_FILE |
| Not found | Invalid endpoint | Verify API URL |
| Rate limit | Too many requests | Implement backoff |

## Resources
- [Oracle Cloud API Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-local-dev-loop`.
