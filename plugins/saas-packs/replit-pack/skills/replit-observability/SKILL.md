---
name: replit-observability
description: |
  Monitor Replit deployments with health checks, uptime tracking, resource usage, and alerting.
  Use when setting up monitoring for Replit apps, building health dashboards,
  or configuring alerting for deployment health and performance.
  Trigger with phrases like "replit monitoring", "replit metrics",
  "replit observability", "monitor replit", "replit alerts", "replit uptime".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, monitoring, observability, alerting]

---
# Replit Observability

## Overview
Monitor Replit deployment health, track cold starts, measure resource usage, and set up alerting. Covers Replit's built-in monitoring, external health checking, structured logging, and integration with monitoring services.

## Prerequisites
- Replit app deployed (Autoscale or Reserved VM)
- Health endpoint implemented (`/health`)
- External monitoring service (UptimeRobot, Better Stack, or Prometheus)

## Instructions

### Step 1: Health Endpoint with Detailed Metrics
```typescript
// src/routes/health.ts — comprehensive health check
import { Router } from 'express';
import { pool } from '../services/postgres';

const router = Router();
const startTime = Date.now();

router.get('/health', async (req, res) => {
  const checks: Record<string, any> = {
    status: 'ok',
    uptime: process.uptime(),
    bootTime: ((Date.now() - startTime) / 1000).toFixed(1) + 's ago',
    timestamp: new Date().toISOString(),
    repl: process.env.REPL_SLUG,
    region: process.env.REPLIT_DEPLOYMENT_REGION,
    env: process.env.NODE_ENV,
  };

  // Database check
  if (process.env.DATABASE_URL) {
    const dbStart = Date.now();
    try {
      await pool.query('SELECT 1');
      checks.database = {
        status: 'connected',
        latencyMs: Date.now() - dbStart,
        pool: { total: pool.totalCount, idle: pool.idleCount },
      };
    } catch (err: any) {
      checks.database = { status: 'disconnected', error: err.message };
      checks.status = 'degraded';
    }
  }

  // Memory metrics
  const mem = process.memoryUsage();
  checks.memory = {
    heapMB: Math.round(mem.heapUsed / 1024 / 1024),
    totalMB: Math.round(mem.heapTotal / 1024 / 1024),
    rssMB: Math.round(mem.rss / 1024 / 1024),
    percent: ((mem.heapUsed / mem.heapTotal) * 100).toFixed(1),
  };

  // Node.js info
  checks.runtime = {
    node: process.version,
    platform: process.platform,
    pid: process.pid,
  };

  res.status(checks.status === 'ok' ? 200 : 503).json(checks);
});

// Lightweight ping for uptime monitors
router.get('/ping', (req, res) => res.send('pong'));

export default router;
```

### Step 2: Structured Logging
```typescript
// src/utils/logger.ts — structured JSON logging
const IS_PROD = process.env.NODE_ENV === 'production';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

function log(level: LogLevel, message: string, data?: Record<string, any>) {
  if (level === 'debug' && IS_PROD) return;

  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    repl: process.env.REPL_SLUG,
    ...data,
  };

  // JSON format for machine parsing, human-readable in dev
  if (IS_PROD) {
    console[level === 'error' ? 'error' : 'log'](JSON.stringify(entry));
  } else {
    console[level === 'error' ? 'error' : 'log'](
      `[${level.toUpperCase()}] ${message}`,
      data || ''
    );
  }
}

export const logger = {
  debug: (msg: string, data?: any) => log('debug', msg, data),
  info: (msg: string, data?: any) => log('info', msg, data),
  warn: (msg: string, data?: any) => log('warn', msg, data),
  error: (msg: string, data?: any) => log('error', msg, data),
};

// Request logging middleware
export function requestLogger(req: any, res: any, next: any) {
  const start = Date.now();
  res.on('finish', () => {
    logger.info('request', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      durationMs: Date.now() - start,
      userId: req.headers['x-replit-user-id'] || 'anonymous',
    });
  });
  next();
}
```

### Step 3: External Uptime Monitoring
Set up external monitors to detect Autoscale cold starts and outages:

```markdown
UptimeRobot (free tier: 50 monitors):
1. Create new monitor: HTTP(s)
2. URL: https://your-app.replit.app/ping
3. Interval: 5 minutes
4. Alert contacts: email, Slack webhook

Better Stack / Datadog / Grafana Cloud:
- Same setup, more features
- Track response time trends
- Detect cold start patterns
- Set up PagerDuty integration

Key metrics to monitor externally:
- Uptime percentage (target: 99.9%)
- Response time P95 (target: < 2s)
- Cold start frequency (Autoscale only)
- SSL certificate expiry
```

### Step 4: Cold Start Detection
```typescript
// Track cold starts for Autoscale deployments
const COLD_START_THRESHOLD_MS = 5000;
let firstRequestTime: number | null = null;

app.use((req, res, next) => {
  if (!firstRequestTime) {
    firstRequestTime = Date.now();
    const bootTime = process.uptime();
    if (bootTime < 30) { // Just started
      logger.info('cold_start_detected', {
        bootTimeMs: Math.round(bootTime * 1000),
        path: req.path,
      });
    }
  }
  next();
});
```

### Step 5: Alerting Rules
```typescript
// src/utils/alerts.ts — send alerts to Slack on issues
async function alertSlack(message: string, severity: 'info' | 'warning' | 'critical') {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  if (!webhookUrl) return;

  const emoji = { info: 'information_source', warning: 'warning', critical: 'rotating_light' };
  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `:${emoji[severity]}: [${severity.toUpperCase()}] ${process.env.REPL_SLUG}\n${message}`,
    }),
  });
}

// Monitor memory usage
setInterval(async () => {
  const mem = process.memoryUsage();
  const heapPercent = (mem.heapUsed / mem.heapTotal) * 100;

  if (heapPercent > 90) {
    await alertSlack(`Memory critical: ${heapPercent.toFixed(1)}% heap used`, 'critical');
  } else if (heapPercent > 75) {
    await alertSlack(`Memory warning: ${heapPercent.toFixed(1)}% heap used`, 'warning');
  }
}, 60000);

// Monitor error rate
let errorCount = 0;
let requestCount = 0;

app.use((req, res, next) => {
  requestCount++;
  res.on('finish', () => {
    if (res.statusCode >= 500) errorCount++;
  });
  next();
});

setInterval(async () => {
  if (requestCount > 0) {
    const errorRate = (errorCount / requestCount) * 100;
    if (errorRate > 5) {
      await alertSlack(`Error rate: ${errorRate.toFixed(1)}% (${errorCount}/${requestCount})`, 'critical');
    }
  }
  errorCount = 0;
  requestCount = 0;
}, 300000); // Check every 5 minutes
```

### Step 6: Replit Dashboard Monitoring
```markdown
Built-in monitoring in Replit:
1. Deployment Settings > Logs: real-time stdout/stderr
2. Deployment Settings > History: deploy timeline + rollbacks
3. Database pane > Settings: storage usage + connection info
4. Billing > Usage: compute, egress, and storage costs

Check deployment logs:
- Click on active deployment
- View real-time log stream
- Filter by error/warning
- Logs persist across container restarts
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cold starts undetected | No external monitor | Set up UptimeRobot or similar |
| Deployment logs missing | Container restarted | Use external log aggregator |
| Memory leak unnoticed | No memory monitoring | Add heap tracking + alerts |
| DB pool exhaustion | Too many connections | Monitor pool.totalCount in health |

## Resources
- [Monitoring Deployments](https://docs.replit.com/cloud-services/deployments/monitoring-a-deployment)
- [Replit Status Page](https://status.replit.com)
- [UptimeRobot](https://uptimerobot.com)

## Next Steps
For incident response, see `replit-incident-runbook`.
