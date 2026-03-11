---
name: customerio-load-scale
description: |
  Implement Customer.io load testing and scaling.
  Use when preparing for high traffic, load testing,
  or scaling integrations for enterprise workloads.
  Trigger with phrases like "customer.io load test", "customer.io scale",
  "customer.io high volume", "customer.io performance test".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Load & Scale

## Overview
Load testing and scaling strategies for high-volume Customer.io integrations including k6 scripts, horizontal scaling, and message queue architectures.

## Prerequisites
- Customer.io integration working
- Load testing tools (k6, Artillery)
- Staging environment with test workspace

## Instructions

### Step 1: Understand Rate Limits and Scaling Targets
Review Customer.io rate limits (100 req/sec per workspace for Track and App APIs) and choose architecture based on volume: direct API for < 1M events/day, queue-based for 1-10M, distributed for > 10M.

### Step 2: Create Load Test Scripts
Build k6 load tests covering identify and track scenarios with ramping rates, error tracking, and latency thresholds.

### Step 3: Configure Horizontal Scaling
Set up Kubernetes deployments with HPA autoscaling based on CPU utilization and queue depth metrics.

### Step 4: Implement Message Queue Architecture
Use Kafka or similar message queue to buffer events between your application and Customer.io workers for reliable processing at scale.

### Step 5: Add Rate Limiting
Use Bottleneck or similar library to stay within Customer.io's 100 req/sec limit with headroom for other services.

### Step 6: Enable Batch Processing
Implement a batch sender that groups operations and processes them with controlled concurrency.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- k6 load test scripts with identify/track scenarios
- Kubernetes deployment with HPA autoscaling
- Kafka-based message queue processor
- Rate limiter with Bottleneck
- Batch processing sender
- Load test execution scripts

## Error Handling
| Issue | Solution |
|-------|----------|
| Rate limited (429) | Reduce concurrency, check limiter config |
| Timeout errors | Increase timeout, check network |
| Queue backlog | Scale workers, increase concurrency |
| Memory pressure | Limit batch and queue sizes |

## Scaling Checklist
- [ ] Rate limits understood
- [ ] Load tests written and baselined
- [ ] Horizontal scaling configured
- [ ] Message queue buffering active
- [ ] Rate limiting implemented
- [ ] Batch processing enabled
- [ ] Monitoring during tests

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Customer.io Rate Limits](https://customer.io/docs/api/track/#section/Limits)

## Next Steps
After load testing, proceed to `customerio-known-pitfalls` for anti-patterns.

## Examples

**Basic usage**: Apply customerio load scale to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio load scale for production environments with multiple constraints and team-specific requirements.