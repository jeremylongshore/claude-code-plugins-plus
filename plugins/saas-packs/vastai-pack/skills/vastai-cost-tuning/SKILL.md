---
name: vastai-cost-tuning
description: |
  Optimize Vast.ai GPU cloud costs through smart instance selection and lifecycle management.
  Use when analyzing GPU spending, reducing training costs,
  or implementing budget controls for Vast.ai workloads.
  Trigger with phrases like "vastai cost", "vastai billing",
  "reduce vastai costs", "vastai pricing", "vastai budget".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, cost-optimization]

---
# Vast.ai Cost Tuning

## Overview
Minimize Vast.ai GPU cloud costs by choosing the right GPU for your workload, leveraging interruptible (spot) instances, eliminating idle compute, and implementing auto-destroy safeguards. Vast.ai pricing is dynamic and varies significantly: RTX 4090 ($0.15-0.30/hr), A100 80GB ($1.00-2.00/hr), H100 SXM ($2.50-4.00/hr).

## Prerequisites
- Vast.ai account with billing history
- Understanding of your workload's GPU requirements
- `vastai` CLI installed

## Instructions

### Step 1: GPU Selection by Cost-Efficiency

```python
# Compare cost-per-TFLOP across GPU types
GPU_SPECS = {
    "RTX_4090":  {"fp16_tflops": 82.6,  "vram": 24},
    "A100":      {"fp16_tflops": 77.97, "vram": 80},
    "H100_SXM":  {"fp16_tflops": 267,   "vram": 80},
    "RTX_3090":  {"fp16_tflops": 35.6,  "vram": 24},
    "A6000":     {"fp16_tflops": 38.7,  "vram": 48},
}

def cost_per_tflop(gpu_name, dph):
    specs = GPU_SPECS.get(gpu_name, {"fp16_tflops": 1})
    return dph / specs["fp16_tflops"]

# Often RTX 4090 is the best value for inference
# A100 is best for training large models needing >24GB VRAM
# H100 is best only when wall-clock time justifies 10x price premium
```

### Step 2: Spot vs On-Demand Analysis

```bash
# Interruptible (spot) instances are 30-60% cheaper
vastai search offers 'num_gpus=1 gpu_name=RTX_4090 rentable=true' \
  --order dph_total --limit 5
# Compare interruptible vs on-demand pricing
# Use interruptible for: batch inference, checkpointed training
# Use on-demand for: final training epochs, production inference
```

### Step 3: Auto-Destroy Safeguards

```python
import time, subprocess, json

def auto_destroy_after(instance_id, max_hours=4):
    """Destroy instance after max_hours to prevent cost overruns."""
    max_seconds = max_hours * 3600
    time.sleep(max_seconds)
    subprocess.run(["vastai", "destroy", "instance", str(instance_id)], check=True)
    print(f"Instance {instance_id} auto-destroyed after {max_hours}h")

# Run in background thread when provisioning
import threading
watchdog = threading.Thread(target=auto_destroy_after, args=(inst_id, 4), daemon=True)
watchdog.start()
```

### Step 4: Idle Instance Detection

```bash
#!/bin/bash
# Find and destroy idle instances (GPU util < 10% for >10 min)
vastai show instances --raw | python3 -c "
import sys, json
for inst in json.load(sys.stdin):
    if inst.get('actual_status') == 'running':
        gpu_util = inst.get('gpu_util', 0)
        if gpu_util < 10:
            print(f'IDLE: Instance {inst[\"id\"]} GPU util={gpu_util}% '
                  f'(\${inst.get(\"dph_total\", 0):.3f}/hr)')
"
```

### Step 5: Cost Reporting

```python
def daily_cost_report():
    """Calculate current daily burn rate from running instances."""
    result = subprocess.run(
        ["vastai", "show", "instances", "--raw"],
        capture_output=True, text=True)
    instances = json.loads(result.stdout)

    total_hourly = 0
    for inst in instances:
        if inst.get("actual_status") == "running":
            dph = inst.get("dph_total", 0)
            total_hourly += dph
            print(f"  {inst['id']}: {inst.get('gpu_name')} ${dph:.3f}/hr")

    print(f"\nTotal: ${total_hourly:.3f}/hr = ${total_hourly * 24:.2f}/day")
```

## Cost Optimization Checklist

- [ ] Always search with `--order dph_total` to find cheapest offers
- [ ] Use interruptible instances for checkpointed workloads
- [ ] Implement auto-destroy timeout on all instances
- [ ] Monitor GPU utilization; destroy idle instances
- [ ] Use RTX 4090 for workloads that fit in 24GB VRAM
- [ ] Only use H100 when wall-clock time savings justify cost premium
- [ ] Pre-install dependencies in Docker images (avoid paying for pip install)

## Output
- GPU cost-efficiency analysis by model
- Spot vs on-demand comparison
- Auto-destroy watchdog for cost protection
- Idle instance detection script
- Daily cost burn rate report

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Unexpected $50+ bill | Forgot to destroy instances | Implement auto-destroy watchdog |
| GPU idle at $2/hr | Waiting for data download | Pre-stage data before provisioning GPU |
| Spot preemption mid-job | Cheapest instance reclaimed | Checkpoint frequently; auto-recover |

## Resources
- [Vast.ai Pricing](https://vast.ai/)
- [Search & Filter](https://docs.vast.ai/search-and-filter-gpu-offers)

## Next Steps
For reference architecture, see `vastai-reference-architecture`.

## Examples

**Budget cap**: Set `dph_total<=0.25` in search queries and `auto_destroy_after(inst_id, 4)` to cap any single job at $1.00.

**GPU comparison**: Run the same workload on RTX 4090 ($0.20/hr) vs A100 ($1.50/hr). If the A100 finishes in less than 1/7th the time, it's cheaper overall.
