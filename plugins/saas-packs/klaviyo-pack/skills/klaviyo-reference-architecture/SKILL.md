---
name: klaviyo-reference-architecture
description: |
  Implement Klaviyo reference architecture with best-practice project layout.
  Use when designing new Klaviyo integrations, reviewing project structure,
  or establishing architecture standards for Klaviyo applications.
  Trigger with phrases like "klaviyo architecture", "klaviyo best practices",
  "klaviyo project structure", "how to organize klaviyo", "klaviyo layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo Reference Architecture

## Overview
Production-ready architecture patterns for Klaviyo integrations.

## Prerequisites
- Understanding of layered architecture
- Klaviyo SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-klaviyo-project/
├── src/
│   ├── klaviyo/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── klaviyo/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── klaviyo/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── klaviyo/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── klaviyo/
│   └── integration/
│       └── klaviyo/
├── config/
│   ├── klaviyo.development.json
│   ├── klaviyo.staging.json
│   └── klaviyo.production.json
└── docs/
    └── klaviyo/
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
│          Klaviyo Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/klaviyo/client.ts
export class KlaviyoService {
  private client: KlaviyoClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: KlaviyoConfig) {
    this.client = new KlaviyoClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('klaviyo');
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
// src/klaviyo/errors.ts
export class KlaviyoServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'KlaviyoServiceError';
  }
}

export function wrapKlaviyoError(error: unknown): KlaviyoServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/klaviyo/health.ts
export async function checkKlaviyoHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await klaviyoClient.ping();
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
│ Klaviyo    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Klaviyo    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/klaviyo.ts
export interface KlaviyoConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadKlaviyoConfig(): KlaviyoConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./klaviyo.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Klaviyo operations.

### Step 4: Configure Health Checks
Add health check endpoint for Klaviyo connectivity.

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
| Type errors | Missing types | Add Klaviyo types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/klaviyo/{handlers} src/services/klaviyo src/api/klaviyo
touch src/klaviyo/{client,config,types,errors}.ts
touch src/services/klaviyo/{index,sync,cache}.ts
```

## Resources
- [Klaviyo SDK Documentation](https://docs.klaviyo.com/sdk)
- [Klaviyo Best Practices](https://docs.klaviyo.com/best-practices)

## Flagship Skills
For multi-environment setup, see `klaviyo-multi-env-setup`.