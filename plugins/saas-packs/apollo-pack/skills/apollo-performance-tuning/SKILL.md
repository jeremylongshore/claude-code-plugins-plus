---
name: apollo-performance-tuning
description: |
  Optimize Apollo.io API performance.
  Use when improving API response times, reducing latency,
  or optimizing bulk operations.
  Trigger with phrases like "apollo performance", "optimize apollo",
  "apollo slow", "apollo latency", "speed up apollo".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Performance Tuning

## Overview
Optimize Apollo.io API performance through caching, connection pooling, request optimization, and efficient data handling.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-performance-tuning:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-performance-tuning/references/implementation-guide.md)`

## Output
- Connection pooling configuration
- LRU cache with TTL per endpoint
- Parallel request patterns
- Query optimization techniques
- Performance monitoring setup

## Error Handling
| Issue | Resolution |
|-------|------------|
| High latency | Check network, enable caching |
| Cache misses | Tune TTL, check key generation |
| Rate limits | Reduce concurrency, add delays |
| Memory issues | Limit cache size, stream results |

## Resources
- [Node.js HTTP Agent](https://nodejs.org/api/http.html#class-httpagent)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)

## Next Steps
Proceed to `apollo-cost-tuning` for cost optimization.
