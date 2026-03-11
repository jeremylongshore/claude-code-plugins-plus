---
name: linear-enterprise-rbac
description: |
  Implement enterprise role-based access control with Linear.
  Use when setting up team permissions, implementing SSO,
  or managing access control for Linear integrations.
  Trigger with phrases like "linear RBAC", "linear permissions",
  "linear enterprise access", "linear SSO", "linear role management".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Enterprise RBAC

## Overview
Implement enterprise-grade role-based access control for Linear integrations.

## Prerequisites
- Linear organization admin access
- Understanding of Linear's permission model
- SSO provider (Okta, Azure AD, Google Workspace)

## Instructions
- Step 1: Define Application Roles
- Step 2: Permission Guard Implementation
- Step 3: Secure Linear Client Factory
- Step 4: SSO Integration
- Step 5: Audit Logging
- Step 6: API Middleware

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ForbiddenError` | Permission denied | Check user role and team access |
| `Invalid SSO token` | Token expired | Re-authenticate user |
| `Role not found` | Unknown role | Map to default role |

## Resources
- [Linear OAuth Documentation](https://developers.linear.app/docs/oauth)
- [RBAC Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [SSO Integration Guide](https://linear.app/docs/sso)

## Next Steps
Complete your Linear knowledge with `linear-migration-deep-dive`.
