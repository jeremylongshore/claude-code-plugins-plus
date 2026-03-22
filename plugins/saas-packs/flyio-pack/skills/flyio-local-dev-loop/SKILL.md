---
name: flyio-local-dev-loop
description: |
  Configure Fly.io local development with Docker, proxy, and SSH console.
  Use when setting up local dev against Fly services, testing Dockerfiles,
  or establishing a fast iteration cycle.
  Trigger: "fly.io dev setup", "fly.io local development", "fly proxy".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Local Dev Loop

## Overview

Fast local development workflow for Fly.io apps: build and test Docker containers locally, proxy remote Fly services (Postgres, Redis) to localhost, and use `fly deploy` for integration testing.

## Instructions

### Step 1: Local Docker Testing

```bash
# Build and run locally — same Dockerfile used by Fly
docker build -t my-app .
docker run -p 3000:3000 \
  -e NODE_ENV=development \
  -e DATABASE_URL="postgres://localhost:5432/dev" \
  my-app

# Test
curl http://localhost:3000/health
```

### Step 2: Proxy Remote Fly Services

```bash
# Proxy Fly Postgres to localhost:5432
fly proxy 5432 -a my-db &

# Now use local tools against remote Fly Postgres
psql postgres://postgres:password@localhost:5432/mydb
npx prisma studio  # Prisma GUI works against proxied DB

# Proxy Redis
fly proxy 6379 -a my-redis &
redis-cli -h localhost -p 6379
```

### Step 3: Development fly.toml

```toml
# fly.dev.toml — dev overrides (not committed)
app = "my-app-dev"
primary_region = "iad"

[env]
  NODE_ENV = "development"
  LOG_LEVEL = "debug"

[http_service]
  internal_port = 3000
  auto_stop_machines = "off"  # Keep running for debugging
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory = "256mb"  # Smaller for dev
```

### Step 4: Fast Deploy Cycle

```bash
# Deploy to dev app
fly deploy -a my-app-dev --config fly.dev.toml

# Watch logs while testing
fly logs -a my-app-dev --no-tail &

# SSH in for debugging
fly ssh console -a my-app-dev

# Quick restart after config change
fly apps restart my-app-dev
```

### Dev Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "docker:build": "docker build -t my-app .",
    "docker:run": "docker run -p 3000:3000 --env-file .env.local my-app",
    "fly:dev": "fly deploy -a my-app-dev --config fly.dev.toml",
    "fly:proxy:db": "fly proxy 5432 -a my-db",
    "fly:logs": "fly logs -a my-app-dev",
    "fly:ssh": "fly ssh console -a my-app-dev"
  }
}
```

## Resources

- [Fly.io Local Development](https://fly.io/docs/getting-started/essentials/)
- [fly proxy](https://fly.io/docs/flyctl/proxy/)

## Next Steps

See `flyio-sdk-patterns` for Machines API client patterns.
