---
name: replit-sdk-patterns
description: |
  Apply production-ready patterns for Replit Database, Object Storage, and Auth APIs.
  Use when implementing Replit integrations, structuring data access layers,
  or establishing team coding standards for Replit services.
  Trigger with phrases like "replit patterns", "replit best practices",
  "replit code patterns", "idiomatic replit", "replit SDK".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, python, typescript, patterns]

---
# Replit SDK Patterns

## Overview
Production-ready patterns for Replit's built-in services: Key-Value Database (`@replit/database` / `replit.db`), Object Storage (`@replit/object-storage`), PostgreSQL (`DATABASE_URL`), and Auth headers. Covers singleton clients, error handling, and type-safe wrappers.

## Prerequisites
- `.replit` and `replit.nix` configured (see `replit-install-auth`)
- Familiarity with async/await patterns
- Understanding of Replit's service model

## Instructions

### Step 1: Database Client Singleton (Node.js)
```typescript
// src/db/kv.ts — Replit Key-Value Database wrapper
import Database from '@replit/database';

let instance: Database | null = null;

export function getKV(): Database {
  if (!instance) {
    instance = new Database();
  }
  return instance;
}

// Type-safe KV operations
export async function kvGet<T>(key: string): Promise<T | null> {
  const value = await getKV().get(key);
  return value as T | null;
}

export async function kvSet<T>(key: string, value: T): Promise<void> {
  await getKV().set(key, value);
}

export async function kvList(prefix = ''): Promise<string[]> {
  return getKV().list(prefix);
}

export async function kvDelete(key: string): Promise<void> {
  await getKV().delete(key);
}

// Limits: 50 MiB total, 5,000 keys, 1 KB/key, 5 MiB/value
```

### Step 2: Object Storage Wrapper
```typescript
// src/storage/objects.ts — Replit App Storage (Object Storage)
import { Client } from '@replit/object-storage';

let storage: Client | null = null;

export function getStorage(): Client {
  if (!storage) {
    storage = new Client();
  }
  return storage;
}

// Upload with error handling
export async function uploadText(path: string, content: string): Promise<void> {
  try {
    await getStorage().uploadFromText(path, content);
  } catch (err: any) {
    if (err.name === 'BucketNotFoundError') {
      throw new Error('Object Storage bucket not provisioned. Create one in the Object Storage pane.');
    }
    if (err.name === 'TooManyRequestsError') {
      throw new Error('Object Storage rate limited. Retry after backoff.');
    }
    throw err;
  }
}

// Download with fallback
export async function downloadText(path: string, fallback = ''): Promise<string> {
  try {
    const { value } = await getStorage().downloadAsText(path);
    return value ?? fallback;
  } catch {
    return fallback;
  }
}

// List with prefix filtering
export async function listObjects(prefix: string): Promise<string[]> {
  const objects = await getStorage().list({ prefix });
  return objects.map(obj => obj.name);
}
```

### Step 3: PostgreSQL Connection Pool
```typescript
// src/db/postgres.ts — Replit PostgreSQL
import { Pool, PoolConfig } from 'pg';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    if (!process.env.DATABASE_URL) {
      throw new Error('DATABASE_URL not set. Provision PostgreSQL in the Database pane.');
    }
    const config: PoolConfig = {
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    };
    pool = new Pool(config);
    pool.on('error', (err) => {
      console.error('PostgreSQL pool error:', err.message);
    });
  }
  return pool;
}

// Typed query helper
export async function query<T>(sql: string, params?: any[]): Promise<T[]> {
  const result = await getPool().query(sql, params);
  return result.rows as T[];
}

// Transaction helper
export async function withTransaction<T>(
  fn: (client: import('pg').PoolClient) => Promise<T>
): Promise<T> {
  const client = await getPool().connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

### Step 4: Auth Middleware Pattern
```typescript
// src/middleware/auth.ts — Replit Auth header extraction
import { Request, Response, NextFunction } from 'express';

export interface ReplitUser {
  id: string;
  name: string;
  bio: string;
  url: string;
  profileImage: string;
  roles: string;
  teams: string;
}

export function extractUser(req: Request): ReplitUser | null {
  const id = req.headers['x-replit-user-id'] as string;
  if (!id) return null;
  return {
    id,
    name: (req.headers['x-replit-user-name'] as string) || '',
    bio: (req.headers['x-replit-user-bio'] as string) || '',
    url: (req.headers['x-replit-user-url'] as string) || '',
    profileImage: (req.headers['x-replit-user-profile-image'] as string) || '',
    roles: (req.headers['x-replit-user-roles'] as string) || '',
    teams: (req.headers['x-replit-user-teams'] as string) || '',
  };
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const user = extractUser(req);
  if (!user) return res.status(401).json({ error: 'Login required' });
  (req as any).user = user;
  next();
}
```

### Step 5: Python Patterns
```python
# src/services/replit_services.py
from replit import db
from replit.object_storage import Client as ObjectStorage
import os, json

# KV Database — dict-like API
class KVStore:
    @staticmethod
    def get(key: str, default=None):
        return db.get(key, default)

    @staticmethod
    def set(key: str, value):
        db[key] = value

    @staticmethod
    def delete(key: str):
        if key in db:
            del db[key]

    @staticmethod
    def list_keys(prefix: str = '') -> list:
        return db.prefix(prefix) if prefix else list(db.keys())

# Object Storage
class FileStore:
    def __init__(self):
        self._client = ObjectStorage()

    def upload(self, path: str, content: str):
        self._client.upload_from_text(path, content)

    def download(self, path: str) -> str:
        return self._client.download_as_text(path)

    def exists(self, path: str) -> bool:
        return self._client.exists(path)

    def delete(self, path: str):
        self._client.delete(path)

    def list(self, prefix: str = '') -> list:
        return [obj.name for obj in self._client.list(prefix=prefix)]

# Auth helper for Flask
def get_replit_user(request) -> dict | None:
    user_id = request.headers.get('X-Replit-User-Id')
    if not user_id:
        return None
    return {
        'id': user_id,
        'name': request.headers.get('X-Replit-User-Name', ''),
        'roles': request.headers.get('X-Replit-User-Roles', ''),
        'image': request.headers.get('X-Replit-User-Profile-Image', ''),
    }
```

### Step 6: Retry with Backoff
```typescript
// src/utils/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  opts = { maxRetries: 3, baseMs: 1000, maxMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      if (attempt === opts.maxRetries) throw err;
      const delay = Math.min(opts.baseMs * 2 ** attempt, opts.maxMs);
      const jitter = Math.random() * delay * 0.1;
      await new Promise(r => setTimeout(r, delay + jitter));
    }
  }
  throw new Error('Unreachable');
}
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton client | All services | Avoids connection leaks |
| Typed wrappers | KV/SQL queries | Catches schema issues at compile time |
| Retry + backoff | Transient failures | Handles cold starts and rate limits |
| Transaction helper | Multi-step writes | Atomic operations, safe rollback |

## Resources
- [Replit Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Object Storage TS SDK](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/typescript-api-reference)
- [Object Storage Python SDK](https://docs.replit.com/reference/object-storage-python-sdk)
- [Replit Auth](https://docs.replit.com/replit-workspace/replit-auth)

## Next Steps
Apply patterns in `replit-core-workflow-a` for real-world usage.
