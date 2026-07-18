## Examples

### One-Line Health Check

```bash
curl -sf https://api.yourapp.com/health | jq '.services.supabase.status' || echo "UNHEALTHY"
```

### Example 1 — Quick triage script

```typescript
import { createClient } from '@supabase/supabase-js';

async function triageSupabase() {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // 1. Database connectivity
  const { error: dbError } = await supabase.from('_health_check').select('id').limit(1);
  console.log('Database:', dbError ? `ERROR: ${dbError.message}` : 'OK');

  // 2. Auth service
  const { data: authData, error: authError } = await supabase.auth.getSession();
  console.log('Auth service:', authError ? `ERROR: ${authError.message}` : 'OK');

  // 3. Storage service
  const { error: storageError } = await supabase.storage.listBuckets();
  console.log('Storage:', storageError ? `ERROR: ${storageError.message}` : 'OK');

  // 4. Realtime service
  const channel = supabase.channel('health');
  channel.subscribe((status) => {
    console.log('Realtime:', status);
    channel.unsubscribe();
  });
}
```

### Example 2 — Connection leak detector

```sql
-- Run this during an incident to find leaked connections
WITH connection_summary AS (
  SELECT usename, state,
         count(*) AS conn_count,
         max(age(now(), state_change)) AS max_age
  FROM pg_stat_activity
  WHERE datname = current_database()
  GROUP BY usename, state
)
SELECT usename, state, conn_count,
       max_age::text AS max_idle_time,
       CASE
         WHEN state = 'idle in transaction' THEN 'LEAK - kill these'
         WHEN state = 'idle' AND max_age > interval '10 minutes' THEN 'STALE - review'
         ELSE 'OK'
       END AS assessment
FROM connection_summary
ORDER BY conn_count DESC;
```

### Example 3 — Escalation evidence bundle

```typescript
import { createClient } from '@supabase/supabase-js';

async function buildEvidenceBundle() {
  const supabase = createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const evidence = {
    timestamp: new Date().toISOString(),
    projectRef: process.env.SUPABASE_PROJECT_REF,
    symptoms: [],
    diagnostics: {},
  };

  // Collect connection stats
  const { data: connStats } = await supabase.rpc('get_connection_stats');
  evidence.diagnostics['connections'] = connStats;

  // Collect recent errors from your error tracking
  evidence.symptoms.push('Describe the user-facing symptoms here');

  // Include request IDs from failed API calls
  // The x-request-id header from Supabase responses identifies specific requests

  console.log('Evidence bundle for Supabase support:');
  console.log(JSON.stringify(evidence, null, 2));
  // Submit at:
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
