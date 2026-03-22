---
name: sentry-reference-architecture
description: |
  Design best-practice Sentry architecture for organizations.
  Use when designing Sentry integration architecture,
  structuring projects, or planning enterprise rollout.
  Trigger with phrases like "sentry architecture", "sentry best practices",
  "design sentry integration", "sentry project structure".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, architecture, best-practices, enterprise]

---
# Sentry Reference Architecture

## Prerequisites
- Sentry organization created
- Team structure and service inventory documented
- Alert escalation paths established
- Compliance requirements known

## Instructions

### 1. Project Structure Strategy

**Pattern A: One Project Per Service (Recommended)**
```
Organization: acme-corp
├── Team: platform
│   ├── Project: api-gateway
│   ├── Project: auth-service
│   └── Project: user-service
├── Team: payments
│   ├── Project: payment-api
│   └── Project: billing-worker
├── Team: frontend
│   ├── Project: web-app
│   └── Project: mobile-app
└── Team: data
    ├── Project: etl-pipeline
    └── Project: analytics-api
```

**Benefits:** Clear ownership, independent quotas, team-scoped alerts.

**Pattern B: One Project with Environment Tags (Small teams)**
```
Organization: startup-xyz
└── Project: main-app
    ├── Environment: production
    ├── Environment: staging
    └── Environment: development
```

**Benefits:** Simpler setup, unified issue view across environments.

### 2. Shared Configuration Package

Create an internal npm package for consistent SDK setup across services:

```typescript
// packages/sentry-config/index.ts
import * as Sentry from '@sentry/node';

interface ServiceConfig {
  serviceName: string;
  dsn: string;
  environment?: string;
  version?: string;
  tracesSampleRate?: number;
  additionalIntegrations?: Sentry.Integration[];
}

export function initSentry(config: ServiceConfig) {
  Sentry.init({
    dsn: config.dsn,
    environment: config.environment || process.env.NODE_ENV || 'development',
    release: `${config.serviceName}@${config.version || 'unknown'}`,
    serverName: config.serviceName,

    // Organization defaults
    sendDefaultPii: false,
    debug: process.env.NODE_ENV !== 'production',
    maxBreadcrumbs: 50,

    tracesSampleRate: config.tracesSampleRate ?? 0.1,

    integrations: [
      ...(config.additionalIntegrations || []),
    ],

    // Organization-wide filtering
    ignoreErrors: [
      'ResizeObserver loop',
      'Non-Error promise rejection',
      /Loading chunk \d+ failed/,
    ],

    // Mandatory PII scrubbing
    beforeSend(event) {
      if (event.request?.headers) {
        delete event.request.headers['Authorization'];
        delete event.request.headers['Cookie'];
        delete event.request.headers['X-Api-Key'];
      }
      return event;
    },

    // Standard tags for all events
    initialScope: {
      tags: {
        service: config.serviceName,
        team: process.env.TEAM_NAME || 'unknown',
      },
    },
  });
}

// Usage in each service:
// initSentry({ serviceName: 'auth-service', dsn: process.env.SENTRY_DSN });
```

### 3. Global Error Handler Middleware

```typescript
// packages/sentry-config/middleware.ts
import * as Sentry from '@sentry/node';
import { Request, Response, NextFunction } from 'express';

export function sentryRequestMiddleware(serviceName: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    Sentry.setTag('route', req.route?.path || req.path);
    Sentry.setTag('method', req.method);

    if (req.user) {
      Sentry.setUser({
        id: req.user.id,
        // Never set email/ip in production
      });
    }

    next();
  };
}

// Domain-specific error classes
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public httpStatus: number = 500,
    public severity: Sentry.SeverityLevel = 'error'
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public fields: string[]) {
    super(message, 'VALIDATION_ERROR', 400, 'warning');
    this.name = 'ValidationError';
  }
}

export class ExternalServiceError extends AppError {
  constructor(service: string, statusCode: number, message: string) {
    super(`${service}: ${message}`, 'EXTERNAL_SERVICE_ERROR', 502, 'error');
    this.name = 'ExternalServiceError';
  }
}
```

### 4. Distributed Tracing Configuration

```typescript
// All services must propagate trace context

// Express service — automatic with SDK v8
// Just ensure all services use the same org and have tracing enabled

// For non-HTTP communication (message queues, gRPC):
import * as Sentry from '@sentry/node';

// Producer: attach trace headers to message
function publishMessage(queue: string, payload: object) {
  const activeSpan = Sentry.getActiveSpan();
  const headers: Record<string, string> = {};

  if (activeSpan) {
    headers['sentry-trace'] = Sentry.spanToTraceHeader(activeSpan);
    headers['baggage'] = Sentry.spanToBaggageHeader(activeSpan) || '';
  }

  messageQueue.publish(queue, { payload, headers });
}

// Consumer: continue trace from message headers
function onMessage(msg: { payload: object; headers: Record<string, string> }) {
  Sentry.continueTrace(
    {
      sentryTrace: msg.headers['sentry-trace'],
      baggage: msg.headers['baggage'],
    },
    () => {
      Sentry.startSpan(
        { name: `queue.process.${msg.payload.type}`, op: 'queue.task' },
        () => processMessage(msg.payload)
      );
    }
  );
}
```

### 5. Alert Hierarchy

```
Tier 1 — Critical (P0)
  Trigger: Error rate > 50/min OR crash-free sessions < 95%
  Action: PagerDuty → on-call engineer
  Response: 15 min acknowledge, 1 hour resolve

Tier 2 — Warning (P1)
  Trigger: New issue in production OR regression detected
  Action: Slack #alerts-production
  Response: Same business day

Tier 3 — Info (P2)
  Trigger: P95 latency > 2s OR error rate > 10/min
  Action: Slack #alerts-performance
  Response: Next sprint

Tier 4 — Low (P3)
  Trigger: New issue in staging
  Action: Slack #alerts-staging
  Response: Backlog triage
```

### 6. Issue Routing by Team

Configure ownership rules in **Project Settings > Ownership Rules**:

```
# Route by file path
path:src/payments/* #payments-team
path:src/auth/* #platform-team
path:src/api/* #backend-team

# Route by URL
url:*/api/v1/payments/* #payments-team
url:*/api/v1/users/* #platform-team

# Route by tag
tags.service:payment-api #payments-team
tags.service:auth-service #platform-team
```

### 7. Release Strategy

```
Release naming: {service}@{semver}+{git-sha-short}
Examples:
  api-gateway@2.1.0+abc1234
  web-app@3.5.2+def5678
  payment-api@1.8.0+ghi9012

Each service creates its own release in its own project.
Distributed traces link events across services automatically.
```

## Output
- Project structure following one-project-per-service pattern
- Shared configuration package enforcing organization defaults
- Domain-specific error classes with consistent tagging
- Distributed tracing configured across all services
- Alert hierarchy with team routing and escalation paths

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Cross-service traces not linking | Missing trace header propagation | Ensure `sentry-trace` and `baggage` headers forwarded |
| Alerts going to wrong team | Ownership rules not configured | Set up ownership rules in project settings |
| Inconsistent SDK config across services | No shared config package | Create and enforce shared configuration package |
| Alert fatigue | Too many low-priority alerts | Implement tiered alert hierarchy with appropriate thresholds |

## Resources
- [Best Practices](https://docs.sentry.io/product/issues/best-practices/)
- [Distributed Tracing](https://docs.sentry.io/product/performance/distributed-tracing/)
- [Ownership Rules](https://docs.sentry.io/product/issues/ownership-rules/)
- [Alerting Best Practices](https://docs.sentry.io/product/alerts/best-practices/)
