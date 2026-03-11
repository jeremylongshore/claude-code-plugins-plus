---
name: clerk-local-dev-loop
description: |
  Set up local development workflow with Clerk.
  Use when configuring development environment, testing auth locally,
  or setting up hot reload with Clerk.
  Trigger with phrases like "clerk local dev", "clerk development",
  "test clerk locally", "clerk dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Local Dev Loop

## Overview
Configure an efficient local development workflow with Clerk authentication.

## Prerequisites
- Clerk SDK installed
- Development and production instances in Clerk dashboard
- Node.js development environment

## Instructions
1. Step 1: Configure Development Instance
2. Step 2: Set Up Test Users
3. Step 3: Configure Hot Reload
4. Step 4: Development Scripts
5. Step 5: Mock Authentication for Tests

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Development environment configured
- Test users available
- Hot reload working with auth
- Mocked auth for testing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Development/Production mismatch | Using prod keys in dev | Use pk_test_/sk_test_ keys locally |
| SSL Required | Clerk needs HTTPS | Use `next dev --experimental-https` |
| Cookies Not Set | Wrong domain config | Check Clerk dashboard domain settings |
| Session Not Persisting | LocalStorage issues | Clear browser storage, check domain |

## Resources
- [Clerk Development Mode](https://clerk.com/docs/deployments/overview)
- [Test Mode](https://clerk.com/docs/testing/overview)
- [CLI Tools](https://clerk.com/docs/references/cli)

## Next Steps
Proceed to `clerk-sdk-patterns` for common SDK usage patterns.

## Examples

**Basic usage**: Apply clerk local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk local dev loop for production environments with multiple constraints and team-specific requirements.