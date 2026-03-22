---
name: supabase-ci-integration
description: |
  Configure Supabase CI/CD with GitHub Actions: automated testing, migration deployment,
  type generation, and database reset workflows.
  Use when setting up CI pipelines, automating Supabase migrations,
  or running integration tests against Supabase in CI.
  Trigger with phrases like "supabase CI", "supabase GitHub Actions",
  "supabase automated tests", "CI supabase", "supabase pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, ci-cd, github-actions]

---
# Supabase CI Integration

## Overview
Set up GitHub Actions workflows for Supabase: run migrations on deploy, generate TypeScript types, run integration tests against a local Supabase instance, and validate RLS policies.

## Prerequisites
- GitHub repository with Actions enabled
- Supabase project linked (`supabase link`)
- Supabase access token (generate at supabase.com/dashboard/account/tokens)

## Instructions

### Step 1: Store Secrets in GitHub

```bash
# Add secrets to your GitHub repository
gh secret set SUPABASE_ACCESS_TOKEN --body "<your-access-token>"
gh secret set SUPABASE_DB_PASSWORD --body "<your-database-password>"
gh secret set SUPABASE_PROJECT_ID --body "<your-project-ref>"
```

### Step 2: CI Workflow with Local Supabase

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

      - name: Start local Supabase
        run: supabase start -x realtime,storage-api,imgproxy,inbucket,postgrest-manager

      - name: Apply migrations
        run: supabase db reset

      - name: Generate types
        run: |
          supabase gen types typescript --local > lib/database.types.ts
          # Verify types haven't drifted from committed version
          git diff --exit-code lib/database.types.ts || \
            (echo "Types are out of date. Run 'supabase gen types' locally." && exit 1)

      - name: Run tests
        run: npm test
        env:
          SUPABASE_URL: http://127.0.0.1:54321
          SUPABASE_ANON_KEY: ${{ steps.supabase.outputs.anon_key }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ steps.supabase.outputs.service_role_key }}

      - name: Type check
        run: npx tsc --noEmit

      - name: Stop Supabase
        if: always()
        run: supabase stop
```

### Step 3: Deploy Migrations on Merge

```yaml
# .github/workflows/supabase-deploy.yml
name: Deploy Migrations

on:
  push:
    branches: [main]
    paths:
      - 'supabase/migrations/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Link project
        run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_ID }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - name: Push migrations
        run: supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}
```

### Step 4: RLS Policy Validation in CI

```sql
-- supabase/tests/rls_policies.test.sql (pgTAP test)
begin;
select plan(3);

-- Test: RLS is enabled on all public tables
select is(
  (select count(*)::int from pg_tables
   where schemaname = 'public' and rowsecurity = false),
  0,
  'All public tables have RLS enabled'
);

-- Test: todos table has a select policy
select isnt(
  (select count(*)::int from pg_policies
   where tablename = 'todos' and cmd = 'SELECT'),
  0,
  'todos table has a SELECT policy'
);

-- Test: anon role cannot bypass RLS
set role anon;
select is_empty(
  'select * from public.todos',
  'anon role cannot read todos without auth'
);
reset role;

select * from finish();
rollback;
```

```bash
# Run pgTAP tests
supabase test db
```

### Step 5: Type Drift Detection

```yaml
# Add to your PR workflow
- name: Check for type drift
  run: |
    supabase gen types typescript --local > /tmp/generated-types.ts
    diff lib/database.types.ts /tmp/generated-types.ts || {
      echo "::error::Database types are out of sync with schema"
      echo "Run: supabase gen types typescript --local > lib/database.types.ts"
      exit 1
    }
```

## Output
- GitHub Actions workflow running tests against local Supabase
- Automated migration deployment on merge to main
- pgTAP tests validating RLS policies in CI
- Type drift detection preventing stale TypeScript types
- Secrets stored securely in GitHub repository settings

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `supabase start` fails in CI | Docker not available | Use `ubuntu-latest` runner (includes Docker) |
| `supabase db push` unauthorized | Wrong access token | Verify `SUPABASE_ACCESS_TOKEN` secret |
| Type drift detected | Schema changed without regenerating types | Run `supabase gen types typescript --linked` |
| pgTAP test failures | Missing RLS policies | Add policies before merging |

## Resources
- [Supabase CLI in CI](https://supabase.com/docs/guides/local-development/cli/getting-started)
- [Database Testing with pgTAP](https://supabase.com/docs/guides/local-development/testing/pgtap-extended)
- [Managing Environments](https://supabase.com/docs/guides/deployment/managing-environments)

## Next Steps
For deployment to hosting platforms, see `supabase-deploy-integration`.
