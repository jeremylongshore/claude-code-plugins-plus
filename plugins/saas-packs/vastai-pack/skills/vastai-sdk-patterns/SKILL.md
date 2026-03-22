---
name: vastai-sdk-patterns
description: |
  Apply production-ready Vast.ai SDK patterns for Python and REST API.
  Use when implementing Vast.ai integrations, refactoring SDK usage,
  or establishing coding standards for GPU cloud operations.
  Trigger with phrases like "vastai SDK patterns", "vastai best practices",
  "vastai code patterns", "idiomatic vastai".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, python, patterns]

---
# Vast.ai SDK Patterns

## Overview
Production-ready patterns for the Vast.ai CLI, Python SDK, and REST API at `cloud.vast.ai/api/v0`. Covers typed search queries, instance lifecycle management, offer scoring, and error handling.

## Prerequisites
- Completed `vastai-install-auth` setup
- Python 3.8+ with `requests`
- Familiarity with the Vast.ai marketplace model

## Instructions

### Pattern 1: Typed Search Query Builder

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class GPUQuery:
    num_gpus: int = 1
    gpu_name: Optional[str] = None
    gpu_ram_min: Optional[float] = None
    reliability_min: float = 0.95
    max_dph: Optional[float] = None

    def to_filter(self) -> dict:
        f = {"rentable": {"eq": True}, "num_gpus": {"eq": self.num_gpus},
             "reliability2": {"gte": self.reliability_min}}
        if self.gpu_name:
            f["gpu_name"] = {"eq": self.gpu_name}
        if self.gpu_ram_min:
            f["gpu_ram"] = {"gte": self.gpu_ram_min}
        if self.max_dph:
            f["dph_total"] = {"lte": self.max_dph}
        return f
```

### Pattern 2: Context-Managed Instance Lifecycle

```python
from contextlib import contextmanager

@contextmanager
def managed_instance(client, offer_id, image, disk_gb=20, timeout=300):
    """Auto-destroy instance on exit or exception."""
    inst = client.create_instance(offer_id, image, disk_gb)
    instance_id = inst["new_contract"]
    try:
        info = client.poll_until_running(instance_id, timeout)
        yield info
    finally:
        client.destroy_instance(instance_id)

# Usage
with managed_instance(client, offer["id"], "pytorch/pytorch:latest") as inst:
    ssh_exec(inst["ssh_host"], inst["ssh_port"], "python train.py")
```

### Pattern 3: Offer Scoring

```python
def score_offer(offer, weights=None):
    w = weights or {"cost": 0.4, "reliability": 0.3, "perf": 0.3}
    return (w["cost"] * (1.0 / max(offer["dph_total"], 0.01)) +
            w["reliability"] * offer.get("reliability2", 0) * 100 +
            w["perf"] * offer.get("dlperf", 0))

best = max(offers, key=score_offer)
```

### Pattern 4: Retry with Backoff

```python
import time
from functools import wraps

def retry(max_attempts=3, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1: raise
                    time.sleep(backoff ** i)
        return wrapper
    return decorator
```

### Pattern 5: SSH Command Executor

```python
import subprocess

def ssh_exec(host, port, cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no",
         f"root@{host}", cmd],
        capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"SSH failed: {r.stderr}")
    return r.stdout
```

## Output
- Typed `GPUQuery` builder for search filters
- Context-managed instance lifecycle with auto-destroy
- Offer scoring algorithm (cost, reliability, performance)
- Retry decorator with exponential backoff
- SSH command executor for remote jobs

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Offer unavailable | Already rented | Re-search and pick next best |
| SSH key rejected | Key not uploaded | Upload at cloud.vast.ai > SSH Keys |
| Instance destroyed unexpectedly | Spot preemption | Use `managed_instance` with checkpoints |
| API timeout | Network or server issue | Apply retry decorator |

## Resources
- [REST API Reference](https://vast.ai/developers/api)
- [Search Filtering](https://docs.vast.ai/search-and-filter-gpu-offers)
- [vast-cli GitHub](https://github.com/vast-ai/vast-cli)

## Next Steps
See `vastai-core-workflow-a` for the complete provisioning workflow.

## Examples

**Cost-optimized scoring**: Use weights `{"cost": 0.7, "reliability": 0.2, "perf": 0.1}` for batch jobs where price dominates. Use `{"cost": 0.1, "reliability": 0.6, "perf": 0.3}` for long training runs where uptime matters.

**Auto-cleanup**: Wrap any GPU job in `managed_instance` to guarantee destruction even on crash.
