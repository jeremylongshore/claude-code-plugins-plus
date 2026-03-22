---
name: supabase-deploy-integration
description: |
  Deploy Supabase-powered apps to Vercel, Fly.io, and Cloud Run with
  connection pooling, secret management, and Edge Functions.
  Use when deploying to production, configuring platform secrets,
  or setting up Supabase Edge Functions deployment.
  Trigger with phrases like "deploy supabase", "supabase Vercel",
  "supabase Edge Functions deploy", "supabase Cloud Run", "supabase Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*), Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, deployment, edge-functions]

---
# Supabase Deploy Integration

## Overview
Deploy Supabase-powered applications and Edge Functions to production. Covers Vercel, Fly.io, Cloud Run, and Supabase's native Edge Functions deployment with proper secret management and connection pooling.

## Prerequisites
- Supabase production project with API keys
- Platform CLI installed (vercel, fly, gcloud, or supabase)
- Application code tested against staging

## Instructions

### Deploy Supabase Edge Functions

```bash
# Create an Edge Function
supabase functions new process-payment

# Write the function (Deno runtime)
```

```typescript
// supabase/functions/process-payment/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  try {
    // Create Supabase client with the user's auth context
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!,
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    const { amount, currency } = await req.json()

    // Get the authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 })
    }

    // Business logic
    const { data, error } = await supabase
      .from('payments')
      .insert({ user_id: user.id, amount, currency, status: 'pending' })
      .select()
      .single()

    if (error) throw error

    return new Response(JSON.stringify({ payment: data }), {
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500 })
  }
})
```

```bash
# Set secrets for the Edge Function
supabase secrets set STRIPE_SECRET_KEY=sk_live_...
supabase secrets set WEBHOOK_SECRET=whsec_...

# Deploy
supabase functions deploy process-payment

# Deploy all functions
supabase functions deploy
```

### Deploy to Vercel

```bash
# Add Supabase environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production  # server-only

# Use pooled connection string for Vercel (serverless)
vercel env add DATABASE_URL production
# Value: postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Deploy
vercel deploy --prod
```

```typescript
// lib/supabase-server.ts (for Vercel API routes / Server Components)
import { createClient } from '@supabase/supabase-js'

export function createServerClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
}
```

### Deploy to Fly.io

```bash
# Set secrets
fly secrets set SUPABASE_URL=https://<ref>.supabase.co
fly secrets set SUPABASE_ANON_KEY=eyJ...
fly secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...
fly secrets set DATABASE_URL=postgres://postgres.[ref]:[pwd]@aws-0-[region].pooler.supabase.com:5432/postgres

# Deploy
fly deploy
```

### Deploy to Google Cloud Run

```bash
# Store secrets in Secret Manager
echo -n "https://<ref>.supabase.co" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "eyJ..." | gcloud secrets create SUPABASE_ANON_KEY --data-file=-

# Deploy with secret references
gcloud run deploy my-app \
  --source . \
  --set-secrets="SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_ANON_KEY=SUPABASE_ANON_KEY:latest" \
  --region=us-central1 \
  --allow-unauthenticated
```

### Connection Pooling for Serverless

```
# Direct connection (for migrations, long-running servers)
postgres://postgres.[ref]:[password]@db.[ref].supabase.co:5432/postgres

# Pooled connection via Supavisor (for serverless / high-concurrency)
# Transaction mode (default, recommended for serverless):
postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Session mode (for features needing session state like prepared statements):
postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

### Health Check Endpoint

```typescript
// api/health.ts (works on any platform)
import { createClient } from '@supabase/supabase-js'

export async function GET() {
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_ANON_KEY!
  )

  const start = Date.now()
  const { error } = await supabase.rpc('version')
  const latency = Date.now() - start

  return Response.json({
    healthy: !error,
    supabase_latency_ms: latency,
    region: process.env.FLY_REGION || process.env.VERCEL_REGION || 'unknown',
  }, { status: error ? 503 : 200 })
}
```

## Output
- Edge Functions deployed to Supabase's global edge network
- Application deployed to chosen platform with proper secrets
- Connection pooling configured for serverless environments
- Health check endpoint verifying Supabase connectivity

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FetchError` on Vercel | Wrong SUPABASE_URL | Verify env vars in Vercel dashboard |
| Edge Function 500 | Missing Deno import | Use `esm.sh` for npm packages in Edge Functions |
| Connection timeout in serverless | Direct connection instead of pooled | Use Supavisor pooled connection string |
| `supabase functions deploy` fails | Not linked | Run `supabase link --project-ref <ref>` |

## Resources
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [Vercel Integration](https://supabase.com/partners/integrations/vercel)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Edge Functions Quickstart](https://supabase.com/docs/guides/functions/quickstart)

## Next Steps
For webhook handling, see `supabase-webhooks-events`.
