---
name: clerk-core-workflow-b
description: |
  Implement session management and middleware with Clerk.
  Use when managing user sessions, configuring route protection,
  or implementing token refresh logic.
  Trigger with phrases like "clerk session", "clerk middleware",
  "clerk route protection", "clerk token", "clerk JWT".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Core Workflow B: Session & Middleware

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement session management and route protection with Clerk middleware. Covers Next.js middleware configuration, API route protection, role-based access control, and organization-scoped sessions.

## Prerequisites
- Clerk account with application created
- `@clerk/nextjs` package installed
- Next.js 14+ with App Router
- Understanding of JWT session tokens

## Instructions

### Step 1: Configure Clerk Middleware
Create `middleware.ts` at project root. Define public routes (landing, sign-in, webhooks) and admin routes. Use `clerkMiddleware` with `auth.protect()` for private routes and role-based protection for admin routes.

### Step 2: Protect API Routes
Use `auth()` in route handlers to get `userId`, `orgId`, and `has()` for permission checks. Return 401/403 for unauthorized/insufficient permissions.

### Step 3: Handle Session Claims
Access session data, user profile, and generate JWT tokens for external APIs (Supabase, etc.) using `getToken({ template: 'name' })`.

### Step 4: Add Server Component Auth
Use `auth()` in server components with `redirect('/sign-in')` for unauthenticated users. Check roles/permissions with `has()` for conditional UI rendering.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete middleware config, API route examples, session claims, server component patterns, and role-based navigation.

## Output
- Middleware protecting all non-public routes
- API routes with auth and permission checks
- Server components with role-based rendering
- JWT tokens configured for external services

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Middleware redirect loop | Public route not in matcher | Add route to `isPublicRoute` |
| 401 on API route | Token not forwarded | Ensure fetch includes credentials |
| Missing org context | User not in organization | Check `orgId` before org-scoped ops |
| Session expired | Token TTL exceeded | Configure session lifetime in dashboard |

## Examples

### Quick Permission Check
```typescript
const { has } = await auth();
if (has({ permission: 'org:data:write' })) {
  // User can write data in this organization
}
```

## Resources
- [Clerk Middleware](https://clerk.com/docs/references/nextjs/clerk-middleware)
- [Clerk Auth Helper](https://clerk.com/docs/references/nextjs/auth)
- [Clerk Organizations](https://clerk.com/docs/organizations/overview)
