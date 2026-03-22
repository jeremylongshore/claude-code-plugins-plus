---
name: supabase-multi-env-setup
description: |
  Configure Supabase across development, staging, and production with separate projects,
  environment-specific secrets, and safe deployment promotion.
  Use when setting up multi-environment deployments, isolating dev from prod data,
  or configuring per-environment Supabase projects.
  Trigger with phrases like "supabase environments", "supabase staging",
  "supabase dev prod", "supabase environment setup", "supabase multi-project".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(vercel:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, deployment, environments]

---
# Supabase Multi-Environment Setup

## Overview
Configure isolated Supabase environments (dev, staging, production) using separate Supabase projects with consistent schema management, safe migration promotion, and environment-specific configuration.

## Prerequisites
- Separate Supabase projects for each environment (create at supabase.com/dashboard)
- Supabase CLI installed
- Secret management solution (Vercel env vars, GitHub Secrets, etc.)

## Instructions

### Step 1: Project Layout

```
# One Supabase CLI project, multiple linked remotes
my-app/
├── supabase/
│   ├── config.toml              # Local config
│   ├── migrations/              # Shared migrations across all envs
│   ├── seed.sql                 # Dev seed data only
│   └── functions/               # Edge Functions (deployed per env)
├── .env.local                   # Local dev (points to supabase start)
├── .env.staging                 # Staging project credentials
├── .env.production              # Production project credentials (NEVER commit)
```

### Step 2: Environment Configuration

```bash
# .env.local (local development)
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...local-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...local-service-key
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# .env.staging
NEXT_PUBLIC_SUPABASE_URL=https://staging-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...staging-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...staging-service-key
DATABASE_URL=postgres://postgres.staging-ref:pwd@aws-0-region.pooler.supabase.com:6543/postgres

# .env.production
NEXT_PUBLIC_SUPABASE_URL=https://prod-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...prod-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...prod-service-key
DATABASE_URL=postgres://postgres.prod-ref:pwd@aws-0-region.pooler.supabase.com:6543/postgres
```

### Step 3: Environment-Aware Client

```typescript
// lib/config.ts
type Environment = 'local' | 'staging' | 'production'

export function getEnvironment(): Environment {
  if (process.env.NEXT_PUBLIC_SUPABASE_URL?.includes('127.0.0.1')) return 'local'
  if (process.env.NEXT_PUBLIC_SUPABASE_URL?.includes('staging')) return 'staging'
  return 'production'
}

export const config = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  isProduction: getEnvironment() === 'production',
}

// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import { config, getEnvironment } from './config'

export const supabase = createClient(config.supabaseUrl, config.supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
  },
  global: {
    headers: {
      'x-environment': getEnvironment(),
    },
  },
})
```

### Step 4: Migration Promotion Workflow

```bash
# Development: create and test migrations locally
supabase start
supabase migration new add_feature_x
# Edit the migration SQL
supabase db reset  # Test locally

# Staging: push migrations to staging project
supabase link --project-ref <staging-ref>
supabase db push
# Run integration tests against staging

# Production: push same migrations to production
supabase link --project-ref <prod-ref>
supabase db push
# Verify with health check

# Edge Functions: deploy per environment
supabase link --project-ref <staging-ref>
supabase functions deploy --project-ref <staging-ref>

supabase link --project-ref <prod-ref>
supabase functions deploy --project-ref <prod-ref>
```

### Step 5: Production Safeguards

```typescript
// Prevent accidental destructive operations in production
import { getEnvironment } from '../lib/config'

export function requireNonProduction(operation: string) {
  if (getEnvironment() === 'production') {
    throw new Error(`[BLOCKED] ${operation} is not allowed in production`)
  }
}

// Usage in services
async function resetTestData() {
  requireNonProduction('resetTestData')
  await supabase.from('test_data').delete().neq('id', '')
}

// Protect seed data from running in production
// supabase/seed.sql should ONLY run via supabase db reset (local only)
```

### Step 6: CI/CD Per Environment

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - name: Deploy migrations to staging
        run: |
          supabase link --project-ref ${{ secrets.STAGING_PROJECT_REF }}
          supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}

      - name: Deploy Edge Functions to staging
        run: supabase functions deploy --project-ref ${{ secrets.STAGING_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

### Step 7: Generate Types Per Environment

```bash
# Generate types from the linked environment
supabase link --project-ref <staging-ref>
supabase gen types typescript --linked > lib/database.types.ts

# Or from local (recommended for development)
supabase gen types typescript --local > lib/database.types.ts
```

## Output
- Separate Supabase projects for dev, staging, and production
- Environment-specific configuration files
- Migration promotion workflow (local -> staging -> production)
- Production safeguards blocking destructive operations
- CI/CD pipelines per environment
- Type generation from any environment

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Wrong project linked | `supabase link` to wrong ref | Verify with `supabase projects list` |
| Migration drift between envs | Skipped staging | Always promote through staging first |
| Secrets in wrong env | Copy-paste error | Use separate secret names per environment |
| Seed data in production | `db reset` on production | Seed only runs on `db reset`; never reset production |

## Resources
- [Managing Environments](https://supabase.com/docs/guides/deployment/managing-environments)
- [Database Migrations](https://supabase.com/docs/guides/deployment/database-migrations)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For monitoring and observability, see `supabase-observability`.
