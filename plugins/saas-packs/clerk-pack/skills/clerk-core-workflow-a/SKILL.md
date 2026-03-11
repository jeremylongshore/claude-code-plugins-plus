---
name: clerk-core-workflow-a
description: |
  Implement user sign-up and sign-in flows with Clerk.
  Use when building authentication UI, customizing sign-in experience,
  or implementing OAuth social login.
  Trigger with phrases like "clerk sign-in", "clerk sign-up",
  "clerk login flow", "clerk OAuth", "clerk social login".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Core Workflow A: Sign-Up & Sign-In

## Overview
Implement comprehensive user authentication flows including email, OAuth, and custom UI.

## Prerequisites
- Clerk SDK installed and configured
- OAuth providers configured in Clerk dashboard (if using social login)
- Sign-in/sign-up URLs configured in environment

## Instructions
1. Step 1: Pre-built Components (Quick Start)
2. Step 2: Custom Sign-In Form
3. Step 3: OAuth Social Login
4. Step 4: Email Verification Flow

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working sign-in/sign-up pages
- OAuth social login configured
- Email verification flow
- Custom authentication UI

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| form_identifier_not_found | Email not registered | Show sign-up prompt |
| form_password_incorrect | Wrong password | Show error, offer reset |
| session_exists | Already signed in | Redirect to dashboard |
| verification_failed | Wrong code | Allow retry, resend code |

## Resources
- [Sign-In Component](https://clerk.com/docs/components/authentication/sign-in)
- [Custom Flows](https://clerk.com/docs/custom-flows/overview)
- [OAuth Configuration](https://clerk.com/docs/authentication/social-connections/overview)

## Next Steps
Proceed to `clerk-core-workflow-b` for session management and middleware.

## Examples

**Basic usage**: Apply clerk core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk core workflow a for production environments with multiple constraints and team-specific requirements.