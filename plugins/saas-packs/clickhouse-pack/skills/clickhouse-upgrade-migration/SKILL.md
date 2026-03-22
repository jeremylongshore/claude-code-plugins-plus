---
name: clickhouse-upgrade-migration
description: |
  Upgrade ClickHouse server versions and @clickhouse/client SDK safely.
  Use when upgrading ClickHouse, handling breaking changes between versions,
  or migrating from older client libraries.
  Trigger: "upgrade clickhouse", "clickhouse version upgrade", "update clickhouse client",
  "clickhouse breaking changes", "new clickhouse version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Upgrade & Migration

## Overview

Safely upgrade ClickHouse server and the `@clickhouse/client` Node.js SDK,
with rollback procedures and breaking change detection.

## Prerequisites

- Current ClickHouse version known (`SELECT version()`)
- Git for version control
- Test suite for integration validation
- Staging environment for pre-production testing

## Instructions

### Step 1: Check Current Versions

```bash
# Check server version (via HTTP)
curl 'http://localhost:8123/?query=SELECT+version()'

# Check Node.js client version
npm list @clickhouse/client

# Check latest available
npm view @clickhouse/client version
```

```sql
-- Server-side version details
SELECT
    version()           AS server_version,
    uptime()            AS uptime_sec,
    currentDatabase()   AS current_db;
```

### Step 2: Review Changelog

```bash
# View release notes
open https://github.com/ClickHouse/clickhouse-js/releases

# Server changelog
open https://github.com/ClickHouse/ClickHouse/blob/master/CHANGELOG.md
```

**Key breaking changes to watch for:**
- Client API signature changes (`createClient` options)
- Default setting changes (compression, timeouts)
- New query result format behavior
- Deprecated SQL functions removed in server upgrades
- MergeTree settings renamed or defaults changed

### Step 3: Upgrade the Node.js Client

```bash
git checkout -b upgrade/clickhouse-client
npm install @clickhouse/client@latest
npm test
```

**Common migration patterns:**

```typescript
// v0.x → v1.x: createClient options restructured
// Before (v0.x)
import { createClient } from '@clickhouse/client';
const client = createClient({
  host: 'http://localhost:8123',
});

// After (v1.x)
const client = createClient({
  url: 'http://localhost:8123',   // 'host' renamed to 'url'
});

// v0.x → v1.x: query result handling
// Before: rs.json() returned { data: [...], statistics: {...} }
// After: rs.json() returns the rows array directly

// Before
const result = await rs.json();
const rows = result.data;

// After
const rows = await rs.json();
```

### Step 4: Upgrade ClickHouse Server

**ClickHouse Cloud:** Upgrades happen automatically. Check release notes in
the Cloud console.

**Self-hosted upgrade procedure:**

```bash
# 1. Backup current data
clickhouse-client --query "BACKUP DATABASE analytics TO Disk('backups', 'pre-upgrade')"

# 2. Check compatibility
clickhouse-client --query "SELECT * FROM system.settings WHERE changed"

# 3. Stop server gracefully
sudo systemctl stop clickhouse-server

# 4. Update packages
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install clickhouse-server clickhouse-client

# 5. Start and verify
sudo systemctl start clickhouse-server
clickhouse-client --query "SELECT version()"

# 6. Check for schema issues
clickhouse-client --query "
    SELECT database, table, engine, metadata_modification_time
    FROM system.tables WHERE database NOT IN ('system', 'INFORMATION_SCHEMA')
"
```

### Step 5: Validate After Upgrade

```typescript
// Post-upgrade validation script
import { createClient } from '@clickhouse/client';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

async function validateUpgrade() {
  const checks = [
    { name: 'ping', fn: () => client.ping() },
    { name: 'version', fn: async () => {
      const rs = await client.query({ query: 'SELECT version()', format: 'JSONEachRow' });
      return rs.json();
    }},
    { name: 'schema', fn: async () => {
      const rs = await client.query({
        query: 'SELECT database, name, engine FROM system.tables WHERE database = {db:String}',
        query_params: { db: 'analytics' },
        format: 'JSONEachRow',
      });
      return rs.json();
    }},
    { name: 'insert', fn: async () => {
      await client.insert({
        table: 'analytics.events',
        values: [{ event_type: 'upgrade_test', user_id: 0, payload: '{}' }],
        format: 'JSONEachRow',
      });
      return { success: true };
    }},
    { name: 'query', fn: async () => {
      const rs = await client.query({
        query: 'SELECT count() AS cnt FROM analytics.events',
        format: 'JSONEachRow',
      });
      return rs.json();
    }},
  ];

  for (const check of checks) {
    try {
      const result = await check.fn();
      console.log(`[PASS] ${check.name}:`, JSON.stringify(result));
    } catch (err) {
      console.error(`[FAIL] ${check.name}:`, (err as Error).message);
    }
  }
}

validateUpgrade();
```

### Step 6: Rollback Procedure

```bash
# Node.js client rollback
npm install @clickhouse/client@<previous-version> --save-exact

# Server rollback (self-hosted)
sudo systemctl stop clickhouse-server
sudo apt-get install clickhouse-server=<previous-version>
sudo systemctl start clickhouse-server

# Restore from backup if needed
clickhouse-client --query "RESTORE DATABASE analytics FROM Disk('backups', 'pre-upgrade')"
```

## Version Compatibility Matrix

| Client Version | Min Server Version | Node.js | Key Changes |
|---------------|-------------------|---------|-------------|
| 1.x | 22.6+ | 18+ | Stable API, `url` option |
| 0.3.x | 22.6+ | 16+ | `host` option, different JSON result shape |
| 0.2.x | 21.8+ | 14+ | Initial release |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Unknown setting` | New default in config | Remove deprecated setting |
| `Cannot parse datetime` | Format change | Update date format strings |
| `Method not found` | Client API changed | Check migration guide |
| `Checksum mismatch` | Corrupted upgrade | Rollback and re-download |

## Resources

- [Client Releases](https://github.com/ClickHouse/clickhouse-js/releases)
- [Server Changelog](https://github.com/ClickHouse/ClickHouse/blob/master/CHANGELOG.md)
- [Cloud Upgrades](https://clickhouse.com/docs/cloud/manage/upgrades)

## Next Steps

For CI/CD integration, see `clickhouse-ci-integration`.
