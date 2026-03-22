---
name: flyio-upgrade-migration
description: |
  Migrate between Fly.io platform versions including Apps v1 to v2 (Machines),
  flyctl upgrades, and Postgres major version upgrades.
  Trigger: "fly.io upgrade", "fly.io migration", "fly apps v2", "fly postgres upgrade".
allowed-tools: Read, Write, Edit, Bash(fly:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Upgrade & Migration

## Overview

Guide for Fly.io platform migrations: Apps v1 (Nomad) to v2 (Machines), flyctl CLI upgrades, Postgres major version upgrades, and region migrations.

## Instructions

### Apps v1 to v2 Migration

```bash
# Check current platform version
fly status -a my-app  # Look for "Platform: machines" vs "nomad"

# Migrate to Apps v2 (Machines)
fly migrate-to-v2 -a my-app

# Verify
fly status -a my-app
fly machine list -a my-app
```

### flyctl CLI Upgrade

```bash
# Check current version
fly version

# Upgrade
fly version update

# Or reinstall
curl -L https://fly.io/install.sh | sh
```

### Postgres Major Version Upgrade

```bash
# Check current version
fly postgres connect -a my-db -c "SELECT version();"

# Create new cluster with target version
fly postgres create --name my-db-v16 --region iad --image-ref flyio/postgres-flex:16

# Migrate data
fly postgres import pg_dump_url -a my-db-v16

# Update app to point to new cluster
fly postgres detach my-db -a my-app
fly postgres attach my-db-v16 -a my-app
fly deploy -a my-app  # Picks up new DATABASE_URL
```

### Region Migration

```bash
# Add machines in new region
fly scale count 1 --region fra -a my-app

# Verify new region is healthy
fly status -a my-app

# Remove machines from old region
fly scale count 0 --region iad -a my-app

# For volumes: create new volume, migrate data, destroy old
fly volumes create data --size 10 --region fra -a my-app
```

## Migration Checklist

- [ ] Current state documented (`fly status`, `fly scale show`)
- [ ] Database backed up before migration
- [ ] Tested migration in staging app first
- [ ] DNS/certificates transferred if changing domains
- [ ] Monitoring confirms healthy after cutover
- [ ] Old resources cleaned up

## Resources

- [Apps v2 Migration](https://fly.io/docs/reference/apps/)
- [Postgres Upgrades](https://fly.io/docs/postgres/)

## Next Steps

For CI integration, see `flyio-ci-integration`.
