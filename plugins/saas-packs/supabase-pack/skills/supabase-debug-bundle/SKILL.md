---
name: supabase-debug-bundle
description: |
  Collect Supabase diagnostic info for troubleshooting and support tickets.
  Use when debugging connection failures, auth issues, Realtime drops, Storage
  errors, RLS misconfigurations, or preparing a support escalation.
  Trigger: "supabase debug", "supabase diagnostics", "supabase support bundle",
  "collect supabase logs", "debug supabase connection".
allowed-tools: Read, Bash(npx:*), Bash(node:*), Bash(curl:*), Bash(supabase:*), Bash(tar:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, support, diagnostics]
---

# Supabase Debug Bundle

Collect a comprehensive, redacted diagnostic bundle from a Supabase project. Tests connectivity, auth, Realtime, Storage, RLS policy behavior, and database health — then packages everything into a single archive safe for sharing with Supabase support.

## Current State

!`node --version 2>/dev/null || echo 'Node.js not found'`
!`npx supabase --version 2>/dev/null || echo 'Supabase CLI not found'`
!`npm list @supabase/supabase-js 2>/dev/null | grep supabase || echo '@supabase/supabase-js not installed'`

## Prerequisites

- **Node.js 18+** with `@supabase/supabase-js` v2 installed in the project
- **Supabase CLI** installed (`npm i -g supabase` or `npx supabase`)
- **Environment variables** set: `SUPABASE_URL` and `SUPABASE_ANON_KEY` (minimum); `SUPABASE_SERVICE_ROLE_KEY` for full diagnostics
- Project linked via `supabase link --project-ref <ref>` (for CLI commands)

## Instructions

### Step 1: Gather Environment and Connectivity

Collect SDK version, project URL, key type, and test basic connectivity against the REST and Auth endpoints.

```typescript
import { createClient } from '@supabase/supabase-js'

const url = process.env.SUPABASE_URL!
const anonKey = process.env.SUPABASE_ANON_KEY!
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

// Identify which key is in use
const keyType = serviceKey ? 'service_role' : 'anon'
const supabase = createClient(url, serviceKey ?? anonKey, {
  auth: { autoRefreshToken: false, persistSession: false }
})

const diagnostics: Record<string, unknown> = {}

// 1a — SDK + environment
diagnostics.environment = {
  supabase_js_version: require('@supabase/supabase-js/package.json').version,
  node_version: process.version,
  project_url: url.replace(/https:\/\/([^.]+)\..*/, 'https://$1.***'),
  key_type: keyType,
  timestamp: new Date().toISOString(),
}

// 1b — REST API connectivity
const restStart = Date.now()
const restRes = await fetch(`${url}/rest/v1/`, {
  headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
})
diagnostics.rest_api = {
  status: restRes.status,
  latency_ms: Date.now() - restStart,
  ok: restRes.ok,
}

// 1c — Auth health
const authStart = Date.now()
const { data: sessionData, error: sessionErr } = await supabase.auth.getSession()
diagnostics.auth = {
  status: sessionErr ? `error: ${sessionErr.message}` : 'ok',
  has_session: !!sessionData?.session,
  latency_ms: Date.now() - authStart,
}

// 1d — Database connectivity probe
const dbStart = Date.now()
const { error: dbErr } = await supabase.from('_test_ping').select('*').limit(1)
diagnostics.database = {
  // 42P01 = table doesn't exist, which proves the connection works
  status: (!dbErr || dbErr.code === '42P01') ? 'connected' : `error: ${dbErr.code}`,
  latency_ms: Date.now() - dbStart,
}

console.log(JSON.stringify(diagnostics, null, 2))
```

**What to check:** REST API should return `200`. Auth should return `ok`. Database probe returning `42P01` (relation not found) is normal — it confirms the PostgREST connection works.

### Step 2: Test Realtime, Storage, and RLS

Probe the three subsystems that cause the most support tickets.

```typescript
// 2a — Realtime subscription test
const realtimeResult = await new Promise<Record<string, unknown>>((resolve) => {
  const timeout = setTimeout(() => {
    resolve({ status: 'timeout', detail: 'No SUBSCRIBED event within 5s' })
  }, 5000)

  const channel = supabase.channel('debug-probe')
  channel.subscribe((status) => {
    if (status === 'SUBSCRIBED') {
      clearTimeout(timeout)
      channel.unsubscribe()
      resolve({ status: 'ok', detail: 'Channel subscribed successfully' })
    } else if (status === 'CHANNEL_ERROR') {
      clearTimeout(timeout)
      channel.unsubscribe()
      resolve({ status: 'error', detail: 'CHANNEL_ERROR on subscribe' })
    }
  })
})
diagnostics.realtime = realtimeResult

// 2b — Storage bucket listing
const { data: buckets, error: storageErr } = await supabase.storage.listBuckets()
diagnostics.storage = {
  status: storageErr ? `error: ${storageErr.message}` : 'ok',
  bucket_count: buckets?.length ?? 0,
  buckets: buckets?.map((b) => ({ name: b.name, public: b.public })) ?? [],
}

// 2c — RLS comparison: anon vs service_role
// Query the same table with both key types to detect RLS misconfiguration
if (serviceKey) {
  const anonClient = createClient(url, anonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
  // Pick the first public table from pg_tables (or fall back)
  const { data: tables } = await supabase
    .from('information_schema.tables' as any)
    .select('table_name')
    .eq('table_schema', 'public')
    .limit(1)

  const testTable = tables?.[0]?.table_name
  if (testTable) {
    const { count: anonCount } = await anonClient
      .from(testTable)
      .select('*', { count: 'exact', head: true })
    const { count: serviceCount } = await supabase
      .from(testTable)
      .select('*', { count: 'exact', head: true })
    diagnostics.rls = {
      table: testTable,
      anon_visible_rows: anonCount ?? 0,
      service_role_visible_rows: serviceCount ?? 0,
      rls_active: (anonCount ?? 0) !== (serviceCount ?? 0),
    }
  } else {
    diagnostics.rls = { status: 'skipped', detail: 'No public tables found' }
  }
} else {
  diagnostics.rls = { status: 'skipped', detail: 'No service_role key — cannot compare' }
}
```

**What to check:** Realtime should reach `SUBSCRIBED` within 5 seconds. Storage should list buckets without error. RLS comparison showing identical row counts for anon and service_role on a table you expect to be protected means RLS policies may be missing.

### Step 3: Collect Database Health and Package the Bundle

Pull database statistics via the Supabase CLI inspect commands and the platform status page, then archive everything.

```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="supabase-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

# 3a — Supabase CLI status (local dev)
npx supabase status > "$BUNDLE_DIR/cli-status.txt" 2>&1 || echo "CLI status unavailable (not linked or no local dev)" > "$BUNDLE_DIR/cli-status.txt"

# 3b — Database inspection via CLI
npx supabase inspect db table-sizes   > "$BUNDLE_DIR/table-sizes.txt"   2>&1 || true
npx supabase inspect db index-usage   > "$BUNDLE_DIR/index-usage.txt"   2>&1 || true
npx supabase inspect db cache-hit     > "$BUNDLE_DIR/cache-hit.txt"     2>&1 || true
npx supabase inspect db seq-scans     > "$BUNDLE_DIR/seq-scans.txt"     2>&1 || true
npx supabase inspect db long-running-queries > "$BUNDLE_DIR/long-queries.txt" 2>&1 || true
npx supabase inspect db bloat         > "$BUNDLE_DIR/bloat.txt"         2>&1 || true
npx supabase inspect db replication-slots > "$BUNDLE_DIR/replication.txt" 2>&1 || true

# 3c — Platform status page
curl -sf https://status.supabase.com/api/v2/status.json \
  | python3 -m json.tool > "$BUNDLE_DIR/platform-status.json" 2>/dev/null \
  || echo '{"error": "Could not reach status.supabase.com"}' > "$BUNDLE_DIR/platform-status.json"

# 3d — Redact secrets from all collected files
find "$BUNDLE_DIR" -type f -exec sed -i \
  -e 's/eyJ[A-Za-z0-9_-]\{20,\}\(\.[A-Za-z0-9_-]*\)*/[JWT_REDACTED]/g' \
  -e 's/sbp_[A-Za-z0-9]\{20,\}/[SBP_KEY_REDACTED]/g' \
  -e 's/[A-Za-z0-9._%+-]\+@[A-Za-z0-9.-]\+\.[A-Za-z]\{2,\}/[EMAIL_REDACTED]/g' {} +

# 3e — Package
tar czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
echo "Debug bundle created: ${BUNDLE_DIR}.tar.gz"
echo "Contents:"
ls -lh "$BUNDLE_DIR"/
```

**What to check:** Review `cache-hit.txt` — index and table hit rates below 99% indicate memory pressure. `bloat.txt` values above 50% on large tables warrant a `VACUUM`. `seq-scans.txt` highlights tables needing indexes.

## Output

The skill produces `supabase-debug-YYYYMMDD-HHMMSS.tar.gz` containing:

| File | Contents |
|------|----------|
| `cli-status.txt` | Local Supabase stack status (services, ports, URLs) |
| `table-sizes.txt` | All tables with row counts and disk usage |
| `index-usage.txt` | Index scan frequency — unused indexes are candidates for removal |
| `cache-hit.txt` | Buffer cache and index cache hit ratios |
| `seq-scans.txt` | Tables with high sequential scan counts (missing indexes) |
| `long-queries.txt` | Currently running queries over the duration threshold |
| `bloat.txt` | Table and index bloat percentages |
| `replication.txt` | Replication slot status (relevant for Realtime) |
| `platform-status.json` | Supabase platform health from status.supabase.com |

Plus the TypeScript diagnostics output (connectivity, auth, Realtime, Storage, RLS) printed to stdout.

All JWT tokens, Supabase project keys (`sbp_*`), and email addresses are automatically redacted before archiving.

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| REST API returns `401` | Invalid or expired `anon` key | Regenerate key in Dashboard > Settings > API |
| REST API returns `000` or times out | Wrong `SUPABASE_URL` or project paused | Verify URL; unpause project in Dashboard |
| Realtime returns `CHANNEL_ERROR` | WebSocket blocked by firewall/proxy | Check corporate proxy; try from a different network |
| Realtime times out (5s) | Realtime addon not enabled or quota hit | Enable Realtime on the table in Dashboard > Database > Replication |
| Storage `listBuckets` returns `403` | RLS enabled on storage without policy | Add a storage policy or use `service_role` key |
| `supabase inspect db` fails | CLI not linked to remote project | Run `supabase link --project-ref <ref>` first |
| `cache-hit` below 95% | Database instance too small for workload | Upgrade compute size or optimize queries |
| RLS shows identical counts | No RLS policies on the table | Add policies via `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` |
| `pg_stat_statements` not available | Extension not enabled | Enable in Dashboard > Database > Extensions |

## Examples

**Quick connectivity check (no service key needed):**

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!)

const start = Date.now()
const { error } = await supabase.from('any_table').select('*').limit(1)
console.log({
  connected: !error || error.code === '42P01',
  latency_ms: Date.now() - start,
  error: error?.message ?? null,
})
```

**API endpoint test with curl:**

```bash
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  "https://<project-ref>.supabase.co/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY"
```

**Check auth session from a running app:**

```typescript
const { data, error } = await supabase.auth.getSession()
if (error) console.error('Auth error:', error.message)
else if (!data.session) console.log('No active session (user not logged in)')
else console.log('Session valid, expires:', data.session.expires_at)
```

## Resources

- [Supabase Troubleshooting Guide](https://supabase.com/docs/guides/platform/troubleshooting) — official first-stop for common issues
- [Database Inspect (CLI)](https://supabase.com/docs/guides/database/inspect) — `supabase inspect db` command reference
- [Supabase Status Page](https://status.supabase.com) — live platform health
- [Supabase Support](https://supabase.com/support) — file a ticket with your debug bundle attached
- [RLS Guide](https://supabase.com/docs/guides/database/postgres/row-level-security) — row-level security policy authoring
- [Realtime Quotas](https://supabase.com/docs/guides/realtime/quotas) — connection and message limits

## Next Steps

- Run `supabase-common-errors` to match diagnostic output against known issue patterns
- Run `supabase-rate-limits` if the bundle reveals 429 responses or throttled connections
- Run `supabase-performance-tuning` if cache hit ratios are below 99% or sequential scans are high
- Run `supabase-observability` to set up ongoing monitoring so issues surface before they become tickets
