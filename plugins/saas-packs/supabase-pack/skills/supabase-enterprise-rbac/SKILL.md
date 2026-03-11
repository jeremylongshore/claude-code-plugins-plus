---
name: supabase-enterprise-rbac
description: |
  Configure Supabase enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Supabase.
  Trigger with phrases like "supabase SSO", "supabase RBAC",
  "supabase enterprise", "supabase roles", "supabase permissions", "supabase SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Enterprise Rbac

## Prerequisites
- Supabase Enterprise tier subscription
- Identity Provider (IdP) with SAML/OIDC support
- Understanding of role-based access patterns
- Audit logging infrastructure

## Instructions

### Step 1: Define Roles
Map organizational roles to Supabase permissions.

### Step 2: Configure SSO
Set up SAML or OIDC integration with your IdP.

### Step 3: Implement Middleware
Add permission checks to API endpoints.

### Step 4: Enable Audit Logging
Track all access for compliance.

## Output
- Role definitions implemented
- SSO integration configured
- Permission middleware active
- Audit trail enabled

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Enterprise Guide](https://supabase.com/docs/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)
