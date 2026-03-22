---
name: sentry-reliability-patterns
description: |
  Build reliable Sentry integrations that handle failures gracefully.
  Use when handling SDK failures gracefully,
  implementing fallback logging, or ensuring error tracking uptime.
  Trigger with phrases like "sentry reliability", "sentry failover",
  "sentry sdk failure handling", "resilient sentry setup".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, reliability, resilience, circuit-breaker]

---
# Sentry Reliability Patterns

## Prerequisites
- Understanding of failure modes (network, SDK, Sentry outage)
- Fallback logging strategy (console, file, external logger)
- Graceful shutdown requirements documented
- Application SLA requirements known

## Instructions

### 1. Safe Initialization with Fallback

```typescript
// lib/sentry-safe.ts — never let Sentry crash your app
import * as Sentry from '@sentry/node';

let sentryInitialized = false;

export function initSentrySafe(dsn: string, options: Partial<Sentry.NodeOptions> = {}) {
  try {
    Sentry.init({
      dsn,
      ...options,
      beforeSend(event) {
        // Custom beforeSend wrapped in try/catch
        try {
          return options.beforeSend?.(event, {}) ?? event;
        } catch (e) {
          console.error('[Sentry] beforeSend error:', e);
          return event; // Send the event even if beforeSend fails
        }
      },
    });

    sentryInitialized = !!Sentry.getClient();
    if (!sentryInitialized) {
      console.warn('[Sentry] Client not created — DSN may be invalid');
    }
  } catch (error) {
    console.error('[Sentry] Initialization failed:', error);
    sentryInitialized = false;
    // App continues without Sentry — never crash on init failure
  }
}

export function isSentryActive(): boolean {
  return sentryInitialized;
}
```

### 2. Fallback Error Capture

```typescript
// lib/error-capture.ts — captures to Sentry with console fallback
import * as Sentry from '@sentry/node';
import { isSentryActive } from './sentry-safe';

export function captureError(
  error: Error,
  context?: Record<string, unknown>
): string | undefined {
  // Always log to console/file as backup
  console.error(`[Error] ${error.name}: ${error.message}`, context || '');

  if (!isSentryActive()) {
    // Sentry is down — log locally
    writeToFallbackLog(error, context);
    return undefined;
  }

  try {
    let eventId: string | undefined;

    Sentry.withScope((scope) => {
      if (context) {
        scope.setContext('error_context', context);
      }
      eventId = Sentry.captureException(error);
    });

    return eventId;
  } catch (sentryError) {
    // Sentry itself threw — fall back gracefully
    console.error('[Sentry] Capture failed:', sentryError);
    writeToFallbackLog(error, context);
    return undefined;
  }
}

function writeToFallbackLog(error: Error, context?: Record<string, unknown>) {
  const entry = {
    timestamp: new Date().toISOString(),
    error: { name: error.name, message: error.message, stack: error.stack },
    context,
  };

  // Write to file, structured logging, or external service
  console.error('[Fallback Log]', JSON.stringify(entry));
}
```

### 3. Circuit Breaker Pattern

```typescript
// lib/sentry-circuit-breaker.ts
import * as Sentry from '@sentry/node';

class SentryCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private maxFailures = 5,
    private resetTimeMs = 60_000, // 1 minute cooldown
  ) {}

  async captureException(error: Error, context?: Record<string, unknown>) {
    // Check circuit state
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = 'half-open'; // Try one request
      } else {
        console.error('[Sentry Circuit Open]', error.message);
        return; // Skip Sentry, log locally
      }
    }

    try {
      Sentry.withScope((scope) => {
        if (context) scope.setContext('app', context);
        Sentry.captureException(error);
      });

      // Success — reset circuit
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failures = 0;
        console.log('[Sentry Circuit] Recovered — circuit closed');
      }
    } catch (sentryError) {
      this.failures++;
      this.lastFailure = Date.now();

      if (this.failures >= this.maxFailures) {
        this.state = 'open';
        console.error(`[Sentry Circuit Open] ${this.failures} failures — pausing for ${this.resetTimeMs}ms`);
      }
    }
  }

  getState() {
    return { state: this.state, failures: this.failures };
  }
}

export const sentryBreaker = new SentryCircuitBreaker();
```

### 4. Graceful Shutdown

```typescript
import * as Sentry from '@sentry/node';

// Ensure pending events are sent before process exits
async function gracefulShutdown(signal: string) {
  console.log(`${signal} received — shutting down gracefully`);

  // 1. Stop accepting new connections
  server.close();

  // 2. Flush pending Sentry events
  try {
    const flushed = await Sentry.close(2000); // 2 second timeout
    console.log(`Sentry flush: ${flushed ? 'complete' : 'timed out'}`);
  } catch (error) {
    console.error('Sentry flush error:', error);
  }

  // 3. Close database connections, etc.
  await db.close();

  process.exit(0);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Handle uncaught exceptions — capture and exit
process.on('uncaughtException', async (error) => {
  console.error('Uncaught exception:', error);
  Sentry.captureException(error);
  await Sentry.close(2000);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('Unhandled rejection:', reason);
  Sentry.captureException(reason instanceof Error ? reason : new Error(String(reason)));
});
```

### 5. Health Check Endpoint

```typescript
// routes/health.ts
import * as Sentry from '@sentry/node';

app.get('/health/sentry', async (req, res) => {
  const client = Sentry.getClient();

  if (!client) {
    return res.status(503).json({
      status: 'unhealthy',
      error: 'Sentry client not initialized',
    });
  }

  // Quick connectivity test
  try {
    Sentry.captureMessage('health-check', 'debug');
    const flushed = await Sentry.flush(3000);

    res.json({
      status: flushed ? 'healthy' : 'degraded',
      sdk_version: Sentry.SDK_VERSION,
      environment: client.getOptions().environment,
      release: client.getOptions().release,
      flush_ok: flushed,
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});
```

### 6. Offline Event Queue

```typescript
// For applications with intermittent connectivity (mobile, IoT, edge)
import * as Sentry from '@sentry/node';
import { writeFileSync, readFileSync, existsSync, unlinkSync } from 'fs';

const QUEUE_FILE = '/tmp/sentry-offline-queue.json';

function queueEvent(error: Error, context?: Record<string, unknown>) {
  const queue = existsSync(QUEUE_FILE)
    ? JSON.parse(readFileSync(QUEUE_FILE, 'utf-8'))
    : [];

  queue.push({
    timestamp: Date.now(),
    error: { name: error.name, message: error.message, stack: error.stack },
    context,
  });

  // Keep max 1000 events in queue
  if (queue.length > 1000) queue.splice(0, queue.length - 1000);

  writeFileSync(QUEUE_FILE, JSON.stringify(queue));
}

async function drainQueue() {
  if (!existsSync(QUEUE_FILE)) return;

  const queue = JSON.parse(readFileSync(QUEUE_FILE, 'utf-8'));
  console.log(`Draining ${queue.length} queued Sentry events`);

  for (const item of queue) {
    Sentry.withScope((scope) => {
      scope.setTag('offline_queued', 'true');
      scope.setTag('queued_at', new Date(item.timestamp).toISOString());
      if (item.context) scope.setContext('queued', item.context);
      Sentry.captureException(new Error(item.error.message));
    });
  }

  await Sentry.flush(10000);
  unlinkSync(QUEUE_FILE);
  console.log('Queue drained successfully');
}

// Drain queue on startup or when connectivity is restored
drainQueue().catch(console.error);
```

### 7. Dual-Write for Critical Errors

```typescript
// For mission-critical errors, write to multiple destinations
async function captureCritical(error: Error, context: Record<string, unknown>) {
  const destinations = [
    // Primary: Sentry
    () => {
      Sentry.withScope(scope => {
        scope.setLevel('fatal');
        scope.setContext('critical', context);
        Sentry.captureException(error);
      });
    },
    // Secondary: CloudWatch / Datadog / file
    () => {
      console.error(JSON.stringify({
        level: 'FATAL',
        error: error.message,
        stack: error.stack,
        context,
        timestamp: new Date().toISOString(),
      }));
    },
  ];

  // Fire all destinations — don't let one failure block others
  await Promise.allSettled(destinations.map(fn => fn()));
}
```

## Output
- Safe initialization preventing SDK crashes from affecting the app
- Fallback error capture logging locally when Sentry is unavailable
- Circuit breaker pausing Sentry calls after repeated failures
- Graceful shutdown flushing events before process exit
- Health check endpoint for monitoring Sentry connectivity
- Dual-write pattern for mission-critical errors

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| App crashes on Sentry init | Invalid DSN or SDK bug | Wrap `Sentry.init()` in try/catch |
| Events lost on shutdown | No `Sentry.close()` call | Add shutdown handler with `Sentry.close(timeout)` |
| Sentry outage cascading | No circuit breaker | Implement circuit breaker pattern |
| Lost events during network blip | No offline queue | Implement file-based offline queue |
| Silent event loss | Sentry failing without errors | Add health check endpoint, monitor flush success |

## Resources
- [Configuration](https://docs.sentry.io/platforms/javascript/configuration/)
- [Transport Options](https://docs.sentry.io/platforms/javascript/configuration/transports/)
- [Shutdown & Draining](https://docs.sentry.io/platforms/javascript/configuration/draining/)
- [Sentry Status](https://status.sentry.io)
