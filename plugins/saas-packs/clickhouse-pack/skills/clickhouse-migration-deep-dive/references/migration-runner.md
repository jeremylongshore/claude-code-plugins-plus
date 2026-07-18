# Versioned Migration Runner & Best Practices

A versioned migration runner applies numbered `.sql` files in order, tracks what
has been applied in a `_migrations` table, and stops on the first failure. This
reference contains the full runner, example migration files, and the operation
downtime matrix.

## Versioned Migration Runner

```typescript
// src/clickhouse/migrations/runner.ts
import { createClient } from '@clickhouse/client';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

async function runMigrations() {
  // Create migration tracking table
  await client.command({
    query: `
      CREATE TABLE IF NOT EXISTS _migrations (
          version     String,
          name        String,
          applied_at  DateTime DEFAULT now(),
          checksum    String
      )
      ENGINE = ReplacingMergeTree(applied_at)
      ORDER BY version
    `,
  });

  // Get applied migrations
  const rs = await client.query({
    query: 'SELECT version FROM _migrations FINAL',
    format: 'JSONEachRow',
  });
  const applied = new Set((await rs.json<{ version: string }>()).map((r) => r.version));

  // Read migration files
  const migrationsDir = join(__dirname, 'sql');
  const files = readdirSync(migrationsDir)
    .filter((f) => f.endsWith('.sql'))
    .sort();  // 001-create-events.sql, 002-add-country.sql, etc.

  for (const file of files) {
    const version = file.split('-')[0];  // "001"
    if (applied.has(version)) {
      console.log(`  [SKIP] ${file} (already applied)`);
      continue;
    }

    const sql = readFileSync(join(migrationsDir, file), 'utf-8');
    console.log(`  [APPLY] ${file}...`);

    try {
      // Split on semicolons to handle multi-statement files
      const statements = sql.split(';').filter((s) => s.trim());
      for (const stmt of statements) {
        await client.command({ query: stmt });
      }

      // Record migration
      await client.insert({
        table: '_migrations',
        values: [{ version, name: file, checksum: '' }],
        format: 'JSONEachRow',
      });
      console.log(`  [OK] ${file}`);
    } catch (err) {
      console.error(`  [FAIL] ${file}: ${(err as Error).message}`);
      throw err;  // Stop on first failure
    }
  }

  console.log('Migrations complete.');
}

runMigrations();
```

## Example Migration Files

```sql
-- migrations/sql/001-create-events.sql
CREATE TABLE IF NOT EXISTS analytics.events (
    event_id    UUID DEFAULT generateUUIDv4(),
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (event_type, created_at)
PARTITION BY toYYYYMM(created_at);
```

```sql
-- migrations/sql/002-add-country.sql
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS country LowCardinality(String) DEFAULT '';
```

```sql
-- migrations/sql/003-add-ttl.sql
ALTER TABLE analytics.events
    MODIFY TTL created_at + INTERVAL 90 DAY;
```

```sql
-- migrations/sql/004-add-bloom-index.sql
ALTER TABLE analytics.events
    ADD INDEX IF NOT EXISTS idx_session session_id TYPE bloom_filter(0.01) GRANULARITY 4;
ALTER TABLE analytics.events MATERIALIZE INDEX idx_session;
```

## Migration Best Practices

| Operation | Downtime? | Notes |
|-----------|-----------|-------|
| ADD COLUMN | None | Instant metadata change |
| DROP COLUMN | None | Mutation runs in background |
| MODIFY COLUMN type | None* | Mutation rewrites — can be slow on large tables |
| Change ORDER BY | Brief | Requires table recreation + RENAME |
| Change ENGINE | Brief | Requires table recreation + RENAME |
| ADD INDEX | None | MATERIALIZE runs in background |
| ALTER TTL | None | Takes effect on next merge |

*No application downtime, but queries on the affected column may be slower during mutation.
