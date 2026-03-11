---
name: sentry-enterprise-rbac
description: |
  Configure enterprise role-based access control in Sentry.
  Use when setting up team permissions, SSO integration,
  or managing organizational access.
  Trigger with phrases like "sentry rbac", "sentry permissions",
  "sentry team access", "sentry sso setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Enterprise Rbac

## Prerequisites

- Sentry Business or Enterprise plan
- Identity provider configured (for SSO)
- Team structure documented
- Permission requirements defined

## Instructions

1. Create teams via dashboard or API following naming conventions
2. Add members to teams with appropriate roles (admin, contributor, member)
3. Assign projects to teams based on service ownership
4. Configure SSO/SAML with identity provider settings
5. Set up SAML attribute mapping for email and optional team assignment
6. Enable SCIM provisioning for automated user management
7. Create organization API tokens with minimal required scopes
8. Implement access patterns (team-isolated, cross-team visibility, contractor)
9. Enable audit logging and review access regularly
10. Follow token hygiene practices with quarterly rotation

## Output
- Teams created with appropriate members
- Projects assigned to teams
- SSO/SAML configured
- API tokens with scoped permissions

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Team Management](https://docs.sentry.io/product/accounts/membership/)
- [SSO & SAML](https://docs.sentry.io/product/accounts/sso/)
- [SCIM Provisioning](https://docs.sentry.io/product/accounts/sso/scim-provisioning/)

## Overview

Configure enterprise role-based access control in Sentry.