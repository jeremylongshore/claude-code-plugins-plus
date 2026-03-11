---
name: vastai-deploy-integration
description: |
  Deploy Vast.ai integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Vast.ai-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy vastai", "vastai Vercel",
  "vastai production deploy", "vastai Cloud Run", "vastai Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Deploy Integration

## Overview
Deploy ML training jobs and inference services on Vast.ai GPU cloud. Covers instance provisioning via the REST API, Docker image configuration, data transfer strategies, and automated deployment scripts for GPU workloads.

## Prerequisites
- Vast.ai account with API key stored in `VASTAI_API_KEY` environment variable
- Vast.ai CLI installed (`pip install vastai`)
- Docker image for your workload published to a registry
- SSH key configured for instance access

## Instructions

### Step 1: Search and Provision GPU
```bash
# Search for available GPUs
vastai search offers 'gpu_name=RTX_4090 reliability2>0.95 disk_space>50' \
  -o 'dph_total' --limit 5

# Create instance from best offer
vastai create instance $OFFER_ID \
  --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime \
  --disk 100 \
  --onstart-cmd "cd /workspace && git clone https://github.com/myorg/project.git && pip install -r project/requirements.txt"
```

### Step 2: Deploy Custom Docker Image
```dockerfile
# Dockerfile.gpu
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "train.py", "--config", "config.yaml"]
```

```bash
# Build and push
docker build -f Dockerfile.gpu -t myregistry/ml-trainer:latest .
docker push myregistry/ml-trainer:latest

# Deploy on Vast.ai
vastai create instance $OFFER_ID \
  --image myregistry/ml-trainer:latest \
  --disk 100 \
  --env "WANDB_API_KEY=$WANDB_API_KEY HF_TOKEN=$HF_TOKEN"
```

### Step 3: Automated Deployment Script
```python
import requests
import json
import os

VASTAI_API = "https://cloud.vast.ai/api/v0"
API_KEY = os.environ["VASTAI_API_KEY"]

def deploy_training_job(gpu_type="RTX_4090", disk_gb=100):
    # Find cheapest matching offer
    response = requests.get(f"{VASTAI_API}/bundles", params={
        "api_key": API_KEY,
        "q": json.dumps({
            "gpu_name": {"eq": gpu_type},
            "rentable": {"eq": True},
            "disk_space": {"gte": disk_gb},
            "reliability2": {"gte": 0.95},
        }),
        "order": "dph_total",
        "limit": 1,
    })

    offers = response.json()["offers"]
    if not offers:
        raise ValueError(f"No {gpu_type} available")

    # Provision instance
    result = requests.put(
        f"{VASTAI_API}/asks/{offers[0]['id']}/",
        params={"api_key": API_KEY},
        json={
            "image": "myregistry/ml-trainer:latest",
            "disk": disk_gb,
            "env": {"WANDB_API_KEY": os.environ.get("WANDB_API_KEY", "")},
        },
    )

    instance = result.json()
    print(f"Instance {instance['new_contract']} created at ${offers[0]['dph_total']}/hr")
    return instance
```

### Step 4: Monitor and Cleanup
```bash
# List running instances
vastai show instances

# Check instance status
vastai show instance $INSTANCE_ID

# Download results
vastai scp $INSTANCE_ID:/workspace/output ./results/

# Destroy instance when done
vastai destroy instance $INSTANCE_ID
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No GPU available | High demand | Try different GPU type or region |
| Instance preempted | Outbid on spot | Use on-demand or increase bid |
| SSH connection refused | Instance still booting | Wait for `running` status |
| Out of disk | Large dataset | Increase `--disk` parameter |

## Examples

### Quick Training Deploy
```bash
vastai search offers 'gpu_name=A100_SXM4 num_gpus=1' -o 'dph_total' --limit 3
vastai create instance $BEST_OFFER --image myregistry/trainer:latest --disk 200
```

## Resources
- [Vast.ai Documentation](https://vast.ai/docs)
- [Vast.ai CLI Reference](https://vast.ai/docs/cli)
- [GPU Pricing](https://vast.ai/pricing)

## Next Steps
For multi-environment setup, see `vastai-multi-env-setup`.
