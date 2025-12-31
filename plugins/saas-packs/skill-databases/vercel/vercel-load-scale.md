# vercel-load-scale

## Skill Scaffold

```
vercel-load-scale/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement load testing with k6, auto-scaling with Kubernetes HPA, and capacity planning strategies.
**Workflow:** Used before major releases and periodically to validate capacity headroom.
**Relates to:** Follows vercel-advanced-troubleshooting; leads to vercel-reliability-patterns

## Summary

This skill covers performance testing and scaling for Vercel integrations. It includes k6 load test scripts with staged ramp-up patterns and thresholds, Kubernetes HPA configuration with CPU and custom metrics, connection pooling with generic-pool, capacity metrics to monitor (CPU, memory, queue depth, error rate, latency), capacity estimation functions, and benchmark result templates. The goal is handling 10x traffic surge with minimal latency degradation.
