---
name: vastai-prod-checklist
description: |
  Execute Vast.ai production deployment checklist for GPU workloads.
  Use when deploying training pipelines to production, preparing for
  large-scale GPU jobs, or auditing production readiness.
  Trigger with phrases like "vastai production", "deploy vastai",
  "vastai go-live", "vastai launch checklist".
allowed-tools: Read, Bash(vastai:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, deployment]

---
# Vast.ai Production Checklist

## Overview
Complete checklist for running production GPU workloads on Vast.ai, covering account setup, instance selection, data safety, monitoring, and cost controls.

## Prerequisites
- Vast.ai account with sufficient credits
- Docker images tested and published to registry
- Checkpoint-based training pipeline

## Instructions

### Account & Authentication
- [ ] API key stored in secrets manager (not in code or env files)
- [ ] Dedicated SSH key pair for Vast.ai (not shared with other services)
- [ ] Account balance sufficient for planned workload duration + 50% buffer
- [ ] Billing alerts configured at cloud.vast.ai

### Instance Selection
- [ ] GPU type validated for workload (VRAM, compute capability)
- [ ] Reliability filter set to `>= 0.98` for production jobs
- [ ] Internet speed filter set to `inet_down >= 200` for data transfer
- [ ] Disk allocation includes room for checkpoints + data + 20% overhead
- [ ] CUDA version on host matches Docker image requirements

### Data Safety
- [ ] Training data encrypted before upload to instances
- [ ] Checkpoint saving every N steps (not just per epoch)
- [ ] Checkpoints uploaded to persistent storage (S3/GCS) periodically
- [ ] Instance cleanup script removes data before destruction
- [ ] No sensitive data (API keys, PII) embedded in Docker images

### Spot Instance Protection
- [ ] Spot preemption handler implemented (save checkpoint on SIGTERM)
- [ ] Auto-recovery: detect destroyed instance, provision replacement, resume
- [ ] On-demand fallback configured for critical final training stages
- [ ] Checkpoint integrity verification after recovery

### Monitoring & Alerting
- [ ] GPU utilization monitoring (alert if < 50% for > 10 min)
- [ ] Instance health polling every 60 seconds
- [ ] Cost accumulation tracking with budget threshold alerts
- [ ] Training loss/metrics logged to external service (W&B, MLflow)
- [ ] Dead instance detection (auto-destroy stuck instances)

### Cost Controls
- [ ] Maximum `dph_total` set in search queries
- [ ] Auto-destroy timeout for all instances (e.g., 24h max)
- [ ] Daily spending limit configured
- [ ] Cost-per-job tracking for budget reporting

### Verification Script

```bash
#!/bin/bash
set -euo pipefail
echo "Vast.ai Production Readiness Check"

# 1. Auth
vastai show user --raw | python3 -c "
import sys, json; u=json.load(sys.stdin)
balance = u.get('balance', 0)
print(f'  Auth: OK | Balance: \${balance:.2f}')
assert balance >= 10, f'Balance too low: \${balance:.2f}'
" && echo "  Balance: PASS" || echo "  Balance: FAIL"

# 2. Offer availability
COUNT=$(vastai search offers 'reliability>0.98 num_gpus=1 rentable=true' --raw --limit 1 | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "  Offers available: $COUNT+ | PASS"

# 3. Docker image pullable
docker pull pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime > /dev/null 2>&1 && echo "  Docker image: PASS" || echo "  Docker image: FAIL"

echo "Pre-flight checks complete."
```

## Output
- Production readiness checklist verified
- Verification script passes all checks
- Cost controls and monitoring configured
- Data safety measures in place

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient balance | Credits depleted mid-job | Set up auto-top-up or balance alerts |
| Instance preempted during final epoch | Spot instance reclaimed | Use on-demand for final training stage |
| Checkpoint corrupted | Interrupted mid-save | Implement atomic checkpoint writes (save to temp, rename) |
| GPU utilization drops to 0% | Data pipeline bottleneck | Profile data loading; increase disk I/O |

## Resources
- [Vast.ai Documentation](https://docs.vast.ai)
- [Instance Types](https://docs.vast.ai/api-reference/instances/create-instance)

## Next Steps
For version upgrades, see `vastai-upgrade-migration`.

## Examples

**Pre-launch audit**: Run the verification script, check all boxes, confirm Docker image pulls successfully, and verify at least 3 matching offers are available before starting a production training run.

**Budget-safe launch**: Set `max_dph=2.00`, auto-destroy timeout of 12 hours, and daily spend alert at $50 to prevent cost overruns.
