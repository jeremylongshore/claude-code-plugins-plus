# ClickHouse Upgrade & Migration — Examples

Ready-to-run code for the code-migration, validation, and rollback steps.

## Common migration patterns

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

## Post-upgrade validation script

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

## Rollback commands

```text
# Node.js client rollback
npm install @clickhouse/client@<previous-version> --save-exact

# Server rollback (self-hosted)
sudo systemctl stop clickhouse-server
sudo apt-get install clickhouse-server=<previous-version>
sudo systemctl start clickhouse-server

# Restore from backup if needed
clickhouse-client --query "RESTORE DATABASE analytics FROM Disk('backups', 'pre-upgrade')"
```
