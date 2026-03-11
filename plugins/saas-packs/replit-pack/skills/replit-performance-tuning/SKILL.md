---
name: replit-performance-tuning
description: |
  Optimize Replit API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Replit integrations.
  Trigger with phrases like "replit performance", "optimize replit",
  "replit latency", "replit caching", "replit slow", "replit batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Performance Tuning

## Overview
Optimize Replit workspace performance for deployments and development. Focus on Repl startup time, deployment caching, Nix environment optimization, and efficient use of Replit's hosting infrastructure.

## Prerequisites
- Replit account with deployment access
- Understanding of `.replit` configuration
- Nix environment familiarity
- `replit.nix` for dependency management

## Instructions

### Step 1: Optimize Repl Startup with Caching
```nix
# replit.nix - Pin versions to leverage Nix cache
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript
    pkgs.nodePackages.pnpm
  ];
}
```

```toml
# .replit - Optimize run configuration
run = "node --max-old-space-size=512 dist/index.js"
entrypoint = "src/index.ts"

[nix]
channel = "stable-24_05"

[deployment]
run = ["sh", "-c", "node dist/index.js"]
build = ["sh", "-c", "pnpm install --frozen-lockfile && pnpm build"]
deploymentTarget = "cloudrun"

[env]
NODE_ENV = "production"
```

### Step 2: Build Cache for Faster Deployments
```json
// package.json - Scripts optimized for Replit
{
  "scripts": {
    "build": "tsc --incremental",
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts",
    "prebuild": "rm -rf dist/.tsbuildinfo || true"
  }
}
```

```typescript
// src/index.ts - Lazy module loading for startup speed
const express = await import('express');
const app = express.default();

// Defer heavy imports until needed
app.get('/api/analyze', async (req, res) => {
  const { analyze } = await import('./heavy-module');
  res.json(await analyze(req.query));
});

app.listen(3000, () => console.log('Ready'));
```

### Step 3: Memory Management for Replit Containers
```typescript
// Monitor memory in constrained Replit environment
function getMemoryUsage() {
  const usage = process.memoryUsage();
  return {
    heapUsedMB: Math.round(usage.heapUsed / 1024 / 1024),
    heapTotalMB: Math.round(usage.heapTotal / 1024 / 1024),
    rssMB: Math.round(usage.rss / 1024 / 1024),
    percentUsed: ((usage.heapUsed / usage.heapTotal) * 100).toFixed(1),
  };
}

// Periodic memory check with cleanup
setInterval(() => {
  const mem = getMemoryUsage();
  if (mem.heapUsedMB > 400) {
    console.warn('High memory usage:', mem);
    global.gc?.(); // Requires --expose-gc flag
  }
}, 30000);
```

### Step 4: Secrets and Environment Performance
```typescript
// Access Replit secrets efficiently - read once at startup
const config = {
  dbUrl: process.env.DATABASE_URL!,
  apiKey: process.env.API_KEY!,
  port: parseInt(process.env.PORT || '3000'),
} as const;

// Validate all secrets exist at startup, fail fast
function validateSecrets(required: string[]) {
  const missing = required.filter(k => !process.env[k]);
  if (missing.length) {
    console.error(`Missing secrets: ${missing.join(', ')}`);
    console.error('Add them in Replit Secrets tab');
    process.exit(1);
  }
}

validateSecrets(['DATABASE_URL', 'API_KEY']);
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow cold start | Heavy dependencies at import | Use dynamic imports for non-critical modules |
| OOM killed | Exceeding 512MB limit | Reduce heap size, stream large data |
| Deploy timeout | Build step too slow | Use `--incremental` TypeScript builds |
| Wake-up latency | Repl sleeping after inactivity | Use always-on deployment or health pings |

## Examples

### Health Check with Metrics
```typescript
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    memory: getMemoryUsage(),
    nodeVersion: process.version,
  });
});
```

## Resources
- [Replit Deployments Guide](https://docs.replit.com/hosting/deployments)
- [Replit Nix Configuration](https://docs.replit.com/programming-ide/nix-on-replit)
- [Replit Secrets](https://docs.replit.com/programming-ide/workspace-features/secrets)
