---
name: flyio-install-auth
description: |
  Install flyctl CLI and configure Fly.io authentication with API tokens.
  Use when setting up a new Fly.io project, configuring deploy tokens,
  or initializing the Machines API for edge compute deployments.
  Trigger: "install fly.io", "setup flyctl", "fly.io auth", "fly.io API token".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Install & Auth

## Overview

Install `flyctl` CLI and configure authentication for Fly.io edge compute platform. Two auth methods: **interactive login** (opens browser) and **API tokens** (CI/CD and Machines API). The Machines API base URL is `https://api.machines.dev`.

## Prerequisites

- Fly.io account at [fly.io](https://fly.io)
- macOS, Linux, or WSL2

## Instructions

### Step 1: Install flyctl

```bash
# macOS / Linux
curl -L https://fly.io/install.sh | sh

# Or via Homebrew
brew install flyctl

# Verify
fly version
```

### Step 2: Authenticate

```bash
# Interactive login (opens browser)
fly auth login

# Or with token (CI/CD)
fly auth token  # Get current token
export FLY_API_TOKEN="fo1_your_token_here"

# Verify auth
fly auth whoami
```

### Step 3: Create API Token for Machines API

```bash
# Create deploy token (scoped to an app)
fly tokens create deploy -a my-app

# Create org-level token
fly tokens create org

# Use with Machines API
curl -s -H "Authorization: Bearer $FLY_API_TOKEN" \
  https://api.machines.dev/v1/apps | jq '.[].name'
```

### Step 4: Verify Machines API Access

```typescript
const FLY_API = 'https://api.machines.dev';

async function verifyFlyAccess() {
  const res = await fetch(`${FLY_API}/v1/apps`, {
    headers: { 'Authorization': `Bearer ${process.env.FLY_API_TOKEN}` },
  });
  const apps = await res.json();
  console.log(`Connected. Found ${apps.length} apps.`);
  apps.forEach((app: any) => console.log(`  ${app.name} (${app.organization.slug})`));
}
```

## Token Types

| Token Type | Scope | Lifetime | Use Case |
|------------|-------|----------|----------|
| User token | All orgs/apps | Until revoked | Development, personal |
| Deploy token | Single app | Until revoked | CI/CD per app |
| Org token | All apps in org | Until revoked | Org-wide automation |
| Machines token | API access | Until revoked | Machines API calls |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Error: not authenticated` | No token set | Run `fly auth login` or set `FLY_API_TOKEN` |
| `401 Unauthorized` | Invalid/expired token | Regenerate with `fly tokens create` |
| `Could not find app` | Wrong app name | Check with `fly apps list` |
| `flyctl not found` | CLI not installed | Run install script above |

## Resources

- [Fly.io CLI Reference](https://fly.io/docs/flyctl/)
- [Machines API Docs](https://fly.io/docs/machines/api/)
- [API Tokens](https://fly.io/docs/reference/deploy-tokens/)

## Next Steps

After auth, proceed to `flyio-hello-world` for your first deployment.
