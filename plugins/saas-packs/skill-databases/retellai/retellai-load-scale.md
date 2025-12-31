# retellai-load-scale

> Implement load testing for concurrent calls, auto-scaling, and capacity planning strategies

## Directory Structure

```
retellai-load-scale/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for load testing and scaling |
| examples/example.py | Python | Example load test scripts and capacity analysis tools |

## Summary

**Category:** advanced
**Target Audience:** Performance engineers, SREs, Capacity planners
**Trigger Phrases:** `retell load test`, `retell scale`, `retell concurrent calls`, `retell capacity`, `retell benchmark`

### What This Skill Does

This skill implements load testing and capacity planning for Retell AI deployments. It covers simulating concurrent calls using k6 or Artillery, measuring latency degradation under load, configuring auto-scaling for webhook servers, capacity planning based on expected call volumes, and cost projections at scale.

### Technical Success Criteria

- Load test scripts created for concurrent call simulation
- Benchmark results documented with latency percentiles
- Auto-scaling configured for webhook infrastructure
- Capacity recommendations defined for target call volumes

### Business Success Criteria

- Predictable performance under load
- Cost-efficient capacity planning
- Handle 10x concurrent call surge with <10% latency degradation

## Related Skills

- retellai-webhook-server - Scaling webhook infrastructure
- retellai-observability - Performance monitoring
- retellai-cost-tuning - Cost at scale analysis
