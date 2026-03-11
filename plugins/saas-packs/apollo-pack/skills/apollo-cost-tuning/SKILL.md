---
name: apollo-cost-tuning
description: |
  Optimize Apollo.io costs and credit usage.
  Use when managing Apollo credits, reducing API costs,
  or optimizing subscription usage.
  Trigger with phrases like "apollo cost", "apollo credits",
  "apollo billing", "reduce apollo costs", "apollo usage".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Cost Tuning

## Overview
Optimize Apollo.io costs through efficient credit usage, smart caching, deduplication, and usage monitoring.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-cost-tuning:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-cost-tuning/references/implementation-guide.md)`

## Output
- Cost-aware caching strategy
- Deduplication service
- Smart search scoring
- Usage tracking and alerts
- Budget-aware API client

## Error Handling
| Issue | Resolution |
|-------|------------|
| Budget exceeded | Pause operations, alert team |
| High cache misses | Extend TTL, review patterns |
| Duplicate enrichments | Audit dedup logic |
| Unexpected costs | Review usage reports |

## Resources
- [Apollo Pricing](https://www.apollo.io/pricing)
- [Apollo Credit System](https://knowledge.apollo.io/hc/en-us/articles/4415144183053)
- [Usage Dashboard](https://app.apollo.io/settings/billing)

## Next Steps
Proceed to `apollo-reference-architecture` for architecture patterns.

## Examples

**Basic usage**: Apply apollo cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo cost tuning for production environments with multiple constraints and team-specific requirements.