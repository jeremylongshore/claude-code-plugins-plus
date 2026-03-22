---
name: vastai-webhooks-events
description: |
  Build event-driven workflows around Vast.ai instance lifecycle events.
  Use when monitoring instance status changes, implementing auto-recovery,
  or building event-driven GPU orchestration.
  Trigger with phrases like "vastai events", "vastai instance monitoring",
  "vastai status changes", "vastai lifecycle events".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, webhooks]

---
# Vast.ai Webhooks & Events

## Overview
Build event-driven workflows around Vast.ai GPU instance lifecycle. Vast.ai does not provide traditional webhooks, so event detection relies on polling the REST API at `cloud.vast.ai/api/v0` and reacting to instance status transitions (loading, running, exited, error, offline).

## Prerequisites
- Vast.ai CLI authenticated
- Understanding of instance lifecycle states
- Python 3.8+ for event loop implementation

## Instructions

### Step 1: Instance Status Poller

```python
import time, json, subprocess
from typing import Callable, Dict, List

class InstanceEventPoller:
    """Poll Vast.ai API and emit events on status transitions."""

    def __init__(self, api_key: str, poll_interval: int = 30):
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.previous_states: Dict[int, str] = {}
        self.handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable):
        self.handlers.setdefault(event, []).append(handler)

    def poll_once(self):
        result = subprocess.run(
            ["vastai", "show", "instances", "--raw"],
            capture_output=True, text=True)
        instances = json.loads(result.stdout)

        for inst in instances:
            inst_id = inst["id"]
            status = inst.get("actual_status", "unknown")
            prev = self.previous_states.get(inst_id)

            if prev and prev != status:
                event = f"{prev}_to_{status}"
                for handler in self.handlers.get(event, []):
                    handler(inst)
                for handler in self.handlers.get("any_change", []):
                    handler(inst, prev, status)

            self.previous_states[inst_id] = status

    def run(self):
        print(f"Polling every {self.poll_interval}s...")
        while True:
            self.poll_once()
            time.sleep(self.poll_interval)
```

### Step 2: Event Handlers

```python
def on_instance_running(instance):
    print(f"Instance {instance['id']} is RUNNING")
    print(f"  SSH: ssh -p {instance['ssh_port']} root@{instance['ssh_host']}")
    # Trigger: start training job, send notification, etc.

def on_instance_exited(instance):
    print(f"Instance {instance['id']} EXITED")
    # Trigger: collect results, check for errors, notify team

def on_spot_preemption(instance, old_status, new_status):
    if old_status == "running" and new_status in ("exited", "offline"):
        print(f"ALERT: Instance {instance['id']} may have been preempted")
        # Trigger: auto-recovery, provision replacement

# Wire up handlers
poller = InstanceEventPoller(api_key)
poller.on("loading_to_running", on_instance_running)
poller.on("running_to_exited", on_instance_exited)
poller.on("any_change", on_spot_preemption)
poller.run()
```

### Step 3: Auto-Recovery on Preemption

```python
def auto_recover(instance, old_status, new_status):
    """Automatically replace preempted instances."""
    if old_status != "running" or new_status not in ("exited", "offline", "error"):
        return

    gpu_name = instance.get("gpu_name", "RTX_4090")
    image = instance.get("image_uuid", "pytorch/pytorch:latest")

    print(f"Auto-recovering {instance['id']} ({gpu_name})...")

    # Search for replacement
    offers = json.loads(subprocess.run(
        ["vastai", "search", "offers",
         f"gpu_name={gpu_name} reliability>0.98 rentable=true",
         "--order", "dph_total", "--raw", "--limit", "3"],
        capture_output=True, text=True, check=True).stdout)

    if offers:
        new_id = json.loads(subprocess.run(
            ["vastai", "create", "instance", str(offers[0]["id"]),
             "--image", image, "--disk", "50", "--raw"],
            capture_output=True, text=True, check=True).stdout)["new_contract"]
        print(f"Replacement instance: {new_id}")
```

### Step 4: Cost Event Tracking

```python
def track_costs(instance, old_status, new_status):
    """Log cost events for billing tracking."""
    if new_status == "running":
        print(f"BILLING START: Instance {instance['id']} "
              f"at ${instance.get('dph_total', 0):.3f}/hr")
    elif old_status == "running":
        print(f"BILLING STOP: Instance {instance['id']}")
```

## Output
- Polling-based event detection for instance status changes
- Event handlers for running, exited, preempted states
- Auto-recovery on spot preemption
- Cost tracking event logger

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missed status transition | Poll interval too long | Reduce to 15-30s for critical instances |
| False preemption alert | Instance restarted intentionally | Track expected state changes |
| Auto-recovery loops | Same host keeps failing | Exclude failed host IDs from search |
| API timeout during poll | Network or rate limiting | Retry with backoff; continue polling |

## Resources
- [Vast.ai REST API](https://vast.ai/developers/api)
- [Instance Management](https://docs.vast.ai/api-reference/instances/create-instance)

## Next Steps
For performance optimization, see `vastai-performance-tuning`.

## Examples

**Slack notifications**: Wire `on_instance_running` to send a Slack message with SSH connection details. Wire `on_spot_preemption` to alert the team.

**Training monitor**: Track `running_to_exited` events. If exit was expected (job complete), collect results. If unexpected, trigger auto-recovery with checkpoint resume.
