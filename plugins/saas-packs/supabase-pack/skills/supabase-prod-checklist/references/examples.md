# Examples

### Next.js Production Client Setup

```typescript
// lib/supabase/client.ts — browser client (anon key only)
import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

```typescript
// lib/supabase/server.ts — server-side admin client
import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';

export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);
```

### Health Check Endpoint

```typescript
// app/api/health/route.ts
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export async function GET() {
  const start = Date.now();
  const { data, error } = await supabase
    .from('_health_check')
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

### Complete RLS Policy Set

```sql
-- Enable RLS on the posts table
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

-- Public read for published posts
CREATE POLICY "Public read published" ON public.posts
  FOR SELECT USING (status = 'published');

-- Authors read own drafts
CREATE POLICY "Authors read own drafts" ON public.posts
  FOR SELECT USING (auth.uid() = author_id AND status = 'draft');

-- Authors create posts
CREATE POLICY "Authors create posts" ON public.posts
  FOR INSERT WITH CHECK (auth.uid() = author_id);

-- Authors update own posts
CREATE POLICY "Authors update own posts" ON public.posts
  FOR UPDATE USING (auth.uid() = author_id)
  WITH CHECK (auth.uid() = author_id);

-- Authors delete own drafts only
CREATE POLICY "Authors delete own drafts" ON public.posts
  FOR DELETE USING (auth.uid() = author_id AND status = 'draft');
```

### Storage Bucket Policy

```sql
-- Allow authenticated users to upload to their own folder in avatars bucket
CREATE POLICY "Users upload own avatars"
  ON storage.objects
  FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow public read access to the public-assets bucket
CREATE POLICY "Public read assets"
  ON storage.objects
  FOR SELECT
  USING (bucket_id = 'public-assets');
```

### Edge Function with Secrets

```typescript
// supabase/functions/process-webhook/index.ts
import { createClient } from '@supabase/supabase-js';

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  const body = await req.json();

  const { error } = await supabase
    .from('webhook_events')
    .insert({ payload: body, received_at: new Date().toISOString() });

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

### Rollback Procedure

```bash
# 1. Create a rollback migration for a bad schema change
npx supabase migration new rollback_bad_change
# Edit the generated SQL file with reversal statements
npx supabase db push

# 2. For data issues — use Point-in-Time Recovery
# Dashboard > Database > Backups > PITR
# Select timestamp before the incident

# 3. For application deployment issues
# Vercel:  vercel rollback
# Netlify: netlify deploy --prod --dir=previous-build
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
