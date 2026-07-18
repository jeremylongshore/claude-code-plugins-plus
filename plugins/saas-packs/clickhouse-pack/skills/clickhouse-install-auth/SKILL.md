---
name: clickhouse-install-auth
description: |
  Install @clickhouse/client and configure authentication to ClickHouse Cloud
  or self-hosted. Use when setting up a new ClickHouse project, configuring
  connection strings, or initializing the official Node.js or Python client.
  Trigger with "install clickhouse", "setup clickhouse client", "clickhouse
  auth", "connect to clickhouse", "clickhouse credentials".
allowed-tools: Read, Write, Bash(npm:*), Bash(pnpm:*), Bash(pip:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Install & Auth

## Overview

Set up the official ClickHouse client for Node.js or Python and configure
authentication to ClickHouse Cloud or a self-hosted instance. The workflow
below is the high-level path; each step links to a full walkthrough with
complete code in [references/implementation.md](references/implementation.md).

## Prerequisites

- Node.js 18+ or Python 3.8+
- A running ClickHouse instance (Cloud or self-hosted)
- Connection credentials (host, port, user, password)

## Instructions

Follow these five steps. Read the current project for an existing `.env` before
writing one; write credentials to `.env` (never commit it).

1. **Install the official client.** Node.js uses the HTTP-based
   `@clickhouse/client`; Python uses `clickhouse-connect`.

   ```bash
   npm install @clickhouse/client   # Node.js
   pip install clickhouse-connect   # Python
   ```

2. **Configure environment variables.** Put host, user, and password in `.env`
   and add it to `.gitignore`. Cloud hosts use port `8443` (HTTPS); self-hosted
   uses `8123` (HTTP).

3. **Create the client.** Pass `url`, `username`, and `password` to
   `createClient()` (Node.js) or `get_client()` (Python). Cloud requires TLS —
   supply an `https://` URL and the client handles it.

   ```typescript
   import { createClient } from '@clickhouse/client';
   const client = createClient({
     url: process.env.CLICKHOUSE_HOST,
     username: process.env.CLICKHOUSE_USER,
     password: process.env.CLICKHOUSE_PASSWORD,
   });
   ```

4. **Verify the connection** with `client.ping()` plus a `SELECT version()`
   probe.

5. **Python alternative** — same shape via `clickhouse_connect.get_client(...)`
   with `secure=True` for Cloud.

Full code for every step (Cloud + self-hosted variants, the verify routine,
and the Python client): [references/implementation.md](references/implementation.md).
Every `createClient()` option and a Cloud-vs-self-hosted comparison:
[references/connection-reference.md](references/connection-reference.md).

## Output

After completing the workflow you have:

- The official client installed (`@clickhouse/client` or `clickhouse-connect`).
- A `.env` holding `CLICKHOUSE_HOST` / `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD`
  (gitignored).
- An initialized client module that reads those variables.
- A successful `ping()` returning `success: true` and a `SELECT version()`
  probe printing the server version and uptime — proof the connection and auth
  both work.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED` | Server not running | Check host/port, verify ClickHouse is up |
| `Authentication failed` | Wrong user/password | Verify credentials in ClickHouse users.xml or Cloud console |
| `CERTIFICATE_VERIFY_FAILED` | TLS mismatch | Use `https://` for Cloud, check CA certs for self-hosted |
| `TIMEOUT` | Network/firewall | Check IP allowlists in Cloud console, firewall rules |
| `Database not found` | Wrong database name | Run `SHOW DATABASES` to list available databases |

## Examples

**Connect to ClickHouse Cloud (Node.js).** With `.env` populated, create the
client against the `https://…:8443` host and verify:

```typescript
const alive = await client.ping();        // { success: true }
const rs = await client.query({
  query: 'SELECT version() AS ver',
  format: 'JSONEachRow',
});
console.log((await rs.json())[0].ver);    // e.g. "24.8.1"
```

**Connect to a local self-hosted instance (no TLS).** Point at the HTTP
interface on `8123` with an empty password:

```typescript
const localClient = createClient({
  url: 'http://localhost:8123',
  username: 'default',
  password: '',
});
```

The full Cloud + self-hosted + Python set is in
[references/implementation.md](references/implementation.md).

## Resources

- [Official Node.js Client](https://clickhouse.com/docs/integrations/javascript)
- [Official Python Client](https://clickhouse.com/docs/integrations/python)
- [ClickHouse Cloud Quick Start](https://clickhouse.com/docs/cloud/get-started)
- [HTTP Interface Reference](https://clickhouse.com/docs/interfaces/http)

## Next Steps

Proceed to `clickhouse-hello-world` to create your first table and run an
insert-and-select round trip against the connection you just verified.
