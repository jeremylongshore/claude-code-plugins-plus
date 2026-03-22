---
name: vastai-core-workflow-a
description: |
  Execute Vast.ai primary workflow: GPU instance provisioning and job execution.
  Use when renting GPUs for training, searching offers by price and specs,
  or managing the full instance lifecycle from search to teardown.
  Trigger with phrases like "vastai rent gpu", "vastai training job",
  "vastai provision instance", "run job on vastai".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(curl:*), Bash(ssh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, workflow]

---
# Vast.ai Core Workflow A: Instance Provisioning & Job Execution

## Overview
Primary workflow for Vast.ai: search for GPU offers, provision an instance, transfer data, execute a training or inference job, collect artifacts, and destroy the instance to stop billing. This is the money-path operation for every Vast.ai user.

## Prerequisites
- Completed `vastai-install-auth` setup
- Docker image published to a registry (Docker Hub, GHCR, etc.)
- SSH key uploaded to Vast.ai
- Training data accessible via URL or local path

## Instructions

### Step 1: Search Offers with Filters

```python
import subprocess, json

def search_offers(gpu_name="RTX_4090", min_vram=24, min_reliability=0.95,
                  max_price=0.50, num_gpus=1):
    """Search Vast.ai marketplace with specific filters."""
    query = (
        f"num_gpus={num_gpus} gpu_name={gpu_name} "
        f"gpu_ram>={min_vram} reliability>{min_reliability} "
        f"inet_down>200 dph_total<={max_price} rentable=true"
    )
    result = subprocess.run(
        ["vastai", "search", "offers", query, "--order", "dph_total", "--raw"],
        capture_output=True, text=True, check=True,
    )
    offers = json.loads(result.stdout)
    print(f"Found {len(offers)} offers matching criteria")
    for o in offers[:5]:
        print(f"  ID {o['id']}: {o['gpu_name']} {o['gpu_ram']}GB "
              f"${o['dph_total']:.3f}/hr reliability={o['reliability2']:.3f}")
    return offers
```

### Step 2: Provision an Instance

```python
def provision_instance(offer_id, image, disk_gb=50, onstart_cmd=""):
    """Create an instance from the best offer."""
    cmd = [
        "vastai", "create", "instance", str(offer_id),
        "--image", image,
        "--disk", str(disk_gb),
    ]
    if onstart_cmd:
        cmd.extend(["--onstart-cmd", onstart_cmd])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    instance_info = json.loads(result.stdout)
    instance_id = instance_info.get("new_contract")
    print(f"Instance {instance_id} provisioning...")
    return instance_id
```

### Step 3: Wait for Instance Ready

```python
import time

def wait_for_instance(instance_id, timeout=300):
    """Poll until instance status is 'running'."""
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(
            ["vastai", "show", "instance", str(instance_id), "--raw"],
            capture_output=True, text=True,
        )
        info = json.loads(result.stdout)
        status = info.get("actual_status", "unknown")
        print(f"  Status: {status}")
        if status == "running":
            ssh_host = info.get("ssh_host")
            ssh_port = info.get("ssh_port")
            print(f"  SSH: ssh -p {ssh_port} root@{ssh_host}")
            return info
        time.sleep(15)
    raise TimeoutError(f"Instance {instance_id} did not start within {timeout}s")
```

### Step 4: Transfer Data and Execute Job

```bash
# Upload training data to instance
scp -P $SSH_PORT ./data/training.tar.gz root@$SSH_HOST:/workspace/

# Execute training job remotely
ssh -p $SSH_PORT root@$SSH_HOST << 'REMOTE'
cd /workspace
tar xzf training.tar.gz
python train.py --epochs 10 --batch-size 32 --output /workspace/checkpoints/
REMOTE
```

### Step 5: Collect Artifacts and Destroy

```python
def cleanup_instance(instance_id, ssh_host, ssh_port, output_dir="./results"):
    """Download results and destroy instance."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Download model checkpoints
    subprocess.run([
        "scp", "-P", str(ssh_port), "-r",
        f"root@{ssh_host}:/workspace/checkpoints/",
        output_dir,
    ], check=True)
    print(f"Artifacts saved to {output_dir}")

    # CRITICAL: Destroy instance to stop billing
    subprocess.run(["vastai", "destroy", "instance", str(instance_id)], check=True)
    print(f"Instance {instance_id} destroyed — billing stopped")
```

### Complete Workflow

```python
# End-to-end: search → provision → run → collect → destroy
offers = search_offers(gpu_name="RTX_4090", max_price=0.30)
if not offers:
    raise RuntimeError("No offers available")

instance_id = provision_instance(
    offer_id=offers[0]["id"],
    image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime",
    disk_gb=50,
    onstart_cmd="pip install transformers datasets",
)
info = wait_for_instance(instance_id)
# ... transfer data, run job, collect results ...
cleanup_instance(instance_id, info["ssh_host"], info["ssh_port"])
```

## Output
- GPU instance provisioned from the cheapest matching offer
- Training job executed with GPU acceleration
- Model checkpoints and logs downloaded locally
- Instance destroyed (billing stopped)

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| No offers match filters | GPU type or price too restrictive | Relax `dph_total` or try different `gpu_name` |
| Instance stuck in `loading` | Docker image is very large | Use a smaller base image or pre-cached template |
| SSH timeout after creation | Firewall or key mismatch | Verify SSH key is uploaded at cloud.vast.ai |
| Job OOM killed | Insufficient GPU VRAM | Reduce batch size or search for more VRAM |
| Instance preempted (spot) | Host reclaimed interruptible instance | Use on-demand or implement checkpoint recovery |

## Resources
- [Search & Filter Offers](https://docs.vast.ai/search-and-filter-gpu-offers)
- [Instance Management](https://docs.vast.ai/api-reference/instances/create-instance)
- [CLI Reference](https://docs.vast.ai/cli/get-started)
- [REST API Overview](https://docs.vast.ai/api/overview-and-quickstart)

## Next Steps
For multi-instance orchestration and cost optimization, see `vastai-core-workflow-b`.

## Examples

**Fine-tune LLM**: Search for A100 80GB offers, provision with the `huggingface/transformers` image, upload a LoRA config, run fine-tuning for 3 epochs, download the adapter weights, destroy the instance.

**Batch inference**: Provision 4 cheap RTX 4090 instances in parallel, distribute an inference dataset across them, collect results, and destroy all instances in a loop.
