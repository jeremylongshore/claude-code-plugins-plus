---
name: notion-install-auth
description: |
  Install and configure the Notion API SDK with authentication.
  Use when setting up a new Notion integration, configuring API tokens,
  or initializing @notionhq/client in your project.
  Trigger with phrases like "install notion", "setup notion",
  "notion auth", "configure notion API", "notion integration setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Install & Auth

## Overview
Install the official Notion SDK (`@notionhq/client`) and configure authentication for internal or public integrations.

## Prerequisites
- Node.js 18+ or Python 3.8+
- A Notion account (free or paid)
- Access to [Notion Integrations](https://www.notion.so/my-integrations) dashboard

## Instructions

### Step 1: Create an Internal Integration
1. Go to https://www.notion.so/my-integrations
2. Click **New integration**
3. Name it, select the workspace, and choose capabilities (Read content, Update content, Insert content)
4. Copy the **Internal Integration Secret** (starts with `ntn_` or `secret_`)

### Step 2: Install the SDK
```bash
# Node.js (official SDK)
npm install @notionhq/client

# Python (official SDK)
pip install notion-client
```

### Step 3: Configure Authentication
```bash
# Set environment variable
export NOTION_TOKEN="ntn_your_integration_secret_here"

# Or create .env file
echo 'NOTION_TOKEN=ntn_your_integration_secret_here' >> .env
```

### Step 4: Share Pages with Your Integration
In Notion, open the page or database you want to access. Click the `...` menu, select **Connections**, and add your integration. Without this step, all API calls return 404.

### Step 5: Verify Connection
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function verifyConnection() {
  try {
    // List all users in the workspace (requires user capabilities)
    const response = await notion.users.list({});
    console.log('Connected! Found', response.results.length, 'users');
    console.log('Bot user:', response.results.find(u => u.type === 'bot')?.name);
  } catch (error) {
    if (error.code === 'unauthorized') {
      console.error('Invalid token. Check NOTION_TOKEN.');
    } else {
      console.error('Connection failed:', error.message);
    }
  }
}

verifyConnection();
```

## OAuth for Public Integrations

Public integrations use OAuth 2.0 to get access tokens for other workspaces:

```typescript
import { Client } from '@notionhq/client';

// Step 1: Redirect user to Notion authorization
const authUrl = `https://api.notion.com/v1/oauth/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${REDIRECT_URI}`;

// Step 2: Exchange code for access token
async function exchangeCodeForToken(code: string) {
  const response = await fetch('https://api.notion.com/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64')}`,
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: REDIRECT_URI,
    }),
  });

  const data = await response.json();
  // data.access_token — use this for API calls
  // data.workspace_id — the workspace that authorized
  // data.bot_id — primary key for storing tokens
  return data;
}

// Step 3: Use the token
const notion = new Client({ auth: data.access_token });
```

## Output
- Installed `@notionhq/client` (Node.js) or `notion-client` (Python)
- Environment variable `NOTION_TOKEN` configured
- Integration connected to target pages/databases
- Verified API connectivity

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `unauthorized` | Invalid or expired token | Regenerate at notion.so/my-integrations |
| `object_not_found` | Page not shared with integration | Add integration via Connections menu |
| `restricted_resource` | Missing capabilities | Edit integration capabilities in dashboard |
| `MODULE_NOT_FOUND` | SDK not installed | Run `npm install @notionhq/client` |

## Examples

### Python Setup
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Verify connection
users = notion.users.list()
print(f"Connected! {len(users['results'])} users found")
```

### Client with Custom Retry Config
```typescript
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  timeoutMs: 60_000,
  notionVersion: '2022-06-28',
});
```

## Resources
- [Notion API Authorization](https://developers.notion.com/docs/authorization)
- [Create an Integration](https://developers.notion.com/docs/create-a-notion-integration)
- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client)
- [Notion API Introduction](https://developers.notion.com/reference/intro)

## Next Steps
After successful auth, proceed to `notion-hello-world` for your first API call.
