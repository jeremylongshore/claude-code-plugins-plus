---
name: juicebox-enterprise-rbac
description: |
  Configure Juicebox enterprise role-based access control.
  Use when implementing team permissions, configuring access policies,
  or setting up enterprise security controls.
  Trigger with phrases like "juicebox RBAC", "juicebox permissions",
  "juicebox access control", "juicebox enterprise security".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Enterprise RBAC

## Overview
Implement enterprise-grade role-based access control for Juicebox integrations.

## Prerequisites
- Enterprise Juicebox plan
- Identity provider (Okta, Auth0, Azure AD)
- Understanding of access control patterns

## Instructions
- Step 1: Define Roles and Permissions
- Step 2: Implement Permission Checker
- Step 3: Authorization Middleware
- Step 4: Team-Based Access Control
- Step 5: Audit Trail

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Role and permission definitions
- Permission checker implementation
- Authorization middleware
- Team access control
- Audit logging

## Resources
- [Enterprise Security Guide](https://juicebox.ai/docs/enterprise/security)
- [SSO Configuration](https://juicebox.ai/docs/sso)

## Next Steps
After RBAC setup, see `juicebox-migration-deep-dive` for advanced migrations.
