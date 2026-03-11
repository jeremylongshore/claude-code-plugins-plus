---
name: clerk-sdk-patterns
description: |
  Common Clerk SDK patterns and best practices.
  Use when implementing authentication flows, accessing user data,
  or integrating Clerk SDK methods in your application.
  Trigger with phrases like "clerk SDK", "clerk patterns",
  "clerk best practices", "clerk API usage".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk SDK Patterns

## Overview
Learn common patterns and best practices for using the Clerk SDK effectively.

## Prerequisites
- Clerk SDK installed and configured
- Basic understanding of React/Next.js
- ClerkProvider wrapping application

## Instructions
- Pattern 1: Server-Side Authentication
- Pattern 2: Client-Side Hooks
- Pattern 3: Protected Routes with Middleware
- Pattern 4: Organization-Aware Queries
- Pattern 5: Custom JWT Templates

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Server and client authentication patterns
- Protected route middleware
- Organization-aware queries
- Custom JWT tokens for integrations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| auth() returns null | Not in server context | Use in Server Components or API routes |
| useUser() not updating | Component not re-rendering | Check ClerkProvider placement |
| getToken() fails | Template not configured | Configure JWT template in dashboard |
| orgId is null | No organization selected | Prompt user to select organization |

## Resources
- [Clerk SDK Reference](https://clerk.com/docs/references/nextjs/overview)
- [Authentication Patterns](https://clerk.com/docs/references/nextjs/auth)
- [JWT Templates](https://clerk.com/docs/backend-requests/making/jwt-templates)

## Next Steps
Proceed to `clerk-core-workflow-a` for user sign-up and sign-in flows.
