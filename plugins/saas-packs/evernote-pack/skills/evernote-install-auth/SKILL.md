---
name: evernote-install-auth
description: 'Install and configure Evernote SDK and OAuth authentication.

  Use when setting up a new Evernote integration, configuring API keys,

  or initializing Evernote in your project.

  Trigger with phrases like "install evernote", "setup evernote",

  "evernote auth", "configure evernote API", "evernote oauth".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- evernote
- api
- authentication
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Evernote Install & Auth

## Overview
Set up the Evernote SDK and configure OAuth 1.0a authentication for accessing the Evernote Cloud API. Covers API key provisioning, SDK installation, OAuth flow implementation, and connection verification.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Evernote developer account
- API key from Evernote developer portal (requires approval, allow 5 business days)

## Instructions

### Step 1: Request an API Key
1. Navigate to the [Evernote developer portal](https://dev.evernote.com/)
2. Submit the API key request form
3. Wait for manual approval (up to 5 business days)
4. Receive `consumerKey` and `consumerSecret` credentials

### Step 2: Install the SDK
```bash
set -euo pipefail
# Node.js
npm install evernote

# Python
pip install evernote
```

### Step 3: Configure Environment Variables
```bash
cat << 'EOF' >> .env
EVERNOTE_CONSUMER_KEY=your-consumer-key
EVERNOTE_CONSUMER_SECRET=your-consumer-secret
EVERNOTE_SANDBOX=true
EOF
```

### Step 4: Initialize the OAuth Client
```javascript
const Evernote = require('evernote');

const client = new Evernote.Client({
  consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
  consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
  sandbox: process.env.EVERNOTE_SANDBOX === 'true',
  china: false
});
```

### Step 5: Implement the OAuth Flow
Set up request token acquisition, user authorization redirect, and callback handling. Alternatively, use a developer token for sandbox testing to skip the OAuth flow entirely.

### Step 6: Verify the Connection
Create an authenticated client, access `getUserStore()`, and call `getUser()` to confirm authentication succeeds.

For the complete OAuth callback implementation, developer token setup, Python client initialization, and token expiration handling, see [OAuth flow reference](references/oauth-flow.md).

## Output
- Installed SDK package in node_modules or site-packages
- Environment variables configured for authentication
- Working OAuth flow implementation
- Successful connection verification

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Invalid consumer key | Wrong or unapproved key | Verify key in the developer portal |
| OAuth signature mismatch | Incorrect consumer secret | Check secret matches the portal value |
| Token expired | Access token older than 1 year | Re-authenticate the user via OAuth |
| Rate limit reached | Too many API calls | Implement exponential backoff |
| Permission denied | Insufficient API key scope | Request additional permissions |

## Examples

**Sandbox quickstart**: Obtain a developer token from `sandbox.evernote.com/api/DeveloperToken.action`. Set `EVERNOTE_DEV_TOKEN` in `.env` and initialize the client with `sandbox: true` to skip the full OAuth flow during development.

**Production OAuth**: Request an API key from the developer portal, implement the OAuth 1.0a flow with an HTTPS callback URL, store the access token securely alongside its `edam_expires` timestamp, and schedule token refresh before expiration.

## Resources
- [Evernote Developer Portal](https://dev.evernote.com/)
- [OAuth Documentation](https://dev.evernote.com/doc/articles/authentication.php)
- [API Key Permissions](https://dev.evernote.com/doc/articles/permissions.php)
- [JavaScript SDK](https://github.com/Evernote/evernote-sdk-js)
- [Python SDK](https://github.com/Evernote/evernote-sdk-python)

## Next Steps
After successful auth, proceed to `evernote-hello-world` for the first note creation.
