---
name: replit-known-pitfalls
description: |
  Avoid the top Replit anti-patterns: ephemeral filesystem, public secrets, port binding, Nix gotchas, and database limits.
  Use when reviewing Replit code, onboarding developers,
  or auditing existing Replit apps for common mistakes.
  Trigger with phrases like "replit mistakes", "replit anti-patterns",
  "replit pitfalls", "replit what not to do", "replit code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, audit, anti-patterns]

---
# Replit Known Pitfalls

## Overview
Real gotchas when building on Replit. Each pitfall includes what goes wrong, why, and the correct pattern. Based on common failures in Replit's ephemeral container model, Nix-based environment, and cloud hosting platform.

## Pitfall Reference

### 1. Writing to Local Filesystem for Persistence
**What happens:** Data is lost when the container restarts, deploys, or sleeps.

```python
# BAD — files disappear on container restart
with open("user_data.json", "w") as f:
    json.dump(data, f)

# GOOD — use Replit's persistent storage
from replit import db
db["user_data"] = data

# For files, use Object Storage
from replit.object_storage import Client
storage = Client()
storage.upload_from_text("user_data.json", json.dumps(data))
```

**Rule:** Anything written to the filesystem is ephemeral. Use PostgreSQL, KV Database, or Object Storage for data that must survive restarts.

---

### 2. Hardcoding Secrets in Source Code
**What happens:** Secrets are visible to anyone who views your Repl (public by default on free plans). Replit's Secret Scanner catches some cases but not all.

```python
# BAD — exposed in public Repl
API_KEY = "sk-live-abc123"
DATABASE_URL = "postgresql://user:password@host/db"

# GOOD — use Replit Secrets (lock icon in sidebar)
import os
API_KEY = os.environ["API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
```

---

### 3. Binding to localhost Instead of 0.0.0.0
**What happens:** App starts but Webview is blank. Replit's proxy can't reach the app.

```typescript
// BAD — unreachable from Webview and deployments
app.listen(3000, '127.0.0.1');
app.listen(3000, 'localhost');

// GOOD — accessible to Replit's proxy
app.listen(3000, '0.0.0.0');

// BEST — use PORT env var
const PORT = parseInt(process.env.PORT || '3000');
app.listen(PORT, '0.0.0.0');
```

---

### 4. Ignoring Nix System Dependencies
**What happens:** Python packages with C extensions (Pillow, psycopg2, cryptography) fail to build with cryptic errors.

```nix
# BAD — missing system libraries
{ pkgs }: {
  deps = [ pkgs.python311 ];
}

# GOOD — include system libraries for native packages
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.zlib          # Required for Pillow
    pkgs.libjpeg       # Required for Pillow
    pkgs.libffi        # Required for cffi/cryptography
    pkgs.openssl       # Required for cryptography
    pkgs.postgresql    # Required for psycopg2
  ];
}
```

**After editing `replit.nix`:** Exit and re-enter the Shell tab to reload.

---

### 5. Using Replit KV Database for Large Data
**What happens:** Writes fail silently or throw errors after hitting the 50 MiB limit.

```python
# BAD — storing large blobs in KV (50 MiB limit, 5K keys)
db["images"] = base64_encoded_images  # Hits limit quickly
db["full_dataset"] = huge_json        # 5 MiB per value max

# GOOD — use KV for metadata, PostgreSQL/Storage for data
db["image_count"] = 42
db["last_upload"] = "2025-01-15"

# Large data in Object Storage
storage.upload_from_text("data/full_dataset.json", json.dumps(data))

# Structured data in PostgreSQL
pool.query("INSERT INTO images (url, metadata) VALUES ($1, $2)", [url, meta])
```

**KV Limits:** 50 MiB total, 5,000 keys, 1 KB per key, 5 MiB per value.

---

### 6. Expecting Auth Headers in Development
**What happens:** `X-Replit-User-Id` is always undefined in Workspace Webview.

```typescript
// BAD — breaks during development
app.get('/api/me', (req, res) => {
  const userId = req.headers['x-replit-user-id'] as string;
  // userId is ALWAYS undefined in Workspace Webview
  res.json({ userId }); // { userId: undefined }
});

// GOOD — provide dev fallback
app.get('/api/me', (req, res) => {
  let userId = req.headers['x-replit-user-id'] as string;

  if (!userId && process.env.NODE_ENV !== 'production') {
    userId = 'dev-user-123'; // Mock user for development
  }

  if (!userId) return res.status(401).json({ error: 'Login required' });
  res.json({ userId });
});
```

**Auth only works on:** deployed `.replit.app` URLs, `.replit.dev` preview URLs, and custom domains.

---

### 7. Using "Always On" Instead of Deployments
**What happens:** Legacy "Always On" feature is more expensive and less reliable than modern Deployments.

```markdown
BAD (legacy):
  Settings > Always On > Enable
  - Keeps Repl running but uses more resources
  - No build step, no rollbacks, no scaling

GOOD (modern):
  Deploy button > Autoscale or Reserved VM
  - Built-in rollbacks
  - Separate dev/prod databases
  - Auto-scaling (Autoscale)
  - Build step for optimization
  - Custom domains with auto-SSL
```

---

### 8. Forgetting to Close Database Connections
**What happens:** Connection pool exhaustion. New requests fail with timeout errors.

```python
# BAD — creates a new connection per request
@app.route('/api/data')
def get_data():
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    # ... never closed!

# GOOD — use a connection pool
from psycopg2.pool import SimpleConnectionPool
pool = SimpleConnectionPool(1, 10, os.environ["DATABASE_URL"])

@app.route('/api/data')
def get_data():
    conn = pool.getconn()
    try:
        # ... use connection
        pass
    finally:
        pool.putconn(conn)
```

```python
# Also: close KV database on shutdown
from replit import db
import atexit

atexit.register(db.close)  # Clean termination
```

---

### 9. Not Handling SIGTERM
**What happens:** Container stops mid-request. In-progress work is lost.

```typescript
// BAD — abrupt shutdown
// (no signal handler — process killed immediately)

// GOOD — graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down...');
  server.close();           // Stop accepting new requests
  await pool.end();         // Close database connections
  await saveState();        // Persist in-memory state
  process.exit(0);
});
```

---

### 10. Mixing npm and System Packages
**What happens:** Confusion between Nix system packages and npm/pip language packages.

```markdown
Nix (replit.nix) = system packages:
  - Node.js runtime, Python runtime
  - System libraries (zlib, openssl, libjpeg)
  - CLI tools (postgresql client, git)

npm/pip = language packages:
  - express, flask, react
  - @replit/database, @replit/object-storage
  - pg, psycopg2

Both are needed:
  1. replit.nix: pkgs.nodejs-20_x (provides Node.js)
  2. Shell: npm install express (provides Express)

Common mistake:
  Expecting "npm install" to provide system libraries
  → Need pkgs.openssl in replit.nix for crypto packages
```

## Quick Audit Script
```bash
#!/bin/bash
echo "=== Replit Pitfall Audit ==="

# Check for hardcoded secrets
echo -n "Secrets in code: "
grep -rn "sk[-_]\(live\|test\)" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | wc -l

# Check port binding
echo -n "Localhost binding: "
grep -rn "localhost\|127\.0\.0\.1" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | grep -c "listen\|bind"

# Check filesystem writes
echo -n "Filesystem writes: "
grep -rn "writeFileSync\|open.*['\"]w['\"]" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | grep -v ".replit\|replit.nix" | wc -l

# Check for replit.nix
echo -n "replit.nix: "
[ -f replit.nix ] && echo "exists" || echo "MISSING"

# Check for SIGTERM handler
echo -n "SIGTERM handler: "
grep -rn "SIGTERM" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | wc -l
```

## Resources
- [Replit Docs](https://docs.replit.com)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [Replit Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Secure Vibe Coding](https://blog.replit.com/16-ways-to-vibe-code-securely)

## Next Steps
For production readiness, see `replit-prod-checklist`.
