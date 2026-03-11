---
name: maintainx-multi-env-setup
description: |
  Configure multiple MaintainX environments (dev, staging, production).
  Use when setting up environment-specific configurations,
  managing multiple MaintainX accounts, or implementing environment promotion.
  Trigger with phrases like "maintainx environments", "maintainx staging",
  "maintainx dev prod", "maintainx multi-environment", "maintainx config".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Multi-Environment Setup

## Overview
Configure and manage multiple MaintainX environments for development, staging, and production workflows.

## Prerequisites
- Multiple MaintainX accounts or organizations
- Secret management solution
- CI/CD pipeline configured

## Instructions
Follow these high-level steps to implement maintainx-multi-env-setup:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-multi-env-setup/references/implementation-guide.md)`

## Output
- Environment-specific configurations
- Secret management integration
- Client factory for multi-environment
- Promotion tools for config sync
- CI/CD environment matrix

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [12-Factor App Configuration](https://12factor.net/config)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps
For observability setup, see `maintainx-observability`.

## Examples

**Basic usage**: Apply maintainx multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx multi env setup for production environments with multiple constraints and team-specific requirements.