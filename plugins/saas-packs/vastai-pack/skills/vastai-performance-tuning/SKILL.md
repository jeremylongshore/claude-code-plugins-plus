---
name: vastai-performance-tuning
description: |
  Optimize Vast.ai GPU instance selection, startup time, and training throughput.
  Use when optimizing instance selection, reducing startup latency,
  or maximizing GPU utilization on rented hardware.
  Trigger with phrases like "vastai performance", "optimize vastai",
  "vastai slow", "vastai gpu utilization", "vastai throughput".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(ssh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, performance]

---
# Vast.ai Performance Tuning

## Overview
Optimize GPU instance selection, startup time, and training throughput on Vast.ai. Key levers: Docker image caching, GPU selection by dlperf score, data pipeline optimization, and multi-GPU scaling.

## Prerequisites
- Vast.ai account with active or planned instances
- Understanding of GPU compute bottlenecks
- Profiling tools (nvidia-smi, torch.profiler)

## Instructions

### Step 1: Optimize Instance Selection by Performance

```bash
# Sort by dlperf (deep learning performance benchmark) instead of price
vastai search offers 'num_gpus=1 gpu_ram>=24 reliability>0.95' \
  --order 'dlperf-' --limit 10

# The dlperf field measures actual GPU compute throughput
# Higher dlperf = faster training even at same GPU model
# Variance within same GPU model can be 20-30%
```

```python
def select_by_performance_per_dollar(offers):
    """Select the offer with best performance per dollar."""
    for o in offers:
        o["perf_per_dollar"] = o.get("dlperf", 0) / max(o["dph_total"], 0.01)
    return max(offers, key=lambda o: o["perf_per_dollar"])
```

### Step 2: Reduce Instance Startup Time

```bash
# Use smaller, pre-cached Docker images
# FAST: nvidia/cuda:12.1.1-runtime-ubuntu22.04 (~2GB, widely cached)
# MEDIUM: pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime (~4GB)
# SLOW: custom-image:latest with pip install at build (~10GB+)

# Pre-install deps in the image, not in onstart
# BAD (slow startup):
vastai create instance $ID --image pytorch/pytorch:latest \
  --onstart-cmd "pip install transformers datasets wandb"

# GOOD (fast startup):
# Build custom image with all deps pre-installed
```

### Step 3: Data Pipeline Optimization

```python
# Profile GPU utilization on the instance
# SSH into instance and run:
"""
watch -n 1 nvidia-smi  # Check if GPU util is <80% → data bottleneck

# Common fixes for low GPU utilization:
# 1. Increase DataLoader num_workers
# 2. Use pin_memory=True
# 3. Pre-fetch data to local SSD (not NFS)
# 4. Use WebDataset or FFCV for streaming datasets
"""

# Optimize PyTorch DataLoader
from torch.utils.data import DataLoader

loader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,       # Match CPU cores on instance
    pin_memory=True,     # Faster GPU transfer
    prefetch_factor=2,   # Pre-load 2 batches per worker
    persistent_workers=True,  # Don't respawn workers each epoch
)
```

### Step 4: GPU Memory Optimization

```python
# Check available VRAM before selecting batch size
import torch

def optimal_batch_size(model, sample_input, gpu_memory_gb):
    """Binary search for largest batch size that fits in VRAM."""
    lo, hi, best = 1, 512, 1
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            torch.cuda.empty_cache()
            batch = sample_input.repeat(mid, *([1] * (sample_input.dim() - 1)))
            _ = model(batch.cuda())
            best = mid
            lo = mid + 1
        except torch.cuda.OutOfMemoryError:
            hi = mid - 1
        torch.cuda.empty_cache()
    return best
```

### Step 5: Multi-GPU Scaling

```bash
# Search for multi-GPU offers (NVLink preferred for training)
vastai search offers 'num_gpus>=4 gpu_name=A100 total_flops>=100' \
  --order 'dph_total' --limit 5

# Use torchrun for distributed training
ssh -p $PORT root@$HOST "torchrun --nproc_per_node=4 train.py --batch-size 128"
```

## GPU Performance Reference

| GPU | VRAM | FP16 TFLOPS | Typical $/hr | Best For |
|-----|------|-------------|-------------|----------|
| RTX 4090 | 24GB | 82.6 | $0.15-0.30 | Fine-tuning, inference |
| A100 40GB | 40GB | 77.97 | $0.80-1.50 | Training medium models |
| A100 80GB | 80GB | 77.97 | $1.00-2.00 | Training large models |
| H100 SXM | 80GB | 267 | $2.50-4.00 | High-throughput training |

## Output
- Performance-per-dollar offer selection
- Optimized Docker image for fast startup
- Data pipeline tuning (DataLoader, pin_memory, workers)
- GPU memory optimization with auto batch sizing
- Multi-GPU scaling with torchrun

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Low GPU utilization (<50%) | Data pipeline bottleneck | Increase `num_workers`, use `pin_memory` |
| OOM during training | Batch size too large | Use `optimal_batch_size()` or gradient accumulation |
| Slow instance startup | Large Docker image | Pre-install deps in image, not onstart |
| Poor multi-GPU scaling | Communication bottleneck | Use NVLink-connected GPUs, reduce sync frequency |

## Resources
- [Vast.ai Search Filtering](https://docs.vast.ai/search-and-filter-gpu-offers)
- [PyTorch Performance Guide](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)

## Next Steps
For cost optimization, see `vastai-cost-tuning`.

## Examples

**Profile first**: SSH into instance, run `watch nvidia-smi` during training. If GPU-Util < 80%, the bottleneck is data loading, not compute.

**Best value GPU**: Use `perf_per_dollar` scoring to find hosts where the same GPU model runs faster due to better cooling or fewer co-tenants.
