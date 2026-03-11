---
name: "cursor-sso-integration"
description: |
  Configure SSO and enterprise authentication in Cursor. Triggers on "cursor sso",
  "cursor saml", "cursor oauth", "enterprise cursor auth", "cursor okta". Use when working with cursor sso integration functionality. Trigger with phrases like "cursor sso integration", "cursor integration", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Sso Integration

## Overview

This skill guides you through configuring SSO and enterprise authentication in Cursor. It covers SAML 2.0 and OAuth 2.0/OIDC setup for popular identity providers like Okta, Azure AD, and Google Workspace with step-by-step configuration instructions.

## Prerequisites

- Cursor Business or Enterprise subscription
- Admin access to Identity Provider (Okta, Azure AD, etc.)
- Admin access to Cursor organization
- Verified company domain in Cursor
- Understanding of SAML 2.0 or OAuth 2.0/OIDC

## Instructions

1. Verify domain in Cursor Admin
2. Create SAML application in Identity Provider
3. Configure ACS URL and Entity ID
4. Set up attribute mapping (email, name)
5. Download IdP metadata and upload to Cursor
6. Test SSO with admin account
7. Roll out to organization

## Output

- SSO authentication configured
- SAML/OIDC integration active
- User provisioning enabled
- Role mapping configured
- Security policies enforced

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor SSO Documentation](https://cursor.com/docs/sso)
- [SAML 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/)
- [Okta SAML Setup Guide](https://developer.okta.com/docs/guides/saml-application-setup/)
- [Azure AD Enterprise Apps](https://docs.microsoft.com/en-us/azure/active-directory/manage-apps/)