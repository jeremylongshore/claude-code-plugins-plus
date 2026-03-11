---
name: linear-core-workflow-a
description: |
  Issue lifecycle management with Linear: create, update, and transition issues.
  Use when implementing issue CRUD operations, state transitions,
  or building issue management features.
  Trigger with phrases like "linear issue workflow", "linear issue lifecycle",
  "create linear issues", "update linear issue", "linear state transition".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Core Workflow A: Issue Lifecycle

## Overview
Master issue lifecycle management: creating, updating, transitioning, and organizing issues.

## Prerequisites
- Linear SDK configured
- Access to target team(s)
- Understanding of Linear's issue model

## Instructions
1. Step 1: Create Issues
2. Step 2: Update Issues
3. Step 3: State Transitions
4. Step 4: Issue Relationships
5. Step 5: Comments and Activity

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Issue creation with all metadata
- Bulk update capabilities
- State transition handling
- Parent/child relationships
- Blocking relationships
- Comments and activity

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Issue not found` | Invalid ID or identifier | Verify issue exists |
| `State not found` | Team workflow mismatch | List states for correct team |
| `Validation error` | Invalid field value | Check field constraints |
| `Circular dependency` | Self-blocking issue | Validate relationships |

## Resources
- [Issue Object Reference](https://developers.linear.app/docs/graphql/schema#issue)
- [Workflow States](https://developers.linear.app/docs/graphql/schema#workflowstate)
- [Issue Relations](https://developers.linear.app/docs/graphql/schema#issuerelation)

## Next Steps
Continue to `linear-core-workflow-b` for project and cycle management.

## Examples

**Basic usage**: Apply linear core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear core workflow a for production environments with multiple constraints and team-specific requirements.