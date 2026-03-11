---
name: documenso-enterprise-rbac
description: |
  Configure Documenso enterprise role-based access control and team management.
  Use when implementing team permissions, configuring organizational roles,
  or setting up enterprise access controls.
  Trigger with phrases like "documenso RBAC", "documenso teams",
  "documenso permissions", "documenso enterprise", "documenso roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Enterprise RBAC

## Overview
Configure enterprise-grade role-based access control for Documenso integrations with team management and permission hierarchies.

## Prerequisites
- Documenso Teams or Enterprise plan
- Understanding of RBAC concepts
- Identity provider (optional, for SSO)

## Instructions

### Step 1: Documenso Team Roles
Implement documenso team roles.
### Step 2: Role Implementation
// src/auth/roles.ts
### Step 3: Multi-Tenant Architecture
// src/tenant/context.ts

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Documenso Team Roles
- Role Implementation
- Multi-Tenant Architecture

## Error Handling
| RBAC Issue | Cause | Solution |
|------------|-------|----------|
| 403 Forbidden | Insufficient role | Request role upgrade |
| Cannot delete | Not owner | Check ownership |
| Audit gap | Middleware missing | Add audit middleware |
| Tenant mismatch | Wrong context | Verify tenant ID |

## Resources
- [RBAC Best Practices](https://csrc.nist.gov/publications/detail/sp/800-162/final)
- [Documenso Teams](https://documenso.com/pricing)
- [OWASP Access Control](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)

## Next Steps
For migration strategies, see `documenso-migration-deep-dive`.

## Examples

**Basic usage**: Apply documenso enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso enterprise rbac for production environments with multiple constraints and team-specific requirements.