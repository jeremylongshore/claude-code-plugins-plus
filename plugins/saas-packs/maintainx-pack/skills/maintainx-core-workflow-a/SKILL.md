---
name: maintainx-core-workflow-a
description: |
  Execute MaintainX primary workflow: Work Order lifecycle management.
  Use when creating, updating, and managing work orders through their full lifecycle,
  from creation to completion with all status transitions.
  Trigger with phrases like "maintainx work order", "create work order",
  "work order lifecycle", "maintenance task", "manage work orders".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Core Workflow A: Work Order Lifecycle

## Overview
Master the complete work order lifecycle in MaintainX - from creation through completion. Work orders are the core unit of maintenance operations.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Understanding of maintenance operations
- MaintainX account with work order permissions

## Instructions
Follow these high-level steps to implement maintainx-core-workflow-a:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-core-workflow-a/references/implementation-guide.md)`

## Output
- Created work orders with full metadata
- Proper status transitions
- Completion documentation
- Query results for work orders

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing title | Ensure title field is provided |
| 404 Not Found | Invalid asset/location ID | Verify IDs exist in system |
| 403 Forbidden | Insufficient permissions | Check user role and plan tier |
| Invalid transition | Wrong status flow | Follow valid transition paths |

## Resources
- [MaintainX Work Orders Guide](https://help.getmaintainx.com/about-work-orders)
- [Complete a Work Order](https://help.getmaintainx.com/complete-a-work-order)
- [Work Order Settings](https://help.getmaintainx.com/work-order-settings)

## Next Steps
For asset and location management, see `maintainx-core-workflow-b`.
