---
name: linear-install-auth
description: |
  Install and configure Linear SDK/CLI authentication.
  Use when setting up a new Linear integration, configuring API keys,
  or initializing Linear in your project.
  Trigger with phrases like "install linear", "setup linear",
  "linear auth", "configure linear API key", "linear SDK setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Install & Auth

## Overview
Set up Linear SDK and configure authentication credentials for API access.

## Prerequisites
- Node.js 18+ (Linear SDK is TypeScript/JavaScript only)
- Package manager (npm, pnpm, or yarn)
- Linear account with API access
- Personal API key or OAuth app from Linear settings

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# npm
npm install @linear/sdk

# pnpm
pnpm add @linear/sdk

# yarn
yarn add @linear/sdk
```

### Step 2: Generate API Key
1. Go to Linear Settings > API > Personal API keys
2. Click "Create key"
3. Copy the generated key (shown only once)

### Step 3: Configure Authentication
```bash
# Set environment variable
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxx"

# Or create .env file
echo 'LINEAR_API_KEY=lin_api_xxxxxxxxxxxx' >> .env
```

### Step 4: Verify Connection
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });
const me = await client.viewer;
console.log(`Authenticated as: ${me.name} (${me.email})`);
```

## Output
- Installed `@linear/sdk` package in node_modules
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication failed` | Invalid or expired API key | Generate new key in Linear settings |
| `Invalid API key format` | Key doesn't start with `lin_api_` | Verify key format from Linear |
| `Rate limited` | Too many requests | Implement exponential backoff |
| `Module not found` | Installation failed | Run `npm install @linear/sdk` again |
| `Network error` | Firewall blocking | Ensure outbound HTTPS to api.linear.app |

## Examples

### TypeScript Setup
```typescript
import { LinearClient } from "@linear/sdk";

const linearClient = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY,
});

// Verify connection
async function verifyConnection() {
  try {
    const viewer = await linearClient.viewer;
    console.log(`Connected as ${viewer.name}`);
    return true;
  } catch (error) {
    console.error("Linear connection failed:", error);
    return false;
  }
}
```

### OAuth Setup (for user-facing apps)
```typescript
import { LinearClient } from "@linear/sdk";

// OAuth tokens from your OAuth flow
const client = new LinearClient({
  accessToken: userAccessToken,
});
```

## Resources
- [Linear API Documentation](https://developers.linear.app/docs)
- [Linear SDK Reference](https://developers.linear.app/docs/sdk/getting-started)
- [Linear API Settings](https://linear.app/settings/api)

## Next Steps
After successful auth, proceed to `linear-hello-world` for your first API call.