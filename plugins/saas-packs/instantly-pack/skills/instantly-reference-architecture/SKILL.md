---
name: instantly-reference-architecture
description: |
  Implement Instantly reference architecture with best-practice project layout.
  Use when designing new Instantly integrations, reviewing project structure,
  or establishing architecture standards for Instantly applications.
  Trigger with phrases like "instantly architecture", "instantly best practices",
  "instantly project structure", "how to organize instantly", "instantly layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, instantly]
---

# Instantly Reference Architecture

## Overview
Production-ready architecture patterns for Instantly integrations.

## Prerequisites
- Understanding of layered architecture
- Instantly SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-instantly-project/
├── src/
│   ├── instantly/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── instantly/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── instantly/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── instantly/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── instantly/
│   └── integration/
│       └── instantly/
├── config/
│   ├── instantly.development.json
│   ├── instantly.staging.json
│   └── instantly.production.json
└── docs/
    └── instantly/
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
│          Instantly Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/instantly/client.ts
export class InstantlyService {
  private client: InstantlyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: InstantlyConfig) {
    this.client = new InstantlyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('instantly');
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
// src/instantly/errors.ts
export class InstantlyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'InstantlyServiceError';
  }
}

export function wrapInstantlyError(error: unknown): InstantlyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/instantly/health.ts
export async function checkInstantlyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await instantlyClient.ping();
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
│ Instantly    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Instantly    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/instantly.ts
export interface InstantlyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadInstantlyConfig(): InstantlyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./instantly.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Instantly operations.

### Step 4: Configure Health Checks
Add health check endpoint for Instantly connectivity.

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
| Type errors | Missing types | Add Instantly types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/instantly/{handlers} src/services/instantly src/api/instantly
touch src/instantly/{client,config,types,errors}.ts
touch src/services/instantly/{index,sync,cache}.ts
```

## Resources
- [Instantly SDK Documentation](https://docs.instantly.com/sdk)
- [Instantly Best Practices](https://docs.instantly.com/best-practices)

## Flagship Skills
For multi-environment setup, see `instantly-multi-env-setup`.