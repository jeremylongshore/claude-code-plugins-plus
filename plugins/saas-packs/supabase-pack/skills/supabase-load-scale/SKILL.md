---
name: supabase-load-scale
description: |
  Implement Supabase load testing with k6, connection pool sizing,
  read replicas, and capacity planning for production scale.
  Use when running load tests, planning for high traffic,
  or configuring Supabase for horizontal scaling.
  Trigger with phrases like "supabase load test", "supabase scale",
  "supabase performance test", "supabase capacity", "supabase k6", "supabase benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, load-testing, scaling]

---
# Supabase Load & Scale

## Overview
Load test your Supabase integration, size connection pools correctly, configure read replicas, and build capacity plans based on empirical data. Uses k6 for realistic traffic simulation.

## Prerequisites
- k6 installed (`brew install k6` or `npm install -g k6`)
- Supabase staging project (never load test production directly)
- Baseline performance metrics available

## Instructions

### Step 1: k6 Load Test Script

```javascript
// tests/load/supabase-load.js
import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate } from 'k6/metrics'

const errorRate = new Rate('errors')

const SUPABASE_URL = __ENV.SUPABASE_URL
const SUPABASE_ANON_KEY = __ENV.SUPABASE_ANON_KEY

const headers = {
  'Content-Type': 'application/json',
  'apikey': SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
}

// Traffic profile: ramp up → sustained → spike → cool down
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // ramp up
    { duration: '3m', target: 50 },   // sustained load
    { duration: '30s', target: 100 }, // spike
    { duration: '1m', target: 50 },   // back to sustained
    { duration: '30s', target: 0 },   // cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // P95 < 500ms, P99 < 1s
    errors: ['rate<0.01'],                             // Error rate < 1%
  },
}

export default function () {
  // Scenario 1: Read operation (80% of traffic)
  if (Math.random() < 0.8) {
    const res = http.get(
      `${SUPABASE_URL}/rest/v1/todos?select=id,title,is_complete&limit=20`,
      { headers }
    )
    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    })
    errorRate.add(res.status !== 200)
  }
  // Scenario 2: Write operation (20% of traffic)
  else {
    const res = http.post(
      `${SUPABASE_URL}/rest/v1/todos`,
      JSON.stringify({ title: `Load test ${Date.now()}`, is_complete: false }),
      { headers: { ...headers, 'Prefer': 'return=minimal' } }
    )
    check(res, {
      'status is 201': (r) => r.status === 201,
    })
    errorRate.add(res.status !== 201)
  }

  sleep(0.5 + Math.random() * 1.5)  // 0.5-2s think time
}
```

```bash
# Run the load test
k6 run tests/load/supabase-load.js \
  -e SUPABASE_URL=https://staging-ref.supabase.co \
  -e SUPABASE_ANON_KEY=eyJ...

# Output to JSON for analysis
k6 run --out json=results.json tests/load/supabase-load.js
```

### Step 2: Monitor During Load Test

```sql
-- Run these queries during the load test to identify bottlenecks

-- Active connections (refresh every 10s)
select state, count(*) from pg_stat_activity
where datname = current_database()
group by state;

-- Queries per second estimate
select sum(calls) / extract(epoch from now() - stats_reset) as qps
from pg_stat_statements, pg_stat_statements_info;

-- Cache hit ratio during load
select
  sum(heap_blks_hit) * 100.0 / nullif(sum(heap_blks_hit + heap_blks_read), 0) as cache_ratio
from pg_statio_user_tables;

-- Lock waits during load
select count(*) as blocked_queries
from pg_stat_activity
where wait_event_type = 'Lock';
```

### Step 3: Connection Pool Sizing

```
Supabase connection limits by plan:

| Plan   | Direct | Pooled (Supavisor) |
|--------|--------|--------------------|
| Free   | 60     | 200                |
| Pro    | 60     | 200                |
| Team   | 120    | 400                |

Formula: max_app_connections = pooled_limit / num_instances

Example: Pro plan with 4 serverless instances
- Use pooled connection string (port 6543)
- Each instance: max 50 connections (200 / 4)
- Set application pool to max: 10 per instance (leave headroom)
```

```typescript
// Configure Prisma for Supabase with proper pool sizing
// prisma/schema.prisma
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")        // pooled connection string
  directUrl = env("DIRECT_DATABASE_URL")  // for migrations only
}
```

### Step 4: Read Replicas (Pro Plan)

```typescript
// Configure read replica for read-heavy workloads
// Dashboard > Database > Read Replicas

// Use the read replica for analytics and reporting queries
const supabaseReplica = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!,
  {
    db: {
      schema: 'public',
    },
    // Read replica connection for specific use cases
    // Configure at the database driver level
  }
)

// Pattern: route reads to replica, writes to primary
async function getAnalyticsData() {
  // Use read replica for heavy analytics queries
  // These don't need real-time consistency
  return supabaseReplica.from('analytics_events')
    .select('event_type, count')
    .gte('created_at', '2024-01-01')
}
```

### Step 5: Capacity Planning Template

```markdown
## Capacity Plan: [Project Name]

### Current Metrics
- Database size: X GB
- Daily active users: X,000
- Peak requests/sec: X
- Average query latency P95: X ms

### Growth Projections (6 months)
- Expected DAU: X,000 → Y,000
- Expected data growth: X GB → Y GB
- Expected peak RPS: X → Y

### Resource Requirements
| Resource | Current | 6-Month | Plan |
|----------|---------|---------|------|
| Database | X GB | Y GB | Pro (8 GB included) |
| Connections | X | Y | Pooled via Supavisor |
| Storage | X GB | Y GB | Pro (100 GB included) |
| Bandwidth | X GB/mo | Y GB/mo | Monitor |
| Edge Functions | X invocations | Y | Pro (2M included) |

### Scaling Actions
1. At Y DAU: upgrade compute size
2. At Z GB database: enable read replica
3. At W RPS: add connection pooling
```

## Output
- k6 load test script modeling realistic traffic patterns
- Load test results with P95, P99 latency and error rates
- Connection pool sized correctly for deployment topology
- Read replica configured for heavy read workloads
- Capacity plan projecting resource needs over 6 months

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout under load | Pool exhausted | Use pooled connection string; reduce per-instance pool |
| P95 latency spike | Missing index or lock contention | Run `explain analyze` on slow queries; check locks |
| Error rate > 1% | Rate limiting or RLS | Check for 429s (rate limit) or 403s (RLS) |
| k6 `dial: too many open files` | OS file descriptor limit | `ulimit -n 10240` before running k6 |

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Supabase Compute Add-ons](https://supabase.com/docs/guides/platform/compute-add-ons)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Read Replicas](https://supabase.com/docs/guides/platform/read-replicas)

## Next Steps
For reliability patterns, see `supabase-reliability-patterns`.
