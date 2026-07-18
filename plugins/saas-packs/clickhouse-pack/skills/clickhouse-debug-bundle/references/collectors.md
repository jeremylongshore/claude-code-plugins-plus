# Automated Debug Bundle Collectors

Two ready-to-run collectors that execute every diagnostic query and package the
output into a single artifact you can attach to a support ticket. Use the bash
script for shell/CI environments and the Node.js collector when you already have
a `@clickhouse/client` connection in-process.

## Authentication

Both collectors authenticate over the ClickHouse HTTP interface using
environment variables — no credentials are hardcoded:

- `CLICKHOUSE_HOST` (default `http://localhost:8123`)
- `CLICKHOUSE_USER` (default `default`)
- `CLICKHOUSE_PASSWORD` (default empty)

The bash script passes them to `curl --user`; the Node.js collector expects an
already-authenticated `createClient({ url, username, password })` handle. Never
commit credentials — export them in the shell or read them from your secret
store before running.

## Bash Collector

```bash
#!/bin/bash
# clickhouse-debug-bundle.sh
set -euo pipefail

CH_HOST="${CLICKHOUSE_HOST:-http://localhost:8123}"
CH_USER="${CLICKHOUSE_USER:-default}"
CH_PASS="${CLICKHOUSE_PASSWORD:-}"
BUNDLE="ch-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

ch_query() {
  curl -sS "${CH_HOST}" \
    --user "${CH_USER}:${CH_PASS}" \
    --data-binary "$1" 2>&1
}

echo "Collecting ClickHouse diagnostics..."

ch_query "SELECT version(), uptime(), currentDatabase()" > "$BUNDLE/version.txt"
ch_query "SELECT * FROM system.metrics FORMAT TabSeparatedWithNames" > "$BUNDLE/metrics.tsv"
ch_query "SELECT * FROM system.events FORMAT TabSeparatedWithNames" > "$BUNDLE/events.tsv"
ch_query "SELECT database, table, count() AS parts, sum(rows) AS rows, \
  formatReadableSize(sum(bytes_on_disk)) AS size FROM system.parts \
  WHERE active GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC \
  FORMAT TabSeparatedWithNames" > "$BUNDLE/tables.tsv"
ch_query "SELECT * FROM system.merges FORMAT TabSeparatedWithNames" > "$BUNDLE/merges.tsv"
ch_query "SELECT * FROM system.query_log WHERE type IN ('ExceptionWhileProcessing') \
  AND event_time >= now() - INTERVAL 1 HOUR ORDER BY event_time DESC LIMIT 50 \
  FORMAT TabSeparatedWithNames" > "$BUNDLE/errors.tsv"
ch_query "SELECT * FROM system.replicas FORMAT TabSeparatedWithNames" > "$BUNDLE/replicas.tsv" 2>/dev/null || true

tar -czf "${BUNDLE}.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: ${BUNDLE}.tar.gz"
```

## Node.js Debug Collector

```typescript
import { createClient } from '@clickhouse/client';

async function collectDebugBundle(client: ReturnType<typeof createClient>) {
  const queries = {
    version: 'SELECT version() AS ver, uptime() AS up',
    tables: `SELECT database, table, count() AS parts, sum(rows) AS rows
             FROM system.parts WHERE active GROUP BY database, table
             ORDER BY sum(bytes_on_disk) DESC LIMIT 20`,
    slow: `SELECT query_duration_ms, substring(query,1,200) AS q
           FROM system.query_log WHERE type='QueryFinish'
           AND event_time >= now() - INTERVAL 1 HOUR
           ORDER BY query_duration_ms DESC LIMIT 10`,
    errors: `SELECT exception_code, exception, substring(query,1,200) AS q
             FROM system.query_log WHERE type='ExceptionWhileProcessing'
             AND event_time >= now() - INTERVAL 1 HOUR LIMIT 10`,
    merges: 'SELECT * FROM system.merges',
  };

  const bundle: Record<string, unknown> = {};
  for (const [key, sql] of Object.entries(queries)) {
    try {
      const rs = await client.query({ query: sql, format: 'JSONEachRow' });
      bundle[key] = await rs.json();
    } catch (e) {
      bundle[key] = { error: (e as Error).message };
    }
  }

  return bundle;
}
```
