---
name: vercel-install-auth
description: |
  Install Vercel CLI and configure API token authentication.
  Use when setting up Vercel for the first time, creating access tokens,
  or initializing a project with vercel link.
  Trigger with phrases like "install vercel", "setup vercel",
  "vercel auth", "configure vercel token", "vercel login".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(vercel:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, authentication, cli, setup]

---
# Vercel Install & Auth

## Overview
Install the Vercel CLI, create a scoped access token, and link your local project to a Vercel project. This skill covers both interactive login and headless CI token authentication via the REST API.

## Prerequisites
- Node.js 18+ installed
- npm, pnpm, or yarn available
- A Vercel account (hobby, pro, or enterprise)

## Instructions

### Step 1: Install Vercel CLI
```bash
set -euo pipefail
# Global install (recommended)
npm install -g vercel@latest

# Or project-local
npm install --save-dev vercel@latest

# Verify installation
vercel --version
```

### Step 2: Authenticate — Interactive Login
```bash
# Opens browser for OAuth login, stores token in ~/.config/com.vercel.cli
vercel login

# Or login with a specific email
vercel login your@email.com

# Login with GitHub
vercel login --github

# Login with GitLab
vercel login --gitlab
```

### Step 3: Authenticate — Headless Token (CI/CD)
Create a token in the Vercel dashboard at **Settings > Tokens** or via the API:

```bash
# Use a pre-created token — set as environment variable
export VERCEL_TOKEN="your-access-token-here"

# The CLI reads VERCEL_TOKEN automatically — no login needed
vercel whoami
# Output: your-username

# Scope the token to a specific team
export VERCEL_ORG_ID="team_xxxxxxxxxxxx"
export VERCEL_PROJECT_ID="prj_xxxxxxxxxxxx"
```

### Step 4: Link Local Project
```bash
# Interactive — walks you through project selection
vercel link

# Or link to a specific project by name
vercel link --project my-project-name

# Verify the link — pulls .vercel/project.json
cat .vercel/project.json
# {"orgId":"team_xxx","projectId":"prj_xxx"}
```

### Step 5: Verify Connection via REST API
```bash
# Test token against the REST API directly
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  https://api.vercel.com/v9/projects | jq '.projects[].name'

# List teams
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  https://api.vercel.com/v2/teams | jq '.teams[].name'
```

### Step 6: Pull Environment Variables
```bash
# Pull remote env vars to local .env.development.local
vercel env pull .env.development.local

# Pull for a specific environment
vercel env pull --environment=preview
```

## Token Scopes Reference

| Scope | Access | Use Case |
|-------|--------|----------|
| Full Account | All projects, all teams | Personal dev |
| Team-scoped | One team only | Team CI/CD |
| Project-scoped | One project only | Per-project automation |

Tokens support optional expiration dates. Set short-lived tokens (90 days) for CI and rotate them on a schedule.

## Output
- Vercel CLI installed and on PATH
- Authentication token stored or environment variable set
- Local project linked to Vercel project via `.vercel/project.json`
- Environment variables pulled to local `.env.development.local`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Error: No token found` | Not logged in, no VERCEL_TOKEN | Run `vercel login` or export VERCEL_TOKEN |
| `Error: Invalid token` | Token expired or revoked | Generate new token at vercel.com/account/tokens |
| `EACCES permission denied` | Global install without sudo | Use `npx vercel` or install with `--prefix ~/.npm-global` |
| `Error: Team not found` | Wrong VERCEL_ORG_ID | Check team ID in Vercel dashboard > Settings > General |
| `fetch failed` | Network or proxy issue | Check `HTTPS_PROXY` env var, ensure port 443 outbound |

## `.gitignore` Setup
```gitignore
# Vercel
.vercel/
.env*.local
```

## Resources
- [Vercel CLI Overview](https://vercel.com/docs/cli)
- [Access Tokens](https://vercel.com/docs/rest-api#creating-an-access-token)
- [CLI Project Linking](https://vercel.com/docs/cli/project-linking)
- [Vercel REST API Reference](https://vercel.com/docs/rest-api)

## Next Steps
After successful auth, proceed to `vercel-hello-world` for your first deployment.
