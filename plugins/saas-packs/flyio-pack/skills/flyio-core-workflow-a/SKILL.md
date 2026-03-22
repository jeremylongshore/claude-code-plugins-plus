---
name: flyio-core-workflow-a
description: |
  Execute Fly.io primary workflow: deploy, scale, and manage apps with flyctl and fly.toml.
  Use when deploying applications, configuring regions, setting secrets,
  or managing the app lifecycle on Fly.io.
  Trigger: "fly deploy", "fly.io app management", "fly scale", "fly.io regions".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Core Workflow A: Deploy & Scale

## Overview

The primary Fly.io workflow: configure `fly.toml`, deploy apps, manage secrets, scale across regions, and control machine lifecycle.

## Instructions

### Step 1: Configure fly.toml

```toml
# fly.toml — app configuration
app = "my-app"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  NODE_ENV = "production"
  PORT = "3000"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"    # Stop idle machines
  auto_start_machines = true     # Start on request
  min_machines_running = 1       # Always keep 1 warm

[http_service.concurrency]
  type = "requests"
  hard_limit = 250
  soft_limit = 200

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory = "512mb"
```

### Step 2: Deploy and Manage Secrets

```bash
# Set secrets (encrypted, injected as env vars)
fly secrets set DATABASE_URL="postgres://..." API_KEY="sk_..."

# List secrets (values hidden)
fly secrets list

# Deploy
fly deploy

# Check deployment status
fly status
fly releases
```

### Step 3: Scale Across Regions

```bash
# Add machines in new regions
fly scale count 2 --region iad    # 2 machines in Virginia
fly scale count 1 --region lhr    # 1 machine in London
fly scale count 1 --region nrt    # 1 machine in Tokyo

# Adjust VM size
fly scale vm shared-cpu-2x --memory 1024

# Check current scale
fly scale show
```

### Step 4: Manage App Lifecycle

```bash
# Restart all machines
fly apps restart

# Suspend an app (stop billing)
fly apps suspend my-app

# Resume
fly apps resume my-app

# Destroy (irreversible)
fly apps destroy my-app --yes
```

## fly.toml Key Settings

| Setting | Default | Recommended |
|---------|---------|-------------|
| `auto_stop_machines` | `"stop"` | `"stop"` for most, `"suspend"` for fast resume |
| `auto_start_machines` | `true` | `true` for HTTP services |
| `min_machines_running` | `0` | `1` for production (avoid cold starts) |
| `concurrency.soft_limit` | `200` | Tune based on app capacity |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `failed to build` | Dockerfile issue | Test locally: `docker build .` |
| `health check failed` | App not responding on internal_port | Verify port matches app config |
| `no machines running` | All stopped | Set `min_machines_running = 1` |

## Resources

- [fly.toml Reference](https://fly.io/docs/reference/configuration/)
- [Scaling](https://fly.io/docs/launch/scale-count/)
- [Secrets](https://fly.io/docs/reference/secrets/)

## Next Steps

For Postgres and volumes, see `flyio-core-workflow-b`.
