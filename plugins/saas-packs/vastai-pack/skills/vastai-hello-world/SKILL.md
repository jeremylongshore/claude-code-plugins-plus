---
name: vastai-hello-world
description: |
  Rent your first GPU instance on Vast.ai and run a workload.
  Use when starting a new Vast.ai integration, testing your setup,
  or learning basic Vast.ai GPU rental patterns.
  Trigger with phrases like "vastai hello world", "vastai example",
  "vastai quick start", "rent first gpu", "vastai first instance".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(curl:*), Bash(ssh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, testing]

---
# Vast.ai Hello World

## Overview
Rent your first GPU instance on Vast.ai, run a PyTorch workload, and destroy the instance when done. Demonstrates the full lifecycle: search offers, create instance, connect via SSH, run a job, and tear down.

## Prerequisites
- Completed `vastai-install-auth` setup
- Vast.ai account with credits ($1+ recommended for testing)
- SSH key uploaded to Vast.ai (cloud.vast.ai > Account > SSH Keys)

## Instructions

### Step 1: Search for Available GPUs (CLI)
```bash
# Find cheap single-GPU offers sorted by price
vastai search offers 'num_gpus=1 gpu_ram>=8 inet_down>100 reliability>0.95' \
  --order 'dph_total' --limit 5

# Output columns: ID, GPU, VRAM, $/hr, DLPerf, Reliability, Location
```

### Step 2: Search for Available GPUs (REST API)
```bash
curl -s -H "Authorization: Bearer $VASTAI_API_KEY" \
  "https://cloud.vast.ai/api/v0/bundles/?q=%7B%22num_gpus%22%3A%7B%22eq%22%3A1%7D%2C%22gpu_ram%22%3A%7B%22gte%22%3A8%7D%2C%22reliability2%22%3A%7B%22gte%22%3A0.95%7D%2C%22rentable%22%3A%7B%22eq%22%3Atrue%7D%7D&order=dph_total&limit=5" \
  | jq '.offers[:3] | .[] | {id, gpu_name, num_gpus, gpu_ram, dph_total, reliability2}'
```

### Step 3: Create an Instance (CLI)
```bash
# Replace OFFER_ID with the ID from search results
vastai create instance OFFER_ID \
  --image pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime \
  --disk 20 \
  --onstart-cmd "echo 'Instance ready'"
```

### Step 4: Create an Instance (Python)
```python
from vastai_client import VastClient

client = VastClient()

# Search for affordable RTX 4090 offers
offers = client.search_offers({
    "num_gpus": {"eq": 1},
    "gpu_name": {"eq": "RTX_4090"},
    "reliability2": {"gte": 0.95},
    "rentable": {"eq": True},
})

# Pick the cheapest offer
best = sorted(offers["offers"], key=lambda o: o["dph_total"])[0]
print(f"Best offer: {best['gpu_name']} at ${best['dph_total']:.3f}/hr (ID: {best['id']})")

# Create instance with PyTorch image
instance = client.create_instance(
    offer_id=best["id"],
    image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime",
    disk_gb=20,
    onstart="nvidia-smi && python -c 'import torch; print(torch.cuda.is_available())'",
)
print(f"Instance created: {instance}")
```

### Step 5: Monitor and Connect
```bash
# Check instance status (wait for 'running')
vastai show instances --raw | jq '.[] | {id, actual_status, ssh_host, ssh_port}'

# Connect via SSH once running
ssh -p SSH_PORT root@SSH_HOST

# On the instance: verify GPU access
nvidia-smi
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Step 6: Run a Test Workload
```python
# test_gpu.py — run this ON the rented instance
import torch
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device} ({torch.cuda.get_device_name(0)})")

# Simple matrix multiplication benchmark
size = 4096
a = torch.randn(size, size, device=device)
b = torch.randn(size, size, device=device)

torch.cuda.synchronize()
start = time.time()
c = torch.matmul(a, b)
torch.cuda.synchronize()
elapsed = time.time() - start

tflops = (2 * size**3) / elapsed / 1e12
print(f"Matrix multiply {size}x{size}: {elapsed:.3f}s ({tflops:.2f} TFLOPS)")
print("Hello World from Vast.ai!")
```

### Step 7: Destroy the Instance
```bash
# IMPORTANT: Destroy to stop billing
vastai destroy instance INSTANCE_ID

# Verify it's gone
vastai show instances
```

## Output
- GPU instance rented and running on Vast.ai
- SSH connection established to the remote GPU machine
- PyTorch workload executed successfully with GPU acceleration
- Instance destroyed (billing stopped)

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `No offers found` | Filters too strict | Relax GPU or reliability filters |
| `Insufficient funds` | Account balance too low | Add credits at cloud.vast.ai |
| `Instance failed to start` | Docker image pull failed | Use a smaller or more common image |
| `SSH connection refused` | Instance still loading | Wait 1-2 min for status `running` |
| `CUDA not available` | Driver mismatch | Use a CUDA-compatible Docker image |

## Resources
- [Vast.ai Search & Filter](https://docs.vast.ai/search-and-filter-gpu-offers)
- [Creating Instances](https://docs.vast.ai/api-reference/instances/create-instance)
- [CLI Reference](https://docs.vast.ai/cli/get-started)
- [REST API Quickstart](https://docs.vast.ai/api/overview-and-quickstart)

## Next Steps
Proceed to `vastai-local-dev-loop` for development workflow setup.

## Examples

**Cheapest GPU test**: Search with `vastai search offers 'num_gpus=1' --order 'dph_total' --limit 1`, create an instance with the ubuntu image, SSH in, run `nvidia-smi`, then destroy.

**Specific GPU model**: Filter for H100 with `gpu_name=H100_SXM` and `reliability>0.99` for production-grade hardware. Expect $2.50-4.00/hr.
