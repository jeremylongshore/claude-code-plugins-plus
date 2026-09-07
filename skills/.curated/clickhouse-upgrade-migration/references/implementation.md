# ClickHouse Upgrade & Migration — Full Implementation

Complete, verbatim procedures for each upgrade step. The SKILL.md carries the
lean workflow and skeletons; drill in here for the full command sequences.

## Step 1: Check Current Versions

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

## Step 2: Review Changelog

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

## Step 3: Upgrade the Node.js Client

```bash
git checkout -b upgrade/clickhouse-client
npm install @clickhouse/client@latest
npm test
```

The common code-migration patterns (the `createClient` option rename and the
`rs.json()` result-shape change) live in
[examples.md](examples.md) under "Common migration patterns".

## Step 4: Upgrade ClickHouse Server

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

## Step 5: Validate After Upgrade

The full post-upgrade validation script (ping → version → schema → insert →
query, with PASS/FAIL reporting) lives in [examples.md](examples.md) under
"Post-upgrade validation script".

## Step 6: Rollback Procedure

The client, server, and data-restore rollback commands live in
[examples.md](examples.md) under "Rollback commands".
