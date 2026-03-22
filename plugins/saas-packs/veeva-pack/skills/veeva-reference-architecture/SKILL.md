---
name: veeva-reference-architecture
description: |
  Implement Veeva reference architecture with best-practice project layout.
  Use when designing new Veeva integrations, reviewing project structure,
  or establishing architecture standards for Veeva applications.
  Trigger with phrases like "veeva architecture", "veeva best practices",
  "veeva project structure", "how to organize veeva", "veeva layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva Reference Architecture

## Overview
Production-ready architecture patterns for Veeva integrations.

## Prerequisites
- Understanding of layered architecture
- Veeva SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-veeva-project/
├── src/
│   ├── veeva/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── veeva/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── veeva/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── veeva/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── veeva/
│   └── integration/
│       └── veeva/
├── config/
│   ├── veeva.development.json
│   ├── veeva.staging.json
│   └── veeva.production.json
└── docs/
    └── veeva/
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
│          Veeva Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/veeva/client.ts
export class VeevaService {
  private client: VeevaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: VeevaConfig) {
    this.client = new VeevaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('veeva');
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
// src/veeva/errors.ts
export class VeevaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'VeevaServiceError';
  }
}

export function wrapVeevaError(error: unknown): VeevaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/veeva/health.ts
export async function checkVeevaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await veevaClient.ping();
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
│ Veeva    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Veeva    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/veeva.ts
export interface VeevaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadVeevaConfig(): VeevaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./veeva.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Veeva operations.

### Step 4: Configure Health Checks
Add health check endpoint for Veeva connectivity.

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
| Type errors | Missing types | Add Veeva types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/veeva/{handlers} src/services/veeva src/api/veeva
touch src/veeva/{client,config,types,errors}.ts
touch src/services/veeva/{index,sync,cache}.ts
```

## Resources
- [Veeva SDK Documentation](https://docs.veeva.com/sdk)
- [Veeva Best Practices](https://docs.veeva.com/best-practices)

## Flagship Skills
For multi-environment setup, see `veeva-multi-env-setup`.