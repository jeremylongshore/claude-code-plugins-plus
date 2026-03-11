---
name: maintainx-upgrade-migration
description: |
  Migrate MaintainX API versions and handle breaking changes.
  Use when upgrading API versions, handling deprecations,
  or migrating between MaintainX API releases.
  Trigger with phrases like "maintainx upgrade", "maintainx api version",
  "maintainx migration", "maintainx breaking changes", "maintainx deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Upgrade & Migration

## Overview
Guide for handling MaintainX API version upgrades, deprecations, and breaking changes in your integrations.

## Prerequisites
- Existing MaintainX integration
- Understanding of current API usage
- Test environment available

## Instructions
Follow these high-level steps to implement maintainx-upgrade-migration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-upgrade-migration/references/implementation-guide.md)`

## Output
- API usage analysis report
- Version compatibility layer
- Feature flag configuration
- Migration tests passing
- Rollback procedure documented

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Changelog](https://maintainx.dev/changelog)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps
For CI/CD integration, see `maintainx-ci-integration`.

## Examples

**Basic usage**: Apply maintainx upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx upgrade migration for production environments with multiple constraints and team-specific requirements.