---
name: supabase-prod-checklist
description: |
  Execute Supabase production deployment checklist covering security, performance,
  monitoring, and rollback procedures.
  Use when deploying to production, preparing for launch,
  or auditing a live Supabase project.
  Trigger with phrases like "supabase production", "supabase go-live",
  "supabase launch checklist", "supabase prod ready", "deploy supabase".
allowed-tools: Read, Bash(supabase:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, deployment, production]

---
# Supabase Prod Checklist

## Overview
A comprehensive checklist for taking a Supabase project to production, based on Supabase's official production guide. Covers security hardening, performance optimization, monitoring, backup strategy, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production Supabase project created (separate from development)
- Domain and DNS configured

## Instructions

### Security Checklist

```bash
# 1. Verify RLS on all tables
supabase inspect db table-sizes --linked  # shows all tables

# In SQL Editor, check RLS status:
```

```sql
select schemaname, tablename, rowsecurity
from pg_tables
where schemaname = 'public' and rowsecurity = false;
-- This query should return ZERO rows in production
```

- [ ] RLS enabled on every public table
- [ ] SSL enforcement enabled (Dashboard > Database > Settings > SSL)
- [ ] Database password changed from default
- [ ] Service role key only in server-side environments
- [ ] Email confirmation enabled for Auth
- [ ] OAuth redirect URLs restricted to production domains
- [ ] Custom SMTP configured for auth emails (so users see your domain)
- [ ] Unused auth providers disabled
- [ ] API rate limiting configured

### Performance Checklist

```sql
-- Check for missing indexes on foreign keys
select
  tc.table_name, kcu.column_name,
  case when i.indexname is null then 'MISSING INDEX' else i.indexname end
from information_schema.table_constraints tc
join information_schema.key_column_usage kcu
  on tc.constraint_name = kcu.constraint_name
left join pg_indexes i
  on i.tablename = tc.table_name
  and i.indexdef like '%' || kcu.column_name || '%'
where tc.constraint_type = 'FOREIGN KEY'
  and tc.table_schema = 'public';

-- Review slow queries
select query, calls, mean_exec_time::numeric(10,2) as avg_ms
from pg_stat_statements
order by mean_exec_time desc
limit 10;

-- Check table bloat
select relname, n_live_tup, n_dead_tup,
       round(n_dead_tup::numeric / greatest(n_live_tup, 1) * 100, 1) as dead_pct
from pg_stat_user_tables
where n_dead_tup > 1000
order by n_dead_tup desc;
```

- [ ] Indexes on all foreign keys and frequently filtered columns
- [ ] `pg_stat_statements` enabled for query monitoring
- [ ] Connection pooling via Supavisor (use pooled connection string)
- [ ] Performance Advisor reviewed (Dashboard > Database > Performance)
- [ ] Computed columns for expensive queries
- [ ] Appropriate `statement_timeout` set

### Database Configuration

```sql
-- Set timeouts for the authenticated role
alter role authenticated set statement_timeout = '10s';

-- Enable necessary extensions
create extension if not exists pg_stat_statements;
create extension if not exists pgcrypto;
```

### Backup and Recovery

- [ ] Point-in-Time Recovery (PITR) enabled (Pro plan required)
- [ ] Tested database restore procedure
- [ ] Daily logical backups verified in Dashboard > Database > Backups
- [ ] Migration files committed to version control
- [ ] `supabase db push` tested against a fresh project

### Monitoring

- [ ] Health check endpoint implemented and monitored

```typescript
// api/health.ts
export async function GET() {
  const start = Date.now()
  const { error } = await supabase.from('_health').select('*').limit(1)
  const latency = Date.now() - start

  return Response.json({
    status: error ? 'unhealthy' : 'healthy',
    latency_ms: latency,
    timestamp: new Date().toISOString(),
  }, { status: error ? 503 : 200 })
}
```

- [ ] Error tracking configured (Sentry, LogRocket, etc.)
- [ ] Supabase Log Explorer reviewed (Dashboard > Logs)
- [ ] Alerts configured for error rate spikes and high latency
- [ ] Uptime monitoring on health check endpoint

### Rollback Procedure

```bash
# 1. If a migration causes issues, create a rollback migration
supabase migration new rollback_bad_change

# 2. For data issues, restore from PITR
# Dashboard > Database > Backups > Point-in-Time Recovery

# 3. For application issues, revert deployment
# Your deployment platform handles this (Vercel rollback, etc.)

# 4. For auth issues, disable problematic provider
# Dashboard > Auth > Providers
```

### Pre-Launch Final Checks

- [ ] Load test completed on staging (see `supabase-load-scale`)
- [ ] DNS and custom domain configured
- [ ] CORS settings match production domain
- [ ] Environment variables set correctly in deployment platform
- [ ] Webhook endpoints registered and tested
- [ ] Storage bucket policies verified
- [ ] Realtime enabled only on tables that need it
- [ ] Database connection string uses pooled mode for serverless

## Output
- All checklist items verified and documented
- Health check endpoint deployed and monitored
- Rollback procedure documented and tested
- Production environment hardened and ready for traffic

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High latency after launch | Missing indexes | Run Performance Advisor; add indexes |
| Connection errors under load | Pool exhausted | Switch to pooled connection string via Supavisor |
| Auth emails not delivered | Default SMTP | Configure custom SMTP provider |
| RLS blocking legitimate users | Policy too restrictive | Debug with service role key; fix policy |

## Resources
- [Production Checklist](https://supabase.com/docs/guides/deployment/going-into-prod)
- [Maturity Model](https://supabase.com/docs/guides/deployment/maturity-model)
- [Shared Responsibility Model](https://supabase.com/docs/guides/deployment/shared-responsibility-model)
- [Performance Advisor](https://supabase.com/docs/guides/database/inspect)

## Next Steps
For SDK version upgrades, see `supabase-upgrade-migration`.
