---
name: maintainx-prod-checklist
description: |
  Production deployment checklist for MaintainX integrations.
  Use when preparing to deploy a MaintainX integration to production,
  verifying production readiness, or auditing existing deployments.
  Trigger with phrases like "maintainx production", "deploy maintainx",
  "maintainx go-live", "maintainx production checklist", "maintainx launch".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Production Checklist

## Overview
Comprehensive checklist for deploying MaintainX integrations to production with confidence.

## Prerequisites
- MaintainX integration developed and tested
- Production environment configured
- Deployment pipeline ready

## Instructions
Follow these high-level steps to implement maintainx-prod-checklist:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-prod-checklist/references/implementation-guide.md)`

## Output
- All checklist items verified
- Pre-deployment checks passed
- Post-deployment verification completed
- Production deployment documented

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Status Page](https://status.getmaintainx.com)
- [12 Factor App](https://12factor.net/)

## Next Steps
For API version migrations, see `maintainx-upgrade-migration`.

## Examples

**Basic usage**: Apply maintainx prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx prod checklist for production environments with multiple constraints and team-specific requirements.