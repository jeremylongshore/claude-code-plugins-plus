---
name: evernote-install-auth
description: |
  Install and configure Evernote SDK and OAuth authentication.
  Use when setting up a new Evernote integration, configuring API keys,
  or initializing Evernote in your project.
  Trigger with phrases like "install evernote", "setup evernote",
  "evernote auth", "configure evernote API", "evernote oauth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Install & Auth

## Overview

Set up Evernote SDK and configure OAuth 1.0a authentication for accessing the Evernote Cloud API.

## Prerequisites

- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Evernote developer account
- API key from Evernote Developer Portal (requires approval, allow 5 business days)

## Instructions

### Step 1: Request API Key

1. Go to [Evernote Developer Portal](https://dev.evernote.com/)
2. Request an API key via the contact form
3. Wait for manual approval (up to 5 business days)
4. Receive your `consumerKey` and `consumerSecret`

### Step 2: Install SDK

```bash
set -euo pipefail
# Node.js
npm install evernote

# Python
pip install evernote
```

### Step 3: Configure Environment

```bash
# Create .env file
cat << 'EOF' >> .env
EVERNOTE_CONSUMER_KEY=your-consumer-key
EVERNOTE_CONSUMER_SECRET=your-consumer-secret
EVERNOTE_SANDBOX=true
EOF
```

### Step 4: Initialize OAuth Client

```javascript
// Node.js - Initialize client for OAuth flow
const Evernote = require('evernote');

const client = new Evernote.Client({
  consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
  consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
  sandbox: process.env.EVERNOTE_SANDBOX === 'true',
  china: false
});
```

```python
# Python - Initialize client
from evernote.api.client import EvernoteClient

client = EvernoteClient(
    consumer_key='your-consumer-key',
    consumer_secret='your-consumer-secret',
    sandbox=True
)
```

### Step 5: Implement OAuth Flow

```javascript
// Step 5a: Get request token and redirect URL
const callbackUrl = 'http://localhost:3000/oauth/callback';  # 3000: 3 seconds in ms

client.getRequestToken(callbackUrl, (error, oauthToken, oauthTokenSecret) => {
  if (error) {
    console.error('Failed to get request token:', error);
    return;
  }

  // Store tokens in session (required for callback)
  req.session.oauthToken = oauthToken;
  req.session.oauthTokenSecret = oauthTokenSecret;

  // Redirect user to Evernote authorization page
  const authorizeUrl = client.getAuthorizeUrl(oauthToken);
  res.redirect(authorizeUrl);
});
```

```javascript
// Step 5b: Handle OAuth callback
app.get('/oauth/callback', (req, res) => {
  const oauthVerifier = req.query.oauth_verifier;

  client.getAccessToken(
    req.session.oauthToken,
    req.session.oauthTokenSecret,
    oauthVerifier,
    (error, oauthAccessToken, oauthAccessTokenSecret, results) => {
      if (error) {
        console.error('Failed to get access token:', error);
        return res.status(500).send('Authentication failed');  # HTTP 500 Internal Server Error
      }

      // Store access token securely (valid for 1 year by default)
      req.session.accessToken = oauthAccessToken;

      // Token expiration included in results.edam_expires
      console.log('Token expires:', new Date(parseInt(results.edam_expires)));

      res.redirect('/dashboard');
    }
  );
});
```

### Step 6: Verify Connection

```javascript
// Create authenticated client and verify
const authenticatedClient = new Evernote.Client({
  token: req.session.accessToken,
  sandbox: true
});

const userStore = authenticatedClient.getUserStore();
const noteStore = authenticatedClient.getNoteStore();

// Verify connection
userStore.getUser().then(user => {
  console.log('Authenticated as:', user.username);
  console.log('User ID:', user.id);
}).catch(err => {
  console.error('Authentication verification failed:', err);
});
```

## Development Tokens (Sandbox Only)

For development, use a Developer Token instead of full OAuth:

1. Create a sandbox account at https://sandbox.evernote.com
2. Get a Developer Token from https://sandbox.evernote.com/api/DeveloperToken.action
3. Use directly without OAuth flow:

```javascript
const client = new Evernote.Client({
  token: process.env.EVERNOTE_DEV_TOKEN,
  sandbox: true
});

const noteStore = client.getNoteStore();
```

**Note:** Developer tokens are currently unavailable for production. Use OAuth for production applications.

## Output

- Installed SDK package in node_modules or site-packages
- Environment variables configured
- Working OAuth flow implementation
- Successful connection verification

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid consumer key` | Wrong or unapproved key | Verify key from developer portal |
| `OAuth signature mismatch` | Incorrect consumer secret | Check secret matches portal |
| `Token expired` | Access token > 1 year old | Re-authenticate user via OAuth |
| `RATE_LIMIT_REACHED` | Too many API calls | Implement exponential backoff |
| `Permission denied` | Insufficient API key permissions | Request additional permissions |

## Token Expiration

- Default token validity: **1 year**
- Users can reduce to: 1 day, 1 week, or 1 month
- Expiration timestamp in `edam_expires` parameter
- Implement token refresh before expiration

## Resources

- [Evernote Developer Portal](https://dev.evernote.com/)
- [OAuth Documentation](https://dev.evernote.com/doc/articles/authentication.php)
- [API Key Permissions](https://dev.evernote.com/doc/articles/permissions.php)
- [JavaScript SDK](https://github.com/Evernote/evernote-sdk-js)
- [Python SDK](https://github.com/Evernote/evernote-sdk-python)

## Next Steps

After successful auth, proceed to `evernote-hello-world` for your first note creation.

## Examples

**Sandbox quickstart**: Use a Developer Token from `sandbox.evernote.com/api/DeveloperToken.action` to skip OAuth during development. Set `EVERNOTE_DEV_TOKEN` and `sandbox: true`.

**Production OAuth**: Request full API key from the Developer Portal, implement the OAuth 1.0a flow with HTTPS callback, and store the access token securely with its `edam_expires` timestamp for refresh handling.