---
name: replit-reliability-patterns
description: |
  Implement reliability patterns for Replit: cold start handling, graceful shutdown, persistent state, and keep-alive.
  Use when building fault-tolerant Replit apps, handling container restarts,
  or adding resilience to production Replit deployments.
  Trigger with phrases like "replit reliability", "replit container restart",
  "replit data persistence", "replit always on", "replit graceful shutdown".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, reliability, resilience]

---
# Replit Reliability Patterns

## Overview
Production reliability patterns for Replit's container-based hosting. Replit containers restart on deploy, sleep on inactivity (Autoscale), and have ephemeral filesystems. These patterns ensure your app survives container lifecycle events gracefully.

## Prerequisites
- Replit Deployment configured
- External storage for persistent state (PostgreSQL or Object Storage)
- Understanding of Replit container lifecycle

## Container Lifecycle
```
Container starts → App boots → Handles requests → [Sleep or Restart]
                                                         │
                    ┌────────────────────────────────────┘
                    │
            ┌───────┴──────┐
            │ Sleep trigger │  Autoscale: no traffic for ~5 min
            │ Restart trigger│  Deploy, config change, or crash
            └───────┬──────┘
                    │
        State lost: filesystem, in-memory data, caches
        State kept: PostgreSQL, KV Database, Object Storage, Secrets
```

## Instructions

### Step 1: Graceful Startup
```typescript
// Handle cold starts — prioritize accepting requests over initialization
import express from 'express';

const app = express();
let ready = false;

// Accept requests immediately
app.listen(parseInt(process.env.PORT || '3000'), '0.0.0.0', () => {
  console.log(`Server started in ${process.uptime().toFixed(1)}s`);
  // Initialize in background
  initialize().catch(console.error);
});

// Health endpoint reflects readiness
app.get('/health', (req, res) => {
  res.status(ready ? 200 : 503).json({
    status: ready ? 'ready' : 'initializing',
    uptime: process.uptime(),
  });
});

async function initialize() {
  const start = Date.now();
  // Pre-connect database
  await pool.query('SELECT 1');
  // Warm caches
  await warmCache();
  ready = true;
  console.log(`Initialization complete in ${Date.now() - start}ms`);
}
```

### Step 2: Graceful Shutdown
Replit sends SIGTERM before stopping containers. Save state during shutdown.

```typescript
// Graceful shutdown handler
let shutdownInProgress = false;

async function shutdown(signal: string) {
  if (shutdownInProgress) return;
  shutdownInProgress = true;

  console.log(`${signal} received. Shutting down gracefully...`);

  // 1. Stop accepting new requests
  server.close();

  // 2. Finish in-flight requests (give them 10 seconds)
  await new Promise(resolve => setTimeout(resolve, 10000));

  // 3. Save critical state
  try {
    await saveAppState();
  } catch (err: any) {
    console.error('Failed to save state:', err.message);
  }

  // 4. Close database connections
  await pool.end();

  // 5. Close KV database
  // @replit/database: call close() to terminate cleanly
  // replit.db (Python): call replit.db.close()

  console.log('Shutdown complete');
  process.exit(0);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

const server = app.listen(PORT, '0.0.0.0');
```

### Step 3: Persistent State (Survive Restarts)
Never rely on the local filesystem for data that must persist:

```typescript
// BAD: Local filesystem is ephemeral
import fs from 'fs';
fs.writeFileSync('state.json', JSON.stringify(appState));
// GONE after container restart

// GOOD: Use Replit KV Database for small state
import Database from '@replit/database';
const kv = new Database();

async function saveAppState() {
  await kv.set('app:state', {
    lastActive: Date.now(),
    version: process.env.npm_package_version,
    counters: appCounters,
  });
}

async function loadAppState() {
  return (await kv.get('app:state')) || { lastActive: 0, counters: {} };
}

// GOOD: Use Object Storage for larger data / files
import { Client } from '@replit/object-storage';
const storage = new Client();

async function saveReport(data: any) {
  await storage.uploadFromText(
    `reports/${new Date().toISOString()}.json`,
    JSON.stringify(data)
  );
}
```

**Python equivalent:**
```python
from replit import db
from replit.object_storage import Client as Storage
import json, time, signal, sys

# Persistent state via KV
def save_state(data):
    db["app:state"] = {
        "data": data,
        "saved_at": time.time()
    }

def load_state():
    return db.get("app:state", {"data": {}, "saved_at": 0})

# Persistent files via Object Storage
storage = Storage()

def save_backup(filename, content):
    storage.upload_from_text(f"backups/{filename}", content)

# Graceful shutdown
def shutdown(signum, frame):
    print("Shutting down...")
    save_state(app_data)
    db.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
```

### Step 4: Keep-Alive for Non-Deployment Repls
For Repls not using Deployments, prevent sleep with external pinging:

```markdown
Option 1: External cron service (recommended)
- UptimeRobot (free: 50 monitors, 5-min intervals)
- cron-job.org (free: 1-min intervals)
- URL: https://your-repl.replit.app/ping
- Interval: 4 minutes (Replit sleeps after ~5 min)

Option 2: Self-ping (less reliable — sleeps if service itself sleeps)
```

```typescript
// Lightweight ping endpoint
app.get('/ping', (req, res) => res.send('pong'));
```

```markdown
Best option: Use Replit Deployments instead
- Autoscale: scales to zero but wakes on request
- Reserved VM: always-on, no sleeping
- Both are more reliable than keep-alive hacks
```

### Step 5: Database Connection Resilience
```typescript
// Auto-reconnect on database failures
import { Pool } from 'pg';

function createResilientPool(): Pool {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: 5,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

  pool.on('error', (err) => {
    console.error('Pool error (will auto-reconnect):', err.message);
    // Pool auto-replaces failed connections on next query
  });

  return pool;
}

// Retry wrapper for database queries
async function queryWithRetry(
  pool: Pool,
  sql: string,
  params?: any[],
  retries = 3
): Promise<any> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await pool.query(sql, params);
    } catch (err: any) {
      if (attempt === retries) throw err;
      console.warn(`DB query failed (attempt ${attempt}): ${err.message}`);
      await new Promise(r => setTimeout(r, 1000 * attempt));
    }
  }
}
```

### Step 6: Deployment Health Monitor
```typescript
// Self-monitoring deployment health
const healthMetrics = {
  startTime: Date.now(),
  requestCount: 0,
  errorCount: 0,
  lastError: null as string | null,
};

app.use((req, res, next) => {
  healthMetrics.requestCount++;
  res.on('finish', () => {
    if (res.statusCode >= 500) {
      healthMetrics.errorCount++;
      healthMetrics.lastError = `${res.statusCode} on ${req.method} ${req.path}`;
    }
  });
  next();
});

app.get('/health', (req, res) => {
  const uptime = (Date.now() - healthMetrics.startTime) / 1000;
  const errorRate = healthMetrics.requestCount > 0
    ? (healthMetrics.errorCount / healthMetrics.requestCount * 100).toFixed(2)
    : '0';

  res.json({
    status: parseFloat(errorRate) > 5 ? 'degraded' : 'healthy',
    uptime: `${uptime.toFixed(0)}s`,
    requests: healthMetrics.requestCount,
    errors: healthMetrics.errorCount,
    errorRate: `${errorRate}%`,
    lastError: healthMetrics.lastError,
    memory: Math.round(process.memoryUsage().heapUsed / 1024 / 1024) + 'MB',
  });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data lost on restart | Using local filesystem | Use KV Database or Object Storage |
| Slow first request | Cold start (Autoscale) | Pre-warm, or use Reserved VM |
| Container sleeping | No traffic for 5 min | Use Deployments or external keepalive |
| DB disconnects | Container restart | Auto-reconnect via Pool + retry |
| State inconsistency | Crash before save | Save state periodically + on SIGTERM |

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit KV Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Object Storage](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/overview)
- [Deployment Rollbacks](https://blog.replit.com/introducing-deployment-rollbacks)

## Next Steps
For policy enforcement, see `replit-policy-guardrails`.
