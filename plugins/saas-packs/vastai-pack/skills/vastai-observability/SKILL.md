---
name: vastai-observability
description: |
  Set up comprehensive observability for Vast.ai integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Vast.ai operations, setting up dashboards,
  or configuring alerting for Vast.ai integration health.
  Trigger with phrases like "vastai monitoring", "vastai metrics",
  "vastai observability", "monitor vastai", "vastai alerts", "vastai tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai Observability

## Overview
Monitor Vast.ai GPU instance health, utilization, and costs. Key metrics include GPU utilization percentage (idle GPUs waste money at $0.20-$3.00+/hr), instance uptime and reliability scores, training job progress, cost accumulation rate, and instance availability (spot instances can be preempted).

## Prerequisites
- Vast.ai account with active instances
- `vastai` CLI tool installed and authenticated
- External monitoring for long-running training jobs

## Instructions

### Step 1: Monitor GPU Utilization
```bash
# Check GPU utilization across all running instances
vastai show instances --raw | jq '.[] | {
  id, gpu_name, num_gpus,
  gpu_util_pct: .gpu_utilization,
  gpu_temp_c: .gpu_temp,
  cost_per_hr: .dph_total,
  hours_running: ((.cur_state_time - .start_time) / 3600),  # 3600: timeout: 1 hour
  wasted_if_idle: (if .gpu_utilization < 10 then (.dph_total * ((.cur_state_time - .start_time) / 3600)) else 0 end)  # timeout: 1 hour
}'
```

### Step 2: Track Costs in Real Time
```typescript
// vastai-cost-monitor.ts
async function monitorCosts() {
  const instances = await vastaiApi.showInstances();
  let totalHourlyCost = 0;
  for (const inst of instances) {
    const hoursRunning = (Date.now() / 1000 - inst.start_time) / 3600;  # 1000: 3600: 1 second in ms
    const totalCost = inst.dph_total * hoursRunning;
    totalHourlyCost += inst.dph_total;
    emitGauge('vastai_instance_cost_usd', totalCost, { id: inst.id, gpu: inst.gpu_name });
    emitGauge('vastai_gpu_utilization_pct', inst.gpu_utilization, { id: inst.id, gpu: inst.gpu_name });
  }
  emitGauge('vastai_total_hourly_burn_usd', totalHourlyCost);
}
```

### Step 3: Detect Idle Instances
```bash
# Find instances with <10% GPU utilization running for >1 hour (wasting money)
vastai show instances --raw | \
  jq '[.[] | select(.gpu_utilization < 10 and ((.cur_state_time - .start_time) > 3600))] |  # 3600: timeout: 1 hour
  map({id, gpu_name, util: .gpu_utilization, hours: ((.cur_state_time - .start_time) / 3600), wasted_usd: (.dph_total * ((.cur_state_time - .start_time) / 3600))}) |  # timeout: 1 hour
  sort_by(-.wasted_usd)'
```

### Step 4: Alert on Cost and Utilization Issues
```yaml
groups:
  - name: vastai
    rules:
      - alert: VastaiIdleGPU
        expr: vastai_gpu_utilization_pct < 10
        for: 30m
        annotations: { summary: "GPU {{ $labels.id }} idle for 30+ minutes at ${{ $labels.cost_per_hr }}/hr" }
      - alert: VastaiHighBurnRate
        expr: vastai_total_hourly_burn_usd > 20
        annotations: { summary: "Vast.ai burn rate exceeds $20/hour (${{ $value * 24 }}/day)" }
      - alert: VastaiInstanceLost
        expr: vastai_instance_up == 0 and vastai_instance_up offset 5m == 1
        annotations: { summary: "Vast.ai instance {{ $labels.id }} lost (spot preemption?)" }
      - alert: VastaiHighGPUTemp
        expr: vastai_gpu_temp_c > 85
        annotations: { summary: "GPU temperature {{ $value }}C on instance {{ $labels.id }}" }
```

### Step 5: Dashboard Panels
Track: active instance count, GPU utilization heatmap, cost burn rate ($/hour), idle instance waste ($ wasted on <10% utilization), instance reliability (uptime vs preemptions), and cost per useful GPU-hour. Compare spot vs on-demand costs for budget optimization.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Instance preempted | Spot instance reclaimed | Use on-demand for critical jobs, checkpoint training |
| GPU utilization 0% | Job crashed or data loading bottleneck | Check job logs, verify data pipeline |
| SSH timeout | Instance network issue | Try reconnecting, check Vast.ai status page |
| Unexpected high cost | Instance left running after job | Implement auto-destroy on job completion |

## Examples

**Basic usage**: Apply vastai observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize vastai observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack