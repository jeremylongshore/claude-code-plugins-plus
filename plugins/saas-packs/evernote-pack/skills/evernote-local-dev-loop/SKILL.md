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
Configure an efficient local development environment for Evernote API integration with sandbox testing, hot reload, ENML helpers, and a local Express server for OAuth testing.

## Prerequisites
- Completed `evernote-install-auth` setup
- Node.js 18+ or Python 3.10+
- Evernote sandbox account at https://sandbox.evernote.com

## Instructions

### Step 1: Project Structure

Organize your project with clear separation of concerns:

```
evernote-app/
  src/
    services/       # NoteService, SearchService, etc.
    utils/          # ENML helpers, query builder
    middleware/     # Auth, rate limiting
  test/             # Unit and integration tests
  scripts/          # Dev utilities (test-connection, seed-data)
  .env.development  # Sandbox credentials
  .env.production   # Production credentials (gitignored)
```

### Step 2: Environment Configuration

Create `.env.development` with sandbox credentials. Use a Developer Token for quick iteration (skip OAuth during development). Add `.env*` to `.gitignore`.

```bash
# .env.development
EVERNOTE_CONSUMER_KEY=your-sandbox-key
EVERNOTE_CONSUMER_SECRET=your-sandbox-secret
EVERNOTE_DEV_TOKEN=your-developer-token
EVERNOTE_SANDBOX=true
NODE_ENV=development
PORT=3000
```

### Step 3: Evernote Client Wrapper

Create a client factory that switches between Developer Token (for scripts and tests) and OAuth (for the web app) based on environment configuration.

```javascript
function createClient() {
  if (process.env.EVERNOTE_DEV_TOKEN) {
    return new Evernote.Client({
      token: process.env.EVERNOTE_DEV_TOKEN,
      sandbox: true
    });
  }
  return new Evernote.Client({
    consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
    consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
    sandbox: process.env.EVERNOTE_SANDBOX === 'true'
  });
}
```

### Step 4: ENML Utility Helpers

Build helper functions: `wrapInENML(html)`, `textToENML(text)`, `htmlToENML(html)` (strip forbidden elements), and `validateENML(content)`. These prevent `BAD_DATA_FORMAT` errors during development.

### Step 5: Express Server with OAuth

Set up a local Express server with session management for OAuth flow testing. Include routes for `/auth/start` (get request token), `/auth/callback` (exchange for access token), and `/dashboard` (authenticated operations).

### Step 6: Quick Test Script

Create a `scripts/test-connection.js` that verifies SDK setup by calling `userStore.getUser()` and `noteStore.listNotebooks()`. Run with `node scripts/test-connection.js`.

For the full project setup, Express server, ENML utilities, and test scripts, see [Implementation Guide](references/implementation-guide.md).

## Output
- Project structure with services, utils, and middleware directories
- Environment configuration for sandbox and production
- Client factory with Developer Token and OAuth support
- ENML utility library (wrap, convert, validate)
- Express server with OAuth flow for local testing
- Connection test script for quick verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `EVERNOTE_DEV_TOKEN not set` | Missing dev token | Get from `sandbox.evernote.com/api/DeveloperToken.action` |
| `Invalid consumer key` | Wrong sandbox vs production key | Verify `EVERNOTE_SANDBOX` matches your key type |
| `Session undefined` | Missing express-session middleware | Install and configure `express-session` |
| Port already in use | Another process on port 3000 | Change `PORT` in `.env` or kill the process |

## Resources
- [Sandbox Environment](https://sandbox.evernote.com)
- [Developer Tokens](https://dev.evernote.com/doc/articles/dev_tokens.php)
- [OAuth Guide](https://dev.evernote.com/doc/articles/authentication.php)

## Next Steps
Proceed to `evernote-sdk-patterns` for advanced SDK usage patterns.

## Examples

**Quick sandbox test**: Set `EVERNOTE_DEV_TOKEN`, run `node scripts/test-connection.js` to verify authentication, then create a test note using the Developer Token shortcut.

**Full OAuth loop**: Start the Express server, navigate to `http://localhost:3000/auth/start`, complete the Evernote authorization, and verify the access token is stored in the session.
