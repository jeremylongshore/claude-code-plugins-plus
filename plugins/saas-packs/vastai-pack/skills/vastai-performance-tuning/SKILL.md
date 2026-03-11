---
name: vastai-performance-tuning
description: |
  Optimize Vast.ai API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Vast.ai integrations.
  Trigger with phrases like "vastai performance", "optimize vastai",
  "vastai latency", "vastai caching", "vastai slow", "vastai batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Performance Tuning

## Overview
Optimize GPU instance selection, startup time, and training throughput on Vast.ai. Focus on instance filtering by cost-performance ratio, Docker image caching, data transfer optimization, and multi-GPU orchestration.

## Prerequisites
- Vast.ai account with API key
- `vastai` CLI installed (`pip install vastai`)
- Understanding of GPU types (A100, H100, RTX 4090)
- SSH key configured for instance access

## Instructions

### Step 1: Smart Instance Selection by Cost-Performance
```bash
# Find cheapest A100 instances with high reliability
vastai search offers \
  --type on-demand \
  --gpu-name "A100" \
  --min-ram 32 \
  --min-disk 100 \
  --reliability ">0.95" \
  --order "dph_total" \
  --limit 10

# Filter by DLPerf score for training workloads
vastai search offers \
  --gpu-name "RTX 4090" \
  --min-dlperf 30 \
  --order "dlperf_per_dphtotal-desc" \
  --limit 5
```

```python
# Automated instance selection
import subprocess
import json

def find_best_instance(
    gpu_type: str = "A100",
    max_price: float = 1.50,
    min_reliability: float = 0.95
):
    cmd = [
        "vastai", "search", "offers",
        "--gpu-name", gpu_type,
        "--reliability", f">{min_reliability}",
        "--dph", f"<={max_price}",
        "--order", "dlperf_per_dphtotal-desc",
        "--limit", "1",
        "--raw"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    offers = json.loads(result.stdout)
    return offers[0] if offers else None
```

### Step 2: Optimize Docker Image for Fast Startup
```dockerfile
# Use Vast.ai optimized base images for faster pulls
FROM vastai/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Install dependencies in a cached layer
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy code last (changes most frequently)
COPY . /app/
WORKDIR /app

# Pre-download model weights during build
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('bert-base-uncased')"

CMD ["python", "train.py"]
```

### Step 3: Data Transfer Optimization
```python
import subprocess

def sync_data_to_instance(instance_id: int, local_path: str, remote_path: str):
    """Use rsync with compression for fast data transfer."""
    # Get instance SSH info
    info = subprocess.run(
        ["vastai", "show", "instance", str(instance_id), "--raw"],
        capture_output=True, text=True
    )
    instance = json.loads(info.stdout)
    ssh_host = instance["ssh_host"]
    ssh_port = instance["ssh_port"]

    subprocess.run([
        "rsync", "-avz", "--progress",
        "--compress-level=9",
        "-e", f"ssh -p {ssh_port} -o StrictHostKeyChecking=no",
        local_path,
        f"root@{ssh_host}:{remote_path}"
    ], check=True)

def download_results(instance_id: int, remote_path: str, local_path: str):
    """Download trained model and logs."""
    info = subprocess.run(
        ["vastai", "show", "instance", str(instance_id), "--raw"],
        capture_output=True, text=True
    )
    instance = json.loads(info.stdout)

    subprocess.run([
        "rsync", "-avz",
        "-e", f"ssh -p {instance['ssh_port']}",
        f"root@{instance['ssh_host']}:{remote_path}",
        local_path
    ], check=True)
```

### Step 4: Instance Lifecycle Management
```python
def create_and_monitor(
    template_id: int,
    image: str,
    disk_gb: int = 50
):
    """Create instance and wait until ready."""
    result = subprocess.run([
        "vastai", "create", "instance",
        str(template_id),
        "--image", image,
        "--disk", str(disk_gb),
        "--raw"
    ], capture_output=True, text=True)

    instance_id = json.loads(result.stdout)["new_contract"]

    # Poll until running
    import time
    for _ in range(60):
        status = subprocess.run(
            ["vastai", "show", "instance", str(instance_id), "--raw"],
            capture_output=True, text=True
        )
        info = json.loads(status.stdout)
        if info.get("actual_status") == "running":
            return instance_id
        time.sleep(10)

    raise TimeoutError("Instance did not start within 10 minutes")

def cleanup_instance(instance_id: int):
    """Destroy instance to stop billing."""
    subprocess.run(["vastai", "destroy", "instance", str(instance_id)])
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No offers found | Filters too strict | Relax reliability or price constraints |
| Slow instance startup | Large Docker image | Use pre-cached base images |
| SSH timeout | Instance not ready | Poll status before connecting |
| High data transfer cost | Uploading large datasets | Use compressed rsync, store on instance disk |

## Examples

### Training Job Automation
```python
instance_id = create_and_monitor(
    template_id=best_offer["id"],
    image="pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"
)
sync_data_to_instance(instance_id, "./data/", "/workspace/data/")
# Run training via SSH...
download_results(instance_id, "/workspace/output/", "./results/")
cleanup_instance(instance_id)
```

## Resources
- [Vast.ai CLI Reference](https://vast.ai/docs/cli/commands)
- [Vast.ai Instance Types](https://vast.ai/docs/gpu-faq)
