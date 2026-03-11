---
name: granola-enterprise-rbac
description: |
  Enterprise role-based access control for Granola.
  Use when configuring user roles, setting permissions,
  or implementing access control policies.
  Trigger with phrases like "granola roles", "granola permissions",
  "granola access control", "granola RBAC", "granola admin".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure enterprise role-based access control for Granola meeting notes with SSO integration and compliance auditing.

## Prerequisites
- Granola Business or Enterprise plan
- Organization admin access
- SSO configured (recommended)

## Role Hierarchy
```
Organization Owner -> Organization Admin -> Workspace Admin -> Team Lead -> Member -> Viewer -> Guest
```

## Instructions

### Step 1: Define Roles
Map organizational structure to Granola roles. Org Owner for billing/SSO, Workspace Admin per department, Team Lead for team management, Member for standard users.

### Step 2: Configure SSO Group Mapping
Map SSO groups (Okta/Azure AD) to Granola roles with workspace assignments. Enable JIT provisioning for automatic account creation.

### Step 3: Set Access Policies
- Internal sharing: automatic within teams, admin approval cross-workspace
- External sharing: workspace admin approval, 30-day link expiration
- Public links: disabled for security

### Step 4: Create Custom Roles (Enterprise)
Extend base roles with additional permissions scoped to specific workspaces.

### Step 5: Establish Audit Process
Enable audit logging for role changes and access events. Schedule quarterly access reviews.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete permission matrices, SSO group mapping examples, JIT provisioning config, and user lifecycle procedures.

## Output
- Role hierarchy defined and documented
- SSO group mapping configured
- Access policies enforced
- Audit logging enabled

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| User can't access workspace | Wrong role assignment | Check SSO group mapping |
| External sharing blocked | Policy too restrictive | Review sharing policy settings |
| Guest access expired | Time limit reached | Re-invite or extend expiration |
| Orphaned accounts | Offboarding gap | Run quarterly access review |

## Examples

### Principle of Least Privilege
1. Start all users as Viewer
2. Upgrade to Member when they begin recording
3. Grant Team Lead for management needs
4. Review access quarterly, downgrade unused privileges

## Resources
- [Granola Admin Guide](https://granola.ai/admin)
- [SSO Configuration](https://granola.ai/help/sso)
- [Security Best Practices](https://granola.ai/security)

## Next Steps
Proceed to `granola-migration-deep-dive` for migration from other tools.
