---
name: supabase-cost-tuning
description: 'Optimize Supabase costs through plan selection, database tuning, storage
  cleanup,

  connection pooling, and Edge Function optimization.

  Use when analyzing Supabase billing, reducing costs, right-sizing compute,

  or implementing usage tracking and budget alerts.

  Trigger with phrases like "supabase cost", "supabase billing",

  "reduce supabase costs", "supabase pricing", "supabase expensive", "supabase budget".

  '
allowed-tools: Read, Write, Edit, Grep, Bash(supabase:*)
version: 1.53.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- cost-optimization
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Supabase Cost Tuning

## Overview

Reduce Supabase spend by auditing usage against plan limits, eliminating database and storage waste, and right-sizing compute resources. The three biggest levers: database optimization (vacuum, index cleanup, archival), storage lifecycle management (compress before upload, orphan cleanup), and connection pooling to reduce compute add-on requirements.

Work the three steps below in order — audit first to find where the money goes, then optimize the biggest offenders, then right-size compute. Each step keeps a representative snippet inline; the full query and script sets live in `references/` so this file stays scannable.

## Prerequisites

- Supabase project with Dashboard access (Settings > Billing)
- `@supabase/supabase-js` installed: `npm install @supabase/supabase-js`
- Service role key for admin operations (storage audit, cleanup scripts)
- SQL editor access (Dashboard > SQL Editor or `psql` connection)

## Pricing Reference

| Resource | Free Tier | Pro ($25/mo) | Team ($599/mo) |
| ---------- | ----------- | -------------- | ---------------- |
| Database | 500 MB | 8 GB included, $0.125/GB extra | 8 GB included |
| Storage | 1 GB | 100 GB included, $0.021/GB extra | 100 GB included |
| Bandwidth | 5 GB | 250 GB included, $0.09/GB extra | 250 GB included |
| Edge Functions | 500K invocations | 2M invocations, $2/million extra | 2M invocations |
| Realtime | 200 concurrent | 500 concurrent | 500 concurrent |
| Auth MAU | 50,000 | 100,000 | 100,000 |

**Compute add-ons** (Pro and above):

| Instance | vCPUs | RAM | Price |
| ---------- | ------- | ----- | ------- |
| Micro | 2 | 1 GB | Included with Pro |
| Small | 2 | 2 GB | $25/mo |
| Medium | 2 | 4 GB | $50/mo |
| Large | 4 | 8 GB | $100/mo |
| XL | 8 | 16 GB | $200/mo |
| 2XL | 16 | 32 GB | $400/mo |

**Decision framework:** Read replicas ($25/mo each) beat scaling up when reads dominate and geographic distribution is needed. Connection pooling (Supavisor, free) reduces compute pressure from idle connections.

## Instructions

### Step 1: Audit current usage and identify cost drivers

Find where the database budget is going before changing anything. Run the audit queries in the SQL Editor to surface the biggest tables, unused indexes, dead-tuple bloat, and connection count. Start with total size:

```sql
select pg_size_pretty(pg_database_size(current_database())) as total_db_size;
```

Then audit storage per bucket with a service-role client, and read current spend under **Dashboard > Settings > Billing**. See [full audit queries and storage script](references/audit-queries.md) for the complete SQL set (table sizes, zero-scan indexes, dead-tuple ratio, connection count) and the per-bucket usage script.

### Step 2: Optimize database, storage, and bandwidth

Attack the biggest offenders from Step 1. Archive old rows before deleting, then VACUUM ANALYZE to reclaim space and refresh planner stats:

```sql
vacuum (verbose, analyze) public.events;
```

For storage, compress images client-side before upload and schedule an orphan-cleanup job. For bandwidth, replace `select('*')` with explicit column lists, use `head: true` count queries for totals, and paginate with `.range()`. See [full optimization code](references/optimization.md) for the archival + VACUUM SQL, the compress/clean-orphans scripts, and the bandwidth-reduction patterns.

### Step 3: Right-size compute and reduce Edge Function costs

Prefer pooling and code fixes over a compute upgrade. Route direct `pg` connections (migrations, ORMs) through the Supavisor pooler URL instead of scaling the instance:

```typescript
// Direct:   postgresql://postgres:pw@db.xxx.supabase.co:5432/postgres
// Pooled:   postgresql://postgres:pw@db.xxx.supabase.co:6543/postgres
```

Cut Edge Function cost by keeping imports lightweight (dynamic-import heavy libraries only on the paths that need them) and caching expensive results across warm invocations. Add a lightweight usage-tracking table plus a daily materialized-view summary for spend visibility. See [full compute and Edge Function code](references/optimization.md) for the pooling config, cold-start patterns, and usage-monitoring schema (Step 3 section).

## Output

After completing all three steps, the project has:

- Database size audit with table-level breakdown and dead tuple analysis
- Unused indexes identified and dropped to reclaim storage
- Old data archived and vacuumed to free database space
- Storage orphans cleaned and upload compression implemented
- Bandwidth reduced through column selection and pagination
- Connection pooling configured to avoid unnecessary compute upgrades
- Edge Function cold starts minimized with dynamic imports and caching
- Usage monitoring table and daily summary view for spend visibility

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Database approaching 500 MB (Free) or 8 GB (Pro) | Data growth without archival | Archive old records, VACUUM, drop unused indexes |
| Storage costs climbing monthly | Orphaned uploads accumulating | Schedule cleanup job for files not linked to records |
| Unexpected bandwidth spike | `select('*')` on large tables | Use specific column lists; add `.range()` pagination |
| Edge Function billing spike | Retry loops or heavy imports | Add circuit breaker with max 3 retries; dynamic imports |
| Connection limit errors | Too many direct connections | Switch to pooler URL (port 6543); reduce client pool size |
| Spend cap reached | Usage exceeded Pro included resources | Enable spend cap in Dashboard > Settings > Billing to prevent overage |
| VACUUM not reclaiming space | Long-running transactions holding locks | Check `pg_stat_activity` for idle-in-transaction; terminate stale sessions |

## Examples

**Quick cost check** — read database size and bucket count with a service-role client to see how close a growing project sits to its plan limits.

**Monthly cost estimation** — feed measured usage (DB GB, storage GB, bandwidth GB, Edge Function invocations, MAU) into a Pro-tier overage calculator that prints a line-item breakdown and total.

See [full example scripts](references/examples.md) for the runnable quick-check and the `estimateMonthlyCost` calculator with a worked $31.05/mo case.

## Resources

- [Supabase Pricing](https://supabase.com/pricing) — plan comparison and calculator
- [Compute Add-ons](https://supabase.com/docs/guides/platform/compute-add-ons) — instance sizing guide
- [Spend Cap](https://supabase.com/docs/guides/platform/spend-cap) — prevent unexpected overage charges
- [Database Disk Usage](https://supabase.com/docs/guides/platform/database-size) — monitoring and management
- [Connection Pooling (Supavisor)](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler) — reduce connection overhead
- [Edge Functions Best Practices](https://supabase.com/docs/guides/functions/best-practices) — cold start and performance tips
- [supabase-js Reference](https://supabase.com/docs/reference/javascript/introduction) — `createClient` and SDK patterns

## Next Steps

For architecture patterns, see `supabase-reference-architecture`.
For performance tuning beyond cost, see `supabase-performance-tuning`.
