---
name: supabase-multi-env-setup
description: |
  Configure Supabase across development, staging, and production with separate projects,
  environment-specific secrets, and safe migration promotion.
  Use when setting up multi-environment deployments, isolating dev from prod data,
  configuring per-environment Supabase projects, or promoting migrations through environments.
  Trigger: "supabase environments", "supabase staging", "supabase dev prod",
  "supabase multi-project", "supabase env config", "database branching".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Bash(vercel:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, deployment, environments, multi-env, devops]
---

# Supabase Multi-Environment Setup

## Overview

Production Supabase deployments require separate projects per environment — each with its own URL, API keys, database, and RLS policies. This skill configures a three-tier environment architecture (local dev, staging, production) with safe migration promotion via `supabase db push`, environment-aware `createClient` initialization, database branching for preview deployments, and CI/CD pipelines that prevent accidental cross-environment operations.

**When to use:** Setting up a new project with multiple environments, migrating from a single-project setup to multi-env, adding staging to an existing dev/prod split, or configuring preview environments with database branching.

## Prerequisites

- Three separate Supabase projects created at [supabase.com/dashboard](https://supabase.com/dashboard) (dev, staging, production)
- Supabase CLI installed: `npm install -g supabase` or `npx supabase --version`
- `@supabase/supabase-js` v2+ installed in your project
- Node.js 18+ with framework that supports `.env` files (Next.js, Nuxt, SvelteKit, etc.)
- A secret management solution for CI (GitHub Actions Secrets, Vercel env vars, etc.)

## Instructions

### Step 1: Environment Files and Project Layout

Create one Supabase CLI project with shared migrations and per-environment credential files. Each `.env.*` file points to a different Supabase project.

**Project structure:**

```
my-app/
├── supabase/
│   ├── config.toml              # Local CLI config
│   ├── migrations/              # Shared migrations (all envs use the same schema)
│   │   └── 20260101000000_initial.sql
│   ├── seed.sql                 # Dev-only seed data (runs on db reset only)
│   └── functions/               # Edge Functions (deployed per env)
├── .env.local                   # Local dev → supabase start
├── .env.staging                 # Staging project credentials
├── .env.production              # Production project credentials
└── .gitignore                   # Must include .env.staging, .env.production
```

**Environment files:**

```bash
# .env.local — local development (safe defaults from supabase start)
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
SUPABASE_ENV=local

# .env.staging — staging project
NEXT_PUBLIC_SUPABASE_URL=https://<staging-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...staging-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...staging-service-key
DATABASE_URL=postgres://postgres.<staging-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SUPABASE_ENV=staging

# .env.production — production project (NEVER commit this file)
NEXT_PUBLIC_SUPABASE_URL=https://<prod-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...prod-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...prod-service-key
DATABASE_URL=postgres://postgres.<prod-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SUPABASE_ENV=production
```

**Critical `.gitignore` entries:**

```gitignore
.env.staging
.env.production
# .env.local is safe to commit (contains only local dev keys)
```

**Link each environment to the CLI:**

```bash
# Local development
npx supabase start

# Link staging (stores ref in supabase/.temp/project-ref)
npx supabase link --project-ref <staging-ref>

# Link production (re-links, overwriting staging ref)
npx supabase link --project-ref <prod-ref>
```

> **Note:** The CLI can only link one project at a time. Switch between environments by re-running `supabase link` with the target project ref before any `db push` or `functions deploy` operation.

### Step 2: Environment-Aware Client and Safeguards

Build a `createClient` wrapper that selects the correct URL and keys based on the active environment, plus production safeguards that block destructive operations.

**Environment detection (`lib/env.ts`):**

```typescript
export type Environment = 'local' | 'staging' | 'production';

export function getEnvironment(): Environment {
  // Explicit env var takes priority
  const explicit = process.env.SUPABASE_ENV;
  if (explicit === 'local' || explicit === 'staging' || explicit === 'production') {
    return explicit;
  }

  // Fallback: detect from URL
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? '';
  if (url.includes('127.0.0.1') || url.includes('localhost')) return 'local';
  if (url.includes('staging')) return 'staging';
  return 'production';
}

export function isProduction(): boolean {
  return getEnvironment() === 'production';
}

export function requireNonProduction(operation: string): void {
  if (isProduction()) {
    throw new Error(
      `[BLOCKED] "${operation}" is not allowed in production. ` +
      `Current SUPABASE_ENV=${process.env.SUPABASE_ENV}`
    );
  }
}
```

**Supabase client factory (`lib/supabase.ts`):**

```typescript
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { Database } from './database.types';
import { getEnvironment } from './env';

// Browser client (uses anon key, respects RLS)
export function createBrowserClient(): SupabaseClient<Database> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

  return createClient<Database>(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
    },
    global: {
      headers: { 'x-environment': getEnvironment() },
    },
  });
}

// Server client (uses service role key, bypasses RLS)
export function createServerClient(): SupabaseClient<Database> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

  return createClient<Database>(supabaseUrl, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
```

**Production safeguards:**

```typescript
import { requireNonProduction } from './env';
import { createServerClient } from './supabase';

// Seed data — only runs in local/staging
export async function seedTestData(): Promise<void> {
  requireNonProduction('seedTestData');
  const supabase = createServerClient();
  await supabase.from('test_users').insert([
    { email: 'test@example.com', role: 'admin' },
    { email: 'user@example.com', role: 'member' },
  ]);
}

// Destructive reset — only runs in local
export async function resetDatabase(): Promise<void> {
  requireNonProduction('resetDatabase');
  const supabase = createServerClient();
  await supabase.rpc('truncate_all_tables');
}
```

**Environment-specific RLS policies:**

```sql
-- supabase/migrations/20260115000000_env_rls.sql
-- Allow broader access in staging for QA testing
CREATE POLICY "staging_read_all" ON public.profiles
  FOR SELECT
  USING (
    current_setting('app.environment', true) = 'staging'
    OR auth.uid() = id
  );

-- Set environment in each request via the x-environment header
-- or via a Postgres config parameter in your connection string
```

### Step 3: Migration Promotion and Database Branching

Promote migrations through environments (local -> staging -> production) and use database branching for preview deployments.

**Migration promotion workflow:**

```bash
# 1. Create migration locally
npx supabase migration new add_profiles_table
# Edit: supabase/migrations/20260120000000_add_profiles_table.sql

# 2. Test locally with full reset
npx supabase db reset          # Applies all migrations + seed.sql
npx supabase test db           # Run pgTAP tests if configured

# 3. Push to staging
npx supabase link --project-ref <staging-ref>
npx supabase db push           # Applies only new migrations
# Run integration tests against staging URL

# 4. Push to production (after staging verification)
npx supabase link --project-ref <prod-ref>
npx supabase db push           # Same migrations, production database
# Verify with health check endpoint

# 5. Generate types from the canonical source
npx supabase gen types typescript --local > lib/database.types.ts
# Or from linked project:
# npx supabase gen types typescript --linked > lib/database.types.ts
```

**Database branching for preview environments:**

```bash
# Create a branch for a feature (requires Supabase Pro plan)
npx supabase branches create feature-user-profiles \
  --project-ref <staging-ref>

# Each branch gets its own:
# - Database with current migrations applied
# - Unique API URL and keys
# - Isolated storage buckets

# List active branches
npx supabase branches list --project-ref <staging-ref>

# Connect preview deployment to the branch
# In your CI (e.g., Vercel preview deploys):
NEXT_PUBLIC_SUPABASE_URL=https://<branch-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<branch-anon-key>

# Delete branch after merge
npx supabase branches delete feature-user-profiles \
  --project-ref <staging-ref>
```

**CI/CD per-environment deployment (`.github/workflows/deploy.yml`):**

```yaml
name: Deploy Supabase
on:
  push:
    branches: [develop, main]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
        with:
          version: latest
      - name: Push migrations to staging
        run: |
          npx supabase link --project-ref ${{ secrets.STAGING_PROJECT_REF }}
          npx supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
      - name: Deploy Edge Functions
        run: npx supabase functions deploy --project-ref ${{ secrets.STAGING_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production   # Requires approval in GitHub
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
        with:
          version: latest
      - name: Push migrations to production
        run: |
          npx supabase link --project-ref ${{ secrets.PROD_PROJECT_REF }}
          npx supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
      - name: Deploy Edge Functions
        run: npx supabase functions deploy --project-ref ${{ secrets.PROD_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

**Environment-specific seed data:**

```sql
-- supabase/seed.sql (runs ONLY on `supabase db reset`, never in production)
INSERT INTO public.profiles (id, email, role) VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin@test.local', 'admin'),
  ('00000000-0000-0000-0000-000000000002', 'user@test.local', 'member');

-- Insert test data for local development
INSERT INTO public.projects (name, owner_id) VALUES
  ('Test Project', '00000000-0000-0000-0000-000000000001');
```

## Output

After completing this skill, you will have:

- **Three isolated Supabase projects** — each environment has its own URL, API keys, database, and storage
- **Environment-specific `.env` files** — `.env.local`, `.env.staging`, `.env.production` with correct credentials
- **Environment-aware `createClient`** — browser and server clients auto-configured from env vars with `x-environment` header tracking
- **Production safeguards** — `requireNonProduction()` guard blocks destructive operations outside local/staging
- **Migration promotion pipeline** — `supabase db push` promotes schema changes local -> staging -> production
- **Database branching** — preview environments get isolated database branches (Pro plan)
- **CI/CD workflows** — GitHub Actions deploys migrations and Edge Functions per environment with approval gates for production
- **Generated TypeScript types** — `database.types.ts` generated from local or linked project schema

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find project ref` | CLI not linked to a project | Run `npx supabase link --project-ref <ref>` before `db push` |
| `Migration has already been applied` | Re-running an existing migration | Check `supabase_migrations.schema_migrations` table; migrations are idempotent by ref |
| `Permission denied for schema public` | Wrong database password | Verify `SUPABASE_DB_PASSWORD` matches the project's database password in dashboard |
| `Seed data appeared in production` | Ran `supabase db reset` on prod | `seed.sql` only runs on `db reset` — never reset production; use `db push` instead |
| `Wrong environment keys in client` | `.env` file mismatch | Check `SUPABASE_ENV` var and verify URL matches expected project ref |
| `Branch creation failed` | Free plan or branching not enabled | Database branching requires Supabase Pro plan; enable in project settings |
| `Migration drift between envs` | Skipped staging promotion | Always promote through staging first; compare with `supabase migration list` per project |
| `Type generation mismatch` | Types generated from wrong env | Regenerate from local (`--local`) or re-link to the canonical environment |

## Examples

**Example 1 — Quick three-env bootstrap:**

```bash
# Initialize Supabase in existing project
npx supabase init

# Start local
npx supabase start
# Copy output keys to .env.local

# Create staging + production projects in dashboard
# Copy their URLs and keys to .env.staging / .env.production

# Create first migration
npx supabase migration new create_users
# Edit the migration, then:
npx supabase db reset  # Test locally

# Promote to staging
npx supabase link --project-ref abcdefghijklmnop
npx supabase db push

# Promote to production
npx supabase link --project-ref qrstuvwxyz123456
npx supabase db push
```

**Example 2 — Next.js middleware for environment validation:**

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Add environment header for observability
  const env = process.env.SUPABASE_ENV ?? 'unknown';
  response.headers.set('x-supabase-env', env);

  // Block admin routes in production unless authenticated
  if (env === 'production' && request.nextUrl.pathname.startsWith('/admin/seed')) {
    return NextResponse.json({ error: 'Not available in production' }, { status: 403 });
  }

  return response;
}
```

**Example 3 — Verify environment before destructive operations:**

```typescript
import { getEnvironment, requireNonProduction } from '@/lib/env';

async function adminResetHandler(req: Request) {
  const env = getEnvironment();
  console.log(`[admin-reset] Running in ${env} environment`);

  requireNonProduction('admin-reset');

  // Safe to proceed — we're in local or staging
  const { error } = await supabase.rpc('reset_test_data');
  if (error) throw error;

  return Response.json({ status: 'reset complete', environment: env });
}
```

## Resources

- [Managing Environments — Supabase Docs](https://supabase.com/docs/guides/deployment/managing-environments)
- [Database Migrations — Supabase Docs](https://supabase.com/docs/guides/deployment/database-migrations)
- [Database Branching — Supabase Docs](https://supabase.com/docs/guides/deployment/branching)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [createClient — @supabase/supabase-js](https://supabase.com/docs/reference/javascript/initializing)
- [GitHub Actions with Supabase](https://supabase.com/docs/guides/deployment/managing-environments#using-github-actions)
- [12-Factor App — Config](https://12factor.net/config)

## Next Steps

- For authentication patterns across environments, see `supabase-auth-storage-realtime-core`
- For RLS policy testing and validation, see `supabase-policy-guardrails`
- For local development workflow optimization, see `supabase-local-dev-loop`
- For monitoring and observability across environments, see `supabase-observability`
