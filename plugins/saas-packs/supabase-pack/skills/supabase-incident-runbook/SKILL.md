---
name: supabase-incident-runbook
description: |
  Execute Supabase incident response: triage, platform vs. application isolation,
  mitigation, and postmortem procedures.
  Use when responding to Supabase outages, investigating errors,
  or running post-incident reviews.
  Trigger with phrases like "supabase incident", "supabase outage",
  "supabase down", "supabase on-call", "supabase emergency", "supabase broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, incident-response]

---
# Supabase Incident Runbook

## Overview
Step-by-step incident response for Supabase-related outages. Quickly determine if the issue is platform-side (Supabase infrastructure) or application-side (your code/config), apply mitigation, communicate status, and run a postmortem.

## Prerequisites
- Access to Supabase Dashboard and logs
- Supabase CLI installed
- Access to application monitoring

## Instructions

### Step 1: Quick Triage (First 5 Minutes)

```bash
# 1. Check Supabase platform status
curl -s https://status.supabase.com/api/v2/status.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'Status: {d[\"status\"][\"description\"]}')
print(f'Indicator: {d[\"status\"][\"indicator\"]}')
"

# 2. Check your project health
curl -s -o /dev/null -w "HTTP %{http_code}, %{time_total}s\n" \
  "https://<project-ref>.supabase.co/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY"

# 3. Test database connectivity
supabase db query "SELECT 1 as health_check" --linked 2>&1 || echo "DB unreachable"
```

### Step 2: Decision Tree

```
Is status.supabase.com reporting an incident?
├── YES → Platform issue
│   ├── Monitor status page for updates
│   ├── Enable circuit breaker / fallback mode
│   └── Communicate to users: "Service provider experiencing issues"
│
└── NO → Application issue
    ├── Check recent deployments (git log --oneline -5)
    ├── Check recent migration changes
    ├── Review application error logs
    └── Continue to Step 3
```

### Step 3: Diagnose Application Issues

```sql
-- Check for connection exhaustion
select state, count(*)
from pg_stat_activity
where datname = current_database()
group by state;
-- If "active" count is near your pool limit, you have a connection leak

-- Check for long-running queries
select pid, age(now(), query_start) as duration, query
from pg_stat_activity
where state = 'active' and query_start < now() - interval '30 seconds'
order by query_start;

-- Kill a stuck query if needed
-- select pg_cancel_backend(<pid>);

-- Check for lock contention
select blocked.pid as blocked_pid,
       blocked.query as blocked_query,
       blocking.pid as blocking_pid,
       blocking.query as blocking_query
from pg_stat_activity blocked
join pg_locks bl on bl.pid = blocked.pid
join pg_locks kl on kl.locktype = bl.locktype
  and kl.relation = bl.relation
  and kl.pid != bl.pid
join pg_stat_activity blocking on blocking.pid = kl.pid
where not bl.granted;
```

### Step 4: Common Incident Scenarios

**Scenario: All API requests returning 401**
```
Root cause: JWT expired or key rotated
Fix: Check SUPABASE_ANON_KEY matches Dashboard > Settings > API
     Restart application to pick up new env vars
```

**Scenario: Database connection timeout**
```
Root cause: Connection pool exhausted
Fix: Switch to pooled connection string (port 6543 via Supavisor)
     Kill long-running queries
     Restart application to release stale connections
```

**Scenario: RLS suddenly blocking all requests**
```
Root cause: Migration added restrictive policy or disabled a permissive one
Fix: Check recent migrations for policy changes
     Verify with service role key (bypasses RLS)
     Roll back the problematic migration if needed
```

**Scenario: Realtime subscriptions not receiving events**
```
Root cause: Table not in the supabase_realtime publication
Fix: Dashboard > Database > Replication > enable table
     Or: ALTER PUBLICATION supabase_realtime ADD TABLE public.your_table;
```

**Scenario: Storage uploads failing with 413**
```
Root cause: File exceeds bucket size limit
Fix: Increase bucket file_size_limit in Dashboard > Storage
     Or: use TUS resumable uploads for large files
```

### Step 5: Mitigation Actions

```typescript
// Enable graceful degradation mode
const CIRCUIT_OPEN = process.env.SUPABASE_CIRCUIT_OPEN === 'true'

async function fetchWithFallback<T>(
  primary: () => Promise<T>,
  fallback: T
): Promise<T> {
  if (CIRCUIT_OPEN) {
    console.warn('[CIRCUIT_OPEN] Returning fallback response')
    return fallback
  }

  try {
    return await primary()
  } catch (err) {
    console.error('[SUPABASE_DOWN] Using fallback:', err)
    return fallback
  }
}

// Usage during incident
const todos = await fetchWithFallback(
  () => TodoService.list({ userId }),
  []  // return empty list during outage
)
```

### Step 6: Communication Template

```
Subject: [INCIDENT] Supabase connectivity degraded

Status: Investigating / Identified / Mitigated / Resolved
Impact: [Description of user-facing impact]
Start time: YYYY-MM-DDTHH:MM:SSZ
Current time: YYYY-MM-DDTHH:MM:SSZ

Root cause: [Brief description or "under investigation"]
Mitigation: [What we're doing to reduce impact]
ETA to resolution: [Estimate or "unknown"]

Next update: [Time of next update]
```

### Step 7: Postmortem Template

```markdown
## Incident Postmortem: [Title]

**Date**: YYYY-MM-DD
**Duration**: X hours Y minutes
**Severity**: P1/P2/P3
**Impact**: [Users affected, operations disrupted]

### Timeline
- HH:MM - Issue detected via [monitoring/user report]
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Full resolution confirmed

### Root Cause
[Detailed technical explanation]

### Action Items
- [ ] [Preventive action 1] — Owner: [name] — Due: [date]
- [ ] [Preventive action 2] — Owner: [name] — Due: [date]
```

## Output
- Platform vs. application issue identified within 5 minutes
- Root cause determined with diagnostic queries
- Mitigation applied (circuit breaker, fallback, connection cleanup)
- Stakeholders notified with structured updates
- Postmortem completed with preventive action items

## Resources
- [Supabase Status Page](https://status.supabase.com)
- [Supabase Support](https://supabase.com/support)
- [Database Health Monitoring](https://supabase.com/docs/guides/database/inspect)

## Next Steps
For data compliance, see `supabase-data-handling`.
