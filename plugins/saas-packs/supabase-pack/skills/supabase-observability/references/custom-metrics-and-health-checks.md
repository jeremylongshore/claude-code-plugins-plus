# Custom Metrics, Alerting, and Health Checks

## Custom Metrics via Edge Functions

Emit structured events for business-level monitoring:

```typescript
// supabase/functions/collect-metrics/index.ts
import { createClient } from '@supabase/supabase-js';
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  // Collect quota-relevant metrics
  const { count: userCount } = await supabase
    .from('profiles')
    .select('*', { count: 'exact', head: true });

  const { count: storageObjects } = await supabase
    .storage.from('uploads')
    .list('', { limit: 1, offset: 0 })
    .then(({ data }) => ({ count: data?.length ?? 0 }));

  const { data: dbSize } = await supabase
    .rpc('get_database_size');

  const metrics = {
    timestamp: new Date().toISOString(),
    user_count: userCount,
    db_size_mb: dbSize,
    storage_objects: storageObjects,
  };

  // Store metrics for trend analysis
  await supabase.from('app_metrics').insert(metrics);

  // Alert on quota thresholds
  const DB_LIMIT_MB = 8000; // 8GB Pro plan limit
  if (dbSize > DB_LIMIT_MB * 0.85) {
    console.warn(`[QUOTA_ALERT] Database at ${Math.round(dbSize / DB_LIMIT_MB * 100)}% capacity`);
    // Send alert via webhook, email, or Slack
  }

  return new Response(JSON.stringify(metrics), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

Schedule it with a cron trigger in `supabase/config.toml`:

```toml
[functions.collect-metrics]
schedule = "*/15 * * * *"  # Every 15 minutes
```

## Health Check Endpoint

For uptime monitoring (Uptime Robot, Pingdom, etc.):

```typescript
// supabase/functions/health/index.ts
import { createClient } from '@supabase/supabase-js';
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  const checks: Record<string, { status: string; latency_ms: number; detail?: string }> = {};

  // Database check
  const dbStart = Date.now();
  const { error: dbErr } = await supabase.rpc('version');
  checks.database = {
    status: dbErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - dbStart,
    ...(dbErr && { detail: dbErr.message }),
  };

  // Auth check
  const authStart = Date.now();
  const { error: authErr } = await supabase.auth.admin.listUsers({ perPage: 1 });
  checks.auth = {
    status: authErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - authStart,
  };

  // Storage check
  const storageStart = Date.now();
  const { error: storageErr } = await supabase.storage.listBuckets();
  checks.storage = {
    status: storageErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - storageStart,
  };

  const overall = Object.values(checks).every(c => c.status === 'healthy');
  const statusCode = overall ? 200 : 503;

  return new Response(
    JSON.stringify({ status: overall ? 'healthy' : 'degraded', checks, timestamp: new Date().toISOString() }),
    { status: statusCode, headers: { 'Content-Type': 'application/json' } }
  );
});
```

## Real-time Connection Monitoring

Track active Realtime connections:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Monitor channel state changes
const channel = supabase.channel('monitoring');

channel
  .on('system', { event: '*' }, (payload) => {
    console.log(`[REALTIME] System event:`, payload);
  })
  .subscribe((status) => {
    console.log(`[REALTIME] Connection status: ${status}`);
    if (status === 'CHANNEL_ERROR') {
      console.error('[REALTIME] Connection lost — will auto-reconnect');
    }
  });
```
