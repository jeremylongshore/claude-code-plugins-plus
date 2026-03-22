---
name: vastai-observability
description: |
  Monitor Vast.ai GPU instance health, utilization, and costs.
  Use when setting up monitoring dashboards, configuring alerts,
  or tracking GPU utilization and spending.
  Trigger with phrases like "vastai monitoring", "vastai metrics",
  "vastai observability", "monitor vastai", "vastai alerts".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, monitoring, observability]

---
# Vast.ai Observability

## Overview
Monitor Vast.ai GPU instance health, utilization, and costs. Key metrics: GPU utilization (idle GPUs waste $0.20-$4.00/hr), instance uptime, training progress, cost accumulation, and spot preemption events.

## Prerequisites
- Vast.ai account with active instances
- `vastai` CLI installed
- Optional: Prometheus, Grafana, or Datadog for dashboarding

## Instructions

### Step 1: Instance Metrics Collector

```python
import subprocess, json, time
from datetime import datetime

class VastMetricsCollector:
    def __init__(self, output_file="vast_metrics.jsonl"):
        self.output_file = output_file

    def collect(self):
        result = subprocess.run(
            ["vastai", "show", "instances", "--raw"],
            capture_output=True, text=True)
        instances = json.loads(result.stdout)

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_instances": len(instances),
            "running": 0, "total_hourly_cost": 0,
            "instances": [],
        }

        for inst in instances:
            status = inst.get("actual_status", "unknown")
            dph = inst.get("dph_total", 0)
            if status == "running":
                metrics["running"] += 1
                metrics["total_hourly_cost"] += dph

            metrics["instances"].append({
                "id": inst["id"],
                "gpu": inst.get("gpu_name"),
                "status": status,
                "dph": dph,
                "gpu_util": inst.get("gpu_util", 0),
                "gpu_temp": inst.get("gpu_temp", 0),
            })

        with open(self.output_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")

        return metrics

    def run(self, interval=60):
        while True:
            m = self.collect()
            print(f"[{m['timestamp']}] Running: {m['running']} | "
                  f"Cost: ${m['total_hourly_cost']:.3f}/hr")
            time.sleep(interval)
```

### Step 2: Alert Conditions

```python
def check_alerts(metrics):
    alerts = []

    # Idle GPU alert (running but <10% utilization)
    for inst in metrics["instances"]:
        if inst["status"] == "running" and inst["gpu_util"] < 10:
            alerts.append(f"IDLE: Instance {inst['id']} GPU util={inst['gpu_util']}% "
                         f"(wasting ${inst['dph']:.3f}/hr)")

    # High temperature alert
    for inst in metrics["instances"]:
        if inst.get("gpu_temp", 0) > 85:
            alerts.append(f"HOT: Instance {inst['id']} GPU temp={inst['gpu_temp']}C")

    # Budget alert
    daily_projection = metrics["total_hourly_cost"] * 24
    if daily_projection > 100:
        alerts.append(f"BUDGET: Projected daily cost ${daily_projection:.2f}")

    return alerts
```

### Step 3: Remote GPU Monitoring

```bash
# SSH into instance and collect nvidia-smi metrics
ssh -p $PORT root@$HOST "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits"
# Output: 95, 20480, 24576, 72, 285
```

### Step 4: Prometheus Exporter (Optional)

```python
from prometheus_client import Gauge, start_http_server

gpu_util = Gauge("vastai_gpu_utilization", "GPU utilization %", ["instance_id", "gpu_name"])
hourly_cost = Gauge("vastai_hourly_cost", "Total hourly cost USD")
instance_count = Gauge("vastai_instance_count", "Running instances")

def export_metrics(metrics):
    instance_count.set(metrics["running"])
    hourly_cost.set(metrics["total_hourly_cost"])
    for inst in metrics["instances"]:
        if inst["status"] == "running":
            gpu_util.labels(inst["id"], inst["gpu"]).set(inst["gpu_util"])

start_http_server(9090)  # Prometheus scrape target
```

## Output
- Metrics collector with JSONL output
- Alert conditions (idle GPU, high temp, budget)
- Remote GPU monitoring via SSH + nvidia-smi
- Optional Prometheus exporter for Grafana dashboards

## Error Handling
| Alert | Threshold | Response |
|-------|-----------|----------|
| Idle GPU | util < 10% for > 10 min | Investigate or destroy instance |
| High temp | > 85C sustained | Reduce workload or report to host |
| Budget exceeded | Projected daily > $100 | Destroy non-critical instances |
| Instance offline | Status changed from running | Trigger auto-recovery |

## Resources
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)
- [NVIDIA nvidia-smi](https://developer.nvidia.com/nvidia-system-management-interface)

## Next Steps
For incident response procedures, see `vastai-incident-runbook`.

## Examples

**Quick dashboard**: Run `VastMetricsCollector().run(interval=30)` in tmux on a monitoring server. Pipe alerts to Slack via webhook.

**Cost tracking**: Parse `vast_metrics.jsonl` to plot hourly cost over time and identify spending patterns.
