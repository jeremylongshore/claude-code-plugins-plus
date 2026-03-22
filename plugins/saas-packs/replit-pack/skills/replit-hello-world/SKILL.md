---
name: replit-hello-world
description: |
  Create a minimal working Replit app with database, object storage, and auth.
  Use when starting a new Replit project, testing your setup,
  or learning Replit's built-in services (DB, Auth, Object Storage).
  Trigger with phrases like "replit hello world", "replit starter",
  "replit quick start", "first replit app", "replit example".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, starter, database, api]

---
# Replit Hello World

## Overview
Build a working Replit app that demonstrates core platform services: Express/Flask server, Replit Database (key-value store), Object Storage (file uploads), Auth (user login), and PostgreSQL. Produces a running app you can deploy.

## Prerequisites
- Replit App created (template or blank)
- `.replit` and `replit.nix` configured (see `replit-install-auth`)
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Node.js — Express + Replit Database
```typescript
// index.ts
import express from 'express';
import Database from '@replit/database';

const app = express();
const db = new Database();
app.use(express.json());

// Health check with Replit env vars
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    repl: process.env.REPL_SLUG,
    owner: process.env.REPL_OWNER,
    timestamp: new Date().toISOString(),
  });
});

// Replit Key-Value Database CRUD
// Limits: 50 MiB total, 5,000 keys, 1 KB per key, 5 MiB per value
app.post('/api/items', async (req, res) => {
  const { key, value } = req.body;
  await db.set(key, value);
  res.json({ stored: key });
});

app.get('/api/items/:key', async (req, res) => {
  const value = await db.get(req.params.key);
  if (value === null) return res.status(404).json({ error: 'Not found' });
  res.json({ key: req.params.key, value });
});

app.get('/api/items', async (req, res) => {
  const prefix = (req.query.prefix as string) || '';
  const keys = await db.list(prefix);
  res.json({ keys });
});

app.delete('/api/items/:key', async (req, res) => {
  await db.delete(req.params.key);
  res.json({ deleted: req.params.key });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Repl: ${process.env.REPL_SLUG} by ${process.env.REPL_OWNER}`);
});
```

**package.json dependencies:**
```json
{
  "dependencies": {
    "@replit/database": "^2.0.0",
    "express": "^4.18.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "typescript": "^5.0.0"
  }
}
```

### Step 2: Python — Flask + Replit Database
```python
# main.py
from flask import Flask, request, jsonify
from replit import db
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'repl': os.environ.get('REPL_SLUG'),
        'owner': os.environ.get('REPL_OWNER'),
    })

# Replit DB works like a Python dict
@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.json
    db[data['key']] = data['value']
    return jsonify({'stored': data['key']})

@app.route('/api/items/<key>')
def get_item(key):
    if key not in db:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'key': key, 'value': db[key]})

@app.route('/api/items')
def list_items():
    prefix = request.args.get('prefix', '')
    keys = db.prefix(prefix) if prefix else list(db.keys())
    return jsonify({'keys': keys})

@app.route('/api/items/<key>', methods=['DELETE'])
def delete_item(key):
    if key in db:
        del db[key]
    return jsonify({'deleted': key})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
```

### Step 3: Add Object Storage (File Uploads)
```typescript
// storage.ts — Replit Object Storage (App Storage)
import { Client } from '@replit/object-storage';

const storage = new Client();

// Upload text content
await storage.uploadFromText('notes/hello.txt', 'Hello from Replit!');

// Upload from file on disk
await storage.uploadFromFilename('uploads/photo.jpg', '/tmp/photo.jpg');

// Download as text
const { value } = await storage.downloadAsText('notes/hello.txt');
console.log(value); // "Hello from Replit!"

// Download as bytes
const { value: bytes } = await storage.downloadAsBytes('uploads/photo.jpg');

// List objects with prefix
const objects = await storage.list({ prefix: 'notes/' });
for (const obj of objects) {
  console.log(obj.name);  // "notes/hello.txt"
}

// Check existence
const { exists } = await storage.exists('notes/hello.txt');

// Copy object
await storage.copy('notes/hello.txt', 'archive/hello-backup.txt');

// Delete object
await storage.delete('notes/hello.txt');
```

**Python Object Storage:**
```python
from replit.object_storage import Client

storage = Client()

# Upload text
storage.upload_from_text('notes/hello.txt', 'Hello from Replit!')

# Download
content = storage.download_as_text('notes/hello.txt')

# List with prefix
objects = storage.list(prefix='notes/')

# Delete
storage.delete('notes/hello.txt')

# Check existence
exists = storage.exists('notes/hello.txt')
```

### Step 4: Add Auth-Protected Route
```typescript
// Add to index.ts
app.get('/api/me', (req, res) => {
  const userId = req.headers['x-replit-user-id'];
  if (!userId) return res.status(401).json({ error: 'Login required' });

  res.json({
    id: userId,
    name: req.headers['x-replit-user-name'],
    image: req.headers['x-replit-user-profile-image'],
  });
});

// Client-side: fetch('/__replauthuser') returns current user
```

### Step 5: `.replit` for This App
```toml
entrypoint = "index.ts"
run = "npx tsx index.ts"

modules = ["nodejs-20:v8-20230920-bd784b9"]

[nix]
channel = "stable-24_05"

[env]
PORT = "3000"

[deployment]
run = ["sh", "-c", "npx tsx index.ts"]
deploymentTarget = "autoscale"
```

## Output
After running, verify at these endpoints:
- `GET /health` — returns Repl metadata
- `POST /api/items` — stores key-value data
- `GET /api/items?prefix=` — lists keys
- `GET /api/me` — returns authenticated user (when deployed)

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module '@replit/database'` | Not installed | `npm install @replit/database` |
| `db.set is not a function` | Wrong import | Use `new Database()` not `import db` |
| `REPLIT_DB_URL undefined` | Not on Replit | DB only available inside a Repl |
| Object Storage 403 | No bucket provisioned | Create bucket in Object Storage pane |
| Auth headers empty | Running in dev | Auth works only on deployed `.replit.app` |

## Resources
- [Replit Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Object Storage Overview](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/overview)
- [Object Storage TypeScript SDK](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/typescript-api-reference)
- [Replit Auth](https://docs.replit.com/replit-workspace/replit-auth)

## Next Steps
Deploy with `replit-deploy-integration` or add PostgreSQL with `replit-data-handling`.
