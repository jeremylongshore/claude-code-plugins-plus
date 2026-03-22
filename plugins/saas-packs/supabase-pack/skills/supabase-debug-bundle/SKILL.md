---
name: supabase-debug-bundle
description: |
  Collect Supabase debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support escalations,
  or gathering diagnostic data from a Supabase project.
  Trigger with phrases like "supabase debug", "supabase support bundle",
  "collect supabase logs", "supabase diagnostic", "supabase support ticket".
allowed-tools: Read, Bash(supabase:*), Bash(curl:*), Bash(node:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, support]

---
# Supabase Debug Bundle

## Overview
Collect a comprehensive, redacted debug bundle for Supabase support tickets. Gathers environment info, SDK versions, connection status, recent logs, and database health metrics into a single archive.

## Current State
!`node --version 2>/dev/null || echo 'Node.js not found'`
!`supabase --version 2>/dev/null || echo 'Supabase CLI not found'`
!`npm list @supabase/supabase-js 2>/dev/null | grep supabase || echo '@supabase/supabase-js not installed'`

## Prerequisites
- Supabase CLI installed and project linked
- Access to application logs
- Permission to query database health views

## Instructions

### Step 1: Gather Environment Info

```bash
#!/bin/bash
set -euo pipefail
BUNDLE_DIR="supabase-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

# Environment summary
cat > "$BUNDLE_DIR/environment.txt" << EOF
Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Node: $(node --version 2>/dev/null || echo 'N/A')
OS: $(uname -a)
Supabase CLI: $(supabase --version 2>/dev/null || echo 'N/A')
SDK Version: $(npm list @supabase/supabase-js 2>/dev/null | grep supabase || echo 'N/A')
Docker: $(docker --version 2>/dev/null || echo 'N/A')
EOF
```

### Step 2: Check Project Status

```bash
# Project status (local)
supabase status > "$BUNDLE_DIR/supabase-status.txt" 2>&1 || true

# Check Supabase platform status
curl -s https://status.supabase.com/api/v2/status.json \
  | python3 -m json.tool > "$BUNDLE_DIR/platform-status.json" 2>/dev/null || true
```

### Step 3: Collect Database Health

```sql
-- Run in Supabase SQL Editor or via supabase db query

-- Active connections
select count(*) as active_connections,
       state,
       wait_event_type
from pg_stat_activity
group by state, wait_event_type;

-- Slow queries (top 10)
select query,
       calls,
       mean_exec_time::numeric(10,2) as avg_ms,
       total_exec_time::numeric(10,2) as total_ms
from pg_stat_statements
order by mean_exec_time desc
limit 10;

-- Table sizes
select relname as table_name,
       pg_size_pretty(pg_total_relation_size(relid)) as total_size,
       n_live_tup as live_rows,
       n_dead_tup as dead_rows
from pg_stat_user_tables
order by pg_total_relation_size(relid) desc
limit 20;

-- Index usage
select schemaname, relname as table_name, indexrelname as index_name,
       idx_scan as scans, idx_tup_read as tuples_read
from pg_stat_user_indexes
order by idx_scan asc
limit 10;  -- least-used indexes

-- RLS policies on all tables
select tablename, policyname, cmd, qual
from pg_policies
where schemaname = 'public'
order by tablename;
```

### Step 4: Collect Application Logs (Redacted)

```typescript
// scripts/collect-debug-logs.ts
import { createClient } from '@supabase/supabase-js'
import { writeFileSync } from 'fs'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

async function collectDebugInfo() {
  const results: Record<string, any> = {}

  // Test connectivity
  const start = Date.now()
  const { error } = await supabase.from('_health_check').select('*').limit(1)
  results.connectivity = {
    latency_ms: Date.now() - start,
    status: error ? `error: ${error.code}` : 'ok',
  }

  // Auth health
  const { data: { user } } = await supabase.auth.getUser()
  results.auth = { user_id: user?.id ? '[REDACTED]' : 'none' }

  // Storage buckets
  const { data: buckets } = await supabase.storage.listBuckets()
  results.storage = {
    bucket_count: buckets?.length ?? 0,
    buckets: buckets?.map(b => ({ name: b.name, public: b.public })),
  }

  // Redact any secrets
  const output = JSON.stringify(results, null, 2)
    .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[JWT_REDACTED]')
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL_REDACTED]')

  writeFileSync('supabase-debug-app.json', output)
  console.log('Debug info collected and redacted')
}

collectDebugInfo()
```

### Step 5: Package the Bundle

```bash
# Archive everything
tar czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: ${BUNDLE_DIR}.tar.gz"

# Verify no secrets leaked
if grep -rqE 'eyJ[A-Za-z0-9_-]{20,}' "$BUNDLE_DIR/"; then
  echo "WARNING: Possible JWT tokens found in bundle. Review before sharing."
fi
```

## Output
- `supabase-debug-<timestamp>.tar.gz` archive containing:
  - `environment.txt` - Node, CLI, OS, SDK versions
  - `supabase-status.txt` - Local project status
  - `platform-status.json` - Supabase platform health
  - Database health queries (connections, slow queries, table sizes)
  - `supabase-debug-app.json` - Redacted application diagnostics

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `supabase status` fails | Not in a Supabase project dir | Run from project root with `supabase/` dir |
| `pg_stat_statements` empty | Extension not enabled | Enable via Dashboard > Database > Extensions |
| Permission denied on logs | Service role key not set | Use `SUPABASE_SERVICE_ROLE_KEY` for admin queries |

## Resources
- [Supabase Support](https://supabase.com/support)
- [Supabase Status Page](https://status.supabase.com)
- [Performance Advisor](https://supabase.com/docs/guides/database/inspect)

## Next Steps
For rate-limit-specific issues, see `supabase-rate-limits`.
