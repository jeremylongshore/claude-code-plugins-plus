---
name: supabase-load-scale
description: |
  Implement Supabase load testing, auto-scaling, and capacity planning strategies.
  Use when running performance tests, configuring horizontal scaling,
  or planning capacity for Supabase integrations.
  Trigger with phrases like "supabase load test", "supabase scale",
  "supabase performance test", "supabase capacity", "supabase k6", "supabase benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Load Scale

## Prerequisites
- k6 load testing tool installed
- Kubernetes cluster with HPA configured
- Prometheus for metrics collection
- Test environment API keys

## Instructions

### Step 1: Create Load Test Script
Write k6 test script with appropriate thresholds.

### Step 2: Configure Auto-Scaling
Set up HPA with CPU and custom metrics.

### Step 3: Run Load Test
Execute test and collect metrics.

### Step 4: Analyze and Document
Record results in benchmark template.

## Output
- Load test script created
- HPA configured
- Benchmark results documented
- Capacity recommendations defined

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Supabase Rate Limits](https://supabase.com/docs/rate-limits)
