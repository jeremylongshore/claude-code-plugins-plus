---
name: vastai-reference-architecture
description: |
  Implement Vast.ai reference architecture for GPU compute workflows.
  Use when designing ML training pipelines, structuring GPU orchestration,
  or establishing architecture patterns for Vast.ai applications.
  Trigger with phrases like "vastai architecture", "vastai design pattern",
  "vastai project structure", "vastai ml pipeline".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, architecture]

---
# Vast.ai Reference Architecture

## Overview
Production architecture for GPU compute workflows on Vast.ai. Covers the three-tier pattern (orchestrator, GPU workers, artifact storage), job queue design, and fault-tolerant training pipelines.

## Prerequisites
- Vast.ai account with CLI
- Cloud storage (S3, GCS, or MinIO) for artifacts
- Understanding of ML training pipelines

## Instructions

### Architecture: Three-Tier GPU Compute

```
┌─────────────────────────────────────────────────┐
│  ORCHESTRATOR (your server / CI / cloud function) │
│  - Job queue management                          │
│  - Instance provisioning via Vast.ai API         │
│  - Status monitoring and auto-recovery           │
│  - Cost tracking and budget enforcement          │
└───────────────┬─────────────────────────────────┘
                │ Vast.ai REST API
┌───────────────▼─────────────────────────────────┐
│  GPU WORKERS (Vast.ai rented instances)          │
│  - Training / inference execution                │
│  - Checkpoint saving to cloud storage            │
│  - Health reporting back to orchestrator         │
│  - Graceful shutdown on SIGTERM (spot preemption)│
└───────────────┬─────────────────────────────────┘
                │ S3 / GCS / MinIO
┌───────────────▼─────────────────────────────────┐
│  ARTIFACT STORAGE (persistent)                   │
│  - Model checkpoints                             │
│  - Training logs and metrics                     │
│  - Dataset cache                                 │
│  - Final model artifacts                         │
└─────────────────────────────────────────────────┘
```

### Project Structure

```
ml-pipeline/
  orchestrator/
    job_queue.py         # Job definition and scheduling
    provisioner.py       # Vast.ai instance lifecycle
    monitor.py           # Status polling and auto-recovery
    cost_tracker.py      # Budget enforcement
  worker/
    Dockerfile           # GPU worker image
    train.py             # Training entry point
    checkpoint.py        # Cloud storage checkpoint manager
    health.py            # Report status back to orchestrator
  config/
    gpu_profiles.yaml    # GPU selection criteria per job type
    budgets.yaml         # Cost limits per team/project
  scripts/
    deploy.py            # CLI for launching jobs
    cost_report.py       # Spending analysis
```

### GPU Profile Configuration

```yaml
# config/gpu_profiles.yaml
profiles:
  dev-test:
    gpu_name: RTX_4090
    num_gpus: 1
    max_dph: 0.25
    reliability_min: 0.90
    max_duration_hours: 2

  training-standard:
    gpu_name: A100
    num_gpus: 1
    max_dph: 2.00
    reliability_min: 0.98
    max_duration_hours: 24

  training-distributed:
    gpu_name: H100_SXM
    num_gpus: 4
    max_dph: 4.00
    reliability_min: 0.99
    max_duration_hours: 48

  inference-batch:
    gpu_name: RTX_4090
    num_gpus: 1
    max_dph: 0.15
    reliability_min: 0.95
    max_duration_hours: 4
```

### Checkpoint Manager Pattern

```python
import boto3, os, json, time

class CheckpointManager:
    def __init__(self, bucket, prefix, interval_steps=500):
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix
        self.interval = interval_steps

    def save(self, model, optimizer, step, metrics):
        if step % self.interval != 0:
            return
        checkpoint = {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "step": step, "metrics": metrics,
            "timestamp": time.time(),
        }
        path = f"{self.prefix}/checkpoint-{step}.pt"
        torch.save(checkpoint, f"/tmp/checkpoint-{step}.pt")
        self.s3.upload_file(f"/tmp/checkpoint-{step}.pt", self.bucket, path)

    def load_latest(self):
        objects = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
        if not objects.get("Contents"):
            return None
        latest = max(objects["Contents"], key=lambda o: o["LastModified"])
        self.s3.download_file(self.bucket, latest["Key"], "/tmp/latest.pt")
        return torch.load("/tmp/latest.pt")
```

## Output
- Three-tier architecture (orchestrator, GPU workers, artifact storage)
- Project structure for ML pipeline on Vast.ai
- GPU profile configuration per job type
- Checkpoint manager with cloud storage integration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Orchestrator loses track of instance | API timeout | Implement heartbeat from worker |
| Checkpoint upload fails | S3 permissions | Verify credentials on GPU instance |
| Worker can't reach orchestrator | No public IP | Use polling model (worker pulls jobs) |
| Budget exceeded | No cost controls | Implement profile-based max_duration_hours |

## Resources
- [Vast.ai REST API](https://vast.ai/developers/api)
- [PyTorch Distributed](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html)

## Next Steps
For multi-environment configuration, see `vastai-multi-env-setup`.

## Examples

**Simple pipeline**: Orchestrator searches for offers matching `training-standard` profile, provisions instance, uploads data via SCP, runs training, saves checkpoints to S3, destroys instance.

**Fault-tolerant training**: Worker saves checkpoint every 500 steps to S3. On preemption, orchestrator provisions replacement and worker resumes from latest checkpoint.
