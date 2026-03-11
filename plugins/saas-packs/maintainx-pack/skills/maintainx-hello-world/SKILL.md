---
name: maintainx-hello-world
description: |
  Create a minimal working MaintainX example - your first work order.
  Use when starting a new MaintainX integration, testing your setup,
  or learning basic MaintainX API patterns.
  Trigger with phrases like "maintainx hello world", "maintainx example",
  "maintainx quick start", "create first work order", "simple maintainx code".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Hello World

## Overview
Create your first work order using the MaintainX REST API - the core building block of CMMS operations.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions
Follow these high-level steps to implement maintainx-hello-world:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-hello-world/references/implementation-guide.md)`

## Output
- Working code file with MaintainX client usage
- Successfully created work order in your MaintainX account
- Console output showing:

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing required fields | Include at least `title` field |
| 401 Unauthorized | Invalid API key | Check `MAINTAINX_API_KEY` environment variable |
| 403 Forbidden | Plan limitations | Verify API access on your subscription |
| 422 Unprocessable | Invalid field values | Check enum values (priority, status) |

## Resources
- [MaintainX Work Orders Guide](https://help.getmaintainx.com/about-work-orders)
- [MaintainX API Reference](https://maintainx.dev/)
- [Work Order Settings](https://help.getmaintainx.com/work-order-settings)

## Next Steps
Proceed to `maintainx-local-dev-loop` for development workflow setup.
