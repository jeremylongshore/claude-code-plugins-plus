---
name: replit-reference-architecture
description: |
  Implement Replit reference architecture with best-practice project layout.
  Use when designing new Replit integrations, reviewing project structure,
  or establishing architecture standards for Replit applications.
  Trigger with phrases like "replit architecture", "replit best practices",
  "replit project structure", "how to organize replit", "replit layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Reference Architecture

## Overview
Production architecture for applications on Replit. Covers project structure for deployments, secrets management, database integration with Replit DB and PostgreSQL, and multi-environment configuration.

## Prerequisites
- Replit account with deployment tier
- Understanding of `.replit` and `replit.nix`
- Nix package manager basics
- PostgreSQL or Replit DB familiarity

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Replit Workspace                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ .replit   │  │ replit   │  │ Secrets          │    │
│  │ (config)  │  │ .nix     │  │ (env vars)       │    │
│  └──────────┘  └──────────┘  └──────────────────┘    │
├──────────────────────────────────────────────────────┤
│              Application                              │
│  ┌──────────────────────────────────────────────┐     │
│  │         Express/Fastify Server                │     │
│  │  Routes │ Middleware │ WebSocket              │     │
│  └──────────────────────┬───────────────────────┘     │
│                         │                             │
│  ┌──────────────────────┴───────────────────────┐     │
│  │         Data Layer                            │     │
│  │  Replit DB │ PostgreSQL │ Object Storage      │     │
│  └──────────────────────────────────────────────┘     │
├──────────────────────────────────────────────────────┤
│  Deployment: Autoscale │ Reserved VM │ Static        │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Project Structure
```
my-replit-app/
├── .replit                  # Run configuration
├── replit.nix               # System dependencies
├── src/
│   ├── index.ts             # Entry point
│   ├── routes/
│   │   ├── api.ts           # API routes
│   │   └── health.ts        # Health check
│   ├── services/
│   │   ├── database.ts      # DB connection
│   │   └── cache.ts         # Caching layer
│   └── middleware/
│       ├── auth.ts          # Authentication
│       └── rateLimit.ts     # Rate limiting
├── tests/
├── tsconfig.json
└── package.json
```

### Step 2: Replit Configuration Files
```toml
# .replit
run = "npm start"
entrypoint = "src/index.ts"

[nix]
channel = "stable-24_05"

[env]
NODE_ENV = "production"

[deployment]
run = ["sh", "-c", "npm run build && npm start"]
build = ["sh", "-c", "npm ci && npm run build"]
deploymentTarget = "cloudrun"

[languages.typescript]
pattern = "**/*.ts"
```

```nix
# replit.nix
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript
    pkgs.postgresql
  ];
}
```

### Step 3: Database Integration
```typescript
// src/services/database.ts
import { Pool } from 'pg';

let pool: Pool | null = null;

export function getDB(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 10,
      idleTimeoutMillis: 30000,  # 30000: 30 seconds in ms
      connectionTimeoutMillis: 5000,  # 5000: 5 seconds in ms
    });
  }
  return pool;
}

// Health check for database
export async function checkDBHealth(): Promise<boolean> {
  try {
    const result = await getDB().query('SELECT 1');
    return result.rows.length > 0;
  } catch {
    return false;
  }
}
```

### Step 4: Application Entry Point
```typescript
// src/index.ts
import express from 'express';
import { getDB, checkDBHealth } from './services/database';

const app = express();
app.use(express.json());

// Health endpoint (required for Replit deployments)
app.get('/health', async (req, res) => {
  const dbOk = await checkDBHealth();
  res.status(dbOk ? 200 : 503).json({  # 503: HTTP 200 OK
    status: dbOk ? 'healthy' : 'degraded',
    uptime: process.uptime(),
    memory: process.memoryUsage().heapUsed,
  });
});

app.get('/api/status', (req, res) => {
  res.json({ version: process.env.npm_package_version });
});

const PORT = parseInt(process.env.PORT || '3000');  # 3000: 3 seconds in ms
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start slow | Heavy imports at startup | Use lazy imports for non-critical modules |
| DB connection refused | PostgreSQL not started | Check Replit DB provisioning |
| Secrets undefined | Not set in Secrets tab | Configure in Replit workspace Secrets |
| Deploy fails | Build step error | Test build locally before deploying |

## Examples

### Quick Deployment Check
```bash
set -euo pipefail
# Test build locally before deploying
npm run build && npm start
# Verify health endpoint
curl http://localhost:3000/health  # 3000: 3 seconds in ms
```

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Database](https://docs.replit.com/hosting/databases)
- [Replit Nix Guide](https://docs.replit.com/programming-ide/nix-on-replit)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale