---
name: supabase-ci-integration
description: |
  Configure Supabase CI/CD pipelines with GitHub Actions: link projects,
  push migrations, deploy Edge Functions, generate types, and run tests
  against local Supabase instances.
  Use when setting up CI pipelines for Supabase, automating database
  migrations, deploying Edge Functions in CI, or running integration tests.
  Trigger with phrases like "supabase CI", "supabase GitHub Actions",
  "supabase deploy pipeline", "CI supabase migrations", "supabase preview branches".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, ci-cd, github-actions, devops]
---

# Supabase CI Integration

## Overview

Build GitHub Actions workflows that automate the full Supabase lifecycle: link projects in CI, push migrations on merge, deploy Edge Functions, generate TypeScript types, run tests against a local Supabase instance, and create preview branches for pull requests. Every database change gets validated before it reaches production.

## Prerequisites

- GitHub repository with Actions enabled
- Supabase project created at [supabase.com/dashboard](https://supabase.com/dashboard)
- Supabase CLI initialized locally (`npx supabase init`)
- Node.js 18+ in your project
- `@supabase/supabase-js` installed:

```bash
npm install @supabase/supabase-js
```

## Instructions

### Step 1: Configure GitHub Secrets and Link in CI

Store credentials as GitHub repository secrets. The CI pipeline uses these to authenticate with your Supabase project without exposing tokens in code.

```bash
# Set secrets via GitHub CLI
gh secret set SUPABASE_ACCESS_TOKEN --body "<your-access-token>"
gh secret set SUPABASE_DB_PASSWORD --body "<your-database-password>"
gh secret set SUPABASE_PROJECT_REF --body "<your-project-ref>"
```

Generate your access token at [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens). Find your project ref in Project Settings > General.

Link the project in any CI job that needs remote access:

```yaml
- name: Install Supabase CLI
  uses: supabase/setup-cli@v1
  with:
    version: latest

- name: Link Supabase project
  run: npx supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
  env:
    SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

### Step 2: CI Workflow — Test, Validate Migrations, and Generate Types

This workflow starts a local Supabase instance, applies migrations, generates types, and runs your test suite on every pull request. It catches schema drift, broken migrations, and test failures before merge.

```yaml
# .github/workflows/supabase-ci.yml
name: Supabase CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      # Start local Supabase (disable unused services for speed)
      - name: Start local Supabase
        run: npx supabase start -x realtime,storage-api,imgproxy,inbucket

      # Apply all migrations and seed data from scratch
      - name: Validate migrations
        run: npx supabase db reset

      # Generate types and detect drift from committed version
      - name: Generate and verify TypeScript types
        run: |
          npx supabase gen types typescript --local > src/types/database.types.ts
          git diff --exit-code src/types/database.types.ts || {
            echo "::error::TypeScript types are out of sync with database schema"
            echo "Run: npx supabase gen types typescript --local > src/types/database.types.ts"
            exit 1
          }

      # Run pgTAP database tests
      - name: Run database tests
        run: npx supabase test db

      # Run application tests against local Supabase
      - name: Run application tests
        run: npm test
        env:
          SUPABASE_URL: http://127.0.0.1:54321
          SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
          SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

      - name: Type check
        run: npx tsc --noEmit

      - name: Stop Supabase
        if: always()
        run: npx supabase stop
```

The `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY` above are the default local development keys — safe to commit. They only work against your local Supabase instance.

### Step 3: Deploy Migrations and Edge Functions on Merge

This workflow runs only when migration files or Edge Function source changes are pushed to `main`. It links the remote project and pushes changes to production.

```yaml
# .github/workflows/supabase-deploy.yml
name: Deploy to Supabase

on:
  push:
    branches: [main]
    paths:
      - 'supabase/migrations/**'
      - 'supabase/functions/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Link project
        run: npx supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      # Push pending migrations to production
      - name: Push database migrations
        run: npx supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}

      # Deploy all Edge Functions
      - name: Deploy Edge Functions
        run: npx supabase functions deploy
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      # Regenerate types from production schema
      - name: Generate production types
        run: |
          npx supabase gen types typescript --linked > src/types/database.types.ts
          echo "Types generated from production schema"
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}
```

## Preview Branches

Create isolated Supabase environments for each pull request. Each preview branch gets its own database with migrations applied, so reviewers can test against real infrastructure.

```yaml
# Add to your PR workflow
preview:
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  steps:
    - uses: actions/checkout@v4

    - name: Install Supabase CLI
      uses: supabase/setup-cli@v1
      with:
        version: latest

    - name: Link project
      run: npx supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
      env:
        SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

    - name: Create preview branch
      run: npx supabase branches create "preview-${{ github.event.number }}"
      env:
        SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

Preview branches require a Supabase Pro plan or higher. Each branch incurs compute costs while running.

## Database Test Example

Write pgTAP tests in `supabase/tests/` to validate RLS policies and schema constraints in CI:

```sql
-- supabase/tests/rls_validation.test.sql
begin;
select plan(3);

-- All public tables must have RLS enabled
select is(
  (select count(*)::int from pg_tables
   where schemaname = 'public' and rowsecurity = false),
  0,
  'All public tables have RLS enabled'
);

-- Verify anon role cannot read protected data
set role anon;
select is_empty(
  'select * from public.profiles',
  'anon role cannot read profiles without auth'
);
reset role;

-- Verify authenticated users can only see their own rows
set role authenticated;
select isnt_empty(
  $$select * from pg_policies where tablename = 'profiles' and cmd = 'SELECT'$$,
  'profiles table has a SELECT policy for authenticated users'
);
reset role;

select * from finish();
rollback;
```

Run locally with `npx supabase test db` before pushing.

## Application Test Pattern

Use `createClient` from `@supabase/supabase-js` in tests, pointing at the local instance:

```typescript
// tests/setup.ts
import { createClient } from '@supabase/supabase-js';
import type { Database } from '../src/types/database.types';

export const supabase = createClient<Database>(
  process.env.SUPABASE_URL ?? 'http://127.0.0.1:54321',
  process.env.SUPABASE_ANON_KEY ?? 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
);

// tests/profiles.test.ts
import { supabase } from './setup';

test('can insert and read a profile', async () => {
  const { data, error } = await supabase
    .from('profiles')
    .insert({ id: 'test-user', display_name: 'Test' })
    .select()
    .single();

  expect(error).toBeNull();
  expect(data?.display_name).toBe('Test');
});
```

## Output

After implementing these workflows:

- Pull requests run tests against a fresh local Supabase instance with all migrations applied
- TypeScript type drift is detected automatically — stale types block the PR
- Database migrations deploy to production only on merge to main
- Edge Functions deploy alongside migration changes
- pgTAP tests validate RLS policies and schema constraints in CI
- Preview branches provide isolated environments for PR review (Pro plan)
- GitHub secrets keep `SUPABASE_ACCESS_TOKEN` and `SUPABASE_DB_PASSWORD` out of code

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `supabase start` fails in CI | Docker not available | Use `ubuntu-latest` runner (includes Docker by default) |
| `supabase db push` returns "permission denied" | Invalid or expired access token | Regenerate token at supabase.com/dashboard/account/tokens |
| `supabase link` fails | Wrong project ref | Check project ref in Settings > General, must match `SUPABASE_PROJECT_REF` secret |
| Type drift detected in PR | Schema changed without regenerating types | Run `npx supabase gen types typescript --local > src/types/database.types.ts` |
| `supabase functions deploy` fails | Missing Deno types or syntax errors | Run `npx supabase functions serve` locally first to catch issues |
| pgTAP tests fail | Missing RLS policies or schema constraints | Add policies before merging — `npx supabase test db` runs locally |
| Preview branch creation fails | Free plan limitation | Preview branches require Supabase Pro plan |
| Migration conflict on push | Divergent migration history | Run `npx supabase db pull` to reconcile remote vs local migrations |

## Examples

**Minimal CI for a new project** — just migration validation and type checking:

```yaml
name: Supabase CI
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
        with: { version: latest }
      - run: npx supabase start -x realtime,storage-api,imgproxy,inbucket,edge-runtime
      - run: npx supabase db reset
      - run: npx supabase gen types typescript --local > /tmp/types.ts && diff src/types/database.types.ts /tmp/types.ts
      - if: always()
        run: npx supabase stop
```

**Edge Function deploy with verification:**

```bash
# Deploy a specific function and verify it's live
npx supabase functions deploy my-function --project-ref $PROJECT_REF
curl -s "https://$PROJECT_REF.supabase.co/functions/v1/my-function" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" | jq .
```

## Resources

- [Supabase CLI in CI/CD](https://supabase.com/docs/guides/local-development/cli/getting-started) — official setup guide
- [Database Testing with pgTAP](https://supabase.com/docs/guides/local-development/testing) — writing and running database tests
- [Managing Environments](https://supabase.com/docs/guides/deployment/managing-environments) — staging, production, preview branches
- [Edge Functions Deployment](https://supabase.com/docs/guides/functions/deploy) — deploying Deno functions
- [Type Generation](https://supabase.com/docs/guides/api/rest/generating-types) — keeping TypeScript types in sync
- [Branching & Preview](https://supabase.com/docs/guides/deployment/branching) — per-PR database environments
- [@supabase/supabase-js Reference](https://supabase.com/docs/reference/javascript/introduction) — client SDK documentation

## Next Steps

For deploying Supabase-backed applications to hosting platforms, see `supabase-deploy-integration`. For configuring RLS policies, see `supabase-rls-policies`.
