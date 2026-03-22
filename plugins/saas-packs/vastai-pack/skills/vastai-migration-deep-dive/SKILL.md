---
name: vastai-migration-deep-dive
description: |
  Migrate GPU workloads to or from Vast.ai, or between GPU providers.
  Use when switching from AWS/GCP/Azure GPU instances to Vast.ai,
  migrating between GPU types, or re-platforming ML infrastructure.
  Trigger with phrases like "migrate to vastai", "vastai migration",
  "switch to vastai", "vastai from aws", "vastai from lambda".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, migration]

---
# Vast.ai Migration Deep Dive

## Current State
!`vastai --version 2>/dev/null || echo 'vastai CLI not installed'`
!`pip show vastai 2>/dev/null | grep Version || echo 'N/A'`

## Overview
Migrate GPU workloads to Vast.ai from hyperscaler providers (AWS, GCP, Azure) or other GPU clouds (Lambda, RunPod, CoreWeave). Also covers migrating between GPU types on Vast.ai and the reverse migration away from Vast.ai.

## Prerequisites
- Existing GPU workload with Docker image
- Understanding of current GPU costs and utilization
- Checkpoint-based training pipeline (for training migrations)

## Instructions

### Step 1: Cost Comparison Analysis

```python
# Compare your current GPU costs against Vast.ai marketplace prices
PROVIDER_COSTS = {
    "aws_p4d.24xlarge":      {"gpu": "A100 40GB", "gpus": 8, "hourly": 32.77},
    "aws_p3.2xlarge":        {"gpu": "V100 16GB", "gpus": 1, "hourly": 3.06},
    "gcp_a2-highgpu-1g":     {"gpu": "A100 40GB", "gpus": 1, "hourly": 3.67},
    "azure_NC24ads_A100_v4": {"gpu": "A100 80GB", "gpus": 1, "hourly": 3.67},
    "lambda_1xA100":         {"gpu": "A100",      "gpus": 1, "hourly": 1.25},
}

VASTAI_TYPICAL = {
    "RTX_4090":  0.20,
    "A100":      1.50,
    "H100_SXM":  3.00,
}

def savings_analysis(current_provider, current_hourly, vastai_gpu, vastai_hourly):
    monthly_current = current_hourly * 730  # hours/month
    monthly_vastai = vastai_hourly * 730
    savings = monthly_current - monthly_vastai
    pct = (savings / monthly_current) * 100
    print(f"Current ({current_provider}): ${monthly_current:,.0f}/mo")
    print(f"Vast.ai ({vastai_gpu}): ${monthly_vastai:,.0f}/mo")
    print(f"Savings: ${savings:,.0f}/mo ({pct:.0f}%)")

savings_analysis("AWS p3.2xlarge", 3.06, "RTX_4090", 0.20)
# Output: Savings: $2,088/mo (93%)
```

### Step 2: Docker Image Migration

```bash
# Most Docker images work unchanged on Vast.ai
# Key differences:
# - Vast.ai instances run as root
# - /workspace is the default working directory
# - SSH access (not IAM roles) for authentication

# Adapt your existing Dockerfile
cat << 'DOCKERFILE' > Dockerfile.vastai
FROM your-existing-image:latest

# Vast.ai instances use /workspace by default
WORKDIR /workspace

# Install any Vast.ai-specific tools
RUN pip install boto3  # for S3 checkpoint uploads

# Copy training code
COPY src/ /workspace/src/
COPY configs/ /workspace/configs/

CMD ["python", "src/train.py"]
DOCKERFILE

docker build -t ghcr.io/org/training:vastai -f Dockerfile.vastai .
docker push ghcr.io/org/training:vastai
```

### Step 3: Adapt Cloud Storage Credentials

```python
# On AWS/GCP: IAM roles provide automatic credentials
# On Vast.ai: Pass credentials explicitly via environment variables

# Create instance with env vars for cloud storage access
vastai create instance $OFFER_ID \
  --image ghcr.io/org/training:vastai \
  --disk 100 \
  --env "AWS_ACCESS_KEY_ID=AKIA... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=us-east-1"
```

### Step 4: Migration Validation

```bash
#!/bin/bash
set -euo pipefail
echo "Migration Validation Checklist"

# 1. Docker image runs on Vast.ai
vastai create instance $OFFER_ID --image ghcr.io/org/training:vastai --disk 50
# Wait for running...

# 2. GPU access works
ssh -p $PORT root@$HOST "nvidia-smi && python -c 'import torch; print(torch.cuda.is_available())'"

# 3. Cloud storage works
ssh -p $PORT root@$HOST "aws s3 ls s3://your-bucket/ | head -5"

# 4. Training runs and saves checkpoints
ssh -p $PORT root@$HOST "cd /workspace && python src/train.py --epochs 1 --checkpoint-dir /workspace/ckpt"

# 5. Checkpoints uploaded to cloud storage
ssh -p $PORT root@$HOST "aws s3 sync /workspace/ckpt/ s3://your-bucket/ckpt/"

# 6. Clean up
vastai destroy instance $INSTANCE_ID
echo "Migration validation complete"
```

### Step 5: Rollback Plan

```markdown
## Rollback Procedure
1. Stop all Vast.ai instances: `vastai show instances` → `vastai destroy instance ID`
2. Re-provision on original cloud provider
3. Resume training from cloud-stored checkpoint
4. Vast.ai Docker image remains available for future retry
```

## Migration Comparison

| Factor | AWS/GCP/Azure | Vast.ai |
|--------|--------------|---------|
| Pricing | Fixed, premium | Variable, 50-90% cheaper |
| GPU availability | On-demand guaranteed | Marketplace (may sell out) |
| SLA | 99.9% uptime | No SLA (spot instances) |
| IAM roles | Native | Manual credential passing |
| Networking | VPC, private subnets | Public SSH only |
| Storage | EBS/PD attached | Local disk + cloud storage |
| Support | Enterprise support | Community/email |

## Output
- Cost savings analysis comparing providers
- Adapted Docker image for Vast.ai
- Cloud credential migration pattern
- Validation script for migration testing
- Rollback procedure

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Docker image incompatible | Relies on IAM roles or cloud-specific APIs | Pass credentials via env vars |
| CUDA version mismatch | Different CUDA on Vast.ai hosts | Filter by `cuda_max_good` in search |
| Data transfer too slow | Large dataset over public internet | Stage data in cloud storage, download on instance |
| No matching offers | Specific GPU unavailable | Try alternative GPU type or wait for availability |

## Resources
- [Vast.ai vs AWS](https://vast.ai/)
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)
- [Docker Migration](https://docs.docker.com/get-started/)

## Next Steps
Review `vastai-reference-architecture` for best-practice project structure.

## Examples

**AWS to Vast.ai**: Replace p3.2xlarge ($3.06/hr) with RTX 4090 ($0.20/hr) for a 93% cost reduction. Adapt the Dockerfile to pass AWS credentials via env vars for S3 checkpoint access.

**Hybrid approach**: Use Vast.ai for experimentation and hyperparameter search (cheap GPUs), then run final training on AWS for SLA guarantees.
