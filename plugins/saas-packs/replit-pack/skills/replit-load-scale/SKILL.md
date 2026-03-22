---
name: replit-load-scale
description: |
  Load test and scale Replit deployments with Autoscale tuning, Reserved VM sizing, and capacity planning.
  Use when load testing Replit apps, optimizing Autoscale behavior,
  or planning capacity for production traffic.
  Trigger with phrases like "replit load test", "replit scale",
  "replit capacity", "replit performance test", "replit autoscale tuning".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, testing, performance, scaling]

---
# Replit Load & Scale

## Overview
Load testing, scaling strategies, and capacity planning for Replit deployments. Covers Autoscale behavior tuning, Reserved VM right-sizing, cold start optimization, database connection scaling, and capacity benchmarking.

## Prerequisites
- Replit app deployed (Autoscale or Reserved VM)
- Load testing tool: k6, autocannon, or curl
- Health endpoint implemented

## Replit Scaling Model

| Deployment Type | Scaling Behavior | Cold Start | Best For |
|-----------------|-----------------|------------|----------|
| **Autoscale** | 0 to N instances based on traffic | Yes (5-30s) | Variable traffic |
| **Reserved VM** | Fixed resources, always-on | No | Consistent traffic |
| **Static** | CDN-backed, infinite scale | No | Frontend assets |

## Instructions

### Step 1: Baseline Benchmark
```bash
# Quick benchmark with autocannon (built into Node.js ecosystem)
npx autocannon -c 10 -d 30 https://your-app.replit.app/health
# -c 10: 10 concurrent connections
# -d 30: 30 seconds duration

# Output shows:
# - Requests/sec
# - Latency (p50, p95, p99)
# - Throughput (bytes/sec)
# - Error count
```

### Step 2: Load Test with k6
```javascript
// load-test.js — comprehensive Replit load test
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const coldStartTrend = new Trend('cold_start_duration');

export const options = {
  stages: [
    { duration: '1m', target: 5 },    // Warm up
    { duration: '3m', target: 20 },   // Normal load
    { duration: '2m', target: 50 },   // Peak load
    { duration: '1m', target: 0 },    // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% of requests under 2s
    errors: ['rate<0.05'],              // Error rate under 5%
  },
};

const BASE_URL = __ENV.DEPLOY_URL || 'https://your-app.replit.app';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health returns 200': (r) => r.status === 200,
    'health under 1s': (r) => r.timings.duration < 1000,
  });
  errorRate.add(healthRes.status !== 200);

  // Detect cold start
  if (healthRes.timings.duration > 5000) {
    coldStartTrend.add(healthRes.timings.duration);
  }

  // API endpoint
  const apiRes = http.get(`${BASE_URL}/api/status`);
  check(apiRes, {
    'api returns 200': (r) => r.status === 200,
  });

  sleep(1);
}
```

```bash
# Run k6 load test
k6 run --env DEPLOY_URL=https://your-app.replit.app load-test.js

# With JSON output
k6 run --out json=results.json load-test.js
```

### Step 3: Cold Start Optimization (Autoscale)
```markdown
Autoscale cold starts happen when:
- First request after period of no traffic
- Replit needs to start a new container instance
- Typical: 5-30 seconds depending on app size

Reduction strategies:
1. Minimize startup imports (lazy-load heavy modules)
2. Use smaller Nix dependency set
3. Pre-connect database in background (don't block startup)
4. Keep package count low
5. Use compiled JavaScript (not tsx at runtime)

Before (slow cold start):
  run = "npx tsx src/index.ts"  → compiles TS at startup

After (fast cold start):
  build = "npm run build"  → compiles during deploy
  run = "node dist/index.js"  → runs pre-compiled JS
```

```toml
# .replit — optimized for fast cold start
[deployment]
build = ["sh", "-c", "npm ci --production && npm run build"]
run = ["sh", "-c", "node dist/index.js"]
deploymentTarget = "autoscale"
```

### Step 4: Reserved VM Sizing
```markdown
Choose VM size based on load test results:

If peak CPU < 30% → downsize (save money)
If peak CPU > 70% → upsize (prevent throttling)
If peak memory > 80% → upsize (prevent OOM)

Machine sizes:
  0.25 vCPU / 512 MB  → Simple APIs, < 50 req/s
  0.5 vCPU / 1 GB     → Standard apps, < 200 req/s
  1 vCPU / 2 GB       → Moderate traffic, < 500 req/s
  2 vCPU / 4 GB       → High traffic, < 1000 req/s
  4 vCPU / 8-16 GB    → Compute-heavy, > 1000 req/s

To change:
  Deployment Settings > Machine Size > Select new tier
  Redeployment required to apply
```

### Step 5: Database Connection Scaling
```typescript
// Tune PostgreSQL pool for Replit container limits
import { Pool } from 'pg';

// Small container (0.25 vCPU / 512 MB)
const smallPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 3,                    // Few connections
  idleTimeoutMillis: 10000,  // Release quickly
});

// Medium container (1 vCPU / 2 GB)
const mediumPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 10,                   // More headroom
  idleTimeoutMillis: 30000,
});

// Large container (4 vCPU / 8 GB)
const largePool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 20,
  idleTimeoutMillis: 60000,
});

// Dynamic pool sizing based on container resources
function createOptimalPool(): Pool {
  const memMB = Math.round(process.memoryUsage().rss / 1024 / 1024);
  const maxConns = memMB < 256 ? 3 : memMB < 1024 ? 10 : 20;

  return new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: maxConns,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });
}
```

### Step 6: Capacity Planning Template
```markdown
## Capacity Assessment

### Current State
- Deployment type: [Autoscale / Reserved VM]
- Machine size: [vCPU / RAM]
- Peak RPS: [from load test]
- P95 latency: [from load test]
- Cold start time: [Autoscale only]

### Load Test Results
| Metric | Idle | Normal (20 VU) | Peak (50 VU) |
|--------|------|----------------|--------------|
| RPS | 0 | X | Y |
| P50 latency | - | Xms | Yms |
| P95 latency | - | Xms | Yms |
| Error rate | - | X% | Y% |
| Memory | XMB | XMB | XMB |

### Recommendations
1. [Scale action based on results]
2. [Database pool adjustment]
3. [Cold start mitigation]
4. [Cost optimization]

### Scaling Triggers
- CPU > 70% sustained: upgrade VM
- Memory > 80%: upgrade VM or fix leak
- P95 > 2s: add caching or optimize queries
- Error rate > 1%: investigate root cause
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start > 15s | Heavy startup | Pre-compile, lazy imports |
| Connection pool exhausted | Too many concurrent requests | Increase pool.max or add queueing |
| OOM during load test | Memory leak under load | Profile with /debug/memory |
| Inconsistent results | Autoscale scaling up | Warm up before measuring |

## Resources
- [Autoscale Deployments](https://blog.replit.com/autoscale)
- [Reserved VM Deployments](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)
- [k6 Documentation](https://k6.io/docs/)
- [autocannon](https://github.com/mcollina/autocannon)

## Next Steps
For reliability patterns, see `replit-reliability-patterns`.
