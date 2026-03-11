---
name: gamma-enterprise-rbac
description: |
  Implement enterprise role-based access control for Gamma integrations.
  Use when configuring team permissions, multi-tenant access,
  or enterprise authorization patterns.
  Trigger with phrases like "gamma RBAC", "gamma permissions",
  "gamma access control", "gamma enterprise", "gamma roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement enterprise-grade role-based access control for Gamma integrations with hierarchical roles, multi-tenant isolation, and audit logging.

## Prerequisites
- Enterprise Gamma subscription
- Identity provider (IdP) integration
- Database for permission storage
- Understanding of RBAC concepts

## Instructions

### Step 1: Define Role Hierarchy
Create a role hierarchy (Viewer < Editor < Team Lead < Workspace Admin < Org Admin) with permission inheritance.

### Step 2: Implement Permission Resolution
Build a service that resolves inherited permissions by walking the role hierarchy and caching the computed permission sets.

### Step 3: Create Authorization Middleware
Wrap API routes with middleware that checks required permissions against the user's resolved role.

### Step 4: Add Resource-Level Authorization
Implement resource-specific policies (e.g., owner can edit own, team lead can edit team presentations).

### Step 5: Configure Multi-Tenant Isolation
Add tenant middleware that verifies workspace membership before allowing any workspace-scoped operations.

### Step 6: Enable Audit Logging
Log all authorization decisions (granted and denied) with metrics for denied access alerts.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Role hierarchy with inherited permissions
- Authorization middleware for API routes
- Resource-level access policies
- Multi-tenant workspace isolation
- Authorization audit trail

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Insufficient role | Verify role assignment in database |
| Orphaned memberships | User deleted | Clean up with cascading deletes |
| Privilege escalation | Missing inheritance check | Validate role hierarchy on assignment |

## Examples

### Permission Matrix
| Permission | Viewer | Editor | Team Lead | Workspace Admin | Org Admin |
|------------|--------|--------|-----------|-----------------|-----------|
| View presentations | Yes | Yes | Yes | Yes | Yes |
| Create presentations | No | Yes | Yes | Yes | Yes |
| Edit team presentations | No | No | Yes | Yes | Yes |
| Manage workspace | No | No | No | Yes | Yes |
| Manage billing | No | No | No | No | Yes |

## Resources
- [Gamma Enterprise Features](https://gamma.app/enterprise)
- [RBAC Best Practices](https://csrc.nist.gov/projects/role-based-access-control)
