# Step-by-Step Commands

The full SQL, TypeScript, and CLI commands for each checklist step in
`SKILL.md`. SKILL.md keeps the intro + checklist for every step; this file
holds the deep code so the workflow reads cleanly and you drill in per step.

## Step 1: Enforce Row Level Security on ALL Tables

```sql
-- Audit: find tables WITHOUT RLS enabled
-- This query MUST return zero rows before going live
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = false;
```

```sql
-- Enable RLS on a table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create a basic read policy (authenticated users see own rows)
CREATE POLICY "Users can view own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Create an insert policy
CREATE POLICY "Users can insert own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create an update policy
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

## Step 2: Enforce Key Separation — Anon vs Service Role

```typescript
// Client-side — ONLY use anon key
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!  // Safe for browsers
);
```

```typescript
// Server-side only — service_role key (API routes, webhooks, cron jobs)
import { createClient } from '@supabase/supabase-js';

const supabaseAdmin = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,  // NEVER expose to client
  { auth: { autoRefreshToken: false, persistSession: false } }
);
```

## Step 3: Configure Connection Pooling (Supavisor)

```
# Direct connection (migrations, admin tasks only)
postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# Pooled connection via Supavisor (application code — USE THIS)
# Port 6543 = Supavisor pooler (vs 5432 direct)
postgresql://postgres.[REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

```typescript
// For serverless environments — use pooled connection
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!,
  {
    db: { schema: 'public' },
    // Supavisor handles pooling at port 6543 (the transaction-mode pooler);
    // no need to configure pgBouncer settings in the client
  }
);
```

## Step 9: Review Monitoring Dashboards

```typescript
// Health check endpoint — deploy this to your application
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export async function GET() {
  const start = Date.now();
  const { data, error } = await supabase
    .from('_health_check')  // Create a small table for this
    .select('id')
    .limit(1);

  const latency = Date.now() - start;

  return Response.json({
    status: error ? 'unhealthy' : 'healthy',
    latency_ms: latency,
    timestamp: new Date().toISOString(),
    supabase_reachable: !error,
  }, { status: error ? 503 : 200 });
}
```

## Step 10: Deploy Edge Functions with Proper Env Vars

```bash
# Set secrets for Edge Functions
npx supabase secrets set STRIPE_SECRET_KEY=sk_live_...
npx supabase secrets set RESEND_API_KEY=re_...

# List current secrets
npx supabase secrets list

# Deploy all Edge Functions
npx supabase functions deploy

# Deploy a specific function
npx supabase functions deploy process-webhook
```

```typescript
// supabase/functions/process-webhook/index.ts
import { createClient } from '@supabase/supabase-js';

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!  // Available automatically
  );

  const body = await req.json();
  // Process webhook payload...

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

## Step 11: Verify Storage Bucket Policies

```sql
-- Check storage bucket configurations
SELECT id, name, public, file_size_limit, allowed_mime_types
FROM storage.buckets;

-- Check existing storage policies
SELECT policyname, tablename, cmd, qual
FROM pg_policies
WHERE schemaname = 'storage';
```

```sql
-- Example: Allow authenticated users to upload to their own folder
CREATE POLICY "Users can upload own files"
  ON storage.objects
  FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Example: Allow public read access to a bucket
CREATE POLICY "Public read access"
  ON storage.objects
  FOR SELECT
  USING (bucket_id = 'public-assets');
```

## Step 12: Add Database Indexes on Frequently Queried Columns

```sql
-- Find missing indexes on foreign keys
SELECT
  tc.table_name, kcu.column_name,
  CASE WHEN i.indexname IS NULL THEN '** MISSING INDEX **' ELSE i.indexname END AS index_status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
LEFT JOIN pg_indexes i
  ON i.tablename = tc.table_name
  AND i.indexdef LIKE '%' || kcu.column_name || '%'
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';

-- Find slow queries (requires pg_stat_statements extension)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT query, calls, mean_exec_time::numeric(10,2) AS avg_ms,
       total_exec_time::numeric(10,2) AS total_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check table bloat (dead tuples from updates/deletes)
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup::numeric / greatest(n_live_tup, 1) * 100, 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

```sql
-- Create indexes on commonly filtered columns
CREATE INDEX idx_profiles_user_id ON public.profiles(user_id);
CREATE INDEX idx_orders_created_at ON public.orders(created_at DESC);
CREATE INDEX idx_posts_status ON public.posts(status) WHERE status = 'published';  -- Partial index

-- Set query timeout for the authenticated role
ALTER ROLE authenticated SET statement_timeout = '10s';
```

## Step 13: Apply Migrations with `npx supabase db push`

```bash
# Generate a migration from local changes
npx supabase db diff --use-migra -f add_indexes

# Apply migrations to production (linked project)
npx supabase db push

# Verify migration history
npx supabase migration list

# If a migration fails, create a rollback
npx supabase migration new rollback_bad_change
```

## Step 14: Pre-Launch Final Verification

```bash
# Verify RLS status one final time
npx supabase inspect db table-sizes --linked

# Check that the project is linked to production
npx supabase status

# Verify connection string works
npx supabase db ping --linked
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
