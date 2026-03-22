---
name: replit-reference-architecture
description: |
  Implement Replit reference architecture with best-practice project layout, data layer, and deployment.
  Use when designing new Replit apps, reviewing project structure,
  or establishing architecture standards for production Replit applications.
  Trigger with phrases like "replit architecture", "replit best practices",
  "replit project structure", "how to organize replit", "replit production layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, architecture, reference]

---
# Replit Reference Architecture

## Overview
Production architecture for applications on Replit. Covers project structure, configuration files, data layer (PostgreSQL + KV + Object Storage), authentication, deployment strategy, and the platform constraints that shape architectural decisions.

## Architecture Diagram
```
                    ┌──────────────────────────┐
                    │    Client (Browser)       │
                    └──────────┬───────────────┘
                               │ HTTPS
                    ┌──────────▼───────────────┐
                    │  Replit Proxy (TLS, Auth) │
                    │  Injects X-Replit-User-*  │
                    └──────────┬───────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                 Replit Deployment                            │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ .replit      │  │ replit.nix   │  │ Secrets (AES-256) │  │
│  │ (run/build)  │  │ (Nix deps)   │  │ (env vars)        │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Express / Flask Server                   │   │
│  │  Routes │ Auth Middleware │ Error Handler │ Health    │   │
│  └────────┬───────────────────────────────────┬─────────┘   │
│           │                                   │              │
│  ┌────────▼──────────┐  ┌───────────────────▼────────────┐ │
│  │  PostgreSQL       │  │  Replit KV Database            │ │
│  │  (DATABASE_URL)   │  │  (REPLIT_DB_URL)               │ │
│  │  Dev + Prod DBs   │  │  50 MiB, 5K keys              │ │
│  └───────────────────┘  └────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Object Storage (App Storage)                           ││
│  │  File uploads, backups, large data                      ││
│  │  @replit/object-storage SDK                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Deployment: Autoscale │ Reserved VM │ Static               │
└──────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Project Structure
```
my-replit-app/
├── .replit                    # Run + deployment configuration
├── replit.nix                 # System-level Nix dependencies
├── package.json               # npm dependencies + scripts
├── tsconfig.json              # TypeScript config
├── src/
│   ├── index.ts               # Entry point — Express setup
│   ├── config.ts              # Secrets validation + env config
│   ├── routes/
│   │   ├── api.ts             # Business logic endpoints
│   │   ├── auth.ts            # Auth-related routes
│   │   └── health.ts          # Health check (required for deploy)
│   ├── services/
│   │   ├── postgres.ts        # PostgreSQL pool singleton
│   │   ├── kv.ts              # Replit KV Database wrapper
│   │   └── storage.ts         # Object Storage wrapper
│   ├── middleware/
│   │   ├── auth.ts            # Replit Auth header extraction
│   │   ├── rateLimit.ts       # Rate limiting
│   │   └── errors.ts          # Global error handler
│   └── types/
│       └── index.ts           # Shared type definitions
├── tests/
│   ├── api.test.ts            # API integration tests
│   └── services.test.ts       # Service unit tests
└── scripts/
    └── migrate.ts             # Database migration scripts
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
build = ["sh", "-c", "npm ci --production"]
deploymentTarget = "autoscale"

[unitTest]
language = "nodejs"

[languages.typescript]
pattern = "**/*.ts"
```

```nix
# replit.nix
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
  ];
}
```

### Step 3: Configuration Module
```typescript
// src/config.ts — centralized configuration with validation
export const config = {
  port: parseInt(process.env.PORT || '3000'),
  nodeEnv: process.env.NODE_ENV || 'development',
  isProduction: process.env.NODE_ENV === 'production',
  repl: {
    slug: process.env.REPL_SLUG || 'unknown',
    owner: process.env.REPL_OWNER || 'unknown',
    id: process.env.REPL_ID,
  },
  db: {
    url: process.env.DATABASE_URL,
    kvUrl: process.env.REPLIT_DB_URL,
  },
} as const;

// Validate required secrets at import time
const REQUIRED_SECRETS = ['DATABASE_URL'];
const missing = REQUIRED_SECRETS.filter(k => !process.env[k]);
if (missing.length > 0 && config.isProduction) {
  console.error(`FATAL: Missing secrets: ${missing.join(', ')}`);
  process.exit(1);
}
```

### Step 4: Data Layer Strategy
| Storage | Use When | Limits |
|---------|----------|--------|
| **PostgreSQL** | Structured data, relations, queries | Plan-dependent |
| **Replit KV** | Simple cache, session data, counters | 50 MiB, 5K keys |
| **Object Storage** | Files, images, backups, large blobs | Plan-dependent |

```typescript
// src/services/postgres.ts
import { Pool } from 'pg';
import { config } from '../config';

export const pool = new Pool({
  connectionString: config.db.url,
  ssl: { rejectUnauthorized: false },
  max: 5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

// src/services/kv.ts
import Database from '@replit/database';
export const kv = new Database();

// src/services/storage.ts
import { Client } from '@replit/object-storage';
export const storage = new Client();
```

### Step 5: Entry Point Pattern
```typescript
// src/index.ts
import express from 'express';
import { config } from './config';
import { pool } from './services/postgres';
import healthRouter from './routes/health';
import apiRouter from './routes/api';
import { requireAuth } from './middleware/auth';
import { errorHandler } from './middleware/errors';

const app = express();
app.use(express.json({ limit: '1mb' }));

// Public routes
app.use(healthRouter);

// Protected routes
app.use('/api', requireAuth, apiRouter);

// Global error handler (must be last)
app.use(errorHandler);

// Start server — bind to 0.0.0.0 (required for Replit)
app.listen(config.port, '0.0.0.0', () => {
  console.log(`[${config.repl.slug}] Running on port ${config.port}`);
  // Pre-connect database
  pool.query('SELECT 1').catch(err => {
    console.error('Database connection failed:', err.message);
  });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down...');
  await pool.end();
  process.exit(0);
});
```

## Platform Constraints
| Constraint | Impact | Mitigation |
|-----------|--------|------------|
| Ephemeral filesystem | Files lost on restart | Use DB or Object Storage |
| Cold starts (Autoscale) | 5-30s first request | Reserved VM or lazy loading |
| Memory limits | OOM kills | Stream data, limit pool size |
| Public Repls | Source visible | Never hardcode secrets |
| Container restarts | State loss | External state (DB/Storage) |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start slow | Heavy imports at startup | Lazy-load non-critical modules |
| DB connection refused | PostgreSQL not provisioned | Create database in Database pane |
| Secrets undefined | Not in Secrets tab | Add via sidebar lock icon |
| Filesystem writes lost | Ephemeral container | Use Object Storage or PostgreSQL |

## Resources
- [Replit App Configuration](https://docs.replit.com/replit-app/configuration)
- [PostgreSQL on Replit](https://docs.replit.com/cloud-services/storage-and-databases/postgresql-on-replit)
- [Object Storage](https://docs.replit.com/cloud-services/storage-and-databases/object-storage/overview)
- [Replit Deployments](https://docs.replit.com/hosting/deployments)

## Next Steps
For deployment, see `replit-deploy-integration`. For multi-environment, see `replit-multi-env-setup`.
