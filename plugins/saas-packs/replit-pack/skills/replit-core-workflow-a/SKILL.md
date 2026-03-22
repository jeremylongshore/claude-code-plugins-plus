---
name: replit-core-workflow-a
description: |
  Build a full-stack web app on Replit with Express/Flask, PostgreSQL, Auth, and deployment.
  Use when creating a new production app on Replit from scratch,
  building the primary user-facing workflow, or following Replit best practices.
  Trigger with phrases like "build replit app", "replit full stack",
  "replit web app", "create replit project", "replit express flask".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, workflow, full-stack]

---
# Replit Core Workflow A — Full-Stack App

## Overview
Build a production-ready web app on Replit: Express or Flask server, PostgreSQL database, Replit Auth for user login, Object Storage for file uploads, and Autoscale deployment. This is the primary money-path workflow for shipping apps on Replit.

## Prerequisites
- Replit account (Core plan or higher for deployments)
- `.replit` and `replit.nix` configured (see `replit-install-auth`)
- PostgreSQL provisioned in the Database pane

## Instructions

### Step 1: Project Structure
```
my-app/
├── .replit                 # Run + deployment config
├── replit.nix              # System dependencies
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts            # Express entry point
│   ├── routes/
│   │   ├── api.ts          # API endpoints
│   │   ├── auth.ts         # Auth routes
│   │   └── health.ts       # Health check
│   ├── services/
│   │   ├── db.ts           # PostgreSQL pool
│   │   └── storage.ts      # Object Storage
│   └── middleware/
│       ├── auth.ts         # Replit Auth middleware
│       └── errors.ts       # Error handler
└── tests/
```

### Step 2: Configuration Files
```toml
# .replit
entrypoint = "src/index.ts"
run = "npx tsx src/index.ts"

modules = ["nodejs-20:v8-20230920-bd784b9"]

[nix]
channel = "stable-24_05"

[env]
NODE_ENV = "development"

[deployment]
run = ["sh", "-c", "npx tsx src/index.ts"]
build = ["sh", "-c", "npm ci"]
deploymentTarget = "autoscale"
```

```nix
# replit.nix
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
    pkgs.postgresql
  ];
}
```

### Step 3: Database Layer
```typescript
// src/services/db.ts
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

// Initialize schema
export async function initDB() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      profile_image TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS posts (
      id SERIAL PRIMARY KEY,
      user_id TEXT REFERENCES users(id),
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);
}

export async function upsertUser(id: string, username: string, image: string) {
  return pool.query(
    `INSERT INTO users (id, username, profile_image)
     VALUES ($1, $2, $3)
     ON CONFLICT (id) DO UPDATE SET username = $2, profile_image = $3
     RETURNING *`,
    [id, username, image]
  );
}

export async function createPost(userId: string, title: string, content: string) {
  return pool.query(
    'INSERT INTO posts (user_id, title, content) VALUES ($1, $2, $3) RETURNING *',
    [userId, title, content]
  );
}

export async function getPosts(limit = 20) {
  return pool.query(
    `SELECT p.*, u.username, u.profile_image
     FROM posts p JOIN users u ON p.user_id = u.id
     ORDER BY p.created_at DESC LIMIT $1`,
    [limit]
  );
}

export { pool };
```

### Step 4: Auth Middleware
```typescript
// src/middleware/auth.ts
import { Request, Response, NextFunction } from 'express';
import { upsertUser } from '../services/db';

export interface AuthedRequest extends Request {
  user: { id: string; name: string; image: string };
}

export async function requireAuth(req: Request, res: Response, next: NextFunction) {
  const userId = req.headers['x-replit-user-id'] as string;
  if (!userId) return res.status(401).json({ error: 'Login required' });

  const name = (req.headers['x-replit-user-name'] as string) || '';
  const image = (req.headers['x-replit-user-profile-image'] as string) || '';

  // Upsert user in database on every authenticated request
  await upsertUser(userId, name, image);
  (req as any).user = { id: userId, name, image };
  next();
}
```

### Step 5: API Routes
```typescript
// src/routes/api.ts
import { Router } from 'express';
import { requireAuth, AuthedRequest } from '../middleware/auth';
import { createPost, getPosts } from '../services/db';
import { Client as StorageClient } from '@replit/object-storage';

const router = Router();
const storage = new StorageClient();

// Public: list posts
router.get('/posts', async (req, res) => {
  const { rows } = await getPosts();
  res.json(rows);
});

// Protected: create post
router.post('/posts', requireAuth, async (req, res) => {
  const { title, content } = req.body;
  const user = (req as AuthedRequest).user;
  const { rows } = await createPost(user.id, title, content);
  res.status(201).json(rows[0]);
});

// Protected: upload file to Object Storage
router.post('/upload', requireAuth, async (req, res) => {
  const user = (req as AuthedRequest).user;
  const filename = `uploads/${user.id}/${Date.now()}-${req.body.name}`;
  await storage.uploadFromText(filename, req.body.content);
  res.json({ path: filename });
});

export default router;
```

### Step 6: Entry Point
```typescript
// src/index.ts
import express from 'express';
import { initDB, pool } from './services/db';
import apiRoutes from './routes/api';

const app = express();
app.use(express.json());

// Health check (required for Replit deployments)
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', uptime: process.uptime() });
  } catch {
    res.status(503).json({ status: 'degraded' });
  }
});

// Auth info endpoint (client-side: GET /__replauthuser)
app.get('/api/me', (req, res) => {
  const id = req.headers['x-replit-user-id'];
  if (!id) return res.json({ loggedIn: false });
  res.json({
    loggedIn: true,
    id,
    name: req.headers['x-replit-user-name'],
    image: req.headers['x-replit-user-profile-image'],
  });
});

app.use('/api', apiRoutes);

const PORT = parseInt(process.env.PORT || '3000');
initDB().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
  });
});
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| DATABASE_URL undefined | PostgreSQL not provisioned | Create database in Database pane |
| Auth headers empty | Running in dev mode | Auth only works on deployed `.replit.app` |
| Object Storage 403 | No bucket created | Provision bucket in Object Storage pane |
| Port conflict | Multiple services on same port | Use different ports, set `ignorePorts` |

## Resources
- [Replit Deployments](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)
- [PostgreSQL on Replit](https://docs.replit.com/cloud-services/storage-and-databases/postgresql-on-replit)
- [Replit Auth](https://docs.replit.com/replit-workspace/replit-auth)
- [Object Storage](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/overview)

## Next Steps
For collaboration and admin workflows, see `replit-core-workflow-b`.
