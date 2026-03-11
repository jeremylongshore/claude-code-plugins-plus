---
name: maintainx-migration-deep-dive
description: |
  Execute complete platform migrations to or from MaintainX.
  Use when migrating from legacy CMMS systems, performing major re-platforming,
  or transitioning to MaintainX from spreadsheets or other tools.
  Trigger with phrases like "migrate to maintainx", "maintainx migration",
  "cmms migration", "switch to maintainx", "maintainx data migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Migration Deep Dive

## Overview
Comprehensive guide for migrating to MaintainX from legacy CMMS systems, spreadsheets, or other maintenance management tools.

## Prerequisites
- MaintainX account with API access
- Access to source system data
- Understanding of both systems' data models

## Instructions
Follow these high-level steps to implement maintainx-migration-deep-dive:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-migration-deep-dive/references/implementation-guide.md)`

## Output
- Assessment report
- Data mapping configuration
- Migration results
- Validation report
- Rollback plan

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Import Guide](https://help.getmaintainx.com/)
- [Data Migration Best Practices](https://martinfowler.com/articles/data-migration-patterns.html)

## Next Steps
Congratulations! You have completed the MaintainX skill pack. For additional support, contact MaintainX at support@getmaintainx.com.
