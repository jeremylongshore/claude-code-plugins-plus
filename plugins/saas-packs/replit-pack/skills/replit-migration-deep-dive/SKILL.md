---
name: replit-migration-deep-dive
description: |
  Migrate to Replit from Heroku, Railway, Vercel, or local development environments.
  Use when moving an existing app to Replit, migrating databases,
  or converting Docker/buildpack apps to Replit's Nix-based system.
  Trigger with phrases like "migrate to replit", "heroku to replit",
  "move to replit", "replit migration", "railway to replit", "convert to replit".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, migration, heroku, railway]

---
# Replit Migration Deep Dive

## Current State
!`cat .replit 2>/dev/null | head -10 || echo 'No .replit found'`
!`cat Procfile 2>/dev/null || echo 'No Procfile (not Heroku)'`
!`cat Dockerfile 2>/dev/null | head -10 || echo 'No Dockerfile'`
!`cat railway.json 2>/dev/null || echo 'No railway.json'`

## Overview
Comprehensive guide for migrating existing applications to Replit from Heroku, Railway, Vercel, Render, or local development. Covers converting configuration files, migrating databases, adapting to Replit's Nix-based environment, and setting up Replit-native features.

## Prerequisites
- Source application with working deployment
- Access to current database for export
- Git repository with application code
- Replit Core or Teams plan

## Migration Paths

| From | Complexity | Duration | Key Changes |
|------|-----------|----------|-------------|
| Local dev | Low | 1-2 hours | Add .replit + replit.nix |
| Heroku | Medium | 2-4 hours | Procfile to .replit, addons to Replit services |
| Railway | Low-Medium | 1-3 hours | railway.json to .replit |
| Vercel | Low | 1-2 hours | Usually frontend-only, use Static deploy |
| Docker | Medium | 3-6 hours | Dockerfile to replit.nix |

## Instructions

### Step 1: Import from GitHub
```markdown
1. Go to replit.com > Create Repl > Import from GitHub
2. Paste your repository URL
3. Replit auto-detects language and creates default config
4. Review and adjust .replit and replit.nix
```

### Step 2: Convert from Heroku

**Procfile to .replit:**
```bash
# Heroku Procfile
web: npm start
worker: node worker.js
release: node migrate.js
```

```toml
# Equivalent .replit
run = "npm start"
entrypoint = "index.js"

[deployment]
run = ["sh", "-c", "node migrate.js && npm start"]
build = ["sh", "-c", "npm ci --production"]
deploymentTarget = "autoscale"

[env]
NODE_ENV = "production"
```

**Heroku addons to Replit services:**
| Heroku Addon | Replit Equivalent |
|-------------|-------------------|
| Heroku Postgres | Replit PostgreSQL (Database pane) |
| Heroku Redis | Upstash Redis (external) or Replit KV |
| Heroku Scheduler | Replit Automations or external cron |
| Papertrail | Replit deployment logs + external |
| SendGrid | Same (use API key in Secrets) |
| Cloudinary | Replit Object Storage or same |

**Environment variables:**
```bash
# Export from Heroku
heroku config -s > heroku-env.txt

# Import to Replit: copy each line into Secrets tab
# Or use Replit Secrets tool (lock icon in sidebar)
```

### Step 3: Convert from Railway

**railway.json to .replit:**
```json
// railway.json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/health"
  }
}
```

```toml
# Equivalent .replit
run = "npm start"

[deployment]
run = ["sh", "-c", "npm start"]
build = ["sh", "-c", "npm ci"]
deploymentTarget = "autoscale"
```

### Step 4: Convert from Docker

**Dockerfile to replit.nix:**
```dockerfile
# Dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y python3 postgresql-client
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
CMD ["node", "dist/index.js"]
```

```nix
# Equivalent replit.nix
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.python311
    pkgs.postgresql
  ];
}
```

```toml
# .replit
run = "node dist/index.js"

[deployment]
run = ["sh", "-c", "node dist/index.js"]
build = ["sh", "-c", "npm ci --production && npm run build"]
deploymentTarget = "autoscale"
```

### Step 5: Database Migration

**Export from source:**
```bash
# From Heroku Postgres
heroku pg:backups:capture
heroku pg:backups:download
pg_restore -d LOCAL_DB latest.dump

# From Railway
railway run pg_dump > backup.sql

# From any PostgreSQL
pg_dump --format=custom DATABASE_URL > backup.dump
```

**Import to Replit PostgreSQL:**
```bash
# In Replit Shell, after provisioning PostgreSQL in Database pane:

# Option 1: SQL file
psql "$DATABASE_URL" < backup.sql

# Option 2: Custom format dump
pg_restore -d "$DATABASE_URL" backup.dump

# Option 3: Schema only (recreate, then migrate data app-level)
psql "$DATABASE_URL" < schema.sql
node scripts/migrate-data.js
```

**Migrate from non-PostgreSQL (MongoDB, etc.):**
```typescript
// scripts/migrate-from-mongo.ts
import { MongoClient } from 'mongodb';
import { Pool } from 'pg';

const mongo = new MongoClient(process.env.MONGO_URL!);
const pg = new Pool({ connectionString: process.env.DATABASE_URL });

async function migrate() {
  await mongo.connect();
  const users = await mongo.db('app').collection('users').find().toArray();

  await pg.query(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE,
      name TEXT,
      data JSONB,
      created_at TIMESTAMPTZ
    )
  `);

  for (const user of users) {
    await pg.query(
      'INSERT INTO users (id, email, name, data, created_at) VALUES ($1, $2, $3, $4, $5)',
      [user._id.toString(), user.email, user.name, JSON.stringify(user), user.createdAt]
    );
  }

  console.log(`Migrated ${users.length} users`);
  await mongo.close();
  await pg.end();
}

migrate();
```

### Step 6: Post-Migration Checklist
```markdown
## After Migration

### Configuration
- [ ] .replit configured with correct run and build commands
- [ ] replit.nix includes all system dependencies
- [ ] All env vars moved to Replit Secrets
- [ ] PORT reads from environment variable
- [ ] App listens on 0.0.0.0 (not localhost)

### Database
- [ ] PostgreSQL provisioned in Database pane
- [ ] Data imported and verified
- [ ] Connection string uses DATABASE_URL env var
- [ ] SSL configured: { rejectUnauthorized: false }

### Testing
- [ ] App runs successfully in Workspace ("Run")
- [ ] Health endpoint works: /health returns 200
- [ ] All API endpoints functional
- [ ] Auth flow works (if using Replit Auth)
- [ ] File uploads work (if using Object Storage)

### Deployment
- [ ] Deployed successfully (Autoscale or Reserved VM)
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate provisioned
- [ ] Post-deploy health check passes

### Cleanup
- [ ] Old platform deprovisioned after verification period
- [ ] DNS records updated (if custom domain)
- [ ] CI/CD updated to point to Replit
- [ ] Team notified of new deployment URL
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing system package | Not in replit.nix | Add to deps (e.g., pkgs.openssl) |
| Build failure | Different build env | Adapt build command for Replit |
| DB connection refused | Wrong SSL config | Add ssl: { rejectUnauthorized: false } |
| Port binding error | Hardcoded port | Read from process.env.PORT |
| Static files not served | Wrong public directory | Set publicDir in deployment config |

## Resources
- [Import from GitHub](https://docs.replit.com/hosting/deployments/deploying-a-github-repository)
- [Import from Bolt](https://docs.replit.com/getting-started/quickstarts/import-from-bolt)
- [Import from Lovable](https://docs.replit.com/getting-started/quickstarts/import-from-lovable)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [Replit Deployments](https://docs.replit.com/hosting/deployments)

## Next Steps
For advanced troubleshooting after migration, see `replit-advanced-troubleshooting`.
