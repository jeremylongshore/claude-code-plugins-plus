---
name: maintainx-performance-tuning
description: |
  Optimize MaintainX API integration performance.
  Use when experiencing slow API responses, optimizing data fetching,
  or improving integration throughput with MaintainX.
  Trigger with phrases like "maintainx performance", "maintainx slow",
  "optimize maintainx", "maintainx caching", "maintainx faster".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Performance Tuning

## Overview
Optimize your MaintainX integration for maximum performance with caching, efficient queries, and connection pooling.

## Prerequisites
- MaintainX integration working
- Redis or in-memory cache available
- Performance metrics baseline

## Instructions
Follow these high-level steps to implement maintainx-performance-tuning:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-performance-tuning/references/implementation-guide.md)`

## Output
- Caching layer implemented
- Connection pooling configured
- Efficient pagination patterns
- Request deduplication
- DataLoader for batch loading
- Performance monitoring

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
- [Node.js Performance Best Practices](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)

## Next Steps
For cost optimization, see `maintainx-cost-tuning`.

## Examples

**Basic usage**: Apply maintainx performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx performance tuning for production environments with multiple constraints and team-specific requirements.