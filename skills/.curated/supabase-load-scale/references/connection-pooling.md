# Read Replicas and Connection Pooling

Read replicas let you route read-heavy queries (dashboards, reports, search) to replica databases while keeping writes on the primary. Supabase uses **Supavisor** (their pgBouncer replacement) for connection pooling with two modes: **transaction** (default, shares connections between requests) and **session** (holds a connection per client session, needed for prepared statements).

## Configure the Read Replica Client

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

// Primary client — handles all writes and real-time subscriptions
export const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// Read replica client — use for analytics, dashboards, search
// The read replica URL is available in Dashboard > Settings > Database
export const supabaseReadOnly = createClient<Database>(
  process.env.SUPABASE_READ_REPLICA_URL!,  // e.g., https://<project-ref>-ro.supabase.co
  process.env.SUPABASE_ANON_KEY!,          // same anon key works for replicas
  {
    db: { schema: 'public' },
    // Replicas may have slight lag (typically <100ms)
    // Do NOT use for reads-after-writes in the same request
  }
)

// Server-side admin client with connection pooling via Supavisor
// Use the pooled connection string (port 6543) instead of direct (port 5432)
export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: { autoRefreshToken: false, persistSession: false },
    db: { schema: 'public' },
  }
)
```

## Direct Postgres Connections via Supavisor Pooling

```bash
# Transaction mode (default, port 6543) — best for serverless/short-lived connections
# Shares connections across clients. Cannot use prepared statements.
psql "postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Session mode (port 5432 via pooler) — needed for prepared statements, LISTEN/NOTIFY
# One-to-one connection mapping per client.
psql "postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

# Direct connection (no pooling) — for migrations and admin tasks only
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

## Route Queries to the Right Target

```typescript
// services/analytics.ts
import { supabaseReadOnly } from '../lib/supabase'

// Heavy analytics queries go to the read replica
export async function getDashboardMetrics(orgId: string) {
  const { data, error } = await supabaseReadOnly
    .from('events')
    .select('event_type, count:id.count()')
    .eq('org_id', orgId)
    .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())

  if (error) throw new Error(`Dashboard query failed: ${error.message}`)
  return data
}

// services/orders.ts
import { supabase } from '../lib/supabase'

// Writes always go to the primary
export async function createOrder(order: OrderInsert) {
  const { data, error } = await supabase
    .from('orders')
    .insert(order)
    .select('id, status, total, created_at')
    .single()

  if (error) throw new Error(`Order creation failed: ${error.message}`)
  return data
}
```

## Monitor Connection Pool Usage

```sql
-- Check active connections by source (run in SQL Editor)
SELECT
  usename,
  application_name,
  client_addr,
  state,
  count(*) AS connections
FROM pg_stat_activity
WHERE datname = 'postgres'
GROUP BY usename, application_name, client_addr, state
ORDER BY connections DESC;

-- Check connection limits for your compute tier
SHOW max_connections;
-- Micro: 60, Small: 90, Medium: 120, Large: 160, XL: 240, 2XL: 380, 4XL: 480
```
