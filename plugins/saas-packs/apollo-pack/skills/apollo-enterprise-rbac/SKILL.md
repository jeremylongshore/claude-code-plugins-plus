---
name: apollo-enterprise-rbac
description: |
  Enterprise role-based access control for Apollo.io.
  Use when implementing team permissions, restricting data access,
  or setting up enterprise security controls.
  Trigger with phrases like "apollo rbac", "apollo permissions",
  "apollo roles", "apollo team access", "apollo enterprise security".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Enterprise RBAC

## Overview
Implement role-based access control for Apollo.io integrations with granular permissions, team isolation, and audit trails.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-enterprise-rbac:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-enterprise-rbac/references/implementation-guide.md)`

## Output
- Role-based permission system
- Team-based access control
- API key scoping
- Permission middleware
- Admin dashboard endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing permissions | Request role upgrade |
| Team access denied | Check team membership |
| API key scope error | Regenerate with correct scope |
| Role conflict | Higher role takes precedence |

## Resources
- [RBAC Best Practices](https://auth0.com/docs/manage-users/access-control/rbac)
- [OWASP Access Control](https://owasp.org/www-community/Access_Control)
- [Apollo Team Permissions](https://knowledge.apollo.io/)

## Next Steps
Proceed to `apollo-migration-deep-dive` for migration strategies.

## Examples

**Basic usage**: Apply apollo enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo enterprise rbac for production environments with multiple constraints and team-specific requirements.