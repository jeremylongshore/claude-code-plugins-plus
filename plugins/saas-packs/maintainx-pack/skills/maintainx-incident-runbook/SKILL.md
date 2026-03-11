---
name: maintainx-incident-runbook
description: |
  Incident response procedures for MaintainX integration failures.
  Use when experiencing outages, investigating issues,
  or responding to MaintainX integration incidents.
  Trigger with phrases like "maintainx incident", "maintainx outage",
  "maintainx down", "maintainx emergency", "maintainx runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Incident Runbook

## Overview
Step-by-step procedures for responding to MaintainX integration incidents, from detection through resolution.

## Prerequisites
- Access to monitoring dashboards
- MaintainX admin credentials
- On-call contact information

## Instructions
Follow these high-level steps to implement maintainx-incident-runbook:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-incident-runbook/references/implementation-guide.md)`

## Output
- Incident diagnosed
- Mitigation applied
- Root cause identified
- Resolution documented

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX Status Page](https://status.getmaintainx.com)
- [MaintainX Support](https://help.getmaintainx.com)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps
For data handling patterns, see `maintainx-data-handling`.
