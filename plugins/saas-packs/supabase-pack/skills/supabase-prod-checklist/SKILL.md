---
name: supabase-prod-checklist
description: |
  Execute Supabase production deployment checklist covering RLS, key hygiene,
  connection pooling, backups, monitoring, Edge Functions, and Storage policies.
  Use when deploying to production, preparing for launch,
  or auditing a live Supabase project for security and performance gaps.
  Trigger with "supabase production", "supabase go-live",
  "supabase launch checklist", "supabase prod ready", "deploy supabase",
  "supabase production readiness".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, deployment, production, security, rls]
---

# Supabase Production Deployment Checklist

## Overview

Actionable 14-step checklist for taking a Supabase project to production. Covers RLS enforcement, key separation, connection pooling (Supavisor), backups/PITR, network restrictions, custom domains, auth emails, rate limits, monitoring, Edge Functions, Storage policies, indexes, and migrations. Based on Supabase's official [production guide](https://supabase.com/docs/guides/deployment/going-into-prod).

## Prerequisites

- Supabase project on Pro plan or higher (required for PITR, network restrictions)
- Separate production project (never share dev/prod)
- `@supabase/supabase-js` v2+ installed
- Supabase CLI installed (`npx supabase --version`)
- Domain and DNS configured for custom domain
- Deployment platform ready (Vercel, Netlify, Cloudflare, etc.)

## Instructions

### Step 1: Enforce Row Level Security on ALL Tables

RLS is the single most critical production requirement. Without it, any client with your anon key can read/write every row.

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

- [ ] RLS enabled on every public table (zero rows from audit query above)
- [ ] SELECT, INSERT, UPDATE, DELETE policies defined for each table
- [ ] Policies tested with both authenticated and anonymous roles
- [ ] No tables use `USING (true)` without intent (public read tables only)

### Step 2: Enforce Key Separation — Anon vs Service Role

The `anon` key is safe for client-side code. The `service_role` key bypasses RLS entirely and must never leave server-side environments.

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

- [ ] Anon key used in all client-side code (`NEXT_PUBLIC_` prefix)
- [ ] Service role key used only in server-side code (API routes, Edge Functions)
- [ ] Service role key not in any client bundle (verify with `grep -r "service_role" dist/`)
- [ ] Database password changed from the auto-generated default

### Step 3: Configure Connection Pooling (Supavisor)

Supabase uses Supavisor for connection pooling. Serverless functions (Vercel, Netlify, Cloudflare Workers) MUST use the pooled connection string to avoid exhausting the database connection limit.

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
    // Supavisor handles pooling at port 6543
    // No need to configure pgBouncer settings in the client
  }
);
```

- [ ] Application code uses pooled connection string (port 6543)
- [ ] Direct connection reserved for migrations and admin tasks only
- [ ] Connection string in deployment platform env vars (not hardcoded)
- [ ] Verified pool mode: `transaction` for serverless, `session` for long-lived connections

### Step 4: Enable Database Backups

Supabase provides automatic daily backups on Pro plan. Point-in-time recovery (PITR) enables granular restores.

- [ ] Automatic daily backups enabled (Pro plan — verify in Dashboard > Database > Backups)
- [ ] Point-in-time recovery configured (Dashboard > Database > Backups > PITR)
- [ ] Tested restore procedure on a staging project (do not skip this)
- [ ] Migration files committed to version control (`supabase/migrations/` directory)
- [ ] `npx supabase db push` tested against a fresh project to verify migrations replay cleanly

### Step 5: Configure Network Restrictions

Restrict database access to known IP addresses. This prevents unauthorized direct database connections even if credentials leak.

- [ ] IP allowlist configured (Dashboard > Database > Network Restrictions)
- [ ] Only deployment platform IPs and team office IPs are allowed
- [ ] Verified that application still connects after restrictions applied
- [ ] Documented which IPs are allowed and why

### Step 6: Configure Custom Domain

A custom domain replaces the default `*.supabase.co` URLs with your brand domain for API and auth endpoints.

- [ ] Custom domain configured (Dashboard > Settings > Custom Domains)
- [ ] DNS CNAME record added and verified
- [ ] SSL certificate provisioned and active
- [ ] Application code updated to use custom domain URL
- [ ] OAuth redirect URLs updated to use custom domain

### Step 7: Customize Auth Email Templates

Default Supabase auth emails show generic branding. Customize them so users see your domain and brand.

- [ ] Confirmation email template customized (Dashboard > Auth > Email Templates)
- [ ] Password reset email template customized
- [ ] Magic link email template customized
- [ ] Invite email template customized
- [ ] Custom SMTP configured (Dashboard > Auth > SMTP Settings) — avoids rate limits and improves deliverability
- [ ] Email confirmation enabled (Dashboard > Auth > Settings)
- [ ] OAuth redirect URLs restricted to production domains only
- [ ] Unused auth providers disabled

### Step 8: Understand Rate Limits Per Tier

Supabase enforces rate limits that vary by plan. Hitting these in production causes 429 errors.

| Resource | Free | Pro | Team |
|----------|------|-----|------|
| API requests | 500/min | 1,000/min | 5,000/min |
| Auth emails | 4/hour | 30/hour | 100/hour |
| Realtime connections | 200 concurrent | 500 concurrent | 2,000 concurrent |
| Edge Function invocations | 500K/month | 2M/month | 5M/month |
| Storage bandwidth | 2GB/month | 250GB/month | Custom |
| Database size | 500MB | 8GB | 50GB |

- [ ] Rate limits documented for your plan tier
- [ ] Client-side retry logic with exponential backoff for 429 responses
- [ ] Auth email rate limits understood (use custom SMTP to increase)
- [ ] Realtime connection limits planned for expected concurrent users

### Step 9: Review Monitoring Dashboards

Supabase provides built-in monitoring. Review these before launch to establish baselines.

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

- [ ] Dashboard > Reports reviewed (API requests, auth, storage, realtime)
- [ ] Dashboard > Logs > API checked for error patterns
- [ ] Dashboard > Database > Performance Advisor reviewed and recommendations applied
- [ ] Health check endpoint deployed and monitored (uptime service)
- [ ] Error tracking configured (Sentry, LogRocket, etc.)
- [ ] Alerts set for: error rate spikes, high latency, connection pool exhaustion

### Step 10: Deploy Edge Functions with Proper Env Vars

Edge Functions run on Deno Deploy. Environment variables must be set via the Supabase CLI or Dashboard, not hardcoded.

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

- [ ] All Edge Functions deployed to production (`npx supabase functions deploy`)
- [ ] Environment secrets set via `npx supabase secrets set` (not hardcoded)
- [ ] `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` available automatically (no need to set)
- [ ] Edge Functions tested with `npx supabase functions serve` locally before deploying
- [ ] CORS headers configured for Edge Functions that receive browser requests

### Step 11: Verify Storage Bucket Policies

Storage buckets need explicit policies, similar to RLS on tables. Without policies, buckets are inaccessible (default deny).

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

- [ ] Each bucket has explicit SELECT/INSERT/UPDATE/DELETE policies
- [ ] Public buckets are intentionally public (not accidentally open)
- [ ] File size limits set per bucket (`file_size_limit` in bucket config)
- [ ] Allowed MIME types restricted per bucket (`allowed_mime_types`)
- [ ] User upload paths scoped to `auth.uid()` to prevent overwrites

### Step 12: Add Database Indexes on Frequently Queried Columns

Missing indexes are the leading cause of slow queries after launch. Add indexes on foreign keys, filter columns, and sort columns.

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

- [ ] Indexes on all foreign key columns
- [ ] Indexes on columns used in WHERE, ORDER BY, and JOIN clauses
- [ ] `pg_stat_statements` enabled for ongoing query monitoring
- [ ] Performance Advisor reviewed (Dashboard > Database > Performance)
- [ ] `statement_timeout` set for authenticated role to prevent runaway queries
- [ ] Table bloat checked — VACUUM if dead tuple percentage > 10%

### Step 13: Apply Migrations with `npx supabase db push`

All schema changes must go through migration files, never manual Dashboard edits in production.

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

- [ ] All schema changes in `supabase/migrations/` directory (version controlled)
- [ ] `npx supabase db push` tested against a fresh project
- [ ] Migration history matches between local and remote (`npx supabase migration list`)
- [ ] Rollback migration prepared for risky schema changes
- [ ] No manual schema edits in production Dashboard

### Step 14: Pre-Launch Final Verification

```bash
# Verify RLS status one final time
npx supabase inspect db table-sizes --linked

# Check that the project is linked to production
npx supabase status

# Verify connection string works
npx supabase db ping --linked
```

- [ ] CORS settings match production domain (Dashboard > API > CORS)
- [ ] Environment variables set correctly in deployment platform
- [ ] Realtime enabled only on tables that need it (reduces connection usage)
- [ ] Webhook endpoints registered and tested
- [ ] Load test completed on staging (see `supabase-load-scale`)
- [ ] SSL enforcement enabled (Dashboard > Database > Settings > SSL)
- [ ] DNS and custom domain verified end-to-end

## Output

- All 14 checklist sections verified with zero unchecked items
- RLS enforced on every public table with tested policies
- Key separation verified (anon client-side, service_role server-side only)
- Connection pooling via Supavisor (port 6543) for all application code
- Backups, PITR, monitoring, Edge Functions, Storage policies, indexes all verified
- Migrations applied cleanly via `npx supabase db push`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on all API calls | RLS enabled but no policies created | Add SELECT/INSERT/UPDATE/DELETE policies for each role |
| `429 Too Many Requests` | Plan rate limit exceeded | Upgrade plan or implement client-side backoff with retry |
| Connection timeout under load | Using direct connection in serverless | Switch to pooled connection string (port 6543) |
| Auth emails not delivered | Default SMTP rate-limited | Configure custom SMTP provider (SendGrid, Resend, Postmark) |
| `PGRST301` permission denied | Service role key used where anon expected | Check client initialization — use anon key for client-side |
| Edge Function cold starts | First invocation after idle period | Pre-warm with scheduled pings or accept ~200ms cold start |
| Storage upload fails | Missing bucket policy or size limit exceeded | Add INSERT policy and check `file_size_limit` on bucket |
| Slow queries after launch | Missing indexes on filter/join columns | Run Performance Advisor and add indexes per Step 12 |
| Migration conflicts | Manual Dashboard edits diverged from migration files | Run `npx supabase db diff` to capture drift, then commit |

## Examples

### Client Setup (Next.js)

```typescript
// lib/supabase/client.ts — browser (anon key)
import { createClient } from '@supabase/supabase-js';
export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// lib/supabase/server.ts — server only (service role)
export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);
```

### RLS Policy Pattern

```sql
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read published" ON public.posts
  FOR SELECT USING (status = 'published');
CREATE POLICY "Authors manage own" ON public.posts
  FOR ALL USING (auth.uid() = author_id)
  WITH CHECK (auth.uid() = author_id);
```

### Rollback

```bash
npx supabase migration new rollback_bad_change  # Create reversal SQL
npx supabase db push                             # Apply rollback
# For data: Dashboard > Database > Backups > PITR
# For app: vercel rollback / netlify deploy --prod
```

For complete examples including health checks, storage policies, and Edge Functions, see [examples.md](references/examples.md).

## Resources

- [Going to Production](https://supabase.com/docs/guides/deployment/going-into-prod) — Official production checklist
- [Maturity Model](https://supabase.com/docs/guides/deployment/maturity-model) — Project lifecycle stages
- [Shared Responsibility Model](https://supabase.com/docs/guides/deployment/shared-responsibility-model) — What Supabase manages vs. what you manage
- [Performance Advisor](https://supabase.com/docs/guides/database/inspect) — Built-in query analysis
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler) — Supavisor configuration
- [RLS Guide](https://supabase.com/docs/guides/database/postgres/row-level-security) — Policy patterns and examples
- [Edge Functions](https://supabase.com/docs/guides/functions) — Serverless Deno functions
- [Storage](https://supabase.com/docs/guides/storage) — File storage with policies
- [`@supabase/supabase-js` Reference](https://supabase.com/docs/reference/javascript/introduction) — Client SDK docs

## Next Steps

- For SDK version upgrades, see `supabase-upgrade-migration`
- For load testing before launch, see `supabase-load-scale`
- For monitoring in production, see `supabase-monitoring`
- For Edge Function patterns, see `supabase-edge-functions`
