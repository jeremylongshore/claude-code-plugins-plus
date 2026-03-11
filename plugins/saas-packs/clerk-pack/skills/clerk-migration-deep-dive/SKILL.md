---
name: clerk-migration-deep-dive
description: |
  Migrate from other authentication providers to Clerk.
  Use when migrating from Auth0, Firebase, Supabase Auth, NextAuth,
  or custom authentication solutions.
  Trigger with phrases like "migrate to clerk", "clerk migration",
  "switch to clerk", "auth0 to clerk", "firebase auth to clerk".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Migration Deep Dive

## Overview
Comprehensive guide to migrating from other authentication providers to Clerk.

## Prerequisites
- Current auth provider access
- User data export capability
- Clerk account and API keys
- Migration timeline planned

## Instructions
1. Migration Strategy

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- User migration scripts
- Parallel running configuration
- Phased migration plan
- Rollback procedures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Duplicate email | User already exists | Skip or merge |
| Invalid email format | Data quality issue | Clean before import |
| Rate limited | Too fast import | Add delays |
| Password migration | Can't export passwords | Force password reset |

## Resources
- [Clerk Migration Guide](https://clerk.com/docs/deployments/migrate-overview)
- [User Import API](https://clerk.com/docs/users/creating-users)
- [Auth0 Migration](https://clerk.com/docs/deployments/migrate-from-auth0)

## Next Steps
After migration, review `clerk-prod-checklist` for production readiness.

## Examples

**Basic usage**: Apply clerk migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk migration deep dive for production environments with multiple constraints and team-specific requirements.