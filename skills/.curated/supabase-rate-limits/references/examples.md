# Examples

## Example 1 — Serverless Edge Function with rate-limit-safe client

```typescript
// supabase/functions/process-webhook/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const payload = await req.json()

  // Batch insert webhook events (single request vs N)
  const { error } = await supabase
    .from('webhook_events')
    .insert(payload.events.map((e: any) => ({
      type: e.type,
      data: e.data,
      received_at: new Date().toISOString(),
    })))

  if (error) {
    console.error('Insert failed:', error.message)
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify({ processed: payload.events.length }), { status: 200 })
})
```

## Example 2 — Connection string selection for different runtimes

```bash
# Serverless (Vercel, Netlify, Edge Functions) — transaction mode, port 6543
DATABASE_URL="postgresql://postgres.abc123:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# Long-running server (Express, Fastify) — session mode, port 5432
DATABASE_URL="postgresql://postgres.abc123:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

# Direct connection (migrations, schema changes only), port 5432
DATABASE_URL="postgresql://postgres:password@db.abc123.supabase.co:5432/postgres"
```

## Example 3 — Queue-based rate limiting

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation);
}
```

## Example 4 — Monitor rate-limit headers client-side

```typescript
class RateLimitMonitor {
  private remaining: number = 60;
  private resetAt: Date = new Date();

  updateFromHeaders(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
    const resetTimestamp = headers.get('X-RateLimit-Reset');
    if (resetTimestamp) {
      this.resetAt = new Date(parseInt(resetTimestamp) * 1000);
    }
  }

  shouldThrottle(): boolean {
    // Only throttle if low remaining AND reset hasn't happened yet
    return this.remaining < 5 && new Date() < this.resetAt;
  }

  getWaitTime(): number {
    return Math.max(0, this.resetAt.getTime() - Date.now());
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
