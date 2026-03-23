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
tags: [saas, productivity, notion, authentication, sdk, setup]
compatible-with: claude-code, codex, openclaw
---

# Notion Install & Auth

## Overview

Set up the official Notion SDK and configure authentication for internal integrations. The Node.js SDK is `@notionhq/client` (npm) and the Python SDK is `notion-client` (pip). Both wrap the Notion API at `https://api.notion.com/v1` using API version `2022-06-28`.

## Prerequisites

- Node.js 18+ or Python 3.8+
- Package manager (npm, pnpm, yarn, or pip)
- A Notion account (free or paid)
- Access to [My Integrations](https://www.notion.so/my-integrations) dashboard

## Instructions

### Step 1: Create Integration and Install SDK

Create an internal integration at https://www.notion.so/my-integrations:

1. Click **New integration**
2. Name it, select the workspace, and choose capabilities (Read content, Update content, Insert content)
3. Copy the **Internal Integration Secret** (starts with `ntn_` or `secret_`)

Install the SDK:

```bash
# Node.js / TypeScript (official SDK)
npm install @notionhq/client

# Python (official SDK)
pip install notion-client
```

### Step 2: Configure Authentication

Store the token in environment variables -- never hardcode it:

```bash
# Set environment variable
export NOTION_TOKEN="ntn_your_integration_secret_here"

# Or add to .env file (add .env to .gitignore)
echo 'NOTION_TOKEN=ntn_your_integration_secret_here' >> .env
```

**Share pages with your integration:** In Notion, open the page or database you want to access. Click the `...` menu, select **Connections**, and add your integration. Without this step, all API calls return `object_not_found`.

### Step 3: Verify Connection

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

const me = await notion.users.me({});
console.log(`Authenticated as: ${me.name} (${me.type})`);
console.log(`Bot ID: ${me.id}`);
```

If the bot user is returned, authentication is working.

## Output

- SDK package installed (`@notionhq/client` for Node.js, `notion-client` for Python)
- Environment variable `NOTION_TOKEN` configured
- Integration connected to target pages/databases via Connections menu
- Verified API connectivity with `users.me()` call

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `unauthorized` | Invalid or expired token | Regenerate at notion.so/my-integrations |
| `object_not_found` | Page not shared with integration | Open page > `...` > Connections > add integration |
| `restricted_resource` | Missing capabilities | Edit integration capabilities in dashboard |
| `validation_error` | Malformed request body | Check SDK version and parameter types |
| `rate_limited` | Too many requests (3 req/s avg) | Add exponential backoff; SDK retries automatically |
| `MODULE_NOT_FOUND` | SDK not installed | Run `npm install @notionhq/client` |

## Examples

### TypeScript — Full Setup

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  timeoutMs: 60_000,
  notionVersion: '2022-06-28',
});

// Verify connection
const me = await notion.users.me({});
console.log(`Connected as ${me.name}`);

// List all users in the workspace
const users = await notion.users.list({});
console.log(`Workspace has ${users.results.length} users`);
```

### Python — Full Setup

```python
import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Verify connection
me = notion.users.me()
print(f"Connected as {me['name']} ({me['type']})")

# List all users in the workspace
users = notion.users.list()
print(f"Workspace has {len(users['results'])} users")
```

## Resources

- [Notion API Authorization](https://developers.notion.com/docs/authorization)
- [Create an Integration](https://developers.notion.com/docs/create-a-notion-integration)
- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client)
- [notion-client on PyPI](https://pypi.org/project/notion-client/)
- [API Reference](https://developers.notion.com/reference/intro)

## Next Steps

After successful auth, proceed to `notion-hello-world` for your first page query.
