---
name: replit-upgrade-migration
description: |
  Upgrade Replit Nix channels, migrate between database types, and update deployment targets.
  Use when upgrading Nix channel versions, migrating from Replit DB to PostgreSQL,
  switching deployment types, or updating system dependencies.
  Trigger with phrases like "upgrade replit", "replit nix upgrade",
  "migrate replit database", "replit version update", "replit channel update".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, migration, nix, upgrade]

---
# Replit Upgrade & Migration

## Current State
!`cat .replit 2>/dev/null | head -15 || echo 'No .replit found'`
!`cat replit.nix 2>/dev/null || echo 'No replit.nix found'`

## Overview
Guide for upgrading Replit environments: Nix channel updates, package version bumps, database migrations (KV to PostgreSQL, dev to prod), deployment type changes, and Node.js/Python runtime upgrades.

## Prerequisites
- Existing Replit App with `.replit` and `replit.nix`
- Git version control (recommended)
- Backup of critical data before migration

## Instructions

### Step 1: Upgrade Nix Channel
Nix channels determine available package versions. Upgrade to get newer runtimes.

```toml
# .replit — before
[nix]
channel = "stable-23_05"

# .replit — after (2024-2025 stable)
[nix]
channel = "stable-24_05"
```

After changing the channel, reload the shell (exit Shell tab and re-enter). Then verify:
```bash
node --version     # Should show newer version
python3 --version  # Should show newer version
```

### Step 2: Upgrade Node.js or Python Runtime
```nix
# replit.nix — update runtime packages

# Before (Node 18)
{ pkgs }: {
  deps = [
    pkgs.nodejs-18_x
    pkgs.nodePackages.typescript
  ];
}

# After (Node 20)
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
    pkgs.nodePackages.pnpm
  ];
}
```

```toml
# .replit — update modules to match
modules = ["nodejs-20:v8-20230920-bd784b9"]
```

**Verify after upgrade:**
```bash
node --version         # v20.x.x
npm --version          # 10.x.x
npm test               # Run tests to catch breaking changes
```

### Step 3: Migrate from Replit KV to PostgreSQL
When your app outgrows the 50 MiB KV database limit:

```typescript
// scripts/migrate-kv-to-postgres.ts
import Database from '@replit/database';
import { Pool } from 'pg';

const kv = new Database();
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

async function migrate() {
  // Create table
  await pool.query(`
    CREATE TABLE IF NOT EXISTS kv_data (
      key TEXT PRIMARY KEY,
      value JSONB NOT NULL,
      migrated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);

  // Read all KV entries
  const keys = await kv.list();
  console.log(`Migrating ${keys.length} keys...`);

  let migrated = 0;
  let errors = 0;

  for (const key of keys) {
    try {
      const value = await kv.get(key);
      await pool.query(
        'INSERT INTO kv_data (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2',
        [key, JSON.stringify(value)]
      );
      migrated++;
    } catch (err: any) {
      console.error(`Failed to migrate key "${key}": ${err.message}`);
      errors++;
    }
  }

  console.log(`Migration complete: ${migrated} migrated, ${errors} errors`);
}

migrate().then(() => pool.end());
```

### Step 4: Switch Deployment Type
```toml
# .replit — change deployment target

# From Autoscale (scales to zero):
[deployment]
deploymentTarget = "autoscale"
run = ["sh", "-c", "npm start"]

# To Reserved VM (always-on):
[deployment]
deploymentTarget = "cloudrun"
run = ["sh", "-c", "npm start"]

# To Static (frontend only):
[deployment]
deploymentTarget = "static"
publicDir = "dist"
```

After changing: click "Deploy" to create a new deployment with the new type.

### Step 5: Migrate Large Files to Object Storage
```typescript
// Move large values from KV to Object Storage
import Database from '@replit/database';
import { Client } from '@replit/object-storage';

const kv = new Database();
const storage = new Client();

async function migrateToObjectStorage(prefix: string) {
  const keys = await kv.list(prefix);

  for (const key of keys) {
    const value = await kv.get(key);
    const content = typeof value === 'string' ? value : JSON.stringify(value);

    await storage.uploadFromText(`migrated/${key}`, content);
    await kv.delete(key);
    console.log(`Migrated: ${key}`);
  }
}
```

### Step 6: Pre-Migration Checklist
```markdown
## Before Any Upgrade
- [ ] Git commit current working state
- [ ] Back up Replit KV data: export all keys to JSON file
- [ ] Back up PostgreSQL: pg_dump or Replit snapshot
- [ ] Note current deployment URL and settings
- [ ] Run full test suite: npm test
- [ ] Document current .replit and replit.nix content

## After Upgrade
- [ ] Reload shell (exit and re-enter Shell tab)
- [ ] Verify runtime versions
- [ ] npm install / pip install (rebuild packages for new runtime)
- [ ] Run full test suite
- [ ] Test in Workspace Webview
- [ ] Deploy and verify production health check
- [ ] Monitor for 24 hours for regressions
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Package not found` after channel upgrade | Package renamed or removed | Search Nix packages: `nix-env -qaP \| grep name` |
| `node-gyp` build failure | Native addon incompatible | Update the addon or add Nix system deps |
| PostgreSQL connection refused | Pool not using SSL | Add `ssl: { rejectUnauthorized: false }` |
| Old deployment still running | Didn't redeploy | Click "Deploy" to apply new config |

## Resources
- [Replit App Configuration](https://docs.replit.com/replit-app/configuration)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [PostgreSQL on Replit](https://docs.replit.com/cloud-services/storage-and-databases/postgresql-on-replit)
- [Deployment Types](https://docs.replit.com/hosting/deployments)

## Next Steps
For CI integration during upgrades, see `replit-ci-integration`.
