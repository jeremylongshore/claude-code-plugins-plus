---
name: clay-load-scale
description: |
  Implement Clay load testing, auto-scaling, and capacity planning strategies.
  Use when running performance tests, configuring horizontal scaling,
  or planning capacity for Clay integrations.
  Trigger with phrases like "clay load test", "clay scale",
  "clay performance test", "clay capacity", "clay k6", "clay benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Load & Scale

## Overview

Load testing, scaling strategies, and capacity planning for Clay integrations.

## Prerequisites

- k6 load testing tool installed
- Kubernetes cluster with HPA configured
- Prometheus for metrics collection
- Test environment API keys

## Capacity Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Utilization | > 70% | > 85% |
| Memory Usage | > 75% | > 90% |
| Request Queue Depth | > 100 | > 500 |
| Error Rate | > 1% | > 5% |
| P95 Latency | > 1000ms | > 3000ms |

## Instructions

### Step 1: Create Load Test Script

Write a k6 test with ramp-up (2m to 10 VUs), steady state (5m), stress (2m to 50 VUs), and ramp-down stages. Set thresholds: P95 < 500ms, error rate < 1%.

### Step 2: Configure Auto-Scaling

Set up Kubernetes HPA targeting 70% CPU utilization, 2-20 replicas, with custom metric on queue depth.

### Step 3: Implement Connection Pooling

Use `generic-pool` with 5-20 connections and 30s idle timeout to reuse Clay client connections.

### Step 4: Run Load Test and Analyze

```bash
k6 run --env CLAY_API_KEY=${CLAY_API_KEY} clay-load-test.js
```

Record results in the benchmark template: total requests, success rate, P50/P95/P99 latency, max RPS.

For complete k6 scripts, HPA YAML, connection pool code, and capacity estimator, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Load test script created
- HPA configured
- Benchmark results documented
- Capacity recommendations defined

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| k6 timeout | Rate limited | Reduce RPS |
| HPA not scaling | Wrong metrics | Verify metric name |
| Connection refused | Pool exhausted | Increase pool size |
| Inconsistent results | Warm-up needed | Add ramp-up phase |

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Clay Rate Limits](https://docs.clay.com/rate-limits)

## Next Steps

For reliability patterns, see `clay-reliability-patterns`.

## Examples

**Basic usage**: Apply clay load scale to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay load scale for production environments with multiple constraints and team-specific requirements.