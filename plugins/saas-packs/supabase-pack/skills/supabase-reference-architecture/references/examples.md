# Examples — Multi-Tenant Setup and Job Queue Consumer

## Complete Multi-Tenant Setup (TypeScript)

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// 1. Sign in
const { data: { session } } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
})

// 2. Switch tenant context
const { error: claimError } = await supabase.rpc('set_tenant_claim', {
  tenant_id: 'tenant-uuid-here'
})
if (claimError) throw claimError

// 3. Refresh session to pick up new JWT claims
await supabase.auth.refreshSession()

// 4. All subsequent queries are automatically scoped to this tenant
const { data: projects } = await supabase
  .from('projects')
  .select('id, name, created_at')
  .order('created_at', { ascending: false })

console.log('Tenant projects:', projects)
// Only returns projects where org_id matches the JWT claim
```

## Job Queue Consumer (TypeScript)

```typescript
import { getSupabaseAdmin } from './admin'

async function processJobs() {
  const supabase = getSupabaseAdmin()

  while (true) {
    // Atomically claim the next job
    const { data: job, error } = await supabase
      .rpc('claim_next_job', { p_job_type: 'send-email' })

    if (error || !job) {
      // No jobs available — wait before polling again
      await new Promise(r => setTimeout(r, 5000))
      continue
    }

    try {
      // Process the job
      console.log(`Processing job ${job.id}:`, job.payload)
      await sendEmail(job.payload)

      // Mark complete
      await supabase
        .from('job_queue')
        .update({ status: 'completed', completed_at: new Date().toISOString() })
        .eq('id', job.id)
    } catch (err) {
      // Mark failed — pg_cron will retry if attempts < max_attempts
      await supabase
        .from('job_queue')
        .update({
          status: 'failed',
          error_message: err instanceof Error ? err.message : String(err)
        })
        .eq('id', job.id)
    }
  }
}

async function sendEmail(payload: Record<string, unknown>) {
  console.log('Sending email to:', payload.to)
}

processJobs().catch(console.error)
```

## SvelteKit Integration

```typescript
// src/hooks.server.ts — SvelteKit server hooks
import { createClient } from '@supabase/supabase-js'
import type { Handle } from '@sveltejs/kit'
import type { Database } from '@my-platform/supabase'

export const handle: Handle = async ({ event, resolve }) => {
  event.locals.supabase = createClient<Database>(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY,
    {
      global: {
        headers: { cookie: event.request.headers.get('cookie') ?? '' }
      }
    }
  )

  // Server-side admin client for privileged operations
  event.locals.supabaseAdmin = createClient<Database>(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.SUPABASE_SERVICE_ROLE_KEY,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  return resolve(event)
}
```
