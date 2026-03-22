---
name: flyio-core-workflow-b
description: |
  Execute Fly.io secondary workflow: Postgres clusters, persistent volumes, and private networking.
  Use when adding databases, persistent storage, or internal service communication.
  Trigger: "fly postgres", "fly volumes", "fly.io database", "fly.io persistent storage".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(psql:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Core Workflow B: Postgres, Volumes & Networking

## Overview

Set up Fly Postgres, persistent Fly Volumes, and private networking between apps. Fly Postgres runs as a regular Fly app with automated replication. Volumes provide persistent NVMe storage attached to specific machines.

## Instructions

### Step 1: Create Fly Postgres

```bash
# Create a Postgres cluster
fly postgres create --name my-db --region iad --vm-size shared-cpu-1x --volume-size 10

# Attach to your app (sets DATABASE_URL secret automatically)
fly postgres attach my-db -a my-app

# Connect directly
fly postgres connect -a my-db
# psql> SELECT version();

# Proxy to local machine for dev tools
fly proxy 5432 -a my-db
# Now connect: psql postgres://postgres:password@localhost:5432
```

### Step 2: Create Persistent Volumes

```bash
# Create a volume (same region as your machine)
fly volumes create data --size 10 --region iad -a my-app

# List volumes
fly volumes list -a my-app

# Mount in fly.toml
```

```toml
# fly.toml
[mounts]
  source = "data"
  destination = "/data"
```

```bash
# Deploy to pick up mount
fly deploy

# Verify mount inside machine
fly ssh console -C "df -h /data"
```

### Step 3: Private Networking (6PN)

```bash
# Apps in the same org can reach each other via .internal DNS
# my-app can reach my-db at: my-db.internal:5432

# Internal DNS format: <app-name>.internal
# Machine-specific: <machine-id>.vm.<app-name>.internal

# Example: connect from app code
DATABASE_URL=postgres://postgres:password@my-db.internal:5432/my_db
```

```typescript
// Access internal services (no public internet)
const dbUrl = `postgres://postgres:${process.env.DB_PASSWORD}@my-db.internal:5432/mydb`;
const apiUrl = `http://my-api.internal:3000/health`;  // Internal HTTP
```

### Step 4: Postgres Backups and Failover

```bash
# List backups
fly postgres barman list-backups -a my-db

# Create manual backup
fly postgres barman backup -a my-db

# Check replication status
fly postgres barman check -a my-db

# Failover to standby (if primary fails)
fly postgres failover -a my-db
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `volume not found` | Volume in different region | Create volume in same region as machine |
| `connection refused on .internal` | App not running | Check `fly status -a target-app` |
| `database does not exist` | Not yet created | Run `CREATE DATABASE mydb;` via `fly postgres connect` |
| `disk full` | Volume full | Extend: `fly volumes extend vol_xxx --size 20` |

## Resources

- [Fly Postgres](https://fly.io/docs/postgres/)
- [Fly Volumes](https://fly.io/docs/volumes/)
- [Private Networking](https://fly.io/docs/networking/private-networking/)

## Next Steps

For common errors, see `flyio-common-errors`.
