---
name: vastai-reference-architecture
description: |
  Implement Vast.ai reference architecture with best-practice project layout.
  Use when designing new Vast.ai integrations, reviewing project structure,
  or establishing architecture standards for Vast.ai applications.
  Trigger with phrases like "vastai architecture", "vastai best practices",
  "vastai project structure", "how to organize vastai", "vastai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Reference Architecture

## Overview
Production architecture for GPU compute on Vast.ai. Covers instance lifecycle management, training job orchestration, model serving patterns, and cost-optimized instance selection for ML workloads.

## Prerequisites
- Vast.ai account with API key
- `vastai` CLI installed
- Docker for container image management
- SSH key pair configured

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Job Orchestrator                         │
│  Training Jobs │ Inference Serving │ Batch Processing │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│              Vast.ai Instance Manager                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐   │
│  │ Search       │  │ Create       │  │ Monitor   │   │
│  │ (find GPUs)  │  │ (provision)  │  │ (status)  │   │
│  └──────────────┘  └──────────────┘  └───────────┘   │
├──────────────────────────────────────────────────────┤
│              GPU Instance                             │
│  ┌──────────────────────────────────────────────┐     │
│  │  Docker Container                             │     │
│  │  PyTorch │ Data │ Model Weights │ Checkpoints│     │
│  └──────────────────────────────────────────────┘     │
├──────────────────────────────────────────────────────┤
│              Data Transfer                            │
│  rsync (upload) │ S3/GCS (persist) │ rsync (download)│
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Instance Selection Strategy
```python
import subprocess
import json

def search_instances(
    gpu_type: str = "RTX 4090",
    max_price: float = 0.50,
    min_ram_gb: int = 32,
    min_disk_gb: int = 50,
):
    """Search for cost-effective GPU instances."""
    cmd = [
        "vastai", "search", "offers",
        "--gpu-name", gpu_type,
        "--dph", f"<={max_price}",
        "--min-ram", str(min_ram_gb),
        "--min-disk", str(min_disk_gb),
        "--reliability", ">0.95",
        "--order", "dlperf_per_dphtotal-desc",
        "--limit", "5",
        "--raw"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# GPU selection guide:
# Training:    A100 80GB ($1.50-2.50/hr) or H100 ($2.50-4.00/hr)
# Fine-tuning: RTX 4090 ($0.30-0.50/hr) or A6000 ($0.60-1.00/hr)
# Inference:   RTX 3090 ($0.20-0.35/hr) or RTX 4090
```

### Step 2: Training Job Automation
```python
class VastTrainingJob:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def launch(self, offer_id: int, image: str, disk_gb: int = 50):
        result = subprocess.run([
            "vastai", "create", "instance", str(offer_id),
            "--image", image,
            "--disk", str(disk_gb),
            "--onstart-cmd", "cd /workspace && python train.py",
            "--raw"
        ], capture_output=True, text=True)
        return json.loads(result.stdout)

    def wait_until_ready(self, instance_id: int, timeout: int = 600):
        import time
        for _ in range(timeout // 10):
            status = self.get_status(instance_id)
            if status.get("actual_status") == "running":
                return status
            time.sleep(10)
        raise TimeoutError("Instance failed to start")

    def get_status(self, instance_id: int):
        result = subprocess.run(
            ["vastai", "show", "instance", str(instance_id), "--raw"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)

    def destroy(self, instance_id: int):
        subprocess.run(["vastai", "destroy", "instance", str(instance_id)])
```

### Step 3: Docker Image for Training
```dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download model weights during build
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('meta-llama/Llama-3.2-1B')"

ENTRYPOINT ["python", "train.py"]
```

### Step 4: Data Transfer Pattern
```python
def upload_data(instance_id: int, local_path: str, remote_path: str = "/workspace/data"):
    info = get_instance_info(instance_id)
    subprocess.run([
        "rsync", "-avz", "--progress",
        "-e", f"ssh -p {info['ssh_port']} -o StrictHostKeyChecking=no",
        local_path, f"root@{info['ssh_host']}:{remote_path}"
    ], check=True)

def download_results(instance_id: int, remote_path: str, local_path: str):
    info = get_instance_info(instance_id)
    subprocess.run([
        "rsync", "-avz", "--progress",
        "-e", f"ssh -p {info['ssh_port']}",
        f"root@{info['ssh_host']}:{remote_path}", local_path
    ], check=True)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No instances available | Filters too strict | Relax price or GPU type constraints |
| Instance killed | Host maintenance | Use checkpointing, auto-restart |
| Slow data transfer | Large dataset | Pre-load data in Docker image |
| OOM during training | Model too large for VRAM | Use gradient checkpointing, smaller batch |

## Examples

### End-to-End Training Pipeline
```python
job = VastTrainingJob(api_key="...")
offers = search_instances("A100", max_price=2.00)
instance = job.launch(offers[0]["id"], "my-training:latest")
job.wait_until_ready(instance["new_contract"])
upload_data(instance["new_contract"], "./data/")
# Training runs via onstart-cmd
download_results(instance["new_contract"], "/workspace/output/", "./results/")
job.destroy(instance["new_contract"])
```

## Resources
- [Vast.ai CLI Documentation](https://vast.ai/docs/cli/commands)
- [Vast.ai Instance Guide](https://vast.ai/docs)
