---
name: replit-reliability-patterns
description: |
  Implement Replit reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Replit integrations, implementing retry strategies,
  or adding resilience to production Replit services.
  Trigger with phrases like "replit reliability", "replit circuit breaker",
  "replit idempotent", "replit resilience", "replit fallback", "replit bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Reliability Patterns

## Overview
Production reliability patterns for applications hosted on Replit. Replit's container-based hosting, automatic sleep behavior, and ephemeral filesystem require specific resilience strategies for production workloads.

## Prerequisites
- Replit Deployments configured (for always-on)
- Understanding of container lifecycle
- External database for persistent state

## Instructions

### Step 1: Handle Cold Start Gracefully

Replit containers restart on deploy and after sleep. Pre-warm caches and connections on startup.

```python
import time

startup_complete = False
startup_time = None

async def warmup():
    global startup_complete, startup_time
    startup_time = time.time()
    # Pre-load frequently accessed data
    await cache.warm(["config", "feature_flags", "templates"])
    # Verify database connection
    await db.ping()
    startup_complete = True

@app.route('/health')
def health():
    if not startup_complete:
        return {"status": "warming_up"}, 503
    return {"status": "ok", "uptime": time.time() - startup_time}

@app.before_first_request
async def on_startup():
    await warmup()
```

### Step 2: External State for Persistence

Never rely on local filesystem for state that must survive container restarts.

```python
from replit.object_storage import Client as ObjectStorage
import json

class PersistentState:
    def __init__(self):
        self.storage = ObjectStorage()
        self._cache = {}

    def save(self, key: str, data: dict):
        self.storage.upload_from_text(
            f"state/{key}.json",
            json.dumps(data)
        )
        self._cache[key] = data

    def load(self, key: str) -> dict:
        if key in self._cache:
            return self._cache[key]
        try:
            raw = self.storage.download_as_text(f"state/{key}.json")
            data = json.loads(raw)
            self._cache[key] = data
            return data
        except:
            return {}
```

### Step 3: Keep-Alive for Non-Deployment Repls

For Repls not using Deployments, prevent sleep with an external health check ping.

```python
# Internal: expose health endpoint
@app.route('/ping')
def ping():
    return "pong", 200

# External: use a free cron service to ping every 5 minutes
# cron-job.org, UptimeRobot, or similar
# URL: https://your-repl.replit.app/ping
# Interval: 5 minutes
```

### Step 4: Graceful Shutdown Handler

Replit sends SIGTERM before container stop. Save state during shutdown.

```python
import signal, sys

def graceful_shutdown(signum, frame):
    print("Shutting down gracefully...")
    state.save("session", {"last_active": time.time()})
    db.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data loss on restart | Using local filesystem | Use Replit DB or Object Storage |
| Slow first request | Cold start | Pre-warm on startup, show loading state |
| Container sleeping | No activity for 30 min | Use Deployments or external keep-alive |
| Database disconnects | Container restart | Reconnect on startup, connection pooling |

## Examples

### Deployment Health Monitor
```python
health = {
    "container_uptime": time.time() - startup_time,
    "db_connected": await db.ping(),
    "storage_available": storage.exists("state/"),
    "memory_mb": process.memory_info().rss / 1024 / 1024
}
```

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Object Storage](https://docs.replit.com/hosting/databases/object-storage)
