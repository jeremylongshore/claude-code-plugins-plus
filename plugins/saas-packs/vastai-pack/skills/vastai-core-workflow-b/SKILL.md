---
name: vastai-core-workflow-b
description: |
  Execute Vast.ai secondary workflow: multi-instance orchestration, spot recovery, and cost optimization.
  Use when running distributed training, handling spot preemption,
  or optimizing GPU spend across multiple instances.
  Trigger with phrases like "vastai distributed training", "vastai spot recovery",
  "vastai multi-gpu", "vastai cost optimization".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, workflow]

---
# Vast.ai Core Workflow B: Multi-Instance & Cost Optimization

## Overview
Secondary workflow for Vast.ai: orchestrate multiple GPU instances for distributed training, implement automatic spot interruption recovery with checkpoint-based resume, and analyze spending to reduce per-job cost.

## Prerequisites
- Completed `vastai-core-workflow-a`
- Understanding of distributed training (PyTorch DDP, DeepSpeed)
- Checkpoint-based training pipeline

## Instructions

### Step 1: Multi-Instance Provisioning

```python
import subprocess, json, time
from concurrent.futures import ThreadPoolExecutor

def provision_cluster(num_nodes, gpu_name="A100", min_vram=80, image=""):
    """Provision multiple GPU instances for distributed training."""
    # Search for matching offers
    query = (f"num_gpus=1 gpu_name={gpu_name} gpu_ram>={min_vram} "
             f"reliability>0.98 inet_down>500 rentable=true")
    result = subprocess.run(
        ["vastai", "search", "offers", query, "--order", "dph_total",
         "--raw", "--limit", str(num_nodes * 3)],
        capture_output=True, text=True, check=True,
    )
    offers = json.loads(result.stdout)
    if len(offers) < num_nodes:
        raise RuntimeError(f"Only {len(offers)} offers, need {num_nodes}")

    # Provision nodes in parallel
    instances = []
    for i, offer in enumerate(offers[:num_nodes]):
        inst_id = provision_single(offer["id"], image, rank=i)
        instances.append({"id": inst_id, "rank": i, "offer": offer})

    # Wait for all to be running
    for inst in instances:
        info = wait_for_running(inst["id"])
        inst.update({"ssh_host": info["ssh_host"], "ssh_port": info["ssh_port"]})

    return instances
```

### Step 2: Spot Interruption Recovery

```python
class SpotRecoveryManager:
    """Monitor instances and replace preempted spot instances."""

    def __init__(self, client, checkpoint_dir="/workspace/checkpoints"):
        self.client = client
        self.checkpoint_dir = checkpoint_dir

    def monitor_and_recover(self, instances, image, poll_interval=60):
        """Poll instance status; replace any that are destroyed/error."""
        while True:
            for inst in instances:
                result = subprocess.run(
                    ["vastai", "show", "instance", str(inst["id"]), "--raw"],
                    capture_output=True, text=True,
                )
                info = json.loads(result.stdout)
                status = info.get("actual_status", "unknown")

                if status in ("exited", "error", "offline"):
                    print(f"Instance {inst['id']} lost (status={status}). Replacing...")
                    new_inst = self.replace_instance(inst, image)
                    inst.update(new_inst)

            time.sleep(poll_interval)

    def replace_instance(self, old_inst, image):
        """Provision replacement and resume from last checkpoint."""
        # Search for a new offer
        offers = search_offers(gpu_name=old_inst["offer"]["gpu_name"])
        new_id = provision_single(offers[0]["id"], image, rank=old_inst["rank"])
        info = wait_for_running(new_id)

        # Upload last checkpoint to new instance
        subprocess.run([
            "scp", "-P", str(info["ssh_port"]), "-r",
            f"{self.checkpoint_dir}/",
            f"root@{info['ssh_host']}:/workspace/checkpoints/",
        ], check=True)

        return {"id": new_id, "ssh_host": info["ssh_host"],
                "ssh_port": info["ssh_port"]}
```

### Step 3: Cost Analysis

```python
def analyze_spending():
    """Pull billing history and compute cost-per-GPU-hour by GPU type."""
    result = subprocess.run(
        ["vastai", "show", "invoices", "--raw"],
        capture_output=True, text=True,
    )
    invoices = json.loads(result.stdout)

    # Aggregate by GPU type
    by_gpu = {}
    for inv in invoices:
        gpu = inv.get("gpu_name", "unknown")
        cost = inv.get("total_cost", 0)
        hours = inv.get("duration_hours", 0)
        if gpu not in by_gpu:
            by_gpu[gpu] = {"total_cost": 0, "total_hours": 0}
        by_gpu[gpu]["total_cost"] += cost
        by_gpu[gpu]["total_hours"] += hours

    print("GPU Cost Summary:")
    for gpu, data in sorted(by_gpu.items(), key=lambda x: x[1]["total_cost"], reverse=True):
        avg = data["total_cost"] / max(data["total_hours"], 1)
        print(f"  {gpu}: ${data['total_cost']:.2f} total, "
              f"{data['total_hours']:.1f}hrs, ${avg:.3f}/hr avg")
```

### Step 4: Destroy Cluster

```python
def destroy_cluster(instances):
    """Destroy all instances in a cluster to stop billing."""
    for inst in instances:
        subprocess.run(
            ["vastai", "destroy", "instance", str(inst["id"])],
            check=True,
        )
        print(f"Destroyed instance {inst['id']} (rank {inst['rank']})")
    print(f"All {len(instances)} instances destroyed — billing stopped")
```

## Output
- Multi-node GPU cluster provisioned from marketplace offers
- Automatic spot interruption detection and recovery with checkpoint resume
- Cost analysis report comparing GPU types and actual spend
- Clean cluster teardown stopping all billing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient offers for cluster | Not enough matching GPUs available | Reduce `num_nodes` or relax GPU requirements |
| Checkpoint corruption on transfer | Interrupted SCP during preemption | Verify checkpoint integrity with hash check before resume |
| Node communication failure | Firewall between instances | Use instances from the same datacenter if possible |
| Budget exceeded | Unexpected spot price spikes | Set `dph_total` ceiling in search query |

## Resources
- [Vast.ai Instance Types](https://docs.vast.ai/api-reference/instances/create-instance)
- [Search Filtering](https://docs.vast.ai/search-and-filter-gpu-offers)
- [CLI Reference](https://docs.vast.ai/cli/get-started)

## Next Steps
For common errors, see `vastai-common-errors`.

## Examples

**Distributed fine-tuning**: Provision 4x A100 instances, configure PyTorch DDP with `torchrun --nproc_per_node=1 --nnodes=4`, save checkpoints every 500 steps, and implement spot recovery to auto-resume from the latest checkpoint.

**Cost comparison**: Run the same workload on RTX 4090 ($0.20/hr) vs A100 ($1.50/hr) and compare wall-clock time vs total cost to find the optimal GPU type for your specific model.
