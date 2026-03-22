---
name: sentry-reference-architecture
description: |
  Implement Sentry reference architecture with best-practice project layout.
  Use when designing new Sentry integrations, reviewing project structure,
  or establishing architecture standards for Sentry applications.
  Trigger with phrases like "sentry architecture", "sentry best practices",
  "sentry project structure", "how to organize sentry", "sentry layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry Reference Architecture

## Overview
Production-ready architecture patterns for Sentry integrations.

## Prerequisites
- Understanding of layered architecture
- Sentry SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-sentry-project/
├── src/
│   ├── sentry/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── sentry/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── sentry/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── sentry/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── sentry/
│   └── integration/
│       └── sentry/
├── config/
│   ├── sentry.development.json
│   ├── sentry.staging.json
│   └── sentry.production.json
└── docs/
    └── sentry/
        ├── SETUP.md
        └── RUNBOOK.md
```

## Layer Architecture

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (Controllers, Routes, Webhooks)        │
├─────────────────────────────────────────┤
│           Service Layer                  │
│  (Business Logic, Orchestration)         │
├─────────────────────────────────────────┤
│          Sentry Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/sentry/client.ts
export class SentryService {
  private client: SentryClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SentryConfig) {
    this.client = new SentryClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('sentry');
  }

  async get(id: string): Promise<Resource> {
    return this.cache.getOrFetch(id, () =>
      this.monitor.track('get', () => this.client.get(id))
    );
  }
}
```

### Step 2: Error Boundary
```typescript
// src/sentry/errors.ts
export class SentryServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SentryServiceError';
  }
}

export function wrapSentryError(error: unknown): SentryServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/sentry/health.ts
export async function checkSentryHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await sentryClient.ping();
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
    };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}
```

## Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────┐
│   API       │
│   Gateway   │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│   Service   │───▶│   Cache     │
│   Layer     │    │   (Redis)   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ Sentry    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Sentry    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/sentry.ts
export interface SentryConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSentryConfig(): SentryConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./sentry.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Sentry operations.

### Step 4: Configure Health Checks
Add health check endpoint for Sentry connectivity.

## Output
- Structured project layout
- Client wrapper with caching
- Error boundary implemented
- Health checks configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns by layer |
| Config not loading | Wrong paths | Verify config file locations |
| Type errors | Missing types | Add Sentry types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/sentry/{handlers} src/services/sentry src/api/sentry
touch src/sentry/{client,config,types,errors}.ts
touch src/services/sentry/{index,sync,cache}.ts
```

## Resources
- [Sentry SDK Documentation](https://docs.sentry.com/sdk)
- [Sentry Best Practices](https://docs.sentry.com/best-practices)

## Flagship Skills
For multi-environment setup, see `sentry-multi-env-setup`.