---
name: obsidian-enterprise-rbac
description: |
  Implement team vault access patterns and role-based controls.
  Use when managing shared vaults, implementing access controls,
  or building team collaboration features for Obsidian.
  Trigger with phrases like "obsidian team", "obsidian access control",
  "obsidian enterprise", "shared vault permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Enterprise RBAC

## Overview
Implement role-based access control patterns for team vaults and shared Obsidian environments.

## Prerequisites
- Understanding of RBAC concepts
- Multi-user vault setup
- Backend service for authentication (optional)

## Instructions

### Step 1: Permission System

### Step 2: Protected Operations Wrapper

### Step 3: User Management

### Step 4: Audit Logging

### Step 5: UI Integration

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Role-based permission system
- Folder-level access control
- Protected vault operations
- Audit logging
- User management UI

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Insufficient role | Check role assignment |
| User not found | Auth not configured | Set up user management |
| Folder access blocked | Team not assigned | Add user to team |
| Audit log full | No rotation | Implement log rotation |

## Resources
- [RBAC Concepts](https://en.wikipedia.org/wiki/Role-based_access_control)
- [Obsidian Sync Teams](https://obsidian.md/sync)

## Next Steps
For major migrations, see `obsidian-migration-deep-dive`.
