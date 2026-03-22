---
name: flyio-performance-tuning
description: |
  Optimize Fly.io application performance with auto-stop/start tuning,
  VM sizing, multi-region latency optimization, and connection pooling.
  Trigger: "fly.io performance", "fly.io cold start", "fly.io latency", "fly.io VM sizing".
allowed-tools: Read, Write, Edit, Bash(fly:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Performance Tuning

## Overview

Optimize Fly.io performance: eliminate cold starts, right-size VMs, leverage multi-region for low latency, and tune concurrency settings.

## Instructions

### Step 1: Eliminate Cold Starts

```toml
# fly.toml — suspend instead of stop for faster resume (~100ms vs ~5s)
[http_service]
  auto_stop_machines = "suspend"   # Suspend to RAM, not full stop
  auto_start_machines = true
  min_machines_running = 1          # Always-warm in primary region

# For latency-critical: keep machines running in all regions
# min_machines_running applies globally
```

### Step 2: Right-Size VMs

```bash
# Check current allocation
fly scale show -a my-app

# Start small, scale up based on metrics
fly scale vm shared-cpu-1x --memory 256    # Start here
fly scale vm shared-cpu-1x --memory 512    # If memory-constrained
fly scale vm shared-cpu-2x --memory 1024   # If CPU-bound
fly scale vm performance-2x --memory 4096  # For compute-heavy workloads
```

| Workload | VM | Memory | When |
|----------|-------|--------|------|
| Static site / API proxy | shared-cpu-1x | 256mb | Low traffic |
| Node.js API | shared-cpu-1x | 512mb | Most apps |
| Heavy processing | shared-cpu-2x | 1gb | Background jobs |
| Database / ML | performance-2x | 4gb | Compute-intensive |

### Step 3: Multi-Region Latency Optimization

```bash
# Deploy close to your users
fly scale count 1 --region iad    # US East
fly scale count 1 --region lhr    # Europe
fly scale count 1 --region nrt    # Asia Pacific

# Fly automatically routes to nearest region via Anycast
# Verify: curl with timing
curl -w "DNS: %{time_namelookup}s, Connect: %{time_connect}s, Total: %{time_total}s\n" \
  -o /dev/null -s https://my-app.fly.dev/health
```

### Step 4: Connection Pooling for Postgres

```typescript
// Use connection pooling for Fly Postgres
// PgBouncer runs on port 5433 (pooled) vs 5432 (direct)
const pooledUrl = process.env.DATABASE_URL?.replace(':5432/', ':5433/');

// Prisma: add pgbouncer=true
// DATABASE_URL="postgres://user:pass@my-db.internal:5433/db?pgbouncer=true"
```

### Step 5: Tune Concurrency

```toml
[http_service.concurrency]
  type = "requests"       # or "connections"
  hard_limit = 250        # Max before rejecting
  soft_limit = 200        # Start scaling at this point
```

## Resources

- [Auto Stop/Start](https://fly.io/docs/launch/autostop-autostart/)
- [Machine Sizing](https://fly.io/docs/machines/)
- [Suspend/Resume](https://fly.io/docs/reference/suspend-resume/)

## Next Steps

For cost optimization, see `flyio-cost-tuning`.
