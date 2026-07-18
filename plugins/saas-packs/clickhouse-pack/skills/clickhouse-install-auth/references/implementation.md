# ClickHouse Client — Full Implementation Walkthrough

Complete, copy-paste client setup for Node.js and Python, plus a connection
verification routine. The lean five-step summary lives in `SKILL.md`; this file
carries every code block in full.

## Step 1: Install the Official Client

```bash
# Node.js — official client (HTTP-based, supports streaming)
npm install @clickhouse/client

# Python — official client
pip install clickhouse-connect
```

## Step 2: Configure Environment Variables

```bash
# .env (NEVER commit — add to .gitignore)
CLICKHOUSE_HOST=https://abc123.us-east-1.aws.clickhouse.cloud:8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-password-here

# Self-hosted (HTTP interface on port 8123, native on 9000)
# CLICKHOUSE_HOST=http://localhost:8123
```

## Step 3: Create the Client (Node.js)

```typescript
import { createClient } from '@clickhouse/client';

// ClickHouse Cloud
const client = createClient({
  url: process.env.CLICKHOUSE_HOST,           // https://<host>:8443
  username: process.env.CLICKHOUSE_USER,       // default
  password: process.env.CLICKHOUSE_PASSWORD,
  // ClickHouse Cloud requires TLS — the client handles it via https:// URL
});

// Self-hosted (no TLS)
const localClient = createClient({
  url: 'http://localhost:8123',
  username: 'default',
  password: '',
});
```

## Step 4: Verify Connection

```typescript
async function verifyConnection() {
  // Ping returns true if the server is reachable
  const alive = await client.ping();
  console.log('ClickHouse ping:', alive.success);  // true

  // Run a test query
  const rs = await client.query({
    query: 'SELECT version() AS ver, uptime() AS uptime_sec',
    format: 'JSONEachRow',
  });
  const rows = await rs.json<{ ver: string; uptime_sec: number }>();
  console.log('Server version:', rows[0].ver);
  console.log('Uptime (sec):', rows[0].uptime_sec);
}

verifyConnection().catch(console.error);
```

## Step 5: Python Alternative

```python
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='abc123.us-east-1.aws.clickhouse.cloud',
    port=8443,
    username='default',
    password='your-password-here',
    secure=True,
)

result = client.query('SELECT version(), uptime()')
print(f"Version: {result.result_rows[0][0]}")
```
