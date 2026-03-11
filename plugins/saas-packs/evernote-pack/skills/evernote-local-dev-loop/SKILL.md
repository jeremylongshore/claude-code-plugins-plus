---
name: evernote-local-dev-loop
description: |
  Set up efficient local development workflow for Evernote integrations.
  Use when configuring dev environment, setting up sandbox testing,
  or optimizing development iteration speed.
  Trigger with phrases like "evernote dev setup", "evernote local development",
  "evernote sandbox", "test evernote locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Evernote Local Dev Loop

## Overview
Configure an efficient local development environment for Evernote API integration with sandbox testing, hot reload, and debugging tools.

## Prerequisites
- Completed `evernote-install-auth` setup
- Node.js 18+ or Python 3.10+
- Evernote sandbox account at https://sandbox.evernote.com

## Instructions

### Step 1: Project Structure

### Step 2: Environment Configuration

### Step 3: Evernote Client Wrapper

### Step 4: ENML Utility Helpers

### Step 5: Express Server with OAuth

### Step 6: Package.json Scripts

### Step 7: Quick Test Script

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Working local development server
- Hot-reload enabled with nodemon
- OAuth flow implemented
- Dev token shortcut for quick testing
- ENML utility functions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `EVERNOTE_DEV_TOKEN not set` | Missing dev token | Get from sandbox.evernote.com/api/DeveloperToken.action |
| `Invalid consumer key` | Wrong sandbox vs prod | Verify EVERNOTE_SANDBOX matches your key type |
| `Session undefined` | Missing express-session | Ensure session middleware is configured |

## Resources
- [Sandbox Environment](https://sandbox.evernote.com)
- [Developer Tokens](https://dev.evernote.com/doc/articles/dev_tokens.php)
- [OAuth Guide](https://dev.evernote.com/doc/articles/authentication.php)

## Next Steps
Proceed to `evernote-sdk-patterns` for advanced SDK usage patterns.
