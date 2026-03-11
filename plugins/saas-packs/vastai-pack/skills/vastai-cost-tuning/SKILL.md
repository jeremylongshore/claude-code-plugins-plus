---
name: vastai-cost-tuning
description: |
  Optimize Vast.ai costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Vast.ai billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "vastai cost", "vastai billing",
  "reduce vastai costs", "vastai pricing", "vastai expensive", "vastai budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Cost Tuning

## Overview
Minimize Vast.ai GPU cloud costs by choosing the right GPU for your workload, leveraging interruptible (spot) instances, and eliminating idle compute time. Vast.ai is a GPU marketplace with highly variable pricing: RTX 4090 (~$0.15-0.30/hr), A100 80GB (~$1.00-2.00/hr), H100 (~$2.50-4.00/hr). The biggest cost levers are: using interruptible instances (30-60% cheaper), auto-terminating idle GPUs, choosing the cheapest GPU that meets your VRAM/compute requirements, and time-boxing training jobs.

## Prerequisites
- Vast.ai account with `vastai` CLI installed
- Understanding of your workload's GPU requirements (VRAM, compute)
- Checkpointing implemented for interruptible workloads

## Instructions

### Step 1: Choose the Right GPU for Your Workload
```yaml
# GPU selection by workload type
inference_7b_model:
  recommended: RTX 3090 (24GB VRAM)
  cost: "$0.10-0.20/hr"
  why: "Cheapest GPU with enough VRAM for 7B models"

inference_70b_model:
  recommended: A100 40GB or 2x RTX 3090
  cost: "$0.80-1.50/hr"
  why: "Need 40GB+ VRAM for quantized 70B models"

training_small:
  recommended: RTX 4090 (24GB VRAM)
  cost: "$0.15-0.30/hr"
  why: "Best price/performance for fine-tuning up to 13B"

training_large:
  recommended: A100 80GB
  cost: "$1.00-2.00/hr"
  why: "Need 80GB VRAM for full-precision large model training"
```

### Step 2: Use Interruptible Instances
```bash
# Interruptible (spot) instances are 30-60% cheaper
# Search for cheapest interruptible A100
vastai search offers 'gpu_name=A100 num_gpus=1 reliability>0.9 interruptible=true' \
  --order 'dph_total' --limit 5

# Create interruptible instance (must implement checkpointing!)
vastai create instance OFFER_ID --interruptible \
  --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel \
  --onstart-cmd "cd /workspace && python train.py --resume-from-checkpoint"
```

### Step 3: Auto-Terminate Idle Instances
```bash
# Cron job every 15 minutes: kill instances idle >1 hour
#!/bin/bash
vastai show instances --raw | \
  jq -r '.[] | select(.gpu_utilization < 5 and ((.cur_state_time - .start_time) > 3600)) | .id' | \
  while read id; do
    echo "Destroying idle instance $id (GPU util <5% for >1hr)"
    vastai destroy instance "$id"
  done
```

### Step 4: Time-Box Training Jobs
```python
# Set maximum runtime to prevent runaway costs
import subprocess, time

MAX_HOURS = 8  # Budget: 8 hours max
INSTANCE_ID = "12345"

start_time = time.time()
while True:
    elapsed_hours = (time.time() - start_time) / 3600
    if elapsed_hours > MAX_HOURS:
        print(f"Time limit reached ({MAX_HOURS}h). Saving checkpoint and terminating.")
        subprocess.run(["vastai", "destroy", "instance", INSTANCE_ID])
        break
    time.sleep(300)  # Check every 5 minutes
```

### Step 5: Compare Pricing Before Provisioning
```bash
# Always compare offers before creating an instance
vastai search offers 'gpu_name=RTX_4090 num_gpus=1 reliability>0.95 inet_down>200' \
  --order 'dph_total' --limit 10 | \
  head -5
# Price varies 2-3x for same GPU depending on host, region, and demand

# Calculate total cost before starting
echo "Job estimate: 4x A100 for 12 hours"
echo "Cheapest offer: \$(vastai search offers 'gpu_name=A100 num_gpus=4' --order 'dph_total' --limit 1 | awk 'NR==2{print $6}')/hr"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Instance preempted mid-training | Using interruptible without checkpointing | Implement checkpoint saving every 30 minutes |
| Overpaying for GPU | Not comparing offers | Always search and sort by price before provisioning |
| Idle GPU burning money | Job finished but instance still running | Add auto-terminate script to training pipeline |
| Insufficient VRAM | Wrong GPU selected | Check model VRAM requirements before provisioning |

## Examples
```bash
# Quick cost comparison for a training job
for gpu in RTX_3090 RTX_4090 A100; do
  PRICE=$(vastai search offers "gpu_name=$gpu num_gpus=1" --order 'dph_total' --limit 1 2>/dev/null | awk 'NR==2{print $6}')
  echo "$gpu: \$${PRICE}/hr, 24h job = \$$(echo "$PRICE * 24" | bc)"
done
```
