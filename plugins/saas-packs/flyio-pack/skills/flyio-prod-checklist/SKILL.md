---
name: flyio-prod-checklist
description: |
  Execute Fly.io production deployment checklist with health checks,
  auto-scaling, monitoring, and rollback procedures.
  Trigger: "fly.io production", "fly.io go-live", "fly.io prod checklist".
allowed-tools: Read, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Production Checklist

## Overview

Fly.io runs applications on edge infrastructure across 30+ regions with Machines, Volumes, and managed Postgres. A production deployment requires multi-region redundancy, proper secret management, health checks, and rollback procedures. Misconfigured auto-scaling means cold starts; missing volume backups mean data loss. This checklist ensures your Fly.io app is production-hardened.

## Authentication & Secrets

- [ ] `FLY_API_TOKEN` stored in CI secrets (never in fly.toml or source)
- [ ] All app secrets set via `fly secrets` (not `[env]` block)
- [ ] Deploy tokens scoped per app (not org-wide personal tokens)
- [ ] Key rotation scheduled (quarterly, or after team changes)
- [ ] No hardcoded secrets in Dockerfile or codebase

## API Integration

- [ ] Production base URL: app deployed to `https://<app>.fly.dev`
- [ ] `force_https = true` in fly.toml http_service
- [ ] Custom domain with TLS certificate active and auto-renewing
- [ ] `min_machines_running = 1` to avoid cold starts
- [ ] Machines deployed in 2+ regions for redundancy
- [ ] Concurrency limits tuned (`soft_limit`/`hard_limit` per workload)
- [ ] Volumes backed up if using persistent storage

## Error Handling & Resilience

- [ ] Health check endpoint configured with appropriate grace period
- [ ] Graceful shutdown handles SIGTERM within 10s window
- [ ] Auto-stop/auto-start configured for cost optimization
- [ ] Postgres standby replica provisioned for database apps
- [ ] Rollback procedure tested: `fly releases rollback <N>`
- [ ] Dockerfile builds and runs identically local vs deployed

## Monitoring & Alerting

- [ ] `fly logs` streaming configured for centralized logging
- [ ] Machine health monitored via `fly machine status`
- [ ] Platform status checked: `https://status.flyio.net`
- [ ] Alert on health check failures across any region
- [ ] VM resource utilization tracked (`fly scale show`)

## Validation Script

```typescript
async function checkFlyioReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // Fly.io API connectivity
  try {
    const res = await fetch('https://api.machines.dev/v1/apps', {
      headers: { Authorization: `Bearer ${process.env.FLY_API_TOKEN}` },
    });
    checks.push({ name: 'Fly API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Fly API', pass: false, detail: e.message }); }
  // Token present
  checks.push({ name: 'API Token Set', pass: !!process.env.FLY_API_TOKEN, detail: process.env.FLY_API_TOKEN ? 'Present' : 'MISSING' });
  // Platform status
  try {
    const res = await fetch('https://status.flyio.net/api/v2/status.json');
    const data = await res.json();
    const status = data?.status?.indicator || 'unknown';
    checks.push({ name: 'Platform Status', pass: status === 'none', detail: status === 'none' ? 'Operational' : status });
  } catch (e: any) { checks.push({ name: 'Platform Status', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkFlyioReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| Multi-region deployment | Single region outage = full downtime | P1 |
| Volume backups | Data loss on machine replacement | P1 |
| Health check config | Dead machines receive traffic | P2 |
| SIGTERM handling | Dropped requests during deploys | P2 |
| Rollback procedure | Stuck on broken release | P3 |

## Resources

- [Fly.io Production Checklist](https://fly.io/docs/getting-started/essentials/)
- [Fly.io Status](https://status.flyio.net)

## Next Steps

See `flyio-security-basics` for network policies and secret management.
