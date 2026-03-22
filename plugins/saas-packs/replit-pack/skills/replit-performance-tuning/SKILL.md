---
name: replit-performance-tuning
description: |
  Optimize Replit app performance: cold start, memory, Nix caching, and deployment speed.
  Use when experiencing slow startup, high memory usage, deployment timeouts,
  or optimizing Replit container resource usage.
  Trigger with phrases like "replit performance", "optimize replit",
  "replit slow", "replit cold start", "replit memory", "replit startup time".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, performance, optimization]

---
# Replit Performance Tuning

## Overview
Optimize Replit app performance across the entire lifecycle: cold start reduction, Nix environment caching, build speed, runtime memory management, and deployment configuration. Replit containers have resource limits — efficient usage is critical.

## Prerequisites
- Replit app deployed or running in Workspace
- Understanding of `.replit` and `replit.nix`
- Access to deployment monitoring

## Instructions

### Step 1: Reduce Cold Start Time
Autoscale deployments scale to zero when idle. First request triggers a cold start (10-30s). Minimize it:

```typescript
// 1. Lazy-load heavy modules — only import when needed
// BAD: imports everything at startup
import { heavyAnalytics } from './analytics'; // 500ms
import { imageProcessor } from './images';     // 300ms

// GOOD: import on demand
app.get('/api/analyze', async (req, res) => {
  const { heavyAnalytics } = await import('./analytics');
  res.json(await heavyAnalytics.process(req.query));
});

// 2. Defer non-critical initialization
let dbPool: Pool | null = null;

function getDB(): Pool {
  if (!dbPool) {
    dbPool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 5,  // Keep pool small for faster init
    });
  }
  return dbPool;
}

// 3. Start server immediately, initialize after
const app = express();
const PORT = parseInt(process.env.PORT || '3000');
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server ready in ${process.uptime().toFixed(1)}s`);
  // Warm up in background after server is accepting requests
  warmup().catch(console.error);
});

async function warmup() {
  await getDB().query('SELECT 1');  // Pre-connect
}
```

### Step 2: Optimize Nix Environment
```nix
# replit.nix — only include what you actually need

# BAD: kitchen-sink approach
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.python311
    pkgs.go
    pkgs.rustc
    pkgs.cargo
    pkgs.postgresql
    pkgs.redis
    pkgs.imagemagick
  ];
}

# GOOD: minimal deps for a Node.js app
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
  ];
  # Only add postgresql if you need psql CLI:
  # pkgs.postgresql
}
```

```toml
# .replit — pin Nix channel for cache hits
[nix]
channel = "stable-24_05"
# Changing channel invalidates all Nix caches
# Only upgrade when needed
```

### Step 3: Optimize Build Step
```toml
# .replit — fast production builds
[deployment]
build = ["sh", "-c", "npm ci --production && npm run build"]
run = ["sh", "-c", "node dist/index.js"]
```

```json
// package.json — optimize build scripts
{
  "scripts": {
    "build": "tsc --incremental",
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts"
  }
}
```

```json
// tsconfig.json — incremental builds
{
  "compilerOptions": {
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",
    "skipLibCheck": true
  }
}
```

Tips for faster builds:
- Use `npm ci` (not `npm install`) — deterministic, faster
- Add `--production` to skip devDependencies
- Use TypeScript `--incremental` for rebuild caching
- Avoid `postinstall` scripts that compile native addons

### Step 4: Memory Management
Replit containers have memory limits (512 MB to 16 GiB depending on plan/tier):

```typescript
// Monitor memory usage
function logMemory() {
  const usage = process.memoryUsage();
  const mb = (bytes: number) => Math.round(bytes / 1024 / 1024);
  console.log({
    heapUsed: `${mb(usage.heapUsed)} MB`,
    heapTotal: `${mb(usage.heapTotal)} MB`,
    rss: `${mb(usage.rss)} MB`,
    external: `${mb(usage.external)} MB`,
  });
}

// Check every 60 seconds
setInterval(logMemory, 60000);

// Expose via health endpoint
app.get('/health', (req, res) => {
  const mem = process.memoryUsage();
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    memoryMB: Math.round(mem.heapUsed / 1024 / 1024),
    memoryPercent: ((mem.heapUsed / mem.heapTotal) * 100).toFixed(1),
  });
});
```

**Memory optimization patterns:**
```typescript
// Stream large files instead of loading into memory
import { createReadStream } from 'fs';
app.get('/download/:file', (req, res) => {
  const stream = createReadStream(`/tmp/${req.params.file}`);
  stream.pipe(res);
});

// Paginate database queries
app.get('/api/items', async (req, res) => {
  const page = parseInt(req.query.page as string) || 1;
  const limit = 50;
  const offset = (page - 1) * limit;
  const { rows } = await pool.query(
    'SELECT * FROM items ORDER BY id LIMIT $1 OFFSET $2',
    [limit, offset]
  );
  res.json({ items: rows, page, hasMore: rows.length === limit });
});

// Clear caches when memory is high
const cache = new Map<string, any>();
setInterval(() => {
  if (process.memoryUsage().heapUsed > 400 * 1024 * 1024) {
    cache.clear();
    console.log('Cache cleared due to high memory');
  }
}, 30000);
```

### Step 5: Database Connection Efficiency
```typescript
// PostgreSQL pool tuning for Replit
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 5,                    // Small pool — containers are limited
  idleTimeoutMillis: 30000,  // Close idle connections after 30s
  connectionTimeoutMillis: 5000,
});

// Use connection pooling, never create per-request connections
// BAD: new Pool() per request
// GOOD: single pool, shared across requests
```

### Step 6: Deployment Type Selection
| Scenario | Best Type | Why |
|----------|-----------|-----|
| < 100 daily requests | Autoscale | Free when idle |
| Consistent traffic | Reserved VM | No cold starts |
| Static frontend | Static | Fastest, cheapest |
| Latency-sensitive API | Reserved VM | Always warm |
| Cron jobs / webhooks | Reserved VM | Must be always-on |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start > 15s | Heavy imports | Lazy-load, defer init |
| OOM killed | Exceeding memory limit | Stream data, reduce pool size |
| Build timeout | Slow npm install | Use `npm ci --production` |
| Slow first query | DB cold connection | Pre-connect in warmup() |

## Resources
- [Replit App Configuration](https://docs.replit.com/replit-app/configuration)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [Nix Performance](https://blog.replit.com/nix-perf-improvements)
- [Reserved VM Deployments](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)

## Next Steps
For cost optimization, see `replit-cost-tuning`.
