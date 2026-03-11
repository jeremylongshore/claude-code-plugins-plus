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
1. Step 1: Define Application Roles
2. Step 2: Permission Guard Implementation
3. Step 3: Secure Linear Client Factory
4. Step 4: SSO Integration
5. Step 5: Audit Logging
6. Step 6: API Middleware

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

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Linear implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply linear enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear enterprise rbac for production environments with multiple constraints and team-specific requirements.