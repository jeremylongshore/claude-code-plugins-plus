---
name: vercel-multi-env-setup
description: |
  Configure Vercel across development, preview, and production environments with scoped secrets.
  Use when setting up per-environment configuration, managing environment-specific variables,
  or implementing environment isolation on Vercel.
  Trigger with phrases like "vercel environments", "vercel staging",
  "vercel dev prod", "vercel environment setup", "vercel env scoping".
allowed-tools: Read, Write, Edit, Bash(vercel:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, deployment, environments, configuration]

---
# Vercel Multi-Env Setup

## Overview
Configure Vercel's three built-in environments (Development, Preview, Production) with scoped environment variables, branch-specific preview URLs, and custom environments for staging. Uses Vercel's native environment system and the REST API for automation.

## Prerequisites
- Vercel project linked and deployed
- Separate database instances per environment (recommended)
- Access to Vercel dashboard or VERCEL_TOKEN for API

## Instructions

### Step 1: Understand Vercel's Environment Model
Vercel provides three built-in environments:

| Environment | Trigger | URL Pattern | Use Case |
|-------------|---------|-------------|----------|
| Production | Push to production branch | `yourdomain.com` | Live traffic |
| Preview | Push to any other branch | `project-git-branch-team.vercel.app` | PR review |
| Development | `vercel dev` locally | `localhost:3000` | Local dev |

### Step 2: Scope Environment Variables
```bash
# Add a variable scoped to Production only
vercel env add DATABASE_URL production
# Enter: postgres://prod-host:5432/myapp

# Add a variable scoped to Preview only
vercel env add DATABASE_URL preview
# Enter: postgres://staging-host:5432/myapp_staging

# Add a variable scoped to Development only
vercel env add DATABASE_URL development
# Enter: postgres://localhost:5432/myapp_dev

# Add a variable available in ALL environments
vercel env add NEXT_PUBLIC_APP_NAME production preview development
# Enter: My App

# List all env vars with their scopes
vercel env ls
```

### Step 3: Via REST API (Automation)
```bash
# Create env vars with specific scoping
curl -X POST "https://api.vercel.com/v9/projects/my-app/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "DATABASE_URL",
    "value": "postgres://prod-host:5432/myapp",
    "type": "encrypted",
    "target": ["production"]
  }'

# Upsert — update if exists, create if not
curl -X POST "https://api.vercel.com/v9/projects/my-app/env?upsert=true" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "DATABASE_URL",
    "value": "postgres://staging-host:5432/myapp_staging",
    "type": "encrypted",
    "target": ["preview"]
  }'

# List all env vars for a project
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v9/projects/my-app/env" \
  | jq '.envs[] | {key, target, type}'
```

### Step 4: Custom Environments (Beyond Dev/Preview/Prod)
Vercel supports custom environments for staging, QA, etc.:

```bash
# Create a custom environment via API
curl -X POST "https://api.vercel.com/v1/projects/my-app/custom-environments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Staging",
    "slug": "staging",
    "branchPattern": "staging"
  }'
```

Or in the dashboard: **Settings > Environments > Create Environment**

Custom environments let you:
- Link a specific Git branch to the environment
- Scope environment variables to it
- Assign a custom domain (e.g., `staging.yourdomain.com`)

### Step 5: Branch-Specific Preview Domains
```bash
# Assign a custom domain to a specific branch
# In dashboard: Settings > Domains > Add
# Set Git Branch: "staging"
# Domain: staging.yourdomain.com

# Via API — add domain to project with branch targeting
curl -X POST "https://api.vercel.com/v9/projects/my-app/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "staging.yourdomain.com",
    "gitBranch": "staging"
  }'
```

### Step 6: Environment Detection in Code
```typescript
// src/lib/env.ts — detect environment at runtime
export function getEnvironment(): 'production' | 'preview' | 'development' {
  return (process.env.VERCEL_ENV as any) ?? 'development';
}

// Environment-specific behavior
export function getApiBaseUrl(): string {
  switch (getEnvironment()) {
    case 'production':
      return 'https://api.yourdomain.com';
    case 'preview':
      return `https://${process.env.VERCEL_URL}`;
    case 'development':
      return 'http://localhost:3000';
  }
}

// Production safeguards
export function assertNotProduction(operation: string): void {
  if (getEnvironment() === 'production') {
    throw new Error(`Dangerous operation "${operation}" blocked in production`);
  }
}
```

### Step 7: Pull Env Vars for Local Development
```bash
# Pull Development-scoped vars to local file
vercel env pull .env.development.local

# Pull Preview-scoped vars (for testing preview behavior locally)
vercel env pull --environment=preview .env.preview.local

# .gitignore these files
echo '.env*.local' >> .gitignore
```

## Environment Variable Types

| Type | Dashboard Visibility | Log Visibility | Use Case |
|------|---------------------|---------------|----------|
| `plain` | Visible | Visible | Non-sensitive config |
| `encrypted` | Hidden after save | Hidden | API keys, secrets |
| `sensitive` | Always hidden | Hidden | High-security secrets |
| `system` | Auto-set by Vercel | Visible | `VERCEL_ENV`, `VERCEL_URL` |

## Output
- Environment variables scoped per environment (dev/preview/prod)
- Custom staging environment with dedicated branch and domain
- Environment detection logic for runtime behavior switching
- Local development env vars pulled from Vercel

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Env var undefined in preview | Not scoped to Preview target | Re-add with Preview in target array |
| Wrong database in production | Preview DB URL used in prod | Check env var scoping per environment |
| `vercel env pull` empty | No Development-scoped vars | Add vars with Development target |
| Custom env not triggering | Branch pattern doesn't match | Check branch name matches environment slug |
| Sensitive var can't be read | type=sensitive hides value | Re-add the var if value is lost |

## Resources
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Environments](https://vercel.com/docs/deployments/environments)
- [System Environment Variables](https://vercel.com/docs/environment-variables/system-environment-variables)
- [Managing Environment Variables](https://vercel.com/docs/environment-variables/managing-environment-variables)
- [REST API: Environment Variables](https://vercel.com/docs/rest-api/sdk/examples/environment-variables)

## Next Steps
For observability and monitoring, see `vercel-observability`.
