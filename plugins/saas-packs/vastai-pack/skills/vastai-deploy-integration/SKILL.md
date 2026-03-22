---
name: vastai-deploy-integration
description: |
  Deploy ML training jobs and inference services on Vast.ai GPU cloud.
  Use when deploying GPU workloads, configuring Docker images,
  or setting up automated deployment scripts.
  Trigger with phrases like "deploy vastai", "vastai deployment",
  "vastai docker", "vastai production deploy".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(docker:*), Bash(ssh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, deployment]

---
# Vast.ai Deploy Integration

## Overview
Deploy ML training jobs and inference services on Vast.ai GPU cloud. Covers Docker image optimization, automated provisioning scripts, data transfer strategies, and deployment automation.

## Prerequisites
- Vast.ai CLI authenticated
- Docker image published to a registry
- Training/inference code tested locally

## Instructions

### Step 1: Optimized Docker Image

```dockerfile
# Dockerfile.vastai — optimized for fast pulls on Vast.ai
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# Install dependencies in a single layer
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copy application code
COPY src/ /workspace/src/
COPY scripts/ /workspace/scripts/

WORKDIR /workspace
CMD ["python", "src/train.py"]
```

```bash
# Build and push
docker build -t ghcr.io/yourorg/training:v1 -f Dockerfile.vastai .
docker push ghcr.io/yourorg/training:v1
```

### Step 2: Automated Deployment Script

```python
#!/usr/bin/env python3
"""deploy.py — Automated Vast.ai deployment with monitoring."""
import subprocess, json, time, argparse, sys

def deploy(args):
    # Search for matching offer
    query = (f"num_gpus={args.gpus} gpu_name={args.gpu} "
             f"reliability>{args.reliability} dph_total<={args.max_price} "
             f"disk_space>={args.disk} rentable=true")

    offers = json.loads(subprocess.run(
        ["vastai", "search", "offers", query, "--order", "dph_total",
         "--raw", "--limit", "5"],
        capture_output=True, text=True, check=True).stdout)

    if not offers:
        print(f"ERROR: No offers matching: {query}", file=sys.stderr)
        sys.exit(1)

    offer = offers[0]
    print(f"Selected: {offer['gpu_name']} ${offer['dph_total']:.3f}/hr "
          f"(ID: {offer['id']})")

    # Create instance
    cmd = ["vastai", "create", "instance", str(offer["id"]),
           "--image", args.image, "--disk", str(args.disk)]
    if args.onstart:
        cmd.extend(["--onstart-cmd", args.onstart])

    result = json.loads(subprocess.run(
        cmd, capture_output=True, text=True, check=True).stdout)
    instance_id = result["new_contract"]
    print(f"Instance {instance_id} provisioning...")

    # Wait for running
    for _ in range(30):
        info = json.loads(subprocess.run(
            ["vastai", "show", "instance", str(instance_id), "--raw"],
            capture_output=True, text=True).stdout)
        if info.get("actual_status") == "running":
            print(f"READY: ssh -p {info['ssh_port']} root@{info['ssh_host']}")
            return instance_id, info
        time.sleep(10)

    raise TimeoutError("Instance did not start")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", default="RTX_4090")
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--image", required=True)
    parser.add_argument("--disk", type=int, default=50)
    parser.add_argument("--max-price", type=float, default=0.50)
    parser.add_argument("--reliability", type=float, default=0.95)
    parser.add_argument("--onstart", default="")
    deploy(parser.parse_args())
```

### Step 3: Data Transfer Strategies

```bash
# Small datasets (<5GB): SCP directly
scp -P $PORT ./data.tar.gz root@$HOST:/workspace/

# Large datasets (>5GB): Use rsync with compression
rsync -avz --progress -e "ssh -p $PORT" ./data/ root@$HOST:/workspace/data/

# Very large datasets: Pre-stage on cloud storage
ssh -p $PORT root@$HOST "wget -q https://storage.example.com/dataset.tar.gz -O /workspace/data.tar.gz"
```

### Step 4: Health Check After Deploy

```bash
ssh -p $PORT -o StrictHostKeyChecking=no root@$HOST << 'CHECK'
echo "=== Deploy Health Check ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
df -h /workspace | tail -1
echo "=== Ready ==="
CHECK
```

## Output
- Optimized Docker image for fast Vast.ai pulls
- Automated deployment script with GPU/price selection
- Data transfer patterns (SCP, rsync, cloud storage)
- Post-deploy health check verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Docker pull timeout | Image too large (>10GB) | Use multi-stage builds; minimize image layers |
| Disk space exhausted | Insufficient disk allocation | Increase `--disk` parameter |
| SSH timeout after deploy | Instance still loading image | Wait longer or use smaller base image |
| CUDA version mismatch | Image CUDA > host CUDA | Filter offers by `cuda_max_good` |

## Resources
- [Vast.ai Instance Creation](https://docs.vast.ai/api-reference/instances/create-instance)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

## Next Steps
For event-driven workflows, see `vastai-webhooks-events`.

## Examples

**One-command deploy**: `python deploy.py --gpu A100 --image ghcr.io/org/train:v1 --max-price 2.00 --disk 100`

**Multi-GPU deploy**: Set `--gpus 4` and `--gpu H100_SXM` for distributed training with `torchrun`.
