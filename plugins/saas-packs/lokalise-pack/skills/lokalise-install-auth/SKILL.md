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
tags: [saas, lokalise, api, authentication]

---
# Lokalise Install & Auth

## Overview
Set up Lokalise SDK/CLI and configure API token authentication for translation management. Covers the Node.js SDK (`@lokalise/node-api` v12+), the CLI (`lokalise2`), and OAuth2 for Lokalise apps.

## Prerequisites
- Node.js 18+ (SDK v9+ is ESM-only)
- Package manager (npm, pnpm, or yarn)
- Lokalise account with project access
- API token from Lokalise profile settings

## Instructions

### Step 1: Install Node.js SDK
```bash
set -euo pipefail
# SDK v9+ is ESM-only — requires "type": "module" in package.json or .mjs files
npm install @lokalise/node-api

# For CommonJS projects that cannot migrate to ESM, pin to v8
npm install @lokalise/node-api@8
```

### Step 2: Install CLI Tool
```bash
set -euo pipefail
# macOS via Homebrew
brew tap lokalise/cli-2
brew install lokalise2

# Linux — download latest release binary
LATEST_CLI=$(curl -s https://api.github.com/repos/lokalise/lokalise-cli-2-go/releases/latest \
  | grep -oP '"tag_name": "\K[^"]+')
curl -sL "https://github.com/lokalise/lokalise-cli-2-go/releases/download/${LATEST_CLI}/lokalise2_linux_x86_64.tar.gz" | tar xz
sudo mv lokalise2 /usr/local/bin/

# Verify installation
lokalise2 --version
```

### Step 3: Generate API Token
1. Log into [Lokalise](https://app.lokalise.com)
2. Click profile avatar > **Profile Settings**
3. Go to **API tokens** tab
4. Click **Generate new token**
5. Choose **Read and write** for full access (or **Read only** for CI download pipelines)
6. Copy the token immediately (shown only once)

### Step 4: Configure Authentication
```bash
# Set environment variable (recommended)
export LOKALISE_API_TOKEN="your-api-token"

# Or create .env file for local development
echo 'LOKALISE_API_TOKEN=your-api-token' >> .env

# CLI configuration — creates ~/.lokalise2/config.yml
lokalise2 --token "$LOKALISE_API_TOKEN" project list
```

### Step 5: Verify Connection
```typescript
import { LokaliseApi } from "@lokalise/node-api";

const lokaliseApi = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
  enableCompression: true, // Gzip responses for faster transfers
});

// Test connection by listing projects
const projects = await lokaliseApi.projects().list({ limit: 10 });
console.log(`Connected! Found ${projects.items.length} projects.`);
for (const p of projects.items) {
  console.log(`  ${p.project_id}: ${p.name}`);
}
```

### Step 6: OAuth2 Authentication (for Lokalise Apps)
```typescript
import { LokaliseApiOAuth } from "@lokalise/node-api";

// Use token obtained via OAuth2 flow
// OAuth scopes: read_projects, write_projects, read_keys, write_keys, etc.
const lokaliseApi = new LokaliseApiOAuth({
  apiKey: oauthAccessToken,
});

// All SDK methods work identically with OAuth tokens
const projects = await lokaliseApi.projects().list({ limit: 10 });
```

OAuth2 is required when building Lokalise marketplace apps that act on behalf of users. Standard API tokens are sufficient for internal integrations.

## Output
- Installed `@lokalise/node-api` package (ESM v9+ or CJS v8)
- `lokalise2` CLI installed and verified
- Environment variable or .env file with API token
- Successful connection verification listing accessible projects

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Generate new token at Profile Settings > API Tokens |
| `403 Forbidden` | Token lacks required scope | Use read-write token, or check OAuth scopes |
| `ERR_REQUIRE_ESM` | Using `require()` with SDK v9+ | Use ESM `import` or downgrade to `@lokalise/node-api@8` |
| `ENOTFOUND api.lokalise.com` | Network blocked | Check firewall allows outbound HTTPS to `api.lokalise.com` |
| `Cannot find module` | SDK not installed | Run `npm install @lokalise/node-api` |

## Examples

### TypeScript ESM Setup
```typescript
// src/lib/lokalise.ts
import { LokaliseApi } from "@lokalise/node-api";

export function createClient(apiKey?: string): LokaliseApi {
  const key = apiKey ?? process.env.LOKALISE_API_TOKEN;
  if (!key) throw new Error("Set LOKALISE_API_TOKEN or pass apiKey");
  return new LokaliseApi({ apiKey: key, enableCompression: true });
}
```

### CLI Configuration File
```yaml
# ~/.lokalise2/config.yml
token: "your-api-token"
project_id: "123456789.abcdef"
```

### Verify Token Permissions (curl)
```bash
set -euo pipefail
# Check which projects the token can access
curl -s -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=5" \
  | jq '.projects[] | {project_id, name}'
```

## Resources
- [Lokalise Developer Hub](https://developers.lokalise.com/)
- [API Authentication](https://developers.lokalise.com/reference/api-authentication)
- [Node SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [CLI v2 Documentation](https://docs.lokalise.com/en/articles/3401683-lokalise-cli-v2)
- [OAuth2 Guide](https://developers.lokalise.com/docs/oauth2)

## Next Steps
After successful auth, proceed to `lokalise-hello-world` for your first API call.
