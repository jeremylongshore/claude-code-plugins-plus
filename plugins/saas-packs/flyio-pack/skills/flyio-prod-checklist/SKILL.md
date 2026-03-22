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

## Pre-Deployment

### Infrastructure
- [ ] `min_machines_running = 1` (avoid cold starts)
- [ ] Machines in 2+ regions for redundancy
- [ ] VM sized appropriately (`fly scale show`)
- [ ] Volumes backed up (if using persistent storage)
- [ ] Postgres has standby replica

### Configuration
- [ ] All secrets set via `fly secrets` (not `[env]`)
- [ ] `force_https = true`
- [ ] Health check configured with appropriate grace period
- [ ] Custom domain with TLS certificate active
- [ ] Concurrency limits tuned for your app

### Code Quality
- [ ] Dockerfile builds successfully locally
- [ ] App responds on health check endpoint
- [ ] Graceful shutdown handles SIGTERM
- [ ] No hardcoded secrets in codebase

## Production fly.toml

```toml
app = "my-app"
primary_region = "iad"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[http_service.concurrency]
  type = "requests"
  hard_limit = 250
  soft_limit = 200

[http_service.checks]
  grace_period = "15s"
  interval = "10s"
  timeout = "3s"
  path = "/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory = "1gb"
```

## Rollback Procedure

```bash
# List recent releases
fly releases -a my-app

# Rollback to previous release
fly deploy --image registry.fly.io/my-app:previous-version

# Or rollback to specific release
fly releases rollback 5 -a my-app
```

## Monitoring

```bash
# Live logs
fly logs -a my-app

# Machine metrics
fly machine status <machine-id> -a my-app

# Platform status
curl -s https://status.flyio.net/api/v2/status.json | jq '.status.description'
```

## Resources

- [Fly.io Production Checklist](https://fly.io/docs/getting-started/essentials/)
- [Auto Stop/Start](https://fly.io/docs/launch/autostop-autostart/)

## Next Steps

For version upgrades, see `flyio-upgrade-migration`.
