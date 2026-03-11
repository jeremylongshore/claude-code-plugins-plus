---
name: lokalise-install-auth
description: |
  Install and configure Lokalise SDK/CLI authentication.
  Use when setting up a new Lokalise integration, configuring API tokens,
  or initializing Lokalise in your project.
  Trigger with phrases like "install lokalise", "setup lokalise",
  "lokalise auth", "configure lokalise API token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(lokalise2:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Install & Auth

## Overview
Set up Lokalise SDK/CLI and configure API token authentication for translation management.

## Prerequisites
- Node.js 14+ (v18+ recommended for ESM support)
- Package manager (npm, pnpm, or yarn)
- Lokalise account with project access
- API token from Lokalise profile settings

## Instructions

### Step 1: Install Node.js SDK
```bash
set -euo pipefail
# Node.js SDK (ESM module, v9+)
npm install @lokalise/node-api

# For CommonJS projects, use v8
npm install @lokalise/node-api@8
```

### Step 2: Install CLI Tool (Optional)
```bash
# macOS via Homebrew
brew tap lokalise/cli-2
brew install lokalise2

# Linux/Windows via direct download
# Visit: https://github.com/lokalise/lokalise-cli-2-go/releases

# Verify installation
lokalise2 --version
```

### Step 3: Generate API Token
1. Log into [Lokalise](https://app.lokalise.com)
2. Click profile avatar -> Profile Settings
3. Go to "API tokens" tab
4. Click "Generate new token"
5. Choose "Read and write" for full access
6. Copy the token immediately (shown only once)

### Step 4: Configure Authentication
```bash
# Set environment variable
export LOKALISE_API_TOKEN="your-api-token"

# Or create .env file
echo 'LOKALISE_API_TOKEN=your-api-token' >> .env

# CLI configuration (creates ~/.lokalise2/config.yml)
lokalise2 --token "$LOKALISE_API_TOKEN" project list
```

### Step 5: Verify Connection
```typescript
import { LokaliseApi } from "@lokalise/node-api";

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

// Test connection by listing projects
const projects = await lokaliseApi.projects().list();
console.log(`Connected! Found ${projects.items.length} projects.`);
```

## Output
- Installed `@lokalise/node-api` package
- Optional: `lokalise2` CLI installed
- Environment variable or .env file with API token
- Successful connection verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Generate new token in profile settings |
| `403 Forbidden` | Token lacks required permissions | Use read-write token, not read-only |
| `ERR_REQUIRE_ESM` | Using require() with SDK v9+ | Use ESM imports or downgrade to v8 |
| `ENOTFOUND api.lokalise.com` | Network blocked | Check firewall allows outbound HTTPS |

## Examples

### TypeScript Setup (ESM)
```typescript
import { LokaliseApi } from "@lokalise/node-api";

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

// List all projects
const projects = await lokaliseApi.projects().list();
projects.items.forEach(p => console.log(`${p.project_id}: ${p.name}`));
```

### CommonJS Setup (SDK v8)
```javascript
const { LokaliseApi } = require("@lokalise/node-api");

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN,
});

lokaliseApi.projects().list().then(projects => {
  console.log(`Found ${projects.items.length} projects`);
});
```

### CLI Configuration File
```yaml
# ~/.lokalise2/config.yml
token: "your-api-token"
project_id: "123456789.abcdef"
```

### OAuth2 Authentication (for apps)
```typescript
import { LokaliseApiOAuth } from "@lokalise/node-api";

// Use token obtained via OAuth2 flow
const lokaliseApi = new LokaliseApiOAuth({
  apiKey: oauthAccessToken,
});
```

## Resources
- [Lokalise Developer Hub](https://developers.lokalise.com/)
- [API Authentication](https://developers.lokalise.com/reference/api-authentication)
- [Node SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [CLI v2 Documentation](https://docs.lokalise.com/en/articles/3401683-lokalise-cli-v2)

## Next Steps
After successful auth, proceed to `lokalise-hello-world` for your first API call.