---
name: clickhouse-install-auth
description: |
  Install @clickhouse/client and configure authentication to ClickHouse Cloud or self-hosted.
  Use when setting up a new ClickHouse project, configuring connection strings,
  or initializing the official Node.js client.
  Trigger: "install clickhouse", "setup clickhouse client", "clickhouse auth",
  "connect to clickhouse", "clickhouse credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Install & Auth

## Overview

Set up the official ClickHouse client for Node.js or Python and configure authentication
to ClickHouse Cloud or a self-hosted instance.

## Prerequisites

- Node.js 18+ or Python 3.8+
- A running ClickHouse instance (Cloud or self-hosted)
- Connection credentials (host, port, user, password)

## Instructions

### Step 1: Install the Official Client

```bash
# Node.js — official client (HTTP-based, supports streaming)
npm install @clickhouse/client

# Python — official client
pip install clickhouse-connect
```

### Step 2: Configure Environment Variables

```bash
# .env (NEVER commit — add to .gitignore)
CLICKHOUSE_HOST=https://abc123.us-east-1.aws.clickhouse.cloud:8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-password-here

# Self-hosted (HTTP interface on port 8123, native on 9000)
# CLICKHOUSE_HOST=http://localhost:8123
```

### Step 3: Create the Client (Node.js)

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

### Step 4: Verify Connection

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

### Step 5: Python Alternative

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

## Connection Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `url` | `http://localhost:8123` | Full URL including protocol and port |
| `username` | `default` | ClickHouse user |
| `password` | `''` | User password |
| `database` | `default` | Default database for queries |
| `request_timeout` | `30000` | Query timeout in ms |
| `compression.request` | `false` | Compress request bodies (gzip) |
| `compression.response` | `true` | Decompress responses |
| `max_open_connections` | `10` | HTTP keep-alive pool size |
| `clickhouse_settings` | `{}` | Server-side settings per session |

## ClickHouse Cloud vs Self-Hosted

| Feature | Cloud | Self-Hosted |
|---------|-------|-------------|
| Port | 8443 (HTTPS) | 8123 (HTTP) / 8443 (HTTPS) |
| TLS | Required | Optional |
| Engine | SharedMergeTree | MergeTree family |
| Auth | User/password, Cloud API keys | User/password, LDAP, Kerberos |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED` | Server not running | Check host/port, verify ClickHouse is up |
| `Authentication failed` | Wrong user/password | Verify credentials in ClickHouse users.xml or Cloud console |
| `CERTIFICATE_VERIFY_FAILED` | TLS mismatch | Use `https://` for Cloud, check CA certs for self-hosted |
| `TIMEOUT` | Network/firewall | Check IP allowlists in Cloud console, firewall rules |
| `Database not found` | Wrong database name | Run `SHOW DATABASES` to list available databases |

## Resources

- [Official Node.js Client](https://clickhouse.com/docs/integrations/javascript)
- [Official Python Client](https://clickhouse.com/docs/integrations/python)
- [ClickHouse Cloud Quick Start](https://clickhouse.com/docs/cloud/get-started)
- [HTTP Interface Reference](https://clickhouse.com/docs/interfaces/http)

## Next Steps

Proceed to `clickhouse-hello-world` for your first table and query.
