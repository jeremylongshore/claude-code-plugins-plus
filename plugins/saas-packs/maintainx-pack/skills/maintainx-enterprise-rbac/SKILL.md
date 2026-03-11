---
name: maintainx-enterprise-rbac
description: |
  Configure enterprise role-based access control for MaintainX integrations.
  Use when implementing SSO, managing organization-level permissions,
  or setting up enterprise access controls with MaintainX.
  Trigger with phrases like "maintainx rbac", "maintainx sso",
  "maintainx enterprise", "maintainx permissions", "maintainx roles".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Enterprise RBAC

## Overview
Configure enterprise-grade role-based access control for MaintainX integrations, including SSO integration, permission management, and audit logging.

## Prerequisites
- MaintainX Enterprise plan
- Identity Provider (IdP) with SAML/OIDC
- Understanding of RBAC concepts

## Instructions
Follow these high-level steps to implement maintainx-enterprise-rbac:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-enterprise-rbac/references/implementation-guide.md)`

## Output
- Role definitions implemented
- SAML SSO integration
- Permission middleware
- Location-based access control
- Audit logging
- Scoped API keys

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX Enterprise](https://www.getmaintainx.com/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OWASP Access Control](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/)

## Next Steps
For complete platform migration, see `maintainx-migration-deep-dive`.

## Examples

**Basic usage**: Apply maintainx enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx enterprise rbac for production environments with multiple constraints and team-specific requirements.