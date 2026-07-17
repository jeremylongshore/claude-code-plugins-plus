# CLI Inspect Commands

The Supabase CLI ships `supabase inspect db` subcommands that run diagnostic
queries against your linked Postgres instance. Run any of these against a linked
project to surface hotspots the Dashboard reports do not expose.

```bash
# Table sizes — find the largest tables
npx supabase inspect db table-sizes --linked

# Index usage — find unused indexes wasting space
npx supabase inspect db index-usage --linked

# Cache hit ratio — should be > 99% (below 95% means upgrade compute)
npx supabase inspect db cache-hit --linked

# Sequential scans — tables needing indexes
npx supabase inspect db seq-scans --linked

# Long-running queries — find stuck queries
npx supabase inspect db long-running-queries --linked

# Table index sizes — compare index vs table size
npx supabase inspect db table-index-sizes --linked

# Bloat — estimate wasted space from dead tuples
npx supabase inspect db bloat --linked

# Blocking queries — find lock contention
npx supabase inspect db blocking --linked

# Replication slots — check replication health
npx supabase inspect db replication-slots --linked
```

## Dashboard Reports

The Supabase Dashboard provides built-in reports under **Dashboard > Reports**:

| Report | What It Shows |
| -------- | --------------- |
| API Requests | Total requests, response times, error rates by endpoint |
| Database | Active connections, query counts, replication lag |
| Auth Usage | Signups, logins, provider breakdown, failed attempts |
| Storage | Bandwidth, object counts, bucket usage |
| Realtime | Active connections, messages per second, channel counts |
