---
name: hex-install-auth
description: |
  Install and configure Hex SDK/CLI authentication.
  Use when setting up a new Hex integration, configuring API keys,
  or initializing Hex in your project.
  Trigger with phrases like "install hex", "setup hex",
  "hex auth", "configure hex API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Install & Auth

## Overview

Configure Hex API authentication using OAuth 2.0 Bearer tokens. The Hex API at `app.hex.tech/api/v1/` lets you programmatically trigger project runs, check status, manage users, and configure connections. Tokens are generated per-user in the Hex workspace settings.

## Prerequisites

- Hex account (Team or Enterprise plan)
- Workspace admin access for API token generation
- At least one published Hex project

## Instructions

### Step 1: Generate API Token

1. Open Hex workspace settings
2. Navigate to **API tokens** section
3. Click **New Token**
4. Set description and expiration
5. Select scopes: "Read projects" and/or "Run projects"

### Step 2: Configure Environment

```bash
# .env (NEVER commit)
HEX_API_TOKEN=hex_token_abc123...
HEX_WORKSPACE_URL=https://app.hex.tech

# .gitignore
.env
.env.local
```

### Step 3: Verify Connection

```typescript
// verify-hex.ts
import 'dotenv/config';

const TOKEN = process.env.HEX_API_TOKEN!;

async function verify() {
  const response = await fetch('https://app.hex.tech/api/v1/projects', {
    headers: { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error(`Hex API ${response.status}`);
  const projects = await response.json();
  console.log(`Connected! Found ${projects.length} projects`);
  return projects;
}

verify().catch(console.error);
```

```bash
# curl verification
curl -s -H "Authorization: Bearer $HEX_API_TOKEN" \
  https://app.hex.tech/api/v1/projects | python3 -m json.tool
```

## Token Scopes

| Scope | Endpoints | Use Case |
|-------|-----------|----------|
| Read projects | ListProjects, GetProjectRuns, GetRunStatus | Monitoring |
| Run projects | RunProject, CancelRun (+ all read) | Orchestration |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Regenerate in workspace settings |
| `403 Forbidden` | Missing scope | Create token with "Run projects" scope |
| `404 Not Found` | Wrong workspace URL | Verify HEX_WORKSPACE_URL |

## Resources

- [Hex API Overview](https://learn.hex.tech/docs/api/api-overview)
- [Hex API Reference](https://learn.hex.tech/docs/api/api-reference)
- [Scheduled Runs](https://learn.hex.tech/docs/share-insights/scheduled-runs)

## Next Steps

After auth, proceed to `hex-hello-world`.
