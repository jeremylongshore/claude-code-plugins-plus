---
name: maintainx-core-workflow-b
description: |
  Execute MaintainX secondary workflow: Asset and Location management.
  Use when managing equipment assets, organizing locations/facilities,
  building asset hierarchies, and tracking equipment maintenance history.
  Trigger with phrases like "maintainx asset", "maintainx location",
  "equipment tracking", "asset management", "facility hierarchy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Core Workflow B: Asset & Location Management

## Overview
Manage equipment assets and locations in MaintainX. Assets represent equipment that requires maintenance; locations organize your facilities.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Understanding of asset hierarchy concepts
- MaintainX account with asset management permissions

## Instructions
Follow these high-level steps to implement maintainx-core-workflow-b:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-core-workflow-b/references/implementation-guide.md)`

## Output
- Complete location hierarchy view
- Asset inventory analysis
- Asset maintenance history
- Location-based asset groupings
- Preventive maintenance schedules

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Invalid asset/location ID | Verify ID exists |
| Empty Results | No data or wrong filter | Check query parameters |
| Pagination issues | Missing cursor handling | Use pagination helper |
| Permission denied | Insufficient access | Verify user permissions |

## Resources
- [MaintainX Assets Guide](https://help.getmaintainx.com/)
- [MaintainX Locations](https://help.getmaintainx.com/)
- [API Documentation](https://maintainx.dev/)

## Next Steps
For troubleshooting common issues, see `maintainx-common-errors`.

## Examples

**Basic usage**: Apply maintainx core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx core workflow b for production environments with multiple constraints and team-specific requirements.