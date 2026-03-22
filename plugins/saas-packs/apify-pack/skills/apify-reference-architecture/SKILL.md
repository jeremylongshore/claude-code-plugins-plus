---
name: apify-reference-architecture
description: |
  Implement Apify reference architecture with best-practice project layout.
  Use when designing new Apify integrations, reviewing project structure,
  or establishing architecture standards for Apify applications.
  Trigger with phrases like "apify architecture", "apify best practices",
  "apify project structure", "how to organize apify", "apify layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apify]
---

# Apify Reference Architecture

## Overview
Production-ready architecture patterns for Apify integrations.

## Prerequisites
- Understanding of layered architecture
- Apify SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-apify-project/
├── src/
│   ├── apify/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── apify/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── apify/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── apify/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── apify/
│   └── integration/
│       └── apify/
├── config/
│   ├── apify.development.json
│   ├── apify.staging.json
│   └── apify.production.json
└── docs/
    └── apify/
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
│          Apify Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/apify/client.ts
export class ApifyService {
  private client: ApifyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ApifyConfig) {
    this.client = new ApifyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('apify');
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
// src/apify/errors.ts
export class ApifyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ApifyServiceError';
  }
}

export function wrapApifyError(error: unknown): ApifyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/apify/health.ts
export async function checkApifyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await apifyClient.ping();
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
│ Apify    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Apify    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/apify.ts
export interface ApifyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadApifyConfig(): ApifyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./apify.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Apify operations.

### Step 4: Configure Health Checks
Add health check endpoint for Apify connectivity.

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
| Type errors | Missing types | Add Apify types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/apify/{handlers} src/services/apify src/api/apify
touch src/apify/{client,config,types,errors}.ts
touch src/services/apify/{index,sync,cache}.ts
```

## Resources
- [Apify SDK Documentation](https://docs.apify.com/sdk)
- [Apify Best Practices](https://docs.apify.com/best-practices)

## Flagship Skills
For multi-environment setup, see `apify-multi-env-setup`.