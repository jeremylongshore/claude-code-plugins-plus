---
name: replit-data-handling
description: |
  Implement secure data handling on Replit: PostgreSQL, KV Database, Object Storage, and data security patterns.
  Use when handling sensitive data, connecting databases, implementing data access patterns,
  or ensuring secure data flow in Replit-hosted applications.
  Trigger with phrases like "replit data", "replit database",
  "replit PostgreSQL", "replit storage", "replit data security", "replit GDPR".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, database, storage, security]

---
# Replit Data Handling

## Overview
Manage application data securely across Replit's three storage systems: PostgreSQL (relational), Key-Value Database (simple cache/state), and Object Storage (files/blobs). Covers connection patterns, security, data validation, and choosing the right storage for each use case.

## Prerequisites
- Replit account with Workspace access
- PostgreSQL provisioned in Database pane (for SQL use cases)
- Understanding of Replit Secrets for credentials

## Storage Decision Matrix
| Need | Storage | API | Limits |
|------|---------|-----|--------|
| Structured data, queries | PostgreSQL | `pg` npm / `psycopg2` | Plan-dependent |
| Simple key-value, cache | Replit KV Database | `@replit/database` / `replit.db` | 50 MiB, 5K keys |
| Files, images, backups | Object Storage | `@replit/object-storage` | Plan-dependent |

## Instructions

### Step 1: PostgreSQL — Secure Connection
```typescript
// src/services/database.ts
import { Pool, PoolConfig } from 'pg';

function createPool(): Pool {
  if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL not set. Create a database in the Database pane.');
  }

  const config: PoolConfig = {
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }, // Required for Replit PostgreSQL
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  };

  const pool = new Pool(config);

  // Log errors without exposing connection string
  pool.on('error', (err) => {
    console.error('Database pool error:', err.message);
    // Never: console.error(err) — may contain credentials
  });

  return pool;
}

export const pool = createPool();

// Parameterized queries ONLY — never string concatenation
export async function findUser(userId: string) {
  // GOOD: parameterized
  const result = await pool.query(
    'SELECT id, username, created_at FROM users WHERE id = $1',
    [userId]
  );
  return result.rows[0];

  // BAD: SQL injection risk
  // pool.query(`SELECT * FROM users WHERE id = '${userId}'`)
}
```

**Dev vs Production databases:**
```markdown
Replit auto-provisions separate databases:
- Development: used when running in Workspace ("Run" button)
- Production: used when accessed via deployment URL

View in Database pane:
- Development tab: test data, iterate freely
- Production tab: live customer data, handle with care

Both use the same DATABASE_URL — Replit routes automatically.
```

### Step 2: Key-Value Database — Session & Cache

**Node.js:**
```typescript
// src/services/cache.ts
import Database from '@replit/database';

const db = new Database();

// Cache with TTL using KV
export async function cacheGet<T>(key: string): Promise<T | null> {
  const entry = await db.get(key) as { value: T; expiresAt: number } | null;
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    await db.delete(key);
    return null;
  }
  return entry.value;
}

export async function cacheSet<T>(key: string, value: T, ttlMs: number): Promise<void> {
  await db.set(key, { value, expiresAt: Date.now() + ttlMs });
}

// Session storage
export async function setSession(sessionId: string, data: any): Promise<void> {
  await db.set(`session:${sessionId}`, {
    ...data,
    createdAt: Date.now(),
  });
}

export async function getSession(sessionId: string): Promise<any> {
  return db.get(`session:${sessionId}`);
}

// Clean up expired sessions
export async function cleanSessions(): Promise<number> {
  const keys = await db.list('session:');
  let cleaned = 0;
  const oneDay = 24 * 60 * 60 * 1000;

  for (const key of keys) {
    const session = await db.get(key) as any;
    if (session && Date.now() - session.createdAt > oneDay) {
      await db.delete(key);
      cleaned++;
    }
  }
  return cleaned;
}

// Limits reminder: 50 MiB total, 5,000 keys, 1 KB/key, 5 MiB/value
```

**Python:**
```python
from replit import db
import json, time

# Dict-like API
db["settings"] = {"theme": "dark", "lang": "en"}
settings = db["settings"]

# List keys by prefix
user_keys = db.prefix("user:")

# Delete
del db["old_key"]

# Cache pattern with TTL
def cache_set(key: str, value, ttl_seconds: int):
    db[f"cache:{key}"] = {
        "value": value,
        "expires_at": time.time() + ttl_seconds
    }

def cache_get(key: str):
    entry = db.get(f"cache:{key}")
    if not entry or time.time() > entry["expires_at"]:
        return None
    return entry["value"]
```

### Step 3: Object Storage — File Uploads

**Node.js:**
```typescript
// src/services/files.ts
import { Client } from '@replit/object-storage';
import express from 'express';

const storage = new Client();
const router = express.Router();

// File upload endpoint
router.post('/upload', express.raw({ limit: '10mb', type: '*/*' }), async (req, res) => {
  const userId = req.headers['x-replit-user-id'] as string;
  if (!userId) return res.status(401).json({ error: 'Login required' });

  const filename = req.headers['x-filename'] as string || `file-${Date.now()}`;
  const path = `uploads/${userId}/${filename}`;

  await storage.uploadFromBytes(path, req.body);

  res.json({ path, size: req.body.length });
});

// File download
router.get('/files/:userId/:filename', async (req, res) => {
  const path = `uploads/${req.params.userId}/${req.params.filename}`;

  try {
    const { value } = await storage.downloadAsBytes(path);
    res.send(Buffer.from(value));
  } catch {
    res.status(404).json({ error: 'File not found' });
  }
});

// List user files
router.get('/files/:userId', async (req, res) => {
  const objects = await storage.list({ prefix: `uploads/${req.params.userId}/` });
  res.json(objects.map(o => ({ name: o.name })));
});

export default router;
```

**Python:**
```python
from replit.object_storage import Client

storage = Client()

# Upload
storage.upload_from_text("reports/daily.json", json.dumps(report))
storage.upload_from_filename("backups/db.sql", "/tmp/dump.sql")

# Download
content = storage.download_as_text("reports/daily.json")
storage.download_to_filename("backups/db.sql", "/tmp/restore.sql")

# Check existence
if storage.exists("reports/daily.json"):
    storage.delete("reports/daily.json")
```

### Step 4: Data Sanitization
```typescript
// src/middleware/sanitize.ts
import { z } from 'zod';

// Validate all input with Zod schemas
const UserInputSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email().toLowerCase(),
  message: z.string().max(5000).trim(),
});

export function validateInput<T>(schema: z.ZodType<T>, data: unknown) {
  const result = schema.safeParse(data);
  if (!result.success) {
    return { valid: false as const, errors: result.error.flatten().fieldErrors };
  }
  return { valid: true as const, data: result.data };
}

// Strip sensitive fields from responses
export function sanitizeUser(user: any) {
  const { password_hash, email, phone, ...safe } = user;
  return safe;
}

// Safe logging — redact sensitive fields
export function safeLog(message: string, data?: any) {
  if (!data) return console.log(message);

  const redacted = JSON.parse(JSON.stringify(data, (key, value) => {
    if (['password', 'token', 'secret', 'api_key', 'ssn'].includes(key.toLowerCase())) {
      return '[REDACTED]';
    }
    return value;
  }));

  console.log(message, redacted);
}
```

### Step 5: Error Response Safety
```typescript
// Never expose internal details in production
app.use((err: Error, req: any, res: any, next: any) => {
  safeLog('Error:', { message: err.message, path: req.path });

  const isProduction = process.env.NODE_ENV === 'production';
  res.status(500).json({
    error: isProduction ? 'Internal server error' : err.message,
    ...(isProduction ? {} : { stack: err.stack }),
  });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| DATABASE_URL undefined | PostgreSQL not created | Provision in Database pane |
| KV `Max storage exceeded` | Over 50 MiB | Migrate to PostgreSQL or Object Storage |
| Object Storage 403 | Bucket not provisioned | Create in Object Storage pane |
| SQL injection | String concatenation | Use parameterized queries ($1, $2) |
| PII in logs | Full object logging | Use safeLog() with field redaction |

## Resources
- [PostgreSQL on Replit](https://docs.replit.com/cloud-services/storage-and-databases/postgresql-on-replit)
- [Replit KV Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Object Storage](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/overview)
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)

## Next Steps
For team access control, see `replit-enterprise-rbac`.
