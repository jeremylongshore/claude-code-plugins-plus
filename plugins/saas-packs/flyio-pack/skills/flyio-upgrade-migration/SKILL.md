---
name: flyio-upgrade-migration
description: 'Migrate between Fly.io platform versions including Apps v1 to v2 (Machines),

  flyctl upgrades, and Postgres major version upgrades.

  Trigger: "fly.io upgrade", "fly.io migration", "fly apps v2", "fly postgres upgrade".

  '
allowed-tools: Read, Write, Edit, Bash(fly:*), Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Upgrade & Migration

## Overview

Guide for Fly.io platform migrations: Apps v1 (Nomad) to v2 (Machines), flyctl CLI upgrades, Postgres major version upgrades, and region migrations.

## Prerequisites

- Current platform documentation and an inventory of applications, machines, regions, volumes, databases, identities, and dependent consumers.
- A staging environment, synthetic traffic/data, tested backup/restore, rollback owner, and explicit acceptance/reconciliation criteria.

## Output

Produce a migration receipt with versions reviewed, affected resources, staging/canary results, backup/restore evidence, reconciliation outcome, approver, and rollback state. Keep tokens, connection strings, and user data out of the receipt.

## Error Handling

- Stop promotion on health, schema, region, permission, or reconciliation mismatches and restore the prior configuration.
- Quarantine failed migrations by opaque resource ID; do not bulk replay stateful workloads to diagnose failures.
- Escalate potential data loss or credential exposure and retain only approved incident evidence.

## Examples

Migrate a disposable staging app using synthetic traffic, exercise a backup/restore of fictional data, and simulate a failed health check. Verify rollback returns routing and data access to the known-good release before considering a production canary.

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
