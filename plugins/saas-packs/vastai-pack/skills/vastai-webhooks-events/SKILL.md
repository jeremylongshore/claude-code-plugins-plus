---
name: vastai-webhooks-events
description: |
  Implement Vast.ai webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Vast.ai event notifications securely.
  Trigger with phrases like "vastai webhook", "vastai events",
  "vastai webhook signature", "handle vastai events", "vastai notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Webhooks & Events

## Overview
Build event-driven workflows around Vast.ai GPU cloud instance lifecycle. Vast.ai provides a REST API at `cloud.vast.ai/api` for managing GPU instances. This skill covers monitoring instance state changes, handling bid/offer events, and building automated GPU pipeline management with callbacks for training jobs, inference serving, and cost optimization.

## Prerequisites
- Vast.ai account with API key stored in `VASTAI_API_KEY` environment variable
- Vast.ai CLI installed (`pip install vastai`)
- Understanding of Vast.ai instance types (on-demand, interruptible, bid)
- Queue system for managing GPU job lifecycle

## Event Patterns

| Event | Trigger | Use Case |
|-------|---------|----------|
| Instance created | GPU provisioned | Start training job |
| Instance running | Boot complete | Deploy model, begin work |
| Instance destroyed | Termination (manual/bid) | Save checkpoints, cleanup |
| Bid outbid | Higher bid placed | Migrate workload |
| Job completed | Training script exits | Download results |

## Instructions

### Step 1: Monitor Instance Lifecycle
```python
import requests
import time
import os
import json

VASTAI_API = "https://cloud.vast.ai/api/v0"
API_KEY = os.environ["VASTAI_API_KEY"]

def get_instances():
    response = requests.get(
        f"{VASTAI_API}/instances",
        params={"api_key": API_KEY},
    )
    return response.json()["instances"]

def monitor_instances(callback_url, poll_interval=30):
    known_states = {}

    while True:
        instances = get_instances()

        for instance in instances:
            instance_id = instance["id"]
            current_state = instance["actual_status"]
            previous_state = known_states.get(instance_id)

            if previous_state != current_state:
                known_states[instance_id] = current_state
                requests.post(callback_url, json={
                    "event": f"instance.{current_state}",
                    "instance_id": instance_id,
                    "gpu": instance["gpu_name"],
                    "cost_per_hour": instance["dph_total"],
                    "previous_state": previous_state,
                })

        time.sleep(poll_interval)
```

### Step 2: Handle Instance Events
```typescript
app.post("/webhooks/vastai", async (req, res) => {
  const { event, instance_id, gpu, cost_per_hour } = req.body;
  res.status(200).json({ received: true });

  switch (event) {
    case "instance.running":
      await onInstanceReady(instance_id, gpu);
      break;
    case "instance.exited":
      await onInstanceStopped(instance_id);
      break;
    case "instance.destroyed":
      await onInstanceDestroyed(instance_id);
      break;
  }
});

async function onInstanceReady(instanceId: string, gpu: string) {
  console.log(`GPU instance ${instanceId} ready (${gpu})`);

  await executeRemoteCommand(instanceId, [
    "cd /workspace",
    "git clone https://github.com/myorg/training-repo.git",
    "cd training-repo && python train.py --config config.yaml",
  ]);
}

async function onInstanceDestroyed(instanceId: string) {
  const job = await db.jobs.findByInstance(instanceId);
  if (job && !job.completed) {
    await provisionNewInstance(job);
  }
}
```

### Step 3: Automated GPU Provisioning
```python
def create_instance(gpu_type, disk_gb=50):
    response = requests.get(
        f"{VASTAI_API}/bundles",
        params={
            "api_key": API_KEY,
            "q": json.dumps({
                "gpu_name": {"eq": gpu_type},
                "rentable": {"eq": True},
                "disk_space": {"gte": disk_gb},
                "reliability2": {"gte": 0.95},
            }),
            "order": "dph_total",
            "limit": 1,
        },
    )

    offers = response.json()["offers"]
    if not offers:
        raise ValueError(f"No {gpu_type} instances available")

    result = requests.put(
        f"{VASTAI_API}/asks/{offers[0]['id']}/",
        params={"api_key": API_KEY},
        json={
            "image": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
            "disk": disk_gb,
            "onstart": "pip install -r requirements.txt && python train.py",
        },
    )
    return result.json()
```

### Step 4: Cost Monitoring
```python
def check_spending(budget_limit):
    instances = get_instances()
    hourly_total = sum(
        i["dph_total"] for i in instances
        if i["actual_status"] == "running"
    )

    if hourly_total > budget_limit:
        interruptible = sorted(
            [i for i in instances if i["is_bid"]],
            key=lambda x: x["dph_total"],
        )
        for instance in interruptible:
            destroy_instance(instance["id"])
            hourly_total -= instance["dph_total"]
            if hourly_total <= budget_limit:
                break
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Instance preempted | Outbid on spot | Save checkpoints frequently, auto-reprovision |
| SSH connection failed | Instance still booting | Poll status until `running`, then retry |
| Out of disk space | Large model/data | Increase `disk` parameter on creation |
| No available GPUs | High demand | Broaden GPU type search or increase bid |

## Examples

### Quick Instance Launch
```bash
vastai search offers 'gpu_name=RTX_4090 reliability2>0.95' -o 'dph_total'
vastai create instance $OFFER_ID --image pytorch/pytorch:latest --disk 50
```

## Resources
- [Vast.ai API Documentation](https://vast.ai/docs)
- [Vast.ai CLI Reference](https://vast.ai/docs/cli)
- [Vast.ai Instance Types](https://vast.ai/docs/gpu-instances)

## Next Steps
For multi-environment setup, see `vastai-multi-env-setup`.
