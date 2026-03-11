---
name: clerk-enterprise-rbac
description: |
  Configure enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls.
  Trigger with phrases like "clerk SSO", "clerk RBAC",
  "clerk enterprise", "clerk roles", "clerk permissions", "clerk SAML".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Enterprise RBAC

## Overview
Implement enterprise-grade SSO, role-based access control, and organization management.

## Prerequisites
- Clerk Enterprise tier subscription
- Identity Provider (IdP) with SAML/OIDC support
- Understanding of role-based access patterns
- Organization structure defined

## Instructions
- Step 1: Configure SAML SSO
- Step 2: Define Roles and Permissions
- Step 3: Permission Checking
- Step 4: Protected Routes with RBAC
- Step 5: Organization Management
- Step 6: React Components with RBAC
- Step 7: API Route Protection

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- SAML SSO configured
- Roles and permissions defined
- RBAC enforcement in middleware
- Organization management

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| SSO login fails | Misconfigured IdP | Check attribute mapping |
| Permission denied | Missing role | Review role assignments |
| Org not found | User not in org | Prompt org selection |

## Resources
- [Clerk SSO Guide](https://clerk.com/docs/authentication/saml)
- [Organizations](https://clerk.com/docs/organizations/overview)
- [Roles & Permissions](https://clerk.com/docs/organizations/roles-permissions)

## Next Steps
Proceed to `clerk-migration-deep-dive` for auth provider migration.
