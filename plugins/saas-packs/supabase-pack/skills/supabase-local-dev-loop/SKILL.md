---
name: supabase-local-dev-loop
description: |
  Configure Supabase local development with the CLI, Docker, hot reload, and testing.
  Use when setting up a local development environment, running supabase start,
  writing database seeds, or establishing a fast iteration cycle.
  Trigger with phrases like "supabase dev setup", "supabase local",
  "supabase start", "supabase local development", "supabase docker".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(supabase:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, local-development, testing]

---
# Supabase Local Dev Loop

## Overview
Set up a full local Supabase stack using the CLI and Docker. This gives you Postgres, Auth, Storage, Realtime, and Edge Functions running locally with the same APIs as production, enabling offline development and fast iteration.

## Prerequisites
- Docker Desktop running (required for `supabase start`)
- Supabase CLI installed (`npm install -g supabase`)
- Node.js 18+ with npm/pnpm

## Instructions

### Step 1: Initialize and Start

```bash
# Initialize Supabase in your project
supabase init

# Start the local stack (pulls Docker images on first run)
supabase start

# Output includes local credentials:
# API URL:    http://127.0.0.1:54321
# GraphQL:    http://127.0.0.1:54321/graphql/v1
# Studio:     http://127.0.0.1:54323
# Inbucket:   http://127.0.0.1:54324  (email testing)
# anon key:   eyJ...
# service_role key: eyJ...
```

### Step 2: Create Migrations

```bash
# Create a new migration
supabase migration new create_profiles

# Edit the generated file
# supabase/migrations/<timestamp>_create_profiles.sql
```

```sql
-- supabase/migrations/<timestamp>_create_profiles.sql
create table public.profiles (
  id uuid references auth.users(id) primary key,
  username text unique not null,
  avatar_url text,
  updated_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone"
  on public.profiles for select
  using (true);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create profile on user signup via trigger
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, username)
  values (new.id, new.raw_user_meta_data->>'username');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

```bash
# Apply all migrations and re-seed
supabase db reset
```

### Step 3: Seed Data

```sql
-- supabase/seed.sql (runs after migrations on db reset)
insert into auth.users (id, email, raw_user_meta_data)
values
  ('d0e1f2a3-b4c5-6789-0abc-def123456789', 'test@example.com',
   '{"username": "testuser"}');

insert into public.profiles (id, username, avatar_url)
values
  ('d0e1f2a3-b4c5-6789-0abc-def123456789', 'testuser',
   'https://example.com/avatar.png');
```

### Step 4: Local Environment Config

```bash
# .env.local (for local development)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=<anon-key-from-supabase-start>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key-from-supabase-start>
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### Step 5: Diff and Generate Migrations

```bash
# Make changes in Studio (http://127.0.0.1:54323), then:
supabase db diff --use-migra -f add_columns_to_profiles

# This generates a migration file from the diff between
# your local database state and your migration files

# Review and apply
supabase db reset
```

### Step 6: Test with Vitest

```typescript
// tests/supabase.test.ts
import { createClient } from '@supabase/supabase-js'
import { describe, it, expect, beforeAll } from 'vitest'

const supabase = createClient(
  'http://127.0.0.1:54321',
  'eyJ...'  // local anon key from supabase start
)

describe('profiles', () => {
  it('should fetch public profiles', async () => {
    const { data, error } = await supabase
      .from('profiles')
      .select('username')
      .limit(1)

    expect(error).toBeNull()
    expect(data).toBeDefined()
  })
})
```

### Step 7: Edge Function Development

```bash
# Create a new Edge Function
supabase functions new hello-world

# Serve locally with hot reload
supabase functions serve hello-world --env-file .env.local

# Test it
curl -i --location --request POST \
  'http://127.0.0.1:54321/functions/v1/hello-world' \
  --header 'Authorization: Bearer <anon-key>' \
  --header 'Content-Type: application/json' \
  --data '{"name":"World"}'
```

### Step 8: Daily Workflow

```bash
# Start of day
supabase start            # Start local stack
npm run dev               # Start your app

# After schema changes
supabase db diff -f my_change  # Generate migration from diff
supabase db reset              # Reset and replay all migrations

# Before committing
supabase db reset              # Verify clean replay
npm test                       # Run tests against local Supabase

# Stop local stack
supabase stop
```

## Output
- Local Supabase stack running via Docker
- Migration workflow with `supabase db diff` and `supabase db reset`
- Seed data for consistent test state
- Edge Function hot-reload development
- Test suite running against local instance

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot connect to Docker daemon` | Docker not running | Start Docker Desktop |
| `Port 54321 already in use` | Previous instance running | Run `supabase stop` then `supabase start` |
| `supabase db reset` fails | Bad migration SQL | Check migration files for syntax errors |
| `Permission denied on supabase start` | Docker permissions | Add user to docker group or run with sudo |
| Edge Function 500 | Missing env vars | Pass `--env-file .env.local` to `functions serve` |

## Resources
- [Local Development Guide](https://supabase.com/docs/guides/local-development/overview)
- [Supabase CLI Getting Started](https://supabase.com/docs/guides/local-development/cli/getting-started)
- [Database Migrations](https://supabase.com/docs/guides/deployment/database-migrations)
- [Edge Functions Quickstart](https://supabase.com/docs/guides/functions/quickstart)

## Next Steps
Proceed to `supabase-sdk-patterns` for production-ready client patterns.
